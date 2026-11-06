// Exact complete reversal and adjacent block-swap neighborhoods of LABS100.
// Reversal preserves internal aperiodic autocorrelations of the segment.
// Modes: 0=all interval reversals (with/without sign inversion),
// 1=adjacent block exchange with independent sign inversions.
#include <algorithm>
#include <array>
#include <cstdint>
#include <iostream>
#include <climits>
#include <chrono>
#include <cmath>
#include <omp.h>
using namespace std;
using U=__uint128_t;
constexpr int N=100;
static const string inc="++++++--+++++-----++-++--+--++++++++++---+-++--++++-+--++----+--+-+-+-+-++---++---++-+-++-+-++--+-+-";
U mask[N];
inline int pc(U x){return __builtin_popcountll((uint64_t)x)+__builtin_popcountll((uint64_t)(x>>64));}
inline int E(U s,int* O=nullptr){int sum=0,odd=0;for(int k=1;k<100;k++){int c=100-k-2*pc((s^(s>>k))&mask[k]);int z=c*c;sum+=z;if(k&1)odd+=z;}if(O)*O=odd;return sum;}
U fromstr(const string&s){U z=0;for(int i=0;i<100;i++)if(s[i]=='+')z|=(U(1)<<i);return z;}
string fmt(U z){string r;for(int i=0;i<100;i++)r+=((z>>i)&1)?'+':'-';return r;}
inline U take(U s,int i,int j){return (s>>i)&((U(1)<<(j-i))-1);}
U reversebits(U x,int len){U y=0;for(int i=0;i<len;i++)y|=((x>>i)&1)<<(len-i-1);return y;}
U reverse_segment(U s,int i,int j,int negate){
 U orig=take(s,i,j), rev=reversebits(orig,j-i);
 if(negate)rev^=(U(1)<<(j-i))-1;
 return s^(orig<<i)^(rev<<i);
}
U swap_segment(U s,int i,int j,int k,int f1,int f2){
 int m=j-i,n=k-j;
 U a=take(s,i,j),b=take(s,j,k);
 if(f1)a^=(U(1)<<m)-1;
 if(f2)b^=(U(1)<<n)-1;
 U original=take(s,i,k),content=b|(a<<n);
 return s^(original<<i)^(content<<i);
}
struct Result{int best=INT_MAX,odd=INT_MAX,dist=-1;U seq=0;long long checked=0,le650=0,le578=0;};
void note(Result&v,U base,U s){
 int odd=0,e=E(s,&odd);v.checked++;
 if(e<=650)v.le650++;
 if(e<=578)v.le578++;
 if(e<v.best){v.best=e;v.odd=odd;v.dist=pc(base^s);v.seq=s;}
}
int main(int argc,char**argv){
 int mode=argc>1?stoi(argv[1]):0;
 for(int k=1;k<100;k++)mask[k]=(U(1)<<(100-k))-1;
 U base=argc>2?fromstr(argv[2]):fromstr(inc);
 int bE=E(base);
 if(argc==2 && bE!=578)abort();
 auto start=chrono::steady_clock::now();Result best;
 #pragma omp parallel num_threads(4)
 {
  Result local;
  #pragma omp for schedule(dynamic,1)
  for(int i=0;i<100;i++){
   if(mode==0){
    for(int j=i+2;j<=100;j++)
      for(int flip=0;flip<=1;flip++)note(local,base,reverse_segment(base,i,j,flip));
   }else{
    for(int j=i+1;j<100;j++)
      for(int k=j+1;k<=100;k++)
       for(int flags=0;flags<4;flags++)
        note(local,base,swap_segment(base,i,j,k,flags&1,flags>>1));
   }
  }
  #pragma omp critical
  {
   best.checked+=local.checked;
   best.le650+=local.le650;
   best.le578+=local.le578;
   if(local.best<best.best){
     best.best=local.best;best.odd=local.odd;
     best.dist=local.dist;best.seq=local.seq;
   }
  }
 }
 cout<<"SUMMARY mode="<<mode<<" baseE="<<bE<<" tested="<<best.checked
     <<" min="<<best.best<<" O="<<best.odd<<" hamming="<<best.dist
     <<" le578="<<best.le578<<" le650="<<best.le650
     <<" wall_ms="<<chrono::duration_cast<chrono::milliseconds>(
        chrono::steady_clock::now()-start).count()<<" seq="<<fmt(best.seq)<<"\n";
 return 0;
}
