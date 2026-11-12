#include <bits/stdc++.h>
using namespace std;
// Exact reordering of 12–20 variable-size contiguous blocks, selected from
// windows of 40–500 vertices. The globally optimal block permutation is
// found by subset DP on aggregated inter-block weights. This coordinates
// hundreds of vertex positions without requiring a 500-item exact solver.
static constexpr int N=500;
int W[N][N],D[N][N];
using Perm=array<int,N>;
mutex mu;
Perm record_order;
long long record_score;
string output_path;
chrono::steady_clock::time_point deadline;
atomic<long long> trials{0}, positive{0}, records{0};
long long score(const Perm &p){
  long long s=0;
  for(int i=0;i<N;i++)for(int j=i+1;j<N;j++)s+=W[p[i]][p[j]];
  return s;
}
void move(Perm &p,int i,int j){
  int v=p[i];
  if(i<j)for(int a=i;a<j;a++)p[a]=p[a+1];
  else for(int a=i;a>j;a--)p[a]=p[a-1];
  p[j]=v;
}
int descent(Perm &p){
  int steps=0;
  for(;;){
    int best=0,bi=-1,bj=-1;
    for(int i=0;i<N;i++){
      int v=p[i],g=0;
      for(int j=i-1;j>=0;j--){
        g+=D[v][p[j]];
        if(g>best){best=g;bi=i;bj=j;}
      }
      g=0;
      for(int j=i+1;j<N;j++){
        g-=D[v][p[j]];
        if(g>best){best=g;bi=i;bj=j;}
      }
    }
    if(best==0)break;
    move(p,bi,bj);steps++;
  }
  return steps;
}
void publish(const Perm &p,long long value,int worker){
  lock_guard<mutex> guard(mu);
  if(value<=record_score)return;
  assert(score(p)==value);
  record_score=value;record_order=p;records++;
  string tmp=output_path+".tmp"+to_string(worker);
  ofstream f(tmp);f<<"{\"order\":[";
  for(int i=0;i<N;i++){if(i)f<<',';f<<p[i];}
  f<<"]}";f.close();
  rename(tmp.c_str(),output_path.c_str());
  cerr<<"RECORD "<<value<<" worker="<<worker<<" trial="<<trials.load()<<'\n';
}
struct Answer{long long gain;Perm perm;};
Answer exact_block_window(const Perm &p,int left,int length,int count,mt19937_64 &rng){
  vector<int> cuts{0,length};
  while((int)cuts.size()<count+1){
    int c=1+rng()%(length-1);
    if(find(cuts.begin(),cuts.end(),c)==cuts.end())cuts.push_back(c);
  }
  sort(cuts.begin(),cuts.end());
  vector<vector<int>> blocks(count);
  for(int b=0;b<count;b++){
    for(int t=left+cuts[b];t<left+cuts[b+1];t++)blocks[b].push_back(p[t]);
  }
  int A[20][20]{};
  for(int a=0;a<count;a++)for(int b=0;b<count;b++)if(a!=b){
    int s=0;
    for(int v:blocks[a])for(int w:blocks[b])s+=W[v][w];
    A[a][b]=s;
  }
  long long old=0;
  for(int a=0;a<count;a++)for(int b=a+1;b<count;b++)old+=A[a][b];
  int states=1<<count,full=states-1;
  vector<int> Q(count*states);
  for(int v=0;v<count;v++){
    int *row=Q.data()+v*states;
    for(int mask=1;mask<states;mask++){
      int bit=__builtin_ctz((unsigned)mask);
      row[mask]=row[mask&(mask-1)]+A[bit][v];
    }
  }
  vector<long long> dp(states,LLONG_MIN/4);
  vector<unsigned char> parent(states);
  dp[0]=0;
  for(int mask=0;mask<full;mask++){
    long long current=dp[mask];
    int remain=full^mask;
    while(remain){
      int b=__builtin_ctz((unsigned)remain);
      remain&=remain-1;
      int next=mask|(1<<b);
      long long value=current+Q[b*states+mask];
      if(value>dp[next]){dp[next]=value;parent[next]=b;}
    }
  }
  long long gain=dp[full]-old;
  Perm candidate=p;
  if(gain>0){
    vector<int> order;
    int mask=full;
    while(mask){
      int b=parent[mask];
      order.push_back(b);
      mask^=(1<<b);
    }
    reverse(order.begin(),order.end());
    int t=left;
    for(int b:order)for(int v:blocks[b])candidate[t++]=v;
    assert(t==left+length);
  }
  return {gain,candidate};
}
void worker(int id){
  mt19937_64 rng(733137+id*1000003);
  Perm local;
  {
    lock_guard<mutex> guard(mu);
    local=record_order;
  }
  long long current_score=score(local);
  int stale=0,count=0;
  while(chrono::steady_clock::now()<deadline){
    if(++count%210==0){
      lock_guard<mutex> guard(mu);
      local=record_order;current_score=record_score;
    }
    int type=rng()%7;
    int length;
    if(type==0)length=40+rng()%50;
    else if(type==1)length=90+rng()%80;
    else if(type==2)length=170+rng()%120;
    else if(type==3)length=290+rng()%180;
    else if(type==4)length=N;
    else if(type==5)length=60+rng()%160;
    else length=120+rng()%280;
    int left=rng()%(N-length+1);
    int blocks=12+rng()%9; // 12–20 blocks
    Answer result=exact_block_window(local,left,length,blocks,rng);
    trials++;
    if(result.gain>0){
      current_score+=result.gain;local=result.perm;
      assert(score(local)==current_score);
      descent(local);current_score=score(local);
      positive++;stale=0;
      publish(local,current_score,id);
    }else{
      stale++;
    }
    if(stale>120){
      int kicks=2+rng()%13;
      for(int q=0;q<kicks;q++)move(local,rng()%N,rng()%N);
      descent(local);
      current_score=score(local);
      stale=0;
    }
  }
}
int main(int argc,char **argv){
  if(argc!=6){cerr<<"usage: blocks matrix.txt seed.txt output.json seconds threads\n";return 2;}
  ifstream f(argv[1]);int n;f>>n;assert(n==N);
  for(int i=0;i<N;i++)for(int j=0;j<N;j++)f>>W[i][j];
  for(int i=0;i<N;i++)for(int j=0;j<N;j++)D[i][j]=W[i][j]-W[j][i];
  ifstream in(argv[2]);
  for(int &v:record_order)in>>v;
  record_score=score(record_order);output_path=argv[3];
  cerr<<"START "<<record_score<<'\n';
  deadline=chrono::steady_clock::now()+chrono::seconds(atoi(argv[4]));
  int nthreads=atoi(argv[5]);
  vector<thread> workers;
  for(int i=0;i<nthreads;i++)workers.emplace_back(worker,i);
  for(auto &w:workers)w.join();
  cerr<<"FINAL "<<record_score<<" trials="<<trials<<" positives="<<positive<<" records="<<records<<'\n';
  cout<<record_score<<'\n';
}
