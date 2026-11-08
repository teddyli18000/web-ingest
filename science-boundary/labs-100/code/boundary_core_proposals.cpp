// N100 constructive outer-boundary proposals plus 50/60/70/80-spin
// conditional core repair. No hidden target is used to score proposals.
// modes: 0=E578 outer flips, 1=E606 outer flips,
//        2=E578 core / E606 donor outer, 3=E606 core / E578 donor outer.
// g++ -O3 -std=c++20 -fopenmp code/boundary_core_proposals.cpp -o /tmp/propose
// /tmp/propose 0 100 8000 50 0
#include <algorithm>
#include <array>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <random>
#include <vector>
#include <string>
#include <numeric>
#include <chrono>
#include <climits>
#ifdef _OPENMP
#include <omp.h>
#endif
using namespace std;
const string A="++++++--+++++-----++-++--+--++++++++++---+-++--++++-+--++----+--+-+-+-+-++---++---++-+-++-+-++--+-+-";
const string B="+++++--++----++--++++--++++++++++++--+----+++++----++-+----++--++-+++--+--+-+-++-++-+-+-+-+-+--+-+-+";
struct State{
 vector<int8_t>s;vector<int>c;int e=0;
 State(vector<int8_t> v):s(move(v)),c(s.size()){
  int n=s.size();for(int k=1;k<n;k++){int cv=0;for(int i=0;i+k<n;i++)cv+=s[i]*s[i+k];c[k]=cv;e+=cv*cv;}
 }
 int delta(int p)const{int n=s.size(),d=0;for(int k=1;k<n;k++){
  int v=(p>=k?s[p-k]:0)+(p+k<n?s[p+k]:0);int dc=-2*s[p]*v;d+=2*c[k]*dc+dc*dc;
 }return d;}
 void flip(int p){int n=s.size();for(int k=1;k<n;k++){
  int v=(p>=k?s[p-k]:0)+(p+k<n?s[p+k]:0),dc=-2*s[p]*v;e+=2*c[k]*dc+dc*dc;c[k]+=dc;
 }s[p]*=-1;}
};
vector<int8_t> frompm(const string&s){vector<int8_t>v;for(char c:s)v.push_back(c=='+'?1:-1);return v;}
string aspm(const vector<int8_t>&s){string o;for(int a:s)o+=(a>0?'+':'-');return o;}
int orbit_dist(const vector<int8_t>&s,const vector<int8_t>&ref){int n=s.size(),best=n;for(int rev=0;rev<2;rev++)for(int neg=0;neg<2;neg++)for(int alt=0;alt<2;alt++){
 int d=0;for(int i=0;i<n;i++)d+=s[i]!=ref[rev?n-1-i:i]*((neg^(alt&&(i&1)))?-1:1);best=min(best,d);
}return best;}
struct Result{int energy;int plusbest=INT32_MAX;int novelty=INT32_MAX;vector<int8_t>best;vector<int8_t>novel;long long evals=0;};
Result reconstruct(State init,const vector<int>&core,mt19937_64&rng,int steps){
 State cur=init,best=init;vector<int>taboo(init.s.size(),0),order=core;
 int since=0;long long evals=0;
 for(int step=1;step<=steps;step++){
  int pos=-1,val=INT32_MAX,fb=INT32_MAX,fbpos=0;
  shuffle(order.begin(),order.end(),rng);
  for(int p:order){int e=cur.e+cur.delta(p);evals++;
   if(e<fb){fb=e;fbpos=p;}
   if(step>=taboo[p] || e<best.e){if(e<val){val=e;pos=p;}}
  }
  if(pos<0)pos=fbpos;
  cur.flip(pos);taboo[pos]=step+6+(int)(rng()%12);
  if(cur.e<best.e){best=cur;since=0;}else since++;
  if(since>=300){cur=best;shuffle(order.begin(),order.end(),rng);
   for(int i=0,count=8+(int)(rng()%22);i<count;i++)cur.flip(order[i]);
   fill(taboo.begin(),taboo.end(),0);since=0;
  }
 }
 if(State(best.s).e!=best.e)abort();
 return {best.e,INT32_MAX,INT32_MAX,best.s,{},evals};
}
int main(int argc,char**argv){if(argc!=6)return 1;
 int mode=atoi(argv[1]),trials=atoi(argv[2]),steps=atoi(argv[3]),width=atoi(argv[4]),seedtag=atoi(argv[5]);
 vector<int8_t>source=frompm((mode%2==0)?A:B),donor=frompm((mode%2==0)?B:A);
#ifdef _OPENMP
 omp_set_num_threads(4);
#endif
 vector<Result> results(trials);
 auto start=chrono::steady_clock::now();
#pragma omp parallel for schedule(dynamic,1)
 for(int trial=0;trial<trials;trial++){
  mt19937_64 rng(20261108100ULL+seedtag*4838937ULL+(uint64_t)trial*0x9e3779b97f4a7c15ULL);
  vector<int> core;core.reserve(width);
  int lo=(trial%3==0)?(100-width)/2:(trial%3==1?0:(int)(rng()%100));
  vector<bool> inside(100,false);
  for(int i=0;i<width;i++){int p=(lo+i)%100;core.push_back(p);inside[p]=true;}
  vector<int> outer;
  for(int i=0;i<100;i++)if(!inside[i] && (mode<2 || source[i]!=donor[i]))outer.push_back(i);
  shuffle(outer.begin(),outer.end(),rng);
  int r=1+trial%min(20,int(outer.size()));
  auto proposed=source;
  for(int i=0;i<r;i++)proposed[outer[i]]=(mode<2)?-proposed[outer[i]]:donor[outer[i]];
  Result result=reconstruct(State(proposed),core,rng,steps);
  result.novelty=min(orbit_dist(result.best,frompm(A)),orbit_dist(result.best,frompm(B)));
  int prod=1;for(int b:result.best)prod*=b;
  if(prod>0)result.plusbest=result.energy;
  results[trial]=move(result);
 }
 int best=INT32_MAX,bplus=INT32_MAX,bfar=INT32_MAX;string sb,sp,sfar;
 double mean=0;long long e=0;int cntplus=0,near650=0;
 for(auto&x:results){e+=x.evals;mean+=x.energy;
  if(x.energy<best){best=x.energy;sb=aspm(x.best);}
  if(x.plusbest<bplus){bplus=x.plusbest;sp=aspm(x.best);}
  if(x.novelty>=8 && x.energy<bfar){bfar=x.energy;sfar=aspm(x.best);}
  cntplus+=x.plusbest!=INT32_MAX;near650+=x.energy<=650;
 }
 cout<<"SUMMARY mode="<<mode<<" trials="<<trials<<" width="<<width<<" steps="<<steps<<" seedtag="<<seedtag
 <<" evals="<<e<<" meanE="<<mean/trials<<" bestE="<<best<<" bestPlus="<<bplus<<" bestFar="<<bfar
 <<" plusStates="<<cntplus<<" le650="<<near650<<" wall="<<chrono::duration<double>(chrono::steady_clock::now()-start).count()
 <<" best="<<sb<<" plus="<<sp<<" far="<<sfar<<"\n";
 for(int i=0;i<trials;i++)cout<<"TRIAL "<<i<<" E="<<results[i].energy<<" plus="<<results[i].plusbest
 <<" dist="<<results[i].novelty<<" seq="<<aspm(results[i].best)<<"\n";
}
