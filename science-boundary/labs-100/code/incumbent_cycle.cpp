#include <algorithm>
#include <array>
#include <chrono>
#include <cstdint>
#include <iostream>
#include <limits>
#include <random>
#include <string>
#include <vector>
#ifdef _OPENMP
#include <omp.h>
#endif
using Seq=std::array<int8_t,100>; using Corr=std::array<int,100>;
struct Parts{long long odd=0,even=0;};
static const std::string INCSTR="++++++--+++++-----++-++--+--++++++++++---+-++--++++-+--++----+--+-+-+-+-++---++---++-+-++-+-++--+-+-";
static Seq parse(const std::string&z){Seq s{};for(int i=0;i<100;i++)s[i]=z[i]=='+'?1:-1;return s;}
static std::string fmt(const Seq&s){std::string z;for(auto v:s)z+=v>0?'+':'-';return z;}
static Parts parts(const Seq&s,Corr*out=nullptr){Corr c{};Parts p;for(int k=1;k<100;k++){int x=0;for(int i=0;i<100-k;i++)x+=int(s[i])*int(s[i+k]);c[k]=x;if(k&1)p.odd+=1LL*x*x;else p.even+=1LL*x*x;}if(out)*out=c;return p;}
static long long W(const Parts&p,int lam){return 16*p.even+1LL*lam*p.odd;}
static Parts eval_flip(const Seq&s,const Corr&c,const Parts&p,int b){Parts q=p;int sb=s[b];for(int k=1;k<100;k++){int t=0;if(b+k<100)t+=sb*int(s[b+k]);if(b-k>=0)t+=int(s[b-k])*sb;if(!t)continue;int d=-2*t;long long de=2LL*c[k]*d+1LL*d*d;if(k&1)q.odd+=de;else q.even+=de;}return q;}
static void flip(Seq&s,Corr&c,Parts&p,int b){int sb=s[b];for(int k=1;k<100;k++){int t=0;if(b+k<100)t+=sb*int(s[b+k]);if(b-k>=0)t+=int(s[b-k])*sb;if(!t)continue;int d=-2*t;long long de=2LL*c[k]*d+1LL*d*d;c[k]+=d;if(k&1)p.odd+=de;else p.even+=de;}s[b]=-s[b];}
static Seq neg(Seq s){for(auto&v:s)v=-v;return s;}static Seq rev(Seq s){std::reverse(s.begin(),s.end());return s;}static Seq alt(Seq s){for(int i=0;i<100;i+=2)s[i]=-s[i];return s;}
static std::array<Seq,8> orbit(const Seq&s){std::array<Seq,8>o{};int j=0;for(Seq b:{s,rev(s)}){for(Seq t:{b,alt(b)}){o[j++]=t;o[j++]=neg(t);}}return o;}
static int mindist(const Seq&s,const std::array<Seq,8>&o){int best=100;for(auto&t:o){int d=0;for(int i=0;i<100;i++)d+=s[i]!=t[i];best=std::min(best,d);}return best;}
struct R{long long best=578,far=(1LL<<60);Parts bp{50,528},fp{};Seq bs{},fs{};int far_d=0;};
static R one(std::mt19937_64&rng,int cycles,long long steps,int kick_every,int kick_size){Seq inc=parse(INCSTR),s=inc;Corr c{};Parts p=parts(s,&c);auto orb=orbit(inc);R r;r.bs=s;std::array<long long,100>tabu{};std::uniform_int_distribution<int>ten(6,18);std::array<int,100>ord{};for(int i=0;i<100;i++)ord[i]=i;long long g=0;const std::array<int,15>sched={16,8,4,2,1,0,1,2,4,8,16,32,64,32,16};
 for(int cyc=0;cyc<cycles;cyc++)for(int lam:sched){long long sbest=W(p,lam),last=g;for(long long st=0;st<steps;st++,g++){long long bw=LLONG_MAX;int bb=-1;Parts bq{};std::shuffle(ord.begin(),ord.end(),rng);for(int b:ord){Parts q=eval_flip(s,c,p,b);long long w=W(q,lam);bool tb=g<tabu[b];if(tb && q.odd+q.even>=r.best)continue;if(w<bw){bw=w;bb=b;bq=q;}}if(bb<0){tabu.fill(0);continue;}flip(s,c,p,bb);tabu[bb]=g+ten(rng);long long e=p.odd+p.even;if(e<r.best){r.best=e;r.bp=p;r.bs=s;}int d=mindist(s,orb);if(d>=8 && e<r.far){r.far=e;r.fp=p;r.fs=s;r.far_d=d;}if(bw<sbest){sbest=bw;last=g;}if(kick_every>0&&g-last>=kick_every){std::array<int,100>idx{};for(int i=0;i<100;i++)idx[i]=i;std::shuffle(idx.begin(),idx.end(),rng);for(int j=0;j<kick_size;j++)flip(s,c,p,idx[j]);tabu.fill(0);last=g;}}
 }
 return r;}
int main(int argc,char**argv){int runs=16,threads=0,cycles=6,kick_every=2500,kick_size=10;long long steps=3000;uint64_t seed=1;for(int i=1;i<argc;i++){std::string a=argv[i];auto n=[&](){return std::string(argv[++i]);};if(a=="--runs")runs=std::stoi(n());else if(a=="--threads")threads=std::stoi(n());else if(a=="--cycles")cycles=std::stoi(n());else if(a=="--steps")steps=std::stoll(n());else if(a=="--seed")seed=std::stoull(n());}
#ifdef _OPENMP
 if(threads<=0)threads=omp_get_max_threads();omp_set_num_threads(threads);
#else
 threads=1;
#endif
 long long gbest=578,gfar=LLONG_MAX;R gr;auto t0=std::chrono::steady_clock::now();
#pragma omp parallel for schedule(dynamic,1)
 for(int r=0;r<runs;r++){std::mt19937_64 rng(seed+0x9e3779b97f4a7c15ULL*(r+1));R x=one(rng,cycles,steps,kick_every,kick_size);
#pragma omp critical
 {if(x.best<gbest){gbest=x.best;gr=x;std::cout<<"BREAK best="<<x.best<<" odd="<<x.bp.odd<<" even="<<x.bp.even<<" seq="<<fmt(x.bs)<<"\n";}if(x.far<gfar){gfar=x.far;gr=x;std::cout<<"FAR energy="<<x.far<<" odd="<<x.fp.odd<<" even="<<x.fp.even<<" d="<<x.far_d<<" run="<<r<<" seq="<<fmt(x.fs)<<"\n"<<std::flush;}}}
 double sec=std::chrono::duration<double>(std::chrono::steady_clock::now()-t0).count();std::cout<<"FINAL best="<<gbest<<" far="<<gfar<<" seconds="<<sec<<"\n";return gbest<578?0:1;}
