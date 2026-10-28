// Exhaust the complete odd-perfect d=3 skew-core branch with s2=+1.
//
// Write u_j=s_{2j+1} (j=0..49), v_j=s_{2j+2} (j=0..48), with
// prefix (s0,s1,s2)=(+1,b,+1).  The suffix positions 3..99 are skew97.
// For every odd shift 2j+1<99, odd-perfectness is exactly the condition that
// the three products s_i s_{i+2j+1}, i=0,1,2, are not all equal.
// Pairing this condition with its skew97 mirror forces
//
//   u_{j+1}=-u_j, j=1..24,
//   u_1=-u_0,
//
// while v_1..v_24 are arbitrary and v_{49-j}=-v_j.  Therefore this entire
// branch has exactly 2^25 states: b plus 24 free v bits.
#include <array>
#include <atomic>
#include <bit>
#include <chrono>
#include <cstdint>
#include <iostream>
#include <limits>
#include <string>
#ifdef _OPENMP
#include <omp.h>
#endif

constexpr int N=100;
using S=std::array<int8_t,N>;
using C=std::array<int,N>;

static long long exact(const S&s,C*out=nullptr,long long*oddout=nullptr){
 C c{};long long e=0,o=0;
 for(int k=1;k<N;k++){int x=0;for(int i=0;i<N-k;i++)x+=int(s[i])*int(s[i+k]);c[k]=x;long long q=1LL*x*x;e+=q;if(k&1)o+=q;}
 if(out)*out=c;if(oddout)*oddout=o;return e;
}
static std::string fmt(const S&s){std::string z;z.reserve(N);for(auto x:s)z+=x>0?'+':'-';return z;}

static S base_seq(int b){
 S s{};s.fill(0);s[0]=1;s[1]=b;s[2]=1;
 // u_r=(-1)^r b for r=0..25; mirror u_{50-r}=u_r for r=1..24.
 for(int r=0;r<=25;r++)s[2*r+1]=(r&1)?-b:b;
 for(int r=1;r<=24;r++)s[2*(50-r)+1]=s[2*r+1];
 // Start all 24 free v_r at +1; v_0=s2=+1 and v_{49-r}=-v_r.
 for(int r=1;r<=24;r++){s[2*r+2]=1;s[2*(49-r)+2]=-1;}
 return s;
}

static void pair_flip(S&s,C&c,long long&e,int p,int q){
 const int sp=s[p],sq=s[q],dist=q-p,pq=sp*sq;long long ne=0;
 for(int k=1;k<N;k++){
  int t=0;
  if(p+k<N)t+=sp*int(s[p+k]);if(p-k>=0)t+=int(s[p-k])*sp;
  if(q+k<N)t+=sq*int(s[q+k]);if(q-k>=0)t+=int(s[q-k])*sq;
  if(k==dist)t-=2*pq;
  c[k]-=2*t;ne+=1LL*c[k]*c[k];
 }
 s[p]=-s[p];s[q]=-s[q];e=ne;
}
static void flip_v(S&s,C&c,long long&e,int r){
 int p=2*r+2,q=2*(49-r)+2;
 if(p>q)std::swap(p,q);
 pair_flip(s,c,e,p,q);
}

struct Best{long long e=1LL<<60;S s{};unsigned long long count=0,le578=0;};

int main(int argc,char**argv){
 int threads=4;if(argc>1)threads=std::stoi(argv[1]);
#ifdef _OPENMP
 omp_set_num_threads(threads);
#endif
 constexpr int LOW=20,HIGH=4;
 constexpr unsigned long long PER=1ULL<<LOW;
 std::array<Best,32> part{}; // 2 choices b * 16 high-bit assignments
 auto started=std::chrono::steady_clock::now();
#pragma omp parallel for schedule(dynamic,1)
 for(int task=0;task<32;task++){
  int b=(task<16)?1:-1,hm=task&15;S s=base_seq(b);C c{};long long odd=0,e=exact(s,&c,&odd);
  if(odd!=50){std::cerr<<"construction odd-energy failure\n";std::abort();}
  for(int h=0;h<HIGH;h++)if((hm>>h)&1)flip_v(s,c,e,LOW+1+h);
  Best z;z.e=e;z.s=s;z.count=1;if(e<=578)z.le578++;
  for(unsigned long long i=1;i<PER;i++){
   int bit=std::countr_zero(i);flip_v(s,c,e,bit+1);z.count++;
   if(e<z.e){z.e=e;z.s=s;}if(e<=578)z.le578++;
#ifndef NDEBUG
   if((i&0xfffff)==0){long long oo=0,ee=exact(s,nullptr,&oo);if(ee!=e||oo!=50)std::abort();}
#endif
  }
  part[task]=z;
 }
 Best all;
 for(auto&z:part){all.count+=z.count;all.le578+=z.le578;if(z.e<all.e){all.e=z.e;all.s=z.s;}}
 double sec=std::chrono::duration<double>(std::chrono::steady_clock::now()-started).count();long long odd=0,check=exact(all.s,nullptr,&odd);
 std::cout<<"SUMMARY branch=d3-cplus tested="<<all.count<<" expected="<<(1ULL<<25)<<" best="<<all.e<<" le578="<<all.le578<<" seconds="<<sec<<"\n";
 std::cout<<"BESTSEQ energy="<<check<<" odd="<<odd<<" seq="<<fmt(all.s)<<"\n";
 return (all.count==(1ULL<<25)&&check==all.e&&odd==50)?0:2;
}
