// Ejection-chain beam search for a genuinely new 269-block C(15,9,7) covering.
// Start with 269 blocks, allow temporary coverage holes, and recursively change
// which block causes the current defects. Explore coupled swaps, not fixed releases.
#include <bits/stdc++.h>
using namespace std;
using U=uint64_t;
constexpr int N=15;
vector<int> b9,b7;
int ix9[1<<N],ix7[1<<N];
vector<array<int,36>> cov;
vector<array<int,28>> hits;
vector<U> zobrist;
vector<uint8_t> initial;
mt19937_64 rng;
string best_path;
int bestmiss=1000;
struct State {vector<int> bs;U hash;int holes,dist;double rank;};

void build(){
  fill(begin(ix9),end(ix9),-1);fill(begin(ix7),end(ix7),-1);
  for(int m=0;m<(1<<N);m++){
    int k=__builtin_popcount((unsigned)m);
    if(k==9){ix9[m]=b9.size();b9.push_back(m);}
    if(k==7){ix7[m]=b7.size();b7.push_back(m);}
  }
  hits.resize(b7.size());cov.resize(b9.size());vector<int> cn(b7.size());
  for(int j=0;j<(int)b9.size();j++){
    int q=0;
    for(int t=b9[j];t;t=(t-1)&b9[j]){
      if(__builtin_popcount((unsigned)t)==7){
        int i=ix7[t];cov[j][q++]=i;hits[i][cn[i]++]=j;
      }
    }
    assert(q==36);
  }
  for(int n:cn)assert(n==28);
  zobrist.resize(b9.size());for(auto& x:zobrist)x=rng();
}
int hole_count(const vector<int>& bs){
  vector<int> c(b7.size());for(int b:bs)for(int i:cov[b])c[i]++;
  return count(c.begin(),c.end(),0);
}
void save(const vector<int>& ids,const string& path){
  ofstream f(path);f<<"{\"blocks\":[";
  for(int k=0;k<(int)ids.size();k++){
    if(k)f<<",";
    f<<"[";int p=0;
    for(int i=0;i<N;i++)if(b9[ids[k]]>>i&1){if(p++)f<<",";f<<i;}
    f<<"]";
  }
  f<<"]}";
}
void expand(const State& parent,vector<State>& next,int maxholes,
            int per_parent,unordered_set<U>& seen){
  vector<int> c(b7.size()),owner(b7.size(),-1),exclusive(b9.size()),rescue(b9.size());
  vector<uint8_t> active(b9.size());
  for(int b:parent.bs){active[b]=1;for(int t:cov[b])c[t]++;}
  vector<int> missing;
  for(int t=0;t<(int)c.size();t++)if(!c[t])missing.push_back(t);
  for(int b:parent.bs)for(int t:cov[b])if(c[t]==1){exclusive[b]++;owner[t]=b;}
  assert((int)missing.size()==parent.holes);
  shuffle(missing.begin(),missing.end(),rng);
  if(missing.size()>4)missing.resize(4);
  struct Choice {int a,b,holes,dist;double rank;};
  vector<Choice> options;
  unordered_set<int> examined;
  for(int target:missing)for(int a:hits[target]){
    if(active[a]||!examined.insert(a).second)continue;
    int made=0;
    for(int t:cov[a])if(c[t]==0)made++;else if(c[t]==1)rescue[owner[t]]++;
    for(int b:parent.bs){
      int nh=parent.holes-made+exclusive[b]-rescue[b];
      if(nh<=maxholes){
        int dist=parent.dist+(initial[a]==0)-(initial[b]==0);
        double rank=100.*nh-5.*min(dist,20)+.5*(rng()%50);
        options.push_back({a,b,nh,dist,rank});
      }
    }
    for(int t:cov[a])if(c[t]==1)rescue[owner[t]]--;
  }
  sort(options.begin(),options.end(),[](auto& x,auto& y){return x.rank<y.rank;});
  int produced=0;
  for(auto q:options){
    U h=parent.hash^zobrist[q.a]^zobrist[q.b];
    if(!seen.insert(h).second)continue;
    State s=parent;s.hash=h;s.holes=q.holes;s.dist=q.dist;s.rank=q.rank;
    *find(s.bs.begin(),s.bs.end(),q.b)=q.a;
    assert(hole_count(s.bs)==s.holes);
    if(s.holes<bestmiss){
      bestmiss=s.holes;
      save(s.bs,best_path);
      cerr<<"IMPROVEMENT holes="<<bestmiss<<" distance="<<q.dist<<"\n";
    }
    next.push_back(move(s));
    if(++produced>=per_parent)break;
  }
}
int main(int argc,char**argv){
  if(argc!=7){cerr<<"usage: beam input-plain-blocks output.json seconds seed width maxholes\n";return 2;}
  rng.seed(stoull(argv[4]));build();best_path=argv[2];
  ifstream f(argv[1]);string line;vector<int> source;
  while(getline(f,line)){
    if(line.empty())continue;
    istringstream ss(line);int p,mask=0,n=0;
    while(ss>>p){mask|=1<<p;n++;}
    assert(n==9&&ix9[mask]>=0);source.push_back(ix9[mask]);
  }
  assert(source.size()==270);
  initial.assign(b9.size(),0);for(int b:source)initial[b]=1;
  vector<int> coverage(b7.size());
  for(int b:source)for(int t:cov[b])coverage[t]++;
  vector<int> ranked=source;
  sort(ranked.begin(),ranked.end(),[&](int a,int b){
    int ua=0,ub=0;
    for(int t:cov[a])ua+=(coverage[t]==1);
    for(int t:cov[b])ub+=(coverage[t]==1);
    return ua<ub;
  });
  auto start=chrono::steady_clock::now();
  const int width=atoi(argv[5]),maxholes=atoi(argv[6]);
  long rounds=0;
  while(chrono::duration<double>(chrono::steady_clock::now()-start).count()<atof(argv[3])){
    int drop=ranked[rng()%32];
    vector<int> base=source;base.erase(find(base.begin(),base.end(),drop));
    U hash=0;for(int b:base)hash^=zobrist[b];
    int miss=hole_count(base);
    if(miss<bestmiss){bestmiss=miss;save(base,best_path);}
    State seed{base,hash,miss,0,0};
    unordered_set<U> seen;seen.insert(hash);
    vector<State> beam={seed};
    for(int depth=0;depth<18&&!beam.empty();depth++){
      vector<State> candidates;
      for(const auto& s:beam)expand(s,candidates,maxholes,8,seen);
      sort(candidates.begin(),candidates.end(),[](auto& a,auto& b){return a.rank<b.rank;});
      if(candidates.size()>(size_t)width)candidates.resize(width);
      beam=move(candidates);
      if(bestmiss==0){
        cout<<"FOUND 269 verified-incrementally\n";
        return 0;
      }
    }
    if(++rounds%100==0)cerr<<"PROGRESS rounds="<<rounds<<" bestholes="<<bestmiss<<"\n";
  }
  cout<<"FINISHED rounds="<<rounds<<" bestholes="<<bestmiss<<"\n";
}
