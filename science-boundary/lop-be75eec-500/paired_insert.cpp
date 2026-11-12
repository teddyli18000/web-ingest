#include <bits/stdc++.h>
using namespace std;
static constexpr int N=500;
static int W[N][N],D[N][N];
using Perm=array<int,N>;
struct Insertion{int i,j,gain;};
static mutex mx;
static atomic<long long> tested{0}, positives{0};
static long long best;
static atomic<long long> published_best{0};
static Perm best_order;
static string destination;
static chrono::steady_clock::time_point deadline;
long long score(const Perm &p){
  long long s=0;for(int i=0;i<N;i++)for(int j=i+1;j<N;j++)s+=W[p[i]][p[j]];
  return s;
}
void insert(Perm &p,int i,int j){
  int v=p[i];
  if(i<j)for(int t=i;t<j;t++)p[t]=p[t+1];
  else for(int t=i;t>j;t--)p[t]=p[t-1];
  p[j]=v;
}
vector<Insertion> insertion_moves(const Perm &p){
  vector<Insertion> moves;
  moves.reserve(N*(N-1));
  for(int i=0;i<N;i++){
    int v=p[i],gain=0;
    for(int j=i-1;j>=0;j--){gain+=D[v][p[j]];if(j<i-1)moves.push_back({i,j,gain});}
    gain=0;
    for(int j=i+1;j<N;j++){gain-=D[v][p[j]];moves.push_back({i,j,gain});}
  }
  return moves;
}
pair<int,Insertion> best_follow_up(const Perm &p){
  int max_gain=0;Insertion best_move{-1,-1,0};
  for(int i=0;i<N;i++){
    int v=p[i],g=0;
    for(int j=i-1;j>=0;j--){
      g+=D[v][p[j]];
      if(g>max_gain){max_gain=g;best_move={i,j,g};}
    }
    g=0;
    for(int j=i+1;j<N;j++){
      g-=D[v][p[j]];
      if(g>max_gain){max_gain=g;best_move={i,j,g};}
    }
  }
  return {max_gain,best_move};
}
int descent(Perm &p){
  int steps=0;
  for(;;){
    auto [gain,m]=best_follow_up(p);
    if(gain==0)return steps;
    insert(p,m.i,m.j);
    steps++;
  }
}
void publish(const Perm &p,long long s,int first_gain,int second_gain,int epoch){
  lock_guard<mutex> lock(mx);
  if(s<=best)return;
  assert(score(p)==s);
  best=s;published_best.store(s);best_order=p;positives++;
  string tmp=destination+".tmp";
  {
    ofstream out(tmp);out<<"{\"order\":[";
    for(int i=0;i<N;i++){if(i)out<<",";out<<p[i];}
    out<<"]}";
  }
  if(rename(tmp.c_str(),destination.c_str()))throw runtime_error("rename failed");
  cerr<<"RECORD "<<s<<" epoch="<<epoch<<" pair_gain="<<(first_gain+second_gain)
      <<" tested="<<tested.load()<<'\n';
}
void evaluate(const Perm &base,long long base_score,Insertion first,int epoch){
  Perm candidate=base;
  insert(candidate,first.i,first.j);
  auto [gain,second]=best_follow_up(candidate);
  tested++;
  if(first.gain+gain<=0)return;
  insert(candidate,second.i,second.j);
  assert(score(candidate)==base_score+first.gain+gain);
  descent(candidate);
  publish(candidate,score(candidate),first.gain,gain,epoch);
}
int main(int argc,char **argv){
  if(argc<6){cerr<<"usage: pairs matrix.txt seed.txt output.json seconds threads"<<endl;return 2;}
  ifstream input(argv[1]);int n;input>>n;assert(n==N);
  for(int i=0;i<N;i++)for(int j=0;j<N;j++)input>>W[i][j];
  for(int i=0;i<N;i++)for(int j=0;j<N;j++)D[i][j]=W[i][j]-W[j][i];
  ifstream seed(argv[2]);for(int &x:best_order)seed>>x;
  best=score(best_order);published_best.store(best);destination=argv[3];
  int seconds=atoi(argv[4]),cores=atoi(argv[5]);
  deadline=chrono::steady_clock::now()+chrono::seconds(seconds);
  cerr<<"BASE "<<best<<'\n';
  mt19937_64 rng(20261112);
  for(int epoch=0;chrono::steady_clock::now()<deadline;epoch++){
    Perm base;long long base_score;
    {lock_guard<mutex> lock(mx);base=best_order;base_score=best;}
    vector<Insertion> moves=insertion_moves(base);
    // Only the leading 40,000 low-loss moves are scanned per epoch.
    shuffle(moves.begin(),moves.end(),rng);
    int scan_limit=min((int)moves.size(),40000);
    nth_element(moves.begin(),moves.begin()+scan_limit,moves.end(),
       [](const Insertion &a,const Insertion &b){return a.gain>b.gain;});
    moves.resize(scan_limit);
    sort(moves.begin(),moves.end(),[](const Insertion &a,const Insertion &b){return a.gain>b.gain;});
    cerr<<"EPOCH "<<epoch<<" base="<<base_score<<" top_loss="<<-moves.front().gain
        <<" end_loss="<<-moves.back().gain<<" candidates="<<moves.size()<<'\n';
    atomic<int> counter{0};
    auto work=[&](){
      while(chrono::steady_clock::now()<deadline){
        int idx=counter.fetch_add(1);
        if(idx>=(int)moves.size())break;
        if(published_best.load()>base_score)break;
        evaluate(base,base_score,moves[idx],epoch);
      }
    };
    vector<thread> threads;
    for(int t=0;t<cores;t++)threads.emplace_back(work);
    for(auto &t:threads)t.join();
    cerr<<"EPOCH-END "<<epoch<<" checked="<<counter<<" best="<<best<<'\n';
    if(best==base_score && counter>=(int)moves.size())break;
  }
  cerr<<"FINAL "<<best<<" pairs="<<tested<<" records="<<positives<<'\n';
  cout<<best<<'\n';
}
