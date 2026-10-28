// Search structured families consisting of an odd-length free boundary followed
// by a skew-symmetric core. For boundary length d (odd), the tail positions
// d..99 have odd length 100-d and exact skew symmetry.
//
// Phase 1 searches structural-coordinate flips for odd-lag energy 50.
// Phase 2 stays exactly odd-perfect and tabu-searches structural-coordinate
// flips for minimum full LABS energy. d=1 is the canonical (+1,skew99)
// manifold; the reproducible outside-near-skew E=1162 basin is d=3.
#include <algorithm>
#include <array>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <iostream>
#include <limits>
#include <random>
#include <stdexcept>
#include <string>
#include <vector>
#ifdef _OPENMP
#include <omp.h>
#endif

constexpr int N=100;
using S=std::array<int8_t,N>;
using C=std::array<int,N>;

struct Coord{int p,q;};

static long long exact(const S&s,C*out=nullptr,long long*oddout=nullptr){
 C c{};long long e=0,o=0;
 for(int k=1;k<N;k++){int x=0;for(int i=0;i<N-k;i++)x+=int(s[i])*int(s[i+k]);c[k]=x;long long z=1LL*x*x;e+=z;if(k&1)o+=z;}
 if(out)*out=c;if(oddout)*oddout=o;return e;
}
static std::string fmt(const S&s){std::string z;z.reserve(N);for(auto v:s)z+=v>0?'+':'-';return z;}
static inline int contrib(const S&s,int p,int k){int t=0,sp=s[p];if(p+k<N)t+=sp*int(s[p+k]);if(p-k>=0)t+=int(s[p-k])*sp;return t;}

static std::vector<Coord> coords_for(int d){
 if(d<1||d>=100||(d&1)==0)throw std::runtime_error("d must be odd in [1,99]");
 std::vector<Coord> c;
 // Prefix coordinates. Position zero is retained as a coordinate for shape,
 // but search fixes it to +1 and excludes it from active moves by starting at 1.
 for(int p=0;p<d;p++)c.push_back({p,-1});
 const int L=N-d, half=(L-1)/2;
 for(int j=0;j<=half;j++){
  int p=d+j;
  int q=(j==half)?-1:99-j;
  c.push_back({p,q});
 }
 return c;
}

static S random_structured(int d,std::mt19937_64&r){
 S s{};s.fill(0);s[0]=1;
 for(int p=1;p<d;p++)s[p]=(r()&1)?1:-1;
 int L=N-d,half=(L-1)/2;
 for(int j=0;j<=half;j++){
  int p=d+j;int v=(r()&1)?1:-1;s[p]=v;
  if(j<half){int q=99-j;int factor=((half-j)&1)?-1:1;s[q]=factor*v;}
 }
 return s;
}

static bool check_structured(const S&s,int d){
 if(s[0]!=1)return false;
 int L=N-d,half=(L-1)/2;
 for(int j=0;j<half;j++){
  int p=d+j,q=99-j,factor=((half-j)&1)?-1:1;
  if(int(s[q])!=factor*int(s[p]))return false;
 }
 return true;
}

static void coordinate_result(const S&s,const C&c,const Coord&m,long long&e,long long&o){
 const int p=m.p,q=m.q;
 const int pq=(q>=0)?int(s[p])*int(s[q]):0;
 const int dist=(q>=0)?std::abs(q-p):-1;
 e=0;o=0;
 for(int k=1;k<N;k++){
  int t=contrib(s,p,k);
  if(q>=0)t+=contrib(s,q,k);
  if(q>=0&&k==dist)t-=2*pq;
  int cp=c[k]-2*t;long long z=1LL*cp*cp;e+=z;if(k&1)o+=z;
 }
}
static bool coordinate_oddperfect_eval(const S&s,const C&c,const Coord&m,long long&e){
 const int p=m.p,q=m.q,pq=(q>=0)?int(s[p])*int(s[q]):0,dist=(q>=0)?std::abs(q-p):-1;
 long long even=0;
 for(int k=1;k<N;k+=2){int t=contrib(s,p,k);if(q>=0)t+=contrib(s,q,k);if(q>=0&&k==dist)t-=2*pq;int cp=c[k]-2*t;if(std::abs(cp)!=1)return false;}
 for(int k=2;k<N;k+=2){int t=contrib(s,p,k);if(q>=0)t+=contrib(s,q,k);if(q>=0&&k==dist)t-=2*pq;int cp=c[k]-2*t;even+=1LL*cp*cp;}
 e=50+even;return true;
}
static void coordinate_apply(S&s,C&c,long long&e,long long&o,const Coord&m){
 const int p=m.p,q=m.q,pq=(q>=0)?int(s[p])*int(s[q]):0,dist=(q>=0)?std::abs(q-p):-1;
 long long ne=0,no=0;
 for(int k=1;k<N;k++){int t=contrib(s,p,k);if(q>=0)t+=contrib(s,q,k);if(q>=0&&k==dist)t-=2*pq;int cp=c[k]-2*t;c[k]=cp;long long z=1LL*cp*cp;ne+=z;if(k&1)no+=z;}
 s[p]=-s[p];if(q>=0)s[q]=-s[q];e=ne;o=no;
}

static bool make_oddperfect(S&s,const std::vector<Coord>&cs,std::mt19937_64&r,int maxsteps,int tenlo,int tenhi){
 C c{};long long o=0,e=exact(s,&c,&o),best=o;std::vector<int>tabu(cs.size(),0);
 if(o==50)return true;
 for(int st=1;st<=maxsteps;st++){
  long long bo=1LL<<60,be=1LL<<60;int bi=-1,ties=0;
  for(int i=1;i<(int)cs.size();i++){
   long long ee,oo;coordinate_result(s,c,cs[i],ee,oo);
   if(st<tabu[i]&&oo>=best)continue;
   if(oo<bo||(oo==bo&&ee<be)){bo=oo;be=ee;bi=i;ties=1;}
   else if(oo==bo&&ee==be&&r()%++ties==0)bi=i;
  }
  if(bi<0){std::fill(tabu.begin(),tabu.end(),0);continue;}
  coordinate_apply(s,c,e,o,cs[bi]);tabu[bi]=st+tenlo+int(r()%(tenhi-tenlo+1));
  if(o<best)best=o;if(o==50)return true;
 }
 return false;
}

struct Result{long long e=1LL<<60;S s{};int step=0;};
static Result oddperfect_walk(S s,const std::vector<Coord>&cs,std::mt19937_64&r,int steps,int tenlo,int tenhi){
 C c{};long long o=0,e=exact(s,&c,&o);if(o!=50)throw std::runtime_error("phase2 start not odd-perfect");
 Result best{e,s,0};std::vector<int>tabu(cs.size(),0);
 for(int st=1;st<=steps;st++){
  long long me=1LL<<60;int mi=-1,ties=0;bool any=false;
  for(int i=1;i<(int)cs.size();i++){
   long long ee;if(!coordinate_oddperfect_eval(s,c,cs[i],ee))continue;any=true;
   if(st<tabu[i]&&ee>=best.e)continue;
   if(ee<me){me=ee;mi=i;ties=1;}else if(ee==me&&r()%++ties==0)mi=i;
  }
  if(mi<0){if(!any)break;std::fill(tabu.begin(),tabu.end(),0);continue;}
  coordinate_apply(s,c,e,o,cs[mi]);tabu[mi]=st+tenlo+int(r()%(tenhi-tenlo+1));
  if(e<best.e){best={e,s,st};}
#ifndef NDEBUG
  if((st&1023)==0){long long oo=0,ee=exact(s,nullptr,&oo);if(ee!=e||oo!=50)std::abort();}
#endif
 }
 return best;
}

int main(int argc,char**argv){
 int d=1,runs=32,phase1=30000,phase2=50000,threads=0,tenlo=5,tenhi=15;uint64_t seed=1;
 for(int i=1;i<argc;i++){std::string a=argv[i];auto need=[&](){if(i+1>=argc)throw std::runtime_error("missing value");return std::string(argv[++i]);};
  if(a=="--d")d=std::stoi(need());else if(a=="--runs")runs=std::stoi(need());else if(a=="--phase1")phase1=std::stoi(need());else if(a=="--phase2")phase2=std::stoi(need());else if(a=="--threads")threads=std::stoi(need());else if(a=="--seed")seed=std::stoull(need());else if(a=="--tenure-lo")tenlo=std::stoi(need());else if(a=="--tenure-hi")tenhi=std::stoi(need());else throw std::runtime_error("bad arg");}
#ifdef _OPENMP
 if(threads<=0)threads=omp_get_max_threads();omp_set_num_threads(threads);
#else
 threads=1;
#endif
 auto cs=coords_for(d);std::vector<long long>vals(runs,-1);int starts=0;long long gb=1LL<<60;S gs{};int gstep=0;auto t0=std::chrono::steady_clock::now();
#pragma omp parallel for schedule(dynamic,1)
 for(int rr=0;rr<runs;rr++){
  std::mt19937_64 r(seed+0x9e3779b97f4a7c15ULL*uint64_t(rr+1));S s=random_structured(d,r);if(!check_structured(s,d))std::abort();
  if(!make_oddperfect(s,cs,r,phase1,tenlo,tenhi))continue;
  auto z=oddperfect_walk(s,cs,r,phase2,tenlo,tenhi);vals[rr]=z.e;
#pragma omp critical
  {starts++;if(z.e<gb){gb=z.e;gs=z.s;gstep=z.step;std::cout<<"BEST d="<<d<<" energy="<<gb<<" run="<<rr<<" step="<<gstep<<" seq="<<fmt(gs)<<"\n"<<std::flush;}}
 }
 std::vector<long long>good;for(auto v:vals)if(v>=0)good.push_back(v);std::sort(good.begin(),good.end());double sec=std::chrono::duration<double>(std::chrono::steady_clock::now()-t0).count();
 std::cout<<"SUMMARY d="<<d<<" coords="<<cs.size()-1<<" runs="<<runs<<" oddperfect_starts="<<starts<<" best="<<(good.empty()?-1:good.front())<<" median="<<(good.empty()?-1:good[good.size()/2])<<" seconds="<<sec<<"\n";
 if(!good.empty()){long long oo=0,ee=exact(gs,nullptr,&oo);std::cout<<"BESTSEQ energy="<<ee<<" odd="<<oo<<" structured="<<check_structured(gs,d)<<" seq="<<fmt(gs)<<"\n";}
 return 0;
}
