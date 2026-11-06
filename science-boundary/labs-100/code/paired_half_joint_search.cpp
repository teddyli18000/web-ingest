// Constructive paired-swap LABS pilot with parity-half sums fixed to (2,2).
// For two flipped coordinates p,q, pair correlation increments equal the sum
// of independent increments plus 4*s[p]*s[q] at lag |p-q|. This evaluates all
// 25*24 candidate opposite-sign swaps exactly before making each move.
// Scalarized even + lambda*odd objectives test whether low odd energy and low
// total energy can be approached together. Not an exhaustive certificate.
#include <array>
#include <algorithm>
#include <chrono>
#include <climits>
#include <cstdint>
#include <iostream>
#include <numeric>
#include <random>
#include <string>
#include <vector>
using namespace std;
using S=array<int8_t,100>;using C=array<int,100>;
static const string INC="++++++--+++++-----++-++--+--++++++++++---+-++--++++-+--++----+--+-+-+-+-++---++---++-+-++-+-++--+-+-";
int energy(const S &s,C *out=nullptr,int *oddOut=nullptr){
 int E=0,O=0;C c{};
 for(int k=1;k<100;k++){
  int t=0;for(int i=0;i<100-k;i++)t+=s[i]*s[i+k];
  c[k]=t;E+=t*t;if(k%2)O+=t*t;
 }
 if(out)*out=c;if(oddOut)*oddOut=O;return E;
}
int seqsum(const S&s,int parity){
 int a=0;for(int i=parity;i<100;i+=2)a+=s[i];return a;
}
string fmt(const S&s){string z;for(int x:s)z+=x>0?'+':'-';return z;}
void normalize(S&s,int parity,int want,mt19937_64&r){
 int sum=seqsum(s,parity);
 while(sum!=want){
  int p=2*(r()%50)+parity;
  if(sum>want&&s[p]==1){s[p]=-1;sum-=2;}
  else if(sum<want&&s[p]==-1){s[p]=1;sum+=2;}
 }
}
void update_flip(S&s,C&c,int&e,int&o,int p){
 int sb=s[p];
 for(int k=1;k<100;k++){
  int t=0;
  if(p+k<100)t+=sb*s[p+k];
  if(p>=k)t+=s[p-k]*sb;
  if(!t)continue;
  int d=-2*t,delta=2*c[k]*d+d*d;
  e+=delta;if(k&1)o+=delta;c[k]+=d;
 }
 s[p]=-sb;
}
void update_swap(S&s,C&c,int&e,int&o,int p,int q){
 update_flip(s,c,e,o,p);update_flip(s,c,e,o,q);
}
struct Pair{int p=-1,q=-1,dE=0,dO=0,dw=INT_MAX;};
Pair findmove(const S&s,const C&c,int E,int lambda,
              const array<int,100>&tabu,int step,int best,mt19937_64&r){
 int d[100][100]{},de[100]{},doo[100]{};
 for(int p=0;p<100;p++){
  int sp=s[p];
  for(int k=1;k<100;k++){
   int t=0;
   if(p+k<100)t+=sp*s[p+k];
   if(p>=k)t+=s[p-k]*sp;
   d[p][k]=-2*t;
   int x=2*c[k]*d[p][k]+d[p][k]*d[p][k];
   if(k&1)doo[p]+=x;else de[p]+=x;
  }
 }
 Pair out;int ties=0;
 for(int p=0;p<100;p++){
  for(int q=p+2;q<100;q+=2)if(s[p]!=s[q]){
   int o=doo[p]+doo[q],v=de[p]+de[q];
   for(int k=1;k<100;k++){
    int x=2*d[p][k]*d[q][k];
    if(k&1)o+=x;else v+=x;
   }
   // Both spins flipped: restore the mutual bond that two one-flip
   // deltas counted twice. Since p,q have same parity, lag q-p is even.
   int k=q-p,x=4*s[p]*s[q];
   v+=2*(c[k]+d[p][k]+d[q][k])*x+x*x;
   int score=v+lambda*o;
   if((step<tabu[p]||step<tabu[q]) && E+v+o>=best)continue;
   if(score<out.dw){out={p,q,v,o,score};ties=1;}
   else if(score==out.dw&&r()%++ties==0){out={p,q,v,o,score};}
  }
 }
 return out;
}
struct Result{int e=INT_MAX,o=INT_MAX;S s{};};
Result run(S s,mt19937_64&r,int rounds,int steps,const vector<int>&sched){
 C c{};int o=0,e=energy(s,&c,&o);
 Result res{e,o,s};array<int,100>tabu{};int step=0;
 for(int round=0;round<rounds;round++){
  int lambda=sched[round%sched.size()];
  for(int t=0;t<steps;t++){
   Pair m=findmove(s,c,e,lambda,tabu,step,res.e,r);step++;
   if(m.p<0){tabu.fill(0);continue;}
   int oldE=e,oldO=o;
   update_swap(s,c,e,o,m.p,m.q);
   if(e!=oldE+m.dE+m.dO || o!=oldO+m.dO)abort();
   tabu[m.p]=step+4+(r()%9);tabu[m.q]=step+4+(r()%9);
   if(e<res.e){
    res={e,o,s};
    cerr<<"BEST e="<<e<<" odd="<<o<<" round="<<round
        <<" step="<<step<<" seq="<<fmt(s)<<"\n";
   }
  }
  for(int j=0;j<3;j++){
   int parity=r()%2,p=2*(r()%50)+parity,q=2*(r()%50)+parity;
   while(s[p]==s[q])q=2*(r()%50)+parity;
   update_swap(s,c,e,o,p,q);
  }
  tabu.fill(0);
 }
 int checkO,checkE=energy(res.s,nullptr,&checkO);
 if(checkE!=res.e||checkO!=res.o)abort();
 return res;
}
int main(int argc,char**argv){
 int runs=argc>1?stoi(argv[1]):10;
 int steps=argc>2?stoi(argv[2]):200;
 int rounds=argc>3?stoi(argv[3]):10;
 int seed=argc>4?stoi(argv[4]):42;
 int mode=argc>5?stoi(argv[5]):0;
 auto begin=chrono::steady_clock::now();mt19937_64 r(seed);
 S inc{};for(int i=0;i<100;i++)inc[i]=INC[i]=='+'?1:-1;
 Result global;vector<int>scores;
 const vector<int> schedule0{1,4,16,8,2,1,1,4,16,1};
 const vector<int> schedule1{4,16,32,16,8,4,2,1,1,1};
 for(int j=0;j<runs;j++){
  S s{};
  if(j%3==0){s=inc;normalize(s,0,2,r);normalize(s,1,2,r);}
  else{
   for(auto&v:s)v=r()%2?1:-1;
   normalize(s,0,2,r);normalize(s,1,2,r);
  }
  Result v=run(s,r,rounds,steps,mode?schedule1:schedule0);
  scores.push_back(v.e);
  if(v.e<global.e){
   global=v;
   cout<<"GLOBAL e="<<v.e<<" odd="<<v.o
       <<" run="<<j<<" seq="<<fmt(v.s)<<"\n";
  }
  cout<<"RUN i="<<j<<" E="<<v.e<<" O="<<v.o<<"\n"<<flush;
 }
 sort(scores.begin(),scores.end());
 cout<<"SUMMARY runs="<<runs<<" steps="<<steps<<" rounds="<<rounds
     <<" mode="<<mode<<" best="<<global.e<<" odd="<<global.o
     <<" median="<<scores[scores.size()/2]
     <<" ms="<<chrono::duration_cast<chrono::milliseconds>(
        chrono::steady_clock::now()-begin).count()
     <<" seq="<<fmt(global.s)<<"\n";
}
