// Two-ended constructive beam for aperiodic LABS.
// Each step fixes the next left/right endpoint sign jointly; only known
// pair-products contribute to partial correlations. Hidden teacher bits are
// never used. Supports raw partial-E and remaining-pairs-weighted rankings.
// Build: g++ -O3 -std=c++20 -fopenmp code/two_end_beam.cpp -o /tmp/beam
// Example: /tmp/beam 60 100000 4 256 11
#include <algorithm>
#include <array>
#include <chrono>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <string>
#include <vector>
#include <numeric>
#include <climits>
#ifdef _OPENMP
#include <omp.h>
#endif
using namespace std;
using U=__uint128_t;
static uint64_t mix(uint64_t x){x+=0x9e3779b97f4a7c15ULL;x=(x^(x>>30))*0xbf58476d1ce4e5b9ULL;x=(x^(x>>27))*0x94d049bb133111ebULL;return x^(x>>31);}
struct State {
 U bits=0;
 array<int16_t,100> c{};
 int Q=0,LB=0;
 long long rank=0;
 uint64_t tie=0;
};
struct Result {int best;string witness;long long generated;double wall;};
string fmt(U x,int n){string s;for(int i=0;i<n;i++)s+=((x>>i)&1)?'+':'-';return s;}
int complete_energy(U x,int n){int e=0;for(int k=1;k<n;k++){
 int cc=0;for(int i=0;i+k<n;i++){int a=(x>>i)&1,b=(x>>(i+k))&1;cc+=(a==b)?1:-1;}
 e+=cc*cc;
}return e;}
Result solve(int n,int width,int mode,int noise,int seed,bool diagnostics){
 auto t0=chrono::steady_clock::now();
 vector<array<int16_t,100>> remaining(n/2+1);
 for(int t=0;t<=n/2;t++)for(int k=1;k<n;k++){
  int known=0;for(int i=0;i+k<n;i++){
   bool il=(i<t)||(i>=n-t),jr=(i+k<t)||(i+k>=n-t);
   known+=il&&jr;
  }
  remaining[t][k]=n-k-known;
 }
 vector<State> beam(1);long long generated=0;
 for(int t=0;t<n/2;t++){
  int L=t,R=n-1-t;
  vector<State> children(beam.size()*4);
#pragma omp parallel for schedule(static) if(beam.size()>100)
  for(size_t p=0;p<beam.size();p++){
   const auto &base=beam[p];
   array<int16_t,100> dl{},dr{};
   for(int j=0;j<t;j++){
    int v=(base.bits>>j)&1?1:-1;
    dl[L-j]+=v;dr[R-j]+=v;
   }
   for(int j=n-t;j<n;j++){
    int v=(base.bits>>j)&1?1:-1;
    dl[j-L]+=v;dr[j-R]+=v;
   }
   for(int choice=0;choice<4;choice++){
    int x=(choice&1)?1:-1,y=(choice&2)?1:-1;
    State w=base;
    if(x==1)w.bits|=U(1)<<L;
    if(y==1)w.bits|=U(1)<<R;
    int score=0,bound=0;
    for(int k=1;k<n;k++){
     int ck=int(base.c[k])+x*int(dl[k])+y*int(dr[k])+(k==R-L?x*y:0);
     w.c[k]=ck;score+=ck*ck;
     int left=max(0,abs(ck)-int(remaining[t+1][k]));
     if((left&1)!=((n-k)&1))left++;
     bound+=left*left;
    }
    w.Q=score;w.LB=bound;
    long long criterion=score;
    if(mode==1)criterion=score+bound;
    if(mode==2)criterion=score+4*bound;
    if(mode==3)criterion=bound*10+score;
    if(mode>=4){
     int alpha=(mode==4?1:mode==5?5:mode==6?20:1);
     criterion=0;
     for(int k=1;k<n;k++){
      int rem=remaining[t+1][k],ck=w.c[k];
      long long den=rem+alpha;
      if(mode==7)den*=den;
      criterion+=((long long)ck*ck*4096)/den;
     }
    }
    uint64_t h=mix(uint64_t(w.bits)^mix(uint64_t(w.bits>>64)+uint64_t(seed)+uint64_t(t)*113));
    w.tie=h;
    w.rank=criterion*256+(int)(h%max(1,noise));
    children[4*p+choice]=w;
   }
  }
  generated+=children.size();
  if(t==0){
   children.erase(remove_if(children.begin(),children.end(),[](auto const&x){return !(x.bits&U(1));}),children.end());
  }
  if(children.size()>size_t(width)){
   nth_element(children.begin(),children.begin()+width,children.end(),[](const State&a,const State&b){
    if(a.rank!=b.rank)return a.rank<b.rank;return a.tie<b.tie;
   });children.resize(width);
  }
  beam.swap(children);
  if(diagnostics&&(t+1==n/4 || t+1==n/2-5 || t+1==n/2)){
   int qmin=INT32_MAX,lbmin=INT32_MAX;
   for(auto& x:beam){qmin=min(qmin,x.Q);lbmin=min(lbmin,x.LB);}
   cerr<<"DEPTH n="<<n<<" t="<<t+1<<" beam="<<beam.size()<<" minQ="<<qmin<<" minLB="<<lbmin<<"\n";
  }
 }
 int best=INT32_MAX;U seq=0;
 for(auto&w:beam){int e=complete_energy(w.bits,n);if(e!=w.Q||e!=w.LB)abort();if(e<best){best=e;seq=w.bits;}}
 return {best,fmt(seq,n),generated,chrono::duration<double>(chrono::steady_clock::now()-t0).count()};
}
int main(int argc,char**argv){if(argc!=6)return 1;
 int n=atoi(argv[1]),width=atoi(argv[2]),mode=atoi(argv[3]),noise=atoi(argv[4]),seed=atoi(argv[5]);
#ifdef _OPENMP
 omp_set_num_threads(4);
#endif
 auto r=solve(n,width,mode,noise,seed,true);
 cout<<"SUMMARY n="<<n<<" width="<<width<<" mode="<<mode<<" noise="<<noise<<" seed="<<seed
 <<" generated="<<r.generated<<" bestE="<<r.best<<" wall="<<r.wall<<" witness="<<r.witness<<"\n";
}
