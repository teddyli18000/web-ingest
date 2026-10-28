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
using Seq=std::array<int8_t,100>;using Corr=std::array<int,100>;struct Parts{long long odd=0,even=0;};
static Parts parts(const Seq&s,Corr*out=nullptr){Corr c{};Parts p;for(int k=1;k<100;k++){int x=0;for(int i=0;i<100-k;i++)x+=int(s[i])*int(s[i+k]);c[k]=x;if(k&1)p.odd+=1LL*x*x;else p.even+=1LL*x*x;}if(out)*out=c;return p;}
static Seq random_seq(std::mt19937_64&r){Seq s{};for(auto&v:s)v=(r()&1)?1:-1;return s;}
static Seq parse(const std::string&z){if(z.size()!=100)throw std::runtime_error("start must have length 100");Seq s{};for(int i=0;i<100;i++){if(z[i]!='+'&&z[i]!='-')throw std::runtime_error("bad start");s[i]=z[i]=='+'?1:-1;}return s;}
static std::string fmt(const Seq&s){std::string z;z.reserve(100);for(auto v:s)z+=v>0?'+':'-';return z;}
static long long weight(const Parts&p,int lam){return 16*p.even+1LL*lam*p.odd;}
static Parts eval_flip(const Seq&s,const Corr&c,const Parts&p,int bit){Parts q=p;int sb=s[bit];for(int k=1;k<100;k++){int t=0;if(bit+k<100)t+=sb*int(s[bit+k]);if(bit-k>=0)t+=int(s[bit-k])*sb;if(!t)continue;int d=-2*t;long long de=2LL*c[k]*d+1LL*d*d;if(k&1)q.odd+=de;else q.even+=de;}return q;}
static void flip(Seq&s,Corr&c,Parts&p,int bit){int sb=s[bit];for(int k=1;k<100;k++){int t=0;if(bit+k<100)t+=sb*int(s[bit+k]);if(bit-k>=0)t+=int(s[bit-k])*sb;if(!t)continue;int d=-2*t;long long de=2LL*c[k]*d+1LL*d*d;c[k]+=d;if(k&1)p.odd+=de;else p.even+=de;}s[bit]=-s[bit];}
struct Result{long long e=(1LL<<60);Parts p{};Seq s{};};
static Result run_one(Seq s,std::mt19937_64&rng,long long steps,int kick_every,int kick_size){Corr c{};Parts p=parts(s,&c);Result best{p.odd+p.even,p,s};const std::array<int,14>sched={0,1,2,4,8,16,32,64,96,128,96,64,32,16};std::array<long long,100>tabu{};std::uniform_int_distribution<int>ten(6,18);std::array<int,100>ord{};for(int i=0;i<100;i++)ord[i]=i;long long g=0;for(int lam:sched){long long sb=weight(p,lam),last=g;for(long long st=0;st<steps;st++,g++){long long bw=std::numeric_limits<long long>::max();int bit=-1;std::shuffle(ord.begin(),ord.end(),rng);for(int b:ord){Parts q=eval_flip(s,c,p,b);long long w=weight(q,lam);if(g<tabu[b]&&q.odd+q.even>=best.e)continue;if(w<bw){bw=w;bit=b;}}if(bit<0){tabu.fill(0);continue;}flip(s,c,p,bit);tabu[bit]=g+ten(rng);long long e=p.odd+p.even;if(e<best.e)best={e,p,s};if(bw<sb){sb=bw;last=g;}if(kick_every>0&&g-last>=kick_every){std::array<int,100>idx{};for(int i=0;i<100;i++)idx[i]=i;std::shuffle(idx.begin(),idx.end(),rng);for(int j=0;j<kick_size;j++)flip(s,c,p,idx[j]);tabu.fill(0);last=g;}}}Parts cp=parts(best.s);if(cp.odd!=best.p.odd||cp.even!=best.p.even)std::abort();return best;}
int main(int argc,char**argv){int runs=32,threads=0,kick_every=3000,kick_size=10,perturb=0;long long steps=20000,target=574;uint64_t seed=1;std::string start;for(int i=1;i<argc;i++){std::string a=argv[i];auto need=[&](){if(i+1>=argc)throw std::runtime_error("missing value");return std::string(argv[++i]);};if(a=="--runs")runs=std::stoi(need());else if(a=="--threads")threads=std::stoi(need());else if(a=="--steps")steps=std::stoll(need());else if(a=="--kick-every")kick_every=std::stoi(need());else if(a=="--kick-size")kick_size=std::stoi(need());else if(a=="--seed")seed=std::stoull(need());else if(a=="--target")target=std::stoll(need());else if(a=="--start")start=need();else if(a=="--perturb")perturb=std::stoi(need());else throw std::runtime_error("unknown arg");}
#ifdef _OPENMP
if(threads<=0)threads=omp_get_max_threads();omp_set_num_threads(threads);
#else
threads=1;
#endif
Seq base{};bool supplied=!start.empty();if(supplied)base=parse(start);std::vector<long long>vals(runs,(1LL<<60));Result global;auto t0=std::chrono::steady_clock::now();
#pragma omp parallel for schedule(dynamic,1)
for(int r=0;r<runs;r++){std::mt19937_64 rng(seed+0x9e3779b97f4a7c15ULL*(uint64_t)(r+1));Seq s=supplied?base:random_seq(rng);if(supplied&&perturb>0){std::array<int,100>idx{};for(int i=0;i<100;i++)idx[i]=i;std::shuffle(idx.begin(),idx.end(),rng);for(int j=0;j<perturb;j++)s[idx[j]]=-s[idx[j]];}Result got=run_one(s,rng,steps,kick_every,kick_size);vals[r]=got.e;
#pragma omp critical
if(got.e<global.e){global=got;std::cout<<"BEST energy="<<got.e<<" odd="<<got.p.odd<<" even="<<got.p.even<<" run="<<r<<" seq="<<fmt(got.s)<<"\n"<<std::flush;}}
std::sort(vals.begin(),vals.end());auto q=[&](double f){return vals[(size_t)(f*(vals.size()-1))];};double sec=std::chrono::duration<double>(std::chrono::steady_clock::now()-t0).count();std::cout<<"SUMMARY runs="<<runs<<" min="<<vals.front()<<" p10="<<q(.1)<<" median="<<q(.5)<<" p90="<<q(.9)<<" seconds="<<sec<<"\n";std::cout<<"FINAL energy="<<global.e<<" odd="<<global.p.odd<<" even="<<global.p.even<<" seq="<<fmt(global.s)<<"\n";return global.e<=target?0:1;}
