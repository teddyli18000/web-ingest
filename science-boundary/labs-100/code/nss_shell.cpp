// Exact shells in the 50-variable N=100 near-skew subspace obtained by
// prepending +1 to a length-99 skew-symmetric sequence. Every sequence in
// this subspace has |C_k|=1 at all odd lags. A free-variable flip negates the
// corresponding skew pair (or the center bit), and correlations are updated
// exactly in O(N).
#include <array>
#include <algorithm>
#include <chrono>
#include <cstdint>
#include <iostream>
#include <string>
#ifdef _OPENMP
#include <omp.h>
#endif
using S=std::array<int8_t,100>;
using C=std::array<int,100>;

static long long energy(const S&s,C*out=nullptr){
 C c{}; long long e=0;
 for(int k=1;k<100;k++){int x=0;for(int i=0;i<100-k;i++)x+=int(s[i])*int(s[i+k]);c[k]=x;e+=1LL*x*x;}
 if(out)*out=c; return e;
}

static void flip_free(S&s,C&c,long long&e,int v){
 const int p=1+v, q=(v==49?-1:100-v); const int sp=s[p], sq=q>=0?s[q]:0;
 for(int k=1;k<100;k++){
  int t=0;
  if(p+k<100)t+=sp*int(s[p+k]); if(p-k>=0)t+=int(s[p-k])*sp;
  if(q>=0){if(q+k<100)t+=sq*int(s[q+k]);if(q-k>=0)t+=int(s[q-k])*sq;if(k==q-p)t-=2*sp*sq;}
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
 S base=incumbent();C bc{};long long be=energy(base,&bc);if(be!=578)return 2;
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
