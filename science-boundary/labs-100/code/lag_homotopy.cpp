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

using Seq=std::array<int8_t,100>;
using Corr=std::array<int,100>;
struct Parts{long long odd=0,even=0;};

static Parts parts(const Seq&s,Corr*out=nullptr){
 Corr c{};Parts p;
 for(int k=1;k<100;k++){int x=0;for(int i=0;i<100-k;i++)x+=int(s[i])*int(s[i+k]);c[k]=x;if(k&1)p.odd+=1LL*x*x;else p.even+=1LL*x*x;}
 if(out)*out=c;return p;
}
static Seq random_seq(std::mt19937_64&r){Seq s{};for(auto&v:s)v=(r()&1)?1:-1;return s;}
static std::string fmt(const Seq&s){std::string z;z.reserve(100);for(auto v:s)z+=v>0?'+':'-';return z;}
static long long weight(const Parts&p,int lam){return 16*p.even+1LL*lam*p.odd;}

static Parts eval_flip(const Seq&s,const Corr&c,const Parts&p,int bit){
 Parts np=p;int sb=s[bit];
 for(int k=1;k<100;k++){
  int t=0;if(bit+k<100)t+=sb*int(s[bit+k]);if(bit-k>=0)t+=int(s[bit-k])*sb;if(!t)continue;
  int d=-2*t;long long de=2LL*c[k]*d+1LL*d*d;if(k&1)np.odd+=de;else np.even+=de;
 }
 return np;
}
static void do_flip(Seq&s,Corr&c,Parts&p,int bit){
 int sb=s[bit];
 for(int k=1;k<100;k++){
  int t=0;if(bit+k<100)t+=sb*int(s[bit+k]);if(bit-k>=0)t+=int(s[bit-k])*sb;if(!t)continue;
  int d=-2*t;long long de=2LL*c[k]*d+1LL*d*d;c[k]+=d;if(k&1)p.odd+=de;else p.even+=de;
 }
 s[bit]=-s[bit];
}

struct Result{long long e=(1LL<<60);Parts p{};Seq s{};};

static Result run_one(std::mt19937_64&rng,long long steps_per_stage,int kick_every,int kick_size){
 Seq s=random_seq(rng);Corr c{};Parts p=parts(s,&c);
 Result best{p.odd+p.even,p,s};
 // lambda scaled by 16: 0 -> true objective at 16 -> odd-heavy -> return to 16.
 const std::array<int,12> sched={0,1,2,4,8,16,32,64,96,64,32,16};
 std::array<long long,100> tabu{};std::uniform_int_distribution<int> tenure(6,18);
 std::array<int,100> order{};for(int i=0;i<100;i++)order[i]=i;
 long long global_step=0;
 for(int lam:sched){
  long long last_improve=global_step;long long stage_best=weight(p,lam);
  for(long long st=0;st<steps_per_stage;st++,global_step++){
   long long bw=std::numeric_limits<long long>::max();int bb=-1;Parts bp{};
   std::shuffle(order.begin(),order.end(),rng);
   for(int bit:order){
    Parts q=eval_flip(s,c,p,bit);long long w=weight(q,lam);
    bool is_tabu=global_step<tabu[bit];
    if(is_tabu && q.odd+q.even>=best.e)continue;
    if(w<bw){bw=w;bb=bit;bp=q;}
   }
   if(bb<0){tabu.fill(0);continue;}
   do_flip(s,c,p,bb);tabu[bb]=global_step+tenure(rng);
   long long full=p.odd+p.even;
   if(full<best.e){best={full,p,s};}
   if(bw<stage_best){stage_best=bw;last_improve=global_step;}
   if(kick_every>0 && global_step-last_improve>=kick_every){
    std::array<int,100> idx{};for(int i=0;i<100;i++)idx[i]=i;std::shuffle(idx.begin(),idx.end(),rng);
    for(int j=0;j<kick_size;j++)do_flip(s,c,p,idx[j]);tabu.fill(0);last_improve=global_step;
   }
  }
 }
 Corr check{};Parts cp=parts(best.s,&check);if(cp.odd!=best.p.odd||cp.even!=best.p.even){std::cerr<<"consistency failure\n";std::abort();}
 return best;
}

int main(int argc,char**argv){
 int runs=32,threads=0,kick_every=3000,kick_size=10;long long steps=20000,target=574;uint64_t seed=1;
 for(int i=1;i<argc;i++){std::string a=argv[i];auto need=[&](){if(i+1>=argc)throw std::runtime_error("missing value");return std::string(argv[++i]);};
  if(a=="--runs")runs=std::stoi(need());else if(a=="--threads")threads=std::stoi(need());else if(a=="--steps")steps=std::stoll(need());
  else if(a=="--kick-every")kick_every=std::stoi(need());else if(a=="--kick-size")kick_size=std::stoi(need());else if(a=="--seed")seed=std::stoull(need());else if(a=="--target")target=std::stoll(need());else throw std::runtime_error("unknown arg");}
#ifdef _OPENMP
 if(threads<=0)threads=omp_get_max_threads();omp_set_num_threads(threads);
#else
 threads=1;
#endif
 std::vector<long long> vals(runs,(1LL<<60));Result global;auto t0=std::chrono::steady_clock::now();
#pragma omp parallel for schedule(dynamic,1)
 for(int r=0;r<runs;r++){
  std::mt19937_64 rng(seed+0x9e3779b97f4a7c15ULL*(uint64_t)(r+1));Result got=run_one(rng,steps,kick_every,kick_size);vals[r]=got.e;
#pragma omp critical
  if(got.e<global.e){global=got;std::cout<<"BEST energy="<<got.e<<" odd="<<got.p.odd<<" even="<<got.p.even<<" run="<<r<<" seq="<<fmt(got.s)<<"\n"<<std::flush;}
 }
 std::sort(vals.begin(),vals.end());auto q=[&](double f){return vals[(size_t)(f*(vals.size()-1))];};double sec=std::chrono::duration<double>(std::chrono::steady_clock::now()-t0).count();
 std::cout<<"SUMMARY runs="<<runs<<" min="<<vals.front()<<" p10="<<q(.1)<<" median="<<q(.5)<<" p90="<<q(.9)<<" seconds="<<sec<<"\n";
 std::cout<<"FINAL energy="<<global.e<<" odd="<<global.p.odd<<" even="<<global.p.even<<" seq="<<fmt(global.s)<<"\n";
 return global.e<=target?0:1;
}
