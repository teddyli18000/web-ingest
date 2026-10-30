// Exact odd-perfect tabu walk, instrumented to exclude every cyclic near-skew cut.
// A sequence is classified as trivial iff there exists m in Z_50 with
// s[p] = (-1)^(m+p) s[(2m-p) mod 100], equivalently R=(-x)^m U in the
// periodic spectral-factor representation.
#include <algorithm>
#include <array>
#include <chrono>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <limits>
#include <random>
#include <stdexcept>
#include <string>
#ifdef _OPENMP
#include <omp.h>
#endif

using S=std::array<int8_t,100>;
using C=std::array<int,100>;
constexpr int N=100;

static long long exact(const S&s,C*out=nullptr,long long*oddout=nullptr){
 C c{}; long long e=0,o=0;
 for(int k=1;k<N;k++){
  int x=0;for(int i=0;i<N-k;i++)x+=int(s[i])*int(s[i+k]);
  c[k]=x;long long q=1LL*x*x;e+=q;if(k&1)o+=q;
 }
 if(out)*out=c;if(oddout)*oddout=o;return e;
}
static std::string fmt(const S&s){std::string z;z.reserve(N);for(auto v:s)z+=v>0?'+':'-';return z;}
static S randoms(std::mt19937_64&r){S s{};for(auto&v:s)v=(r()&1)?1:-1;return s;}

static int cyclic_nearskew_axis(const S&s){
 for(int m=0;m<50;m++){
  bool ok=true;
  for(int p=0;p<100;p++){
   int q=(2*m-p)%100;if(q<0)q+=100;
   int sign=((m+p)&1)?-1:1;
   if(int(s[p])!=sign*int(s[q])){ok=false;break;}
  }
  if(ok)return m;
 }
 return -1;
}

static inline int contrib(const S&s,int p,int k){
 int t=0,sp=s[p];if(p+k<N)t+=sp*int(s[p+k]);if(p-k>=0)t+=int(s[p-k])*sp;return t;
}
static long long odd_flip_eval(const S&s,const C&c,long long o,int p){
 long long no=o;for(int k=1;k<N;k+=2){int d=-2*contrib(s,p,k);if(d)no+=2LL*c[k]*d+1LL*d*d;}return no;
}
static void flip1(S&s,C&c,long long&e,long long&o,int p){
 for(int k=1;k<N;k++){int d=-2*contrib(s,p,k);if(!d)continue;long long de=2LL*c[k]*d+1LL*d*d;e+=de;if(k&1)o+=de;c[k]+=d;}s[p]=-s[p];
}
static bool make_oddperfect(S&s,std::mt19937_64&r,int max_steps){
 C c{};long long o=0,e=exact(s,&c,&o),best=o;std::array<int,N>tabu{};
 for(int st=1;st<=max_steps;st++){
  long long be=1LL<<60;int bp=-1,ties=0;
  for(int p=0;p<N;p++){
   long long ne=odd_flip_eval(s,c,o,p);if(st<tabu[p]&&ne>=best)continue;
   if(ne<be){be=ne;bp=p;ties=1;}else if(ne==be&&r()%++ties==0)bp=p;
  }
  if(bp<0){tabu.fill(0);continue;}
  flip1(s,c,e,o,bp);tabu[bp]=st+5+int(r()%11);if(o<best)best=o;if(o==50)return true;
 }
 return false;
}

struct Eval{bool ok=false;long long e=0;};
static Eval move_eval(const S&s,const C&c,int p,int q){
 long long even=0;int pq=q>=0?int(s[p])*int(s[q]):0,dist=q>=0?std::abs(q-p):-1;
 for(int k=1;k<N;k+=2){
  int t=contrib(s,p,k);if(q>=0)t+=contrib(s,q,k);if(q>=0&&k==dist)t-=2*pq;
  int cp=c[k]-2*t;if(std::abs(cp)!=1)return{};
 }
 for(int k=2;k<N;k+=2){
  int t=contrib(s,p,k);if(q>=0)t+=contrib(s,q,k);if(q>=0&&k==dist)t-=2*pq;
  int cp=c[k]-2*t;even+=1LL*cp*cp;
 }
 return{true,50+even};
}
static void move_apply(S&s,C&c,long long&e,int p,int q){
 int pq=q>=0?int(s[p])*int(s[q]):0,dist=q>=0?std::abs(q-p):-1;long long ne=0;
 for(int k=1;k<N;k++){
  int t=contrib(s,p,k);if(q>=0)t+=contrib(s,q,k);if(q>=0&&k==dist)t-=2*pq;
  int cp=c[k]-2*t;c[k]=cp;ne+=1LL*cp*cp;
 }
 s[p]=-s[p];if(q>=0)s[q]=-s[q];e=ne;
}

struct R{long long best=1LL<<60,out=1LL<<60;S bs{},os{};int besta=-2;};
static void note(R&r,long long e,const S&s){
 int a=-2;
 if(e<r.best){a=cyclic_nearskew_axis(s);r.best=e;r.bs=s;r.besta=a;}
 if(e<r.out){if(a==-2)a=cyclic_nearskew_axis(s);if(a<0){r.out=e;r.os=s;}}
}
static R walk(S s,std::mt19937_64&rng,int steps,int tenlo,int tenhi){
 C c{};long long o=0,e=exact(s,&c,&o);if(o!=50)throw std::runtime_error("not odd-perfect");
 R r;note(r,e,s);std::array<int,N>tabu{};
 for(int st=1;st<=steps;st++){
  long long me=1LL<<60;int mp=-1,mq=-1,ties=0;bool any=false;
  for(int p=0;p<N;p++)for(int q=p+1;q<N;q++){
   auto z=move_eval(s,c,p,q);if(!z.ok)continue;any=true;
   if((st<tabu[p]||st<tabu[q])&&z.e>=r.best)continue;
   if(z.e<me){me=z.e;mp=p;mq=q;ties=1;}else if(z.e==me&&rng()%++ties==0){mp=p;mq=q;}
  }
  if(mp<0){if(!any)break;tabu.fill(0);continue;}
  move_apply(s,c,e,mp,mq);tabu[mp]=st+tenlo+int(rng()%(tenhi-tenlo+1));tabu[mq]=st+tenlo+int(rng()%(tenhi-tenlo+1));
  note(r,e,s);
 }
 return r;
}

int main(int argc,char**argv){
 int runs=8,steps=2000,oddsteps=40000,threads=0,tenlo=5,tenhi=15;uint64_t seed=1;
 for(int i=1;i<argc;i++){
  std::string a=argv[i];auto need=[&](){if(i+1>=argc)throw std::runtime_error("missing value");return std::string(argv[++i]);};
  if(a=="--runs")runs=std::stoi(need());else if(a=="--steps")steps=std::stoi(need());
  else if(a=="--odd-steps")oddsteps=std::stoi(need());else if(a=="--threads")threads=std::stoi(need());
  else if(a=="--seed")seed=std::stoull(need());else if(a=="--tenure-lo")tenlo=std::stoi(need());
  else if(a=="--tenure-hi")tenhi=std::stoi(need());else throw std::runtime_error("unknown arg");
 }
#ifdef _OPENMP
 if(threads<=0)threads=omp_get_max_threads();omp_set_num_threads(threads);
#else
 threads=1;
#endif
 long long gb=1LL<<60,go=1LL<<60;S gbs{},gos{};int gba=-2,good=0;auto t0=std::chrono::steady_clock::now();
#pragma omp parallel for schedule(dynamic,1)
 for(int rr=0;rr<runs;rr++){
  std::mt19937_64 rng(seed+0x9e3779b97f4a7c15ULL*uint64_t(rr+1));S s=randoms(rng);
  if(!make_oddperfect(s,rng,oddsteps))continue;R z=walk(s,rng,steps,tenlo,tenhi);
#pragma omp critical
  {
   good++;
   if(z.best<gb){gb=z.best;gbs=z.bs;gba=z.besta;std::cout<<"BEST energy="<<gb<<" axis="<<gba<<" seq="<<fmt(gbs)<<"\n"<<std::flush;}
   if(z.out<go){go=z.out;gos=z.os;std::cout<<"NONMONO energy="<<go<<" run="<<rr<<" seq="<<fmt(gos)<<"\n"<<std::flush;}
  }
 }
 double sec=std::chrono::duration<double>(std::chrono::steady_clock::now()-t0).count();
 std::cout<<"SUMMARY runs="<<runs<<" starts="<<good<<" best="<<gb<<" best_axis="<<gba<<" nonmono="<<(go==(1LL<<60)?-1:go)<<" sec="<<sec<<"\n";
 if(go<(1LL<<60))std::cout<<"NONMONOSEQ "<<fmt(gos)<<"\n";
}
