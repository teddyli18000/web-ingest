// Constructive conditional-QUBO search for N=100 LABS, O=58 layer.
// With parity halves A_i=s_(2i), B_i=s_(2i+1),
// C_(2r+1) = sum_{j>=r} A_(j-r) B_j + sum_{j+r+1<50} A_(j+r+1) B_j.
// Hence fixing A yields the exact quadratic form O=B^T (T^T T) B.
// The dual fixed-B form is obtained by swapping the indexing rule.
// Runs are heuristic, never exhaustive.
#include <array>
#include <algorithm>
#include <chrono>
#include <cmath>
#include <climits>
#include <cstdint>
#include <iostream>
#include <numeric>
#include <random>
#include <string>
using namespace std;
static constexpr int N=50;
using H=array<int8_t,N>;
const string incumbent="++++++--+++++-----++-++--+--++++++++++---+-++--++++-+--++----+--+-+-+-+-++---++---++-+-++-+-++--+-+-";
static auto C0=chrono::steady_clock::now();
struct Q {
 int mat[N][N]{},diag[N]{},h[N]{},val=0;
 void init(const H& fixed,const H& moving,bool move_b){
  int T[N][N]{};
  for(int r=0;r<N;r++)for(int j=0;j<N;j++){
   if(move_b){if(j>=r)T[r][j]+=fixed[j-r];if(j+r+1<N)T[r][j]+=fixed[j+r+1];}
   else{if(j+r<N)T[r][j]+=fixed[j+r];if(j>=r+1)T[r][j]+=fixed[j-r-1];}
  }
  for(int i=0;i<N;i++)for(int j=0;j<N;j++){
   int z=0;for(int r=0;r<N;r++)z+=T[r][i]*T[r][j];mat[i][j]=z;
  }
  val=0;
  for(int i=0;i<N;i++){
   diag[i]=mat[i][i];h[i]=0;
   for(int j=0;j<N;j++)h[i]+=mat[i][j]*moving[j];
   val+=moving[i]*h[i];
  }
 }
 int swap_delta(const H& s,int i,int j) const{
  return -4*s[i]*h[i]+4*diag[i]-4*s[j]*h[j]+4*diag[j]+8*s[i]*s[j]*mat[i][j];
 }
 void flip(H& s,int i){
  int old=s[i];for(int j=0;j<N;j++)h[j]-=2*old*mat[i][j];s[i]=-old;
 }
 void swap(H& s,int i,int j){val+=swap_delta(s,i,j);flip(s,i);flip(s,j);}
};
int fullE(const H&a,const H&b,int*Odd=nullptr){
 int s[100];for(int i=0;i<50;i++){s[2*i]=a[i];s[2*i+1]=b[i];}
 int odd=0,even=0;
 for(int k=1;k<100;k++){
  int c=0;for(int i=0;i<100-k;i++)c+=s[i]*s[i+k];
  (k&1?odd:even)+=c*c;
 }
 if(Odd)*Odd=odd;
 return odd+even;
}
string seq(const H&a,const H&b){
 string s;for(int i=0;i<50;i++){s+=(a[i]==1?'+':'-');s+=(b[i]==1?'+':'-');}return s;
}
void sum2(H& h,mt19937_64&r){
 int sum=accumulate(h.begin(),h.end(),0);
 while(sum!=2){
  int i=r()%N;
  if(sum>2&&h[i]==1){h[i]=-1;sum-=2;}
  if(sum<2&&h[i]==-1){h[i]=1;sum+=2;}
 }
}
H random2(mt19937_64&r){
 H h;for(int i=0;i<N;i++)h[i]=i<26?1:-1;
 shuffle(h.begin(),h.end(),r);return h;
}
int polish(H& moving,const H&fixed,bool move_b,mt19937_64&rng,int steps,int tenure){
 Q q;q.init(fixed,moving,move_b);
 int best=q.val;H bestS=moving;
 int tabu[N]{};
 for(int step=1;step<=steps;step++){
  int chooseI=-1,chooseJ=-1,minimum=INT_MAX,ties=0;
  for(int i=0;i<N;i++)if(moving[i]==1)
   for(int j=0;j<N;j++)if(moving[j]==-1){
    int d=q.swap_delta(moving,i,j);
    if((step<tabu[i]||step<tabu[j])&&(q.val+d>=best))continue;
    if(d<minimum){minimum=d;chooseI=i;chooseJ=j;ties=1;}
    else if(d==minimum&&rng()%++ties==0){chooseI=i;chooseJ=j;}
   }
  if(chooseI<0){fill(begin(tabu),end(tabu),0);continue;}
  q.swap(moving,chooseI,chooseJ);
  tabu[chooseI]=step+tenure+(rng()%5);
  tabu[chooseJ]=step+tenure+(rng()%5);
  if(q.val<best){best=q.val;bestS=moving;}
 }
 moving=bestS;
 return best;
}
int main(int argc,char**argv){
 int runs=argc>1?stoi(argv[1]):40;
 int steps=argc>2?stoi(argv[2]):120;
 int rounds=argc>3?stoi(argv[3]):12;
 int seed=argc>4?stoi(argv[4]):1;
 H incA{},incB{};
 for(int i=0;i<N;i++){incA[i]=incumbent[i*2]=='+'?1:-1;incB[i]=incumbent[i*2+1]=='+'?1:-1;}
 mt19937_64 r(seed);
 int minOdd=INT_MAX,minE=INT_MAX,hit58=0,hit50=0,minAt58=INT_MAX;
 for(int run=0;run<runs;run++){
  H a,b;
  if(run%3==0){a=incA;b=incB;sum2(a,r);sum2(b,r);}
  else if(run%3==1){a=random2(r);b=incB;sum2(b,r);}
  else{a=random2(r);b=random2(r);}
  int bestOdd=INT_MAX,bestE=INT_MAX,local50=0,local58=0;
  for(int round=0;round<rounds;round++){
   polish(b,a,true,r,steps,7);polish(a,b,false,r,steps,7);
   int o=0,e=fullE(a,b,&o);
   bestOdd=min(o,bestOdd);bestE=min(e,bestE);
   if(o==50){local50++;hit50++;}
   if(o==58){local58++;hit58++;minAt58=min(minAt58,e);}
   if(o<minOdd || (o==minOdd && e<minE)){
    if(o<minOdd)minE=INT_MAX;
    minOdd=o;minE=min(minE,e);
    cout<<"ODD best="<<o<<" E="<<e<<" run="<<run<<" round="<<round<<" s="<<seq(a,b)<<"\n"<<flush;
   }
   if(e<minE)minE=e;
   if(round+1<rounds){
    int n=1+(r()%5);
    for(int k=0;k<n;k++){
     H&h=(r()%2)?a:b;int i=r()%N,j=r()%N;
     while(h[i]!=1)i=r()%N;while(h[j]!=-1)j=r()%N;
     swap(h[i],h[j]);
    }
   }
  }
  cout<<"RUN i="<<run<<" odd="<<bestOdd<<" E="<<bestE
      <<" hits50="<<local50<<" hits58="<<local58<<"\n"<<flush;
 }
 int ms=chrono::duration_cast<chrono::milliseconds>(chrono::steady_clock::now()-C0).count();
 cout<<"SUMMARY runs="<<runs<<" steps="<<steps<<" rounds="<<rounds
     <<" bestOdd="<<minOdd<<" bestESeen="<<minE
     <<" O50="<<hit50<<" O58="<<hit58
     <<" minAt58="<<minAt58<<" ms="<<ms<<"\n";
}
