// Constructive exact Hall relinking of two independent C7^10 codes.
// Given equally sized independent sets A,B, delete A∩B. The remaining
// conflict graph is bipartite; alpha(G[A∪B])=|A|+|A\B|-maximum_matching.
// A Hall deficiency thus produces a fully explicit improved 10D code.
#include <algorithm>
#include <array>
#include <chrono>
#include <cstdint>
#include <fstream>
#include <functional>
#include <iostream>
#include <numeric>
#include <queue>
#include <random>
#include <stdexcept>
#include <string>
#include <unordered_set>
#include <vector>
using namespace std;
constexpr int U=16807,M=243;
constexpr array<int,5>P{1,7,49,343,2401};
using Code=uint32_t;
struct Word{Code v;array<uint8_t,10>d;};
vector<Word>load(const string&p){
 ifstream f(p);if(!f)throw runtime_error("missing certificate");
 string s((istreambuf_iterator<char>(f)),{});vector<Word>a;
 for(size_t i=0;i+11<s.size();i++){
  if(s[i]!='"'||s[i+11]!='"')continue;
  Word w{};bool ok=true;
  for(int j=0;j<10;j++){char c=s[i+1+j];if(c<'0'||c>'6'){ok=false;break;}
   w.d[j]=c-'0';w.v=w.v*7+w.d[j];}
  if(ok){a.push_back(w);i+=11;}
 }
 unordered_set<Code>uniq;for(auto&w:a)if(!uniq.insert(w.v).second)throw runtime_error("duplicate source");
 if(a.empty())throw runtime_error("empty source");
 return a;
}
Word pack(const array<uint8_t,10>&d){Word x{};x.d=d;for(int i=0;i<10;i++)x.v=x.v*7+d[i];return x;}
string repr(Code x){string s(10,'0');for(int i=9;i>=0;i--){s[i]='0'+x%7;x/=7;}return s;}
vector<Word>moveCode(const vector<Word>&a,int trial){
 mt19937 rng(20261106u+trial*124021u);
 array<int,10>perm{};iota(perm.begin(),perm.end(),0);
 array<int,10>sgn{},shift{};sgn.fill(1);shift.fill(0);
 switch(trial%5){
  case 0:swap(perm[4],perm[5]);shift[0]=trial%7;shift[7]=(trial/3)%7;break;
  case 1:shuffle(perm.begin(),perm.end(),rng);for(int i=0;i<10;i++)shift[i]=rng()%7;break;
  case 2:for(int i=0;i<10;i++)perm[i]=i%2?5+i/2:i/2;
         for(int i=0;i<10;i++)sgn[i]=(i+trial)%3==0?-1:1;break;
  case 3:swap(perm[0],perm[9]);swap(perm[1],perm[8]);
         for(int i=0;i<10;i++)shift[i]=rng()%7;break;
  default:shuffle(perm.begin(),perm.end(),rng);
          for(int i=0;i<10;i++){sgn[i]=rng()%2?1:-1;shift[i]=rng()%7;}
 }
 vector<Word>b;b.reserve(a.size());
 for(auto&w:a){array<uint8_t,10>d{};for(int i=0;i<10;i++)d[i]=(sgn[i]*w.d[perm[i]]+shift[i]+14)%7;b.push_back(pack(d));}
 return b;
}
struct Conf5{
 vector<array<uint16_t,M>>neighbors;
 vector<array<uint64_t,(U+63)/64>>bit;
 Conf5():neighbors(U),bit(U){
  for(int x=0;x<U;x++){
   array<int,5>d{};for(int i=0;i<5;i++)d[i]=x/P[i]%7;
   for(int j=0;j<M;j++){
    int t=j,y=0;for(int i=0;i<5;i++){int o=t%3-1;t/=3;y+=((d[i]+o+7)%7)*P[i];}
    neighbors[x][j]=y;bit[x][y>>6]|=1ULL<<(y&63);
   }
  }
 }
 bool conf(int a,int b)const{return (bit[a][b>>6]>>(b&63))&1ULL;}
};
struct Hall{
 const Conf5&g;const vector<Word>&A;vector<Word>B;
 vector<Code>same;vector<pair<int,int>>L,R;vector<vector<int>>E;
 long long nedges=0;int maxdeg=0;
 Hall(const Conf5&gg,const vector<Word>&a,vector<Word>b):g(gg),A(a),B(move(b)){
  unordered_set<Code>sa,sb;sa.reserve(A.size()*2);sb.reserve(B.size()*2);
  for(auto&w:A)sa.insert(w.v);for(auto&w:B)sb.insert(w.v);
  if(sb.size()!=A.size())throw runtime_error("bad isometry");
  for(auto&w:A){if(sb.count(w.v))same.push_back(w.v);else L.emplace_back(w.v/U,w.v%U);}
  for(auto&w:B)if(!sa.count(w.v))R.emplace_back(w.v/U,w.v%U);
  if(L.size()!=R.size())throw runtime_error("unbalanced sets");
  vector<vector<int>>groups(U);for(int j=0;j<(int)R.size();j++)groups[R[j].first].push_back(j);
  E.resize(L.size());
  for(int i=0;i<(int)L.size();i++){
   auto[u,v]=L[i];auto&edge=E[i];
   for(auto q:g.neighbors[u])for(int j:groups[q])if(g.conf(v,R[j].second))edge.push_back(j);
   nedges+=edge.size();maxdeg=max(maxdeg,(int)edge.size());
  }
 }
 int match(vector<int>&mateL,vector<int>&mateR){
  int n=L.size();mateL.assign(n,-1);mateR.assign(n,-1);
  vector<int>dist(n);
  function<bool(int)>augment=[&](int i){
   for(int j:E[i]){int k=mateR[j];if(k<0||(dist[k]==dist[i]+1&&augment(k))){
    mateL[i]=j;mateR[j]=i;return true;}}
   dist[i]=-1;return false;
  };
  int matched=0;
  for(;;){
   fill(dist.begin(),dist.end(),-1);queue<int>q;
   for(int i=0;i<n;i++)if(mateL[i]<0){dist[i]=0;q.push(i);}
   bool found=false;
   while(!q.empty()){
    int i=q.front();q.pop();
    for(int j:E[i]){int k=mateR[j];if(k<0)found=true;
     else if(dist[k]<0){dist[k]=dist[i]+1;q.push(k);}}
   }
   if(!found)break;
   for(int i=0;i<n;i++)if(mateL[i]<0&&augment(i))matched++;
  }
  return matched;
 }
 vector<Code>witness(const vector<int>&mateL,const vector<int>&mateR,int matched){
  int n=L.size();vector<char>visL(n),visR(n);queue<int>q;
  for(int i=0;i<n;i++)if(mateL[i]<0){visL[i]=1;q.push(i);}
  while(!q.empty()){
   int i=q.front();q.pop();
   for(int j:E[i]){
    if(mateL[i]==j||visR[j])continue;
    visR[j]=1;int k=mateR[j];
    if(k>=0&&!visL[k]){visL[k]=1;q.push(k);}
   }
  }
  vector<Code>out=same;
  for(int i=0;i<n;i++)if(visL[i])out.push_back((Code)L[i].first*U+L[i].second);
  for(int j=0;j<n;j++)if(!visR[j])out.push_back((Code)R[j].first*U+R[j].second);
  if(out.size()!=A.size()+n-matched)throw runtime_error("invalid gain count");
  for(int i=0;i<n;i++)if(visL[i])for(int j:E[i])if(!visR[j])throw runtime_error("cross conflict");
  sort(out.begin(),out.end());
  if(adjacent_find(out.begin(),out.end())!=out.end())throw runtime_error("duplicate witness");
  return out;
 }
};
int main(int argc,char**argv)try{
 if(argc!=5&&argc!=6)throw runtime_error("usage: first.json start count output_dir [second.json]");
 auto A=load(argv[1]);auto B=argc==6?load(argv[5]):A;
 if(A.size()!=B.size())throw runtime_error("source sizes differ");
 int first=stoi(argv[2]),count=stoi(argv[3]);string dir=argv[4];Conf5 g;
 for(int t=first;t<first+count;t++){
  auto start=chrono::steady_clock::now();Hall h(g,A,moveCode(B,t));
  vector<int>ma,mb;int match=h.match(ma,mb),gain=int(h.L.size())-match;
  auto seconds=chrono::duration<double>(chrono::steady_clock::now()-start).count();
  cout<<"TRIAL "<<t<<" overlap="<<h.same.size()<<" left="<<h.L.size()
      <<" conflicts="<<h.nedges<<" degree_max="<<h.maxdeg
      <<" gain="<<gain<<" seconds="<<seconds<<endl;
  if(gain>0){
   auto cert=h.witness(ma,mb,match);
   ofstream f(dir+"/certificate.json");f<<"{\"points\":[";
   for(size_t k=0;k<cert.size();k++)f<<(k?",":"")<<'"'<<repr(cert[k])<<'"';f<<"]}\n";
   cout<<"FOUND "<<cert.size()<<" trial="<<t<<endl;return 0;
  }
 }
 cout<<"NONE trials="<<count<<endl;
}catch(const exception&e){cerr<<"ERROR "<<e.what()<<endl;return 1;}
