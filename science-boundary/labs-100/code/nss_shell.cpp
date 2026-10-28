// Exact shells in the 50-variable N=100 near-skew subspace obtained by
// prepending +1 to a length-99 skew-symmetric sequence. Every sequence in
// this subspace has |C_k|=1 at all odd lags. A free-variable flip negates the
// corresponding skew pair (or the center bit), and correlations are updated
// exactly in O(N).
#include <array>
#include <algorithm>
#include <chrono>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <string>
#ifdef _OPENMP
#include <omp.h>
#endif
using S=std::array<int8_t,100>;
using C=std::array<int,100>;

static long long energy(const S&s,C*out=nullptr,long long*odd_out=nullptr){
 C c{}; long long e=0,odd=0;
 for(int k=1;k<100;k++){int x=0;for(int i=0;i<100-k;i++)x+=int(s[i])*int(s[i+k]);c[k]=x;const long long q=1LL*x*x;e+=q;if(k&1)odd+=q;}
 if(out)*out=c;if(odd_out)*odd_out=odd;return e;
}

static void flip_free(S&s,C&c,long long&e,int v){
 // The length-99 tail occupies full-sequence indices 1..99.  Its skew pair
 // for tail index v is 98-v, hence full-sequence index 99-v.  v=49 is the
 // center tail bit and is flipped alone.
 const int p=1+v, q=(v==49?-1:99-v); const int sp=s[p], sq=q>=0?s[q]:0;
 for(int k=1;k<100;k++){
  int t=0;
  if(p+k<100)t+=sp*int(s[p+k]); if(p-k>=0)t+=int(s[p-k])*sp;
  if(q>=0){if(q+k<100)t+=sq*int(s[q+k]);if(q-k>=0)t+=int(s[q-k])*sq;if(k==std::abs(q-p))t-=2*sp*sq;}
  if(t){const int d=-2*t;e+=2LL*c[k]*d+1LL*d*d;c[k]+=d;}
 }
 s[p]=-s[p]; if(q>=0)s[q]=-s[q];
}

static S incumbent(){
 const std::string z="++++++--+++++-----++-++--+--++++++++++---+-++--++++-+--++----+--+-+-+-+-++---++---++-+-++-+-++--+-+-";
 S s{};for(int i=0;i<100;i++)s[i]=z[i]=='+'?1:-1;return s;
}
static std::string format(const S&s){std::string z;z.reserve(100);for(auto v:s)z+=v>0?'+':'-';return z;}
struct Best{long long e=1LL<<60;S s{};unsigned long long tested=0;};

static void recurse(S&s,C&c,long long&e,int start,int left,Best&b){
 if(left==0){++b.tested;if(e<b.e){b.e=e;b.s=s;}return;}
 for(int v=start;v<=50-left;v++){flip_free(s,c,e,v);recurse(s,c,e,v+1,left-1,b);flip_free(s,c,e,v);}
}
static unsigned long long choose(int n,int r){__int128 x=1;for(int i=1;i<=r;i++)x=x*(n-r+i)/i;return (unsigned long long)x;}

int main(int argc,char**argv){
 if(argc<2||argc>3){std::cerr<<"usage: nss_shell <radius> [threads]\n";return 2;}
 const int r=std::stoi(argv[1]); const int threads=argc==3?std::stoi(argv[2]):0;
 if(r<1||r>50)return 2;
 S base=incumbent();C bc{};long long odd=0;long long be=energy(base,&bc,&odd);if(be!=578||odd!=50)return 2;
 // Sanity-check the coordinate map: each single free-variable flip must keep
 // every odd-lag correlation at parity-minimal total energy 50, and the
 // incremental scorer must match an independent full recomputation.
 for(int v=0;v<50;v++){S s=base;C c=bc;long long e=be;flip_free(s,c,e,v);long long o2=0;long long e2=energy(s,nullptr,&o2);if(e!=e2||o2!=50){std::cerr<<"near-skew coordinate check failed at free variable "<<v<<"\n";return 2;}}
 std::array<Best,50> part{};auto t0=std::chrono::steady_clock::now();
#ifdef _OPENMP
 if(threads>0)omp_set_num_threads(threads);
#endif
#pragma omp parallel for schedule(dynamic,1)
 for(int first=0;first<=50-r;first++){S s=base;C c=bc;long long e=be;flip_free(s,c,e,first);recurse(s,c,e,first+1,r-1,part[first]);}
 Best g;for(auto&b:part){g.tested+=b.tested;if(b.e<g.e){g.e=b.e;g.s=b.s;}}
 const double sec=std::chrono::duration<double>(std::chrono::steady_clock::now()-t0).count();
 std::cout<<"RADIUS free_radius="<<r<<" tested="<<g.tested<<" expected="<<choose(50,r)<<" best="<<g.e<<" seconds="<<sec<<"\n";
 std::cout<<"BESTSEQ "<<format(g.s)<<"\n";
 return g.tested==choose(50,r)?0:1;
}
