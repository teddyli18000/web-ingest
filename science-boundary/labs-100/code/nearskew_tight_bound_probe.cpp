// Validate and calibrate the exact per-correlation chain bound for partial
// assignments in the direct N=100 near-skew manifold.
//
// For a fixed lag k, the product graph s_i s_{i+k} is a disjoint union of
// chains. Between two fixed signs separated by n product edges, the number of
// negative edge products has parity fixed by the endpoint product, so that
// segment contributes a contiguous step-4 arithmetic progression. A free tail
// contributes the full step-2 progression [-n,n]. Summing these segments over
// all chains gives the exact attainable arithmetic progression for C_k under
// the relaxation that currently-free signs are independent.
//
// This file implements both a slow bitset DP and the analytic interval/residue
// formula, checks them against one another lag-by-lag, validates the bound on
// random complete extensions, and measures analytic throughput.
#include <algorithm>
#include <array>
#include <bitset>
#include <chrono>
#include <cstdint>
#include <iostream>
#include <numeric>
#include <random>
#include <string>
#include <vector>

constexpr int N=100, OFF=100, W=201;
using S=std::array<int8_t,N>;
using A=std::array<uint8_t,N>;
struct P { S s{}; A used{}; };

static void assign_coord(P& p,int v,int val){
 int a=1+v;p.s[a]=val;p.used[a]=1;
 if(v!=49){int b=99-v,factor=(a&1)?-1:1;p.s[b]=factor*val;p.used[b]=1;}
}
static P random_partial(int depth,std::mt19937_64&rng){
 P p;p.s[0]=1;p.used[0]=1;assign_coord(p,0,1);
 for(int v=1;v<depth;v++)assign_coord(p,v,(rng()&1)?1:-1);
 return p;
}
static long long cheap_bound(const P&p){
 long long lb=0;
 for(int k=2;k<N;k+=2){
  int f=0,u=0;
  for(int i=0;i<N-k;i++){if(p.used[i]&&p.used[i+k])f+=int(p.s[i])*int(p.s[i+k]);else u++;}
  int m=std::max(0,std::abs(f)-u);if(m&1)++m;lb+=1LL*m*m;
 }
 return lb;
}

static std::bitset<W> lag_values_dp(const P&p,int k){
 std::bitset<W> global;global[OFF]=1;
 for(int start=0;start<k&&start<N;start++){
  std::vector<int> pos;for(int q=start;q<N;q+=k)pos.push_back(q);
  if(pos.size()<2)continue;
  std::array<std::bitset<W>,2> cur{},nxt{};
  auto allow=[&](int q,int sign){return !p.used[q]||int(p.s[q])==sign;};
  if(allow(pos[0],-1))cur[0][OFF]=1;if(allow(pos[0],+1))cur[1][OFF]=1;
  for(size_t j=1;j<pos.size();j++){
   nxt[0].reset();nxt[1].reset();
   for(int ps=0;ps<2;ps++)for(int ns=0;ns<2;ns++){
    int a=ps?1:-1,b=ns?1:-1;if(!allow(pos[j],b))continue;int d=a*b;
    if(d==1)nxt[ns]|=(cur[ps]<<1);else nxt[ns]|=(cur[ps]>>1);
   }
   cur=nxt;
  }
  std::bitset<W> chain=cur[0]|cur[1],combined;
  for(int a=0;a<W;a++)if(global[a])for(int b=0;b<W;b++)if(chain[b]){
   int z=(a-OFF)+(b-OFF);if(z>=-OFF&&z<=OFF)combined[z+OFF]=1;
  }
  global=combined;
 }
 return global;
}

struct AP{int lo=0,hi=0,step=0;};
static void add_open(AP&z,int n){
 if(n<=0)return;z.lo-=n;z.hi+=n;z.step=(z.step==0?2:std::gcd(z.step,2));
}
static void add_closed(AP&z,int n,int endpoint_product){
 if(n<=0)return;
 int parity=endpoint_product<0?1:0;
 int jmin=parity;
 int jmax=n-((n-parity)&1);
 int hi=n-2*jmin,lo=n-2*jmax;
 z.lo+=lo;z.hi+=hi;
 if(lo!=hi)z.step=(z.step==0?4:std::gcd(z.step,4));
}
static AP lag_ap(const P&p,int k){
 AP total;
 for(int start=0;start<k&&start<N;start++){
  std::vector<int> pos;for(int q=start;q<N;q+=k)pos.push_back(q);
  if(pos.size()<2)continue;
  std::vector<int> fi;
  for(int j=0;j<(int)pos.size();j++)if(p.used[pos[j]])fi.push_back(j);
  if(fi.empty()){add_open(total,int(pos.size())-1);continue;}
  add_open(total,fi.front());
  for(int z=0;z+1<(int)fi.size();z++){
   int a=fi[z],b=fi[z+1],n=b-a,ep=int(p.s[pos[a]])*int(p.s[pos[b]]);
   add_closed(total,n,ep);
  }
  add_open(total,int(pos.size())-1-fi.back());
 }
 return total;
}
static int ap_min_abs(const AP&z){
 if(z.lo==z.hi)return std::abs(z.lo);
 int step=z.step;if(step<=0)return std::abs(z.lo);
 if(z.lo<=0&&z.hi>=0){
  int r=((z.lo%step)+step)%step;
  if(r==0)return 0;
  return std::min(r,step-r);
 }
 return std::min(std::abs(z.lo),std::abs(z.hi));
}
static long long tight_bound_ap(const P&p){
 long long lb=0;
 for(int k=2;k<N;k+=2){AP z=lag_ap(p,k);int m=ap_min_abs(z);lb+=1LL*m*m;}
 return lb;
}
static long long tight_bound_dp(const P&p,bool compare_ap){
 long long lb=0;
 for(int k=2;k<N;k+=2){
  auto vals=lag_values_dp(p,k);int m=1000;
  for(int c=-(N-k);c<=N-k;c+=2)if(vals[c+OFF])m=std::min(m,std::abs(c));
  if(m==1000){std::cerr<<"empty lag set k="<<k<<"\n";std::abort();}
  if(compare_ap){
   AP z=lag_ap(p,k);int ma=ap_min_abs(z);
   if(ma!=m){
    std::cerr<<"analytic mismatch k="<<k<<" dp="<<m<<" ap="<<ma<<" range="<<z.lo<<","<<z.hi<<" step="<<z.step<<"\n";
    std::abort();
   }
   if(z.step==0){if(!vals[z.lo+OFF]){std::cerr<<"AP singleton impossible\n";std::abort();}}
   else for(int c=z.lo;c<=z.hi;c+=z.step)if(!vals[c+OFF]){
    std::cerr<<"AP contains impossible c="<<c<<" k="<<k<<"\n";std::abort();
   }
  }
  lb+=1LL*m*m;
 }
 return lb;
}
static S complete_nearskew(P p,std::mt19937_64&rng){for(int v=0;v<50;v++)if(!p.used[1+v])assign_coord(p,v,(rng()&1)?1:-1);return p.s;}
static long long even_energy(const S&s){long long e=0;for(int k=2;k<N;k+=2){int c=0;for(int i=0;i<N-k;i++)c+=int(s[i])*int(s[i+k]);e+=1LL*c*c;}return e;}

int main(int argc,char**argv){
 int samples=100;uint64_t seed=1;if(argc>1)samples=std::stoi(argv[1]);if(argc>2)seed=std::stoull(argv[2]);
 std::mt19937_64 rng(seed);std::vector<int> depths={8,12,16,20,24,28,32,36,40,44};
 for(int d:depths){
  long long sumc=0,sumt=0;int stronger=0,prune=0,cheapprune=0;long long maxgain=0;
  for(int n=0;n<samples;n++){
   P p=random_partial(d,rng);long long c=cheap_bound(p),td=tight_bound_dp(p,true),t=tight_bound_ap(p);
   if(td!=t||t<c){std::cerr<<"bound mismatch depth="<<d<<" cheap="<<c<<" dp="<<td<<" ap="<<t<<"\n";return 2;}
   for(int q=0;q<3;q++){S s=complete_nearskew(p,rng);long long ee=even_energy(s);if(ee<t){std::cerr<<"unsound bound depth="<<d<<" bound="<<t<<" completion="<<ee<<"\n";return 2;}}
   sumc+=c;sumt+=t;if(t>c)stronger++;if(c>524)cheapprune++;if(c<=524&&t>524)prune++;maxgain=std::max(maxgain,t-c);
  }
  std::cout<<"DEPTH "<<d<<" samples="<<samples<<" avgCheap="<<double(sumc)/samples<<" avgTight="<<double(sumt)/samples<<" stronger="<<stronger<<" tightOnlyPrune="<<prune<<" cheapPrune="<<cheapprune<<" maxGain="<<maxgain<<"\n";
 }
 P full=random_partial(50,rng);long long t=tight_bound_ap(full),ee=even_energy(full.s);
 std::cout<<"FULL tight="<<t<<" even="<<ee<<" exact="<<(t==ee)<<"\n";
 constexpr int BENCH=20000;volatile long long sink=0;
 for(int d:{24,28,32,36}){
  std::vector<P> ps;ps.reserve(256);for(int i=0;i<256;i++)ps.push_back(random_partial(d,rng));
  auto t0=std::chrono::steady_clock::now();
  for(int i=0;i<BENCH;i++)sink += tight_bound_ap(ps[i&255]);
  double sec=std::chrono::duration<double>(std::chrono::steady_clock::now()-t0).count();
  std::cout<<"BENCH depth="<<d<<" evals="<<BENCH<<" seconds="<<sec<<" per_sec="<<BENCH/sec<<"\n";
 }
 if(sink==123456789)std::cerr<<sink;
 return t==ee?0:2;
}
