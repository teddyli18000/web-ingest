#include <bits/stdc++.h>
using namespace std;

// Exact sparse-hole neighborhood: choose k occupied ranks and jointly reassign
// all k vertices to those k ranks, leaving every other rank fixed.  Dynamic
// programming over subsets gives an exact O(k 2^k + kn) optimizer of that
// neighborhood; the search varies the holes and the basin between calls.

static constexpr int N=500;
static int W[N][N],D[N][N];
using Perm=array<int,N>;
struct Result {long long gain; Perm order; bool altered;};
static mutex best_mutex;
static long long best_score;
static Perm best_perm;
static string output_file;
static chrono::steady_clock::time_point stop_at;
static atomic<long long> tried{0}, improved{0}, equality{0}, best_updates{0};

long long score(const Perm &p){
  long long total=0;
  for(int i=0;i<N;i++)for(int j=i+1;j<N;j++)total+=W[p[i]][p[j]];
  return total;
}
void insert_move(Perm &p,int i,int j){
  int v=p[i];
  if(i<j)for(int t=i;t<j;t++)p[t]=p[t+1];
  else for(int t=i;t>j;t--)p[t]=p[t-1];
  p[j]=v;
}
int insertion_descent(Perm &p,mt19937_64 &rng){
  int iters=0;
  for(;;){
    int gain_best=0,a=-1,b=-1,first=rng()%N;
    for(int step=0;step<N;step++){
      int i=(first+step)%N,v=p[i],g=0;
      for(int j=i-1;j>=0;j--){
        int u=p[j];g+=D[v][u];
        if(g>gain_best){gain_best=g;a=i;b=j;}
      }
      g=0;
      for(int j=i+1;j<N;j++){
        int u=p[j];g-=D[v][u];
        if(g>gain_best){gain_best=g;a=i;b=j;}
      }
    }
    if(gain_best==0)return iters;
    insert_move(p,a,b);iters++;
  }
}
void publish(const Perm &p,long long s,int worker,int attempt){
  lock_guard<mutex> lock(best_mutex);
  if(s<=best_score)return;
  long long direct=score(p);
  if(direct!=s)throw runtime_error("incorrect incremental score");
  best_score=s;best_perm=p;++best_updates;
  string temporary=output_file+".tmp"+to_string(worker);
  {
    ofstream out(temporary);
    out<<"{\"order\":[";
    for(int i=0;i<N;i++){if(i)out<<',';out<<p[i];}
    out<<"]}";
  }
  if(rename(temporary.c_str(),output_file.c_str()))throw runtime_error("rename failure");
  cerr<<"RECORD "<<s<<" w="<<worker<<" attempt="<<attempt<<" total="<<tried.load()<<'\n';
}
void choose_positions(int mode,int k,const Perm &p,mt19937_64 &rng,vector<int> &pos){
  pos.clear();
  if(mode==0){
    int left=rng()%(N-k+1);
    for(int i=0;i<k;i++)pos.push_back(left+i);
  }else if(mode==1 || mode==2){
    int clusters=mode==1?2:3;
    vector<int> anchors;
    for(int c=0;c<clusters;c++)anchors.push_back(rng()%(N-32));
    int i=0;
    for(int c=0;c<clusters;c++){
      int num=k/clusters+(c<k%clusters);
      for(int t=0;t<num;t++)pos.push_back(anchors[c]+t);
      i+=num;
    }
  }else if(mode==3){
    int center=rng()%N,window=30+rng()%200;
    int left=max(0,min(center-window/2,N-window));
    vector<int> pool;
    for(int i=left;i<left+window;i++)pool.push_back(i);
    shuffle(pool.begin(),pool.end(),rng);
    pos.assign(pool.begin(),pool.begin()+k);
  }else if(mode==4){
    int seed=rng()%N;
    pos.push_back(seed);
    vector<pair<int,int>> weights;
    for(int i=0;i<N;i++)if(i!=seed){
      int dist=abs(i-seed);
      int priority=abs(D[p[i]][p[seed]])*8/(1+dist/20);
      weights.emplace_back(priority+int(rng()%1200),i);
    }
    nth_element(weights.begin(),weights.begin()+k-1,weights.end(),greater<>());
    for(int t=0;t<k-1;t++)pos.push_back(weights[t].second);
  }else if(mode==5){
    // Short nonconsecutive positions, heavily interleaved with fixed vertices.
    int center=rng()%N,span=k+10+rng()%100;
    span=min(span,N);
    int left=min(max(0,center-span/2),N-span);
    vector<int> pool;
    for(int i=left;i<left+span;i++)pool.push_back(i);
    shuffle(pool.begin(),pool.end(),rng);
    pos.assign(pool.begin(),pool.begin()+k);
  }else{
    vector<int> pool(N);iota(pool.begin(),pool.end(),0);
    for(int t=0;t<k;t++){int j=t+rng()%(N-t);swap(pool[t],pool[j]);}
    pos.assign(pool.begin(),pool.begin()+k);
  }
  sort(pos.begin(),pos.end());pos.erase(unique(pos.begin(),pos.end()),pos.end());
  while((int)pos.size()<k){
    int a=rng()%N;
    if(!binary_search(pos.begin(),pos.end(),a))pos.insert(lower_bound(pos.begin(),pos.end(),a),a);
  }
}
Result exact_holes(const Perm &p,const vector<int> &positions){
  int k=positions.size(),states=1<<k,full=states-1;
  vector<int> vertices(k);
  for(int t=0;t<k;t++)vertices[t]=p[positions[t]];
  // U[t][v] is the objective contribution between chosen vertex v in
  // chosen slot t and every non-chosen vertex.
  vector<int> U(k*k),taken(N,0);
  for(int x:positions)taken[x]=1;
  for(int v=0;v<k;v++){
    int x=vertices[v],position=0,gain=0;
    for(int i=0;i<N;i++)if(!taken[i])gain+=W[x][p[i]];
    for(int t=0;t<k;t++){
      while(position<positions[t]){
        if(!taken[position])gain+=W[p[position]][x]-W[x][p[position]];
        position++;
      }
      U[t*k+v]=gain;
    }
  }
  int64_t old=0;
  for(int t=0;t<k;t++){
    old+=U[t*k+t];
    for(int u=0;u<t;u++)old+=W[vertices[u]][vertices[t]];
  }
  // Q[v][mask] = contribution if vertex v is placed after subset mask.
  vector<int> Q(k*states);
  for(int v=0;v<k;v++){
    int *q=Q.data()+v*states,vertex=vertices[v];
    for(int mask=1;mask<states;mask++){
      int bit=__builtin_ctz(unsigned(mask)),prev=mask&(mask-1);
      q[mask]=q[prev]+W[vertices[bit]][vertex];
    }
  }
  vector<int64_t> dp(states,LLONG_MIN/4);
  vector<unsigned char> pred(states);
  dp[0]=0;
  for(int mask=0;mask<states-1;mask++){
    int t=__builtin_popcount(unsigned(mask));
    int64_t base=dp[mask];
    int rest=full^mask;
    while(rest){
      int v=__builtin_ctz(unsigned(rest));rest&=rest-1;
      int next=mask|(1<<v);
      int64_t value=base+U[t*k+v]+Q[v*states+mask];
      if(value>dp[next]){dp[next]=value;pred[next]=v;}
    }
  }
  int64_t gain=dp[full]-old;
  Perm candidate=p;
  int mask=full;
  for(int t=k-1;t>=0;t--){
    int v=pred[mask];
    candidate[positions[t]]=vertices[v];
    mask^=1<<v;
  }
  return {gain,candidate,candidate!=p};
}
void worker(int id){
  mt19937_64 rng(981375+id*129913);
  Perm local;
  {
    lock_guard<mutex> lk(best_mutex);
    local=best_perm;
  }
  long long local_score=score(local);
  int stale=0,attempt=0;
  while(chrono::steady_clock::now()<stop_at){
    attempt++;tried++;
    if(attempt%127==0){
      lock_guard<mutex> lk(best_mutex);
      local=best_perm;local_score=best_score;
    }
    int mode=(attempt/3+id)%7, k=13+int(rng()%7);
    if(mode==0)k=14+int(rng()%6);
    vector<int> positions;
    choose_positions(mode,k,local,rng,positions);
    Result result=exact_holes(local,positions);
    long long new_score=local_score+result.gain;
    if(result.gain>0){
      local=result.order;local_score=new_score;stale=0;improved++;
      publish(local,new_score,id,attempt);
    }else{
      if(result.gain==0 && result.altered && rng()%10==0){
        local=result.order;equality++;
      }
      stale++;
    }
    // For strong BKS, allow rare basin jumps while preserving the global best.
    if(stale>=75){
      int jumps=1+int(rng()%8);
      for(int t=0;t<jumps;t++)insert_move(local,rng()%N,rng()%N);
      insertion_descent(local,rng);
      local_score=score(local);
      stale=0;
    }
  }
}
int main(int argc,char **argv){
  if(argc<6){cerr<<"usage: exact matrix.txt baseline.txt output.json seconds threads"<<endl;return 2;}
  ifstream in(argv[1]);int n;in>>n;assert(n==N);
  for(int i=0;i<N;i++)for(int j=0;j<N;j++)in>>W[i][j];
  for(int i=0;i<N;i++)for(int j=0;j<N;j++)D[i][j]=W[i][j]-W[j][i];
  ifstream start(argv[2]);for(int &x:best_perm)start>>x;
  best_score=score(best_perm);output_file=argv[3];
  cerr<<"START "<<best_score<<'\n';
  stop_at=chrono::steady_clock::now()+chrono::seconds(atoi(argv[4]));
  int threads=atoi(argv[5]);
  vector<thread> workers;
  for(int i=0;i<threads;i++)workers.emplace_back(worker,i);
  for(auto &w:workers)w.join();
  cerr<<"FINAL "<<best_score<<" trials="<<tried<<" exact_improvements="<<improved
      <<" ties="<<equality<<" records="<<best_updates<<'\n';
  cout<<best_score<<'\n';
}
