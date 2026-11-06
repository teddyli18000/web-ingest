// Constructive N=99 core / N=100 boundary Pareto homotopy for LABS.
// E100 = E99 + 99 - 2|H|, H = sum_{k=1}^{98} C99(k)*s_(99-k).
// Run: binary <steps> <seed> <mode> <restart>
// mode=0: original LABS100 scalar fitness, mode=1: changing Pareto weight.
#include <algorithm>
#include <array>
#include <cassert>
#include <cmath>
#include <climits>
#include <cstdint>
#include <iostream>
#include <numeric>
#include <random>
#include <string>
using namespace std;
using Seq=array<int8_t,99>;using Corr=array<int,99>;
static constexpr char N100[]="++++++--+++++-----++-++--+--++++++++++---+-++--++++-+--++----+--+-+-+-+-++---++---++-+-++-+-++--+-+-";
static constexpr char HEX99[]="0CF30C003783CBCC8DA92AAD4";
struct State {Seq s{};Corr c{};int e=0,h=0;};
struct Delta {int e=0,h=0;};
uint64_t mix(uint64_t x){x+=0x9e3779b97f4a7c15ULL;x=(x^(x>>30))*0xbf58476d1ce4e5b9ULL;x=(x^(x>>27))*0x94d049bb133111ebULL;return x^(x>>31);}
void score(State &z){z.c.fill(0);z.e=z.h=0;for(int k=1;k<99;k++){int c=0;for(int i=0;i<99-k;i++)c+=z.s[i]*z.s[i+k];z.c[k]=c;z.e+=c*c;z.h+=c*z.s[99-k];}}
Delta change(const State&z,int p){Delta v;int old=z.s[p];for(int k=1;k<99;k++){int t=0;if(p+k<99)t+=z.s[p+k];if(p>=k)t+=z.s[p-k];int d=-2*old*t;v.e+=2*z.c[k]*d+d*d;v.h+=d*z.s[99-k];if(p>=1&&k==99-p)v.h+=-2*old*(z.c[k]+d);}return v;}
void flip(State &z,int p){Delta v=change(z,p);int old=z.s[p];for(int k=1;k<99;k++){int t=0;if(p+k<99)t+=z.s[p+k];if(p>=k)t+=z.s[p-k];z.c[k]+=-2*old*t;}z.e+=v.e;z.h+=v.h;z.s[p]=-old;}
int energy100(const State&z,int tail){array<int,100>s{};for(int i=0;i<99;i++)s[i]=z.s[i];s[99]=tail;int e=0;for(int k=1;k<100;k++){int c=0;for(int i=0;i<100-k;i++)c+=s[i]*s[i+k];e+=c*c;}return e;}
string sequence(const State&z,int tail){string v;for(int s:z.s)v+=s>0?'+':'-';v+=tail>0?'+':'-';return v;}
State source99(){State z;int i=0;for(char c:string(HEX99)){int v=stoi(string(1,c),nullptr,16);for(int b=3;b>=0&&i<99;b--,i++)z.s[i]=(v>>b&1)?-1:1;}reverse(z.s.begin(),z.s.end());score(z);assert(z.e==553&&abs(z.h)==23);return z;}
State skew99(){State z;for(int i=0;i<99;i++)z.s[i]=N100[i+1]=='+'?1:-1;score(z);assert(z.e==577&&abs(z.h)==49);return z;}
int fullE(const State&z){return z.e+99-2*abs(z.h);}
int tailOf(const State&z){return z.h<0?1:-1;}
struct Record{int e=INT_MAX;State s{};long long at=0;};
void record(const State&z,Record&best,long long iter){int e=fullE(z);if(e>=best.e)return;assert(e==energy100(z,tailOf(z)));best={e,z,iter};cerr<<"RECORD E="<<e<<" E99="<<z.e<<" H="<<abs(z.h)<<" step="<<iter<<" seq="<<sequence(z,tailOf(z))<<"\n";}
void check(){auto a=source99(),b=skew99();assert(fullE(a)==606&&fullE(b)==578);for(auto z:{a,b}){for(int p=0;p<99;p++){auto d=change(z,p);auto q=z;flip(q,p);assert(q.e==z.e+d.e&&q.h==z.h+d.h);auto fresh=q;score(fresh);assert(fresh.e==q.e&&fresh.h==q.h);}assert(energy100(z,tailOf(z))==fullE(z));}}
int main(int argc,char**argv){
 int steps=argc>1?stoi(argv[1]):200000,mode=argc>3?stoi(argv[3]):1,restart=argc>4?stoi(argv[4]):2500;
 uint64_t seed=argc>2?stoull(argv[2]):1;mt19937_64 rng(mix(seed));check();
 auto parentA=source99(),parentB=skew99();Record best;record(parentA,best,0);record(parentB,best,0);
 const array<double,9> weights{0.25,0.38,0.44,0.48,0.54,0.65,0.80,1.0,1.3};
 array<State,9> archive{};array<double,9> archiveScore;archiveScore.fill(1e100);
 auto consider=[&](const State&z){for(int j=0;j<9;j++){double f=z.e-2*weights[j]*abs(z.h);if(f<archiveScore[j]){archive[j]=z;archiveScore[j]=f;}}};
 consider(parentA);consider(parentB);State z=parentA;array<long long,99>tabu{};
 array<int,99>order{};iota(order.begin(),order.end(),0);
 long long near=0,intermediate=0;int bestIntermediate=INT_MAX;
 for(long long step=1;step<=steps;step++){
  int stage=(step-1)/restart;int section=(step-1)%restart;
  if(section==0){
   if(mode==0)z=(stage%2?parentB:parentA);
   else z=(rng()%6==0)?(stage%2?parentB:parentA):archive[stage%9];
   if(stage>0){int n=2+(rng()%15);for(int j=0;j<n;j++)flip(z,rng()%99);}
   tabu.fill(0);
  }
  double lambda=mode==0?1.0:weights[stage%9];
  shuffle(order.begin(),order.end(),rng);int chosen=-1;double bestScore=1e100;
  for(int p:order){
   Delta d=change(z,p);int ep=z.e+d.e,hp=z.h+d.h;
   int full=ep+99-2*abs(hp);
   if(full<best.e){auto w=z;flip(w,p);record(w,best,step);}
   if(tabu[p]>step&&full>=best.e)continue;
   double f=ep-2*lambda*abs(hp);
   if(f<bestScore){bestScore=f;chosen=p;}
  }
  assert(chosen>=0);flip(z,chosen);tabu[chosen]=step+8+(rng()%9);
  record(z,best,step);if(mode==1)consider(z);
  if(z.e<577&&abs(z.h)>23){intermediate++;bestIntermediate=min(bestIntermediate,fullE(z));}
  if(fullE(z)<=606)near++;
  if(step%50000==0){State t=z;score(t);assert(t.e==z.e&&t.h==z.h);cerr<<"PROGRESS steps="<<step<<" mode="<<mode<<" best="<<best.e<<" bridge="<<intermediate<<" minBridge="<<bestIntermediate<<"\n";}
  if(best.e<=574)break;
 }
 cout<<"SUMMARY seed="<<seed<<" mode="<<mode<<" steps="<<steps<<" best="<<best.e<<" E99="<<best.s.e<<" H="<<abs(best.s.h)<<" near="<<near<<" bridge="<<intermediate<<" bestBridge="<<bestIntermediate<<" seq="<<sequence(best.s,tailOf(best.s))<<"\n";
}
