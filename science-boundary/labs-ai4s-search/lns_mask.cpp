// Exact full-environment restricted LABS LNS; not the isolated-subsystem method of Lau/Gangat 2026.
// Compile: g++ -O3 -std=c++17 -Wall -Wextra lns_mask.cpp -o lns_mask
// Run: ./lns_mask --selftest OR ./lns_mask OUT.csv N STAGE BASES SEED M MASKS [record]
#include <algorithm>
#include <cassert>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <numeric>
#include <random>
#include <set>
#include <string>
#include <tuple>
#include <vector>
using namespace std;
using clk=chrono::steady_clock;
using ns=chrono::duration<double>;
struct L {
 int n=0,e=0;vector<int> s,c;
 L()=default;
 explicit L(vector<int> v): n((int)v.size()),s(move(v)),c(n,0) {
  for(int k=1;k<n;k++) {for(int i=0;i<n-k;i++)c[k]+=s[i]*s[i+k];e+=c[k]*c[k];}
 }
 int delta(int p)const {
  int de=0;
  for(int k=1;k<n;k++){
   int t=(p>=k?s[p-k]:0)+(p+k<n?s[p+k]:0),h=-2*s[p]*t;
   de+=2*c[k]*h+h*h;
  }
  return de;
 }
 void flip(int p){
  int d=delta(p);
  for(int k=1;k<n;k++){
   int t=(p>=k?s[p-k]:0)+(p+k<n?s[p+k]:0);c[k]-=2*s[p]*t;
  }
  s[p]=-s[p];e+=d;
 }
 int descend(int rule=0){
  int steps=0;
  while(true){int pos=-1,best=0;
   for(int i=0;i<n;i++) {int d=delta(i);if(d<best){best=d;pos=i;if(rule==1)break;}}
   if(pos<0)break;flip(pos);steps++;if(steps>n*8)throw runtime_error("nonterminating descent");
  }return steps;
 }
};
int energy_direct(const vector<int>& s){
 int n=s.size(),e=0;for(int k=1;k<n;k++){int c=0;for(int i=0;i<n-k;i++)c+=s[i]*s[i+k];e+=c*c;}return e;
}
vector<int> random_mask(int n,int m,mt19937_64 &rng) {
 vector<int> ids(n);iota(ids.begin(),ids.end(),0);
 for(int i=0;i<m;i++){uniform_int_distribution<int> d(i,n-1);swap(ids[i],ids[d(rng)]);}
 ids.resize(m);sort(ids.begin(),ids.end());return ids;
}
vector<int> soft_mask(const vector<int>& ds,int m,mt19937_64 &rng){
 vector<int> ids(ds.size());iota(ids.begin(),ids.end(),0);
 // slight randomized noise, anchored at low one-spin cost
 vector<double> score(ds.size());uniform_real_distribution<double> uni(0.,1.);
 for(int i=0;i<(int)ds.size();i++)score[i]=ds[i]+60.*(-log(max(1e-9,uni(rng))));
 partial_sort(ids.begin(),ids.begin()+m,ids.end(),[&](int a,int b){return score[a]<score[b];});
 ids.resize(m);sort(ids.begin(),ids.end());return ids;
}
vector<int> window_mask(int n,int m,mt19937_64 &rng){
 uniform_int_distribution<int> d(0,n-m);int begin=d(rng);vector<int> x(m);iota(x.begin(),x.end(),begin);return x;
}
vector<int> structural_mask(const vector<int>&ds,const vector<int>&pair,int n,int m,int mode,mt19937_64 &rng){
 // mode 2: negative combined interaction helps group flip; mode 3: high absolute coupling cluster.
 vector<std::pair<double,std::pair<int,int>>> seeds;seeds.reserve(n*(n-1)/2);
 for(int i=0;i<n;i++)for(int j=i+1;j<n;j++){
  double score=mode==2? (ds[i]+ds[j]+pair[i*n+j]): -abs(pair[i*n+j]);
  seeds.push_back({score,{i,j}});
 }
 int take=min(80,(int)seeds.size());
 nth_element(seeds.begin(),seeds.begin()+take-1,seeds.end(),[](auto&a,auto&b){return a.first<b.first;});
 uniform_int_distribution<int> select(0,take-1);auto pr=seeds[select(rng)].second;
 vector<int> ids={pr.first,pr.second};vector<char> used(n,0);used[pr.first]=used[pr.second]=1;
 uniform_real_distribution<double> unif(0.,1.);
 while((int)ids.size()<m){
  int best=-1;double val=1e100;
  for(int i=0;i<n;i++)if(!used[i]){
   double v= mode==2? ds[i]:0;
   for(int j:ids){int p=pair[min(i,j)*n+max(i,j)];v+=mode==2?p:-abs(p);}
   // Gumbel-like randomized greedy to diversify group formation, scale with energy units
   v+=40.*(-log(max(1e-9,unif(rng))));
   if(v<val){val=v;best=i;}
  }
  used[best]=1;ids.push_back(best);
 }
 sort(ids.begin(),ids.end());return ids;
}
vector<int> interactions(const L&b,const vector<int>&ds){
 int n=b.n;vector<int> x(n*n);
 for(int i=0;i<n;i++){
  L t=b;t.flip(i);
  for(int j=i+1;j<n;j++)x[i*n+j]=t.delta(j)-ds[j];
 }
 return x;
}
struct Exit {L repair,excursion;int enum_states=0,dist_repair=0,dist_exit=0,score_repair=0,score_exit=0;};
Exit enumerate(const L &base,const vector<int>&mask,int minimum_distance){
 int m=mask.size(),states=1<<m;L cur=base;
 Exit ans;ans.repair=base;ans.excursion=base;
 ans.score_repair=base.e;ans.score_exit=1e9;
 for(int t=1;t<states;t++){
  int x=__builtin_ctz((unsigned)t);cur.flip(mask[x]);
  int code=t^(t>>1),dist=__builtin_popcount((unsigned)code);
  if(cur.e<ans.score_repair || (cur.e==ans.score_repair && dist>ans.dist_repair)){
   ans.repair=cur;ans.score_repair=cur.e;ans.dist_repair=dist;}
  if(dist>=minimum_distance && cur.e<ans.score_exit){
   ans.excursion=cur;ans.score_exit=cur.e;ans.dist_exit=dist;
  }
 }
 ans.enum_states=states;
 if(ans.score_exit==1e9)throw runtime_error("missing candidate");
 // The Gray path visits all states exactly once but does not end at its origin.

 return ans;
}
void test(){
 mt19937_64 rng(901231);int ct=0;
 for(int n:{12,24,48,64,100})for(int seed=0;seed<35;seed++){
  vector<int> v(n);for(int&i:v)i=rng()%2?1:-1;L b(v);
  for(int i=0;i<n;i++){
   vector<int> w=v;w[i]=-w[i];assert(b.delta(i)==energy_direct(w)-b.e);
   L c=b;c.flip(i);assert(c.e==energy_direct(c.s));ct++;
  }
  int m=min(9,n);auto ids=random_mask(n,m,rng);
  auto z=enumerate(b,ids,3);
  // Independent brute-force check on randomly chosen masks.
  int best=b.e,far=1e9;
  for(int bits=0;bits<(1<<m);bits++){
   vector<int> w=v;for(int j=0;j<m;j++)if(bits>>j&1)w[ids[j]]=-w[ids[j]];
   int e=energy_direct(w);best=min(best,e);
   if(__builtin_popcount((unsigned)bits)>=3)far=min(far,e);
  }
  assert(best==z.score_repair&&far==z.score_exit);
 }
 string cert="++++++--+++++-----++-++--+--++++++++++---+-++--++++-+--++----+--+-+-+-+-++---++---++-+-++-+-++--+-+-";
 vector<int> v;for(char c:cert)v.push_back(c=='+'?1:-1);
 assert((int)v.size()==100&&energy_direct(v)==578);
 cout<<"PASS "<<ct<<" incremental deltas + 175 exhaustive masks against independent direct brute force, N100 E578\n";
}
int main(int argc,char**argv){
 if(argc==2&&string(argv[1])=="--selftest"){test();return 0;}
 if(argc<8){cerr<<"usage: OUT.csv N STAGE BASES SEED M MASKS [record]\n";return 2;}
 ofstream f(argv[1]);int n=stoi(argv[2]),stage=stoi(argv[3]),bases=stoi(argv[4]),m=stoi(argv[6]),masks=stoi(argv[7]);
 bool record=argc>8&&string(argv[8])=="record";
 if(m<4||m>18||m>n)return 3;
 mt19937_64 rng(stoull(argv[5])),proposal_rng(stoull(argv[5])+101007),seed_rng(stoull(argv[5])+51487);
 string cert="++++++--+++++-----++-++--+--++++++++++---+-++--++++-+--++----+--+-+-+-+-++---++---++-+-++-+-++--+-+-";
 vector<int> rec;for(char c:cert)rec.push_back(c=='+'?1:-1);
 uniform_int_distribution<int> bit(0,n-1);
 f<<"n,group,stage,baseE,method,mask,m,repairE,excE,repairDist,excDist,repairSteep,repairFirst,excSteep,excFirst,stepsRepairSteep,stepsRepairFirst,stepsExcSteep,stepsExcFirst,enumStates,selectionSeconds,enumevalSeconds,descentSeconds\n";
 f<<fixed<<setprecision(9);
 for(int g=0;g<bases;g++){
  vector<int> s(n);for(int&i:s)i=seed_rng()%2?1:-1;L base(record?rec:s);base.descend();
  if(!record)for(int t=0;t<stage;t++){
   auto x=base;auto ids=random_mask(n,4,rng);for(int i:ids)x.flip(i);
   x.descend();if(x.e<base.e)base=move(x);
  }
  vector<int> ds(n);for(int i=0;i<n;i++)ds[i]=base.delta(i);
  vector<int> pair;
  for(int method=0;method<5;method++){
   auto ts=clk::now();if(method>=2&&method<=3&&pair.empty())pair=interactions(base,ds);
   double featurecost=ns(clk::now()-ts).count();
   for(int k=0;k<masks;k++){
    auto selectstart=clk::now();vector<int> idx;
    if(method==0)idx=random_mask(n,m,proposal_rng);
    if(method==1)idx=soft_mask(ds,m,proposal_rng);
    if(method==2||method==3)idx=structural_mask(ds,pair,n,m,method,proposal_rng);
    if(method==4)idx=window_mask(n,m,proposal_rng);
    double selection=ns(clk::now()-selectstart).count()+(k==0?featurecost:0);
    auto enumstart=clk::now();auto z=enumerate(base,idx,max(3,m/3));
    double ectime=ns(clk::now()-enumstart).count();
    auto descstart=clk::now();
    L a=z.repair;int sa=a.descend(0);
    L b=z.repair;int sb=b.descend(1);
    L c=z.excursion;int sc=c.descend(0);
    L d=z.excursion;int sd=d.descend(1);
    double desc=ns(clk::now()-descstart).count();
    if(g==0&&k==0){assert(energy_direct(a.s)==a.e&&energy_direct(c.s)==c.e&&energy_direct(d.s)==d.e);}
    f<<n<<","<<g<<","<<stage<<","<<base.e<<","<<method<<","<<k<<","<<m<<","<<z.score_repair<<","<<z.score_exit<<","<<z.dist_repair<<","<<z.dist_exit<<","<<a.e<<","<<b.e<<","<<c.e<<","<<d.e<<","<<sa<<","<<sb<<","<<sc<<","<<sd<<","<<z.enum_states<<","<<selection<<","<<ectime<<","<<desc<<"\n";
   }
  }
  if(g%50==0)cerr<<"n="<<n<<" stage="<<stage<<" g="<<g<<"/"<<bases<<"\n";
 }
}
