#include <array>
#include <chrono>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <random>
#include <stdexcept>
#include <string>
#include <vector>

using S=std::array<int8_t,100>;
using C=std::array<int,100>;

static long long exact(const S&s,C*out=nullptr,long long*odd=nullptr){
 C c{};long long e=0,o=0;
 for(int k=1;k<100;k++){
  int x=0;for(int i=0;i<100-k;i++)x+=int(s[i])*int(s[i+k]);
  c[k]=x;const long long q=1LL*x*x;e+=q;if(k&1)o+=q;
 }
 if(out)*out=c;if(odd)*odd=o;return e;
}
static std::string fmt(const S&s){std::string z;z.reserve(100);for(auto v:s)z+=v>0?'+':'-';return z;}
static bool nss(const S&s){
 if(s[0]!=1||s[1]!=1)return false;
 for(int p=1;p<=49;p++)if(int(s[p])*int(s[100-p])!=((p&1)?-1:1))return false;
 return true;
}
static void flipcoord(S&s,C&c,long long&e,int v){
 const int p=1+v,q=v==49?-1:99-v,sp=s[p],sq=q>=0?s[q]:0;
 const int dist=q>=0?std::abs(q-p):-1,pq=q>=0?sp*sq:0;
 for(int k=1;k<100;k++){
  int t=0;
  if(p+k<100)t+=sp*int(s[p+k]);
  if(p-k>=0)t+=int(s[p-k])*sp;
  if(q>=0){
   if(q+k<100)t+=sq*int(s[q+k]);
   if(q-k>=0)t+=int(s[q-k])*sq;
   if(k==dist)t-=2*pq;
  }
  const int nc=c[k]-2*t;e+=1LL*nc*nc-1LL*c[k]*c[k];c[k]=nc;
 }
 s[p]=-s[p];if(q>=0)s[q]=-s[q];
}
static S random_nss(std::mt19937_64&r){
 S s{};s[0]=1;
 for(int v=0;v<50;v++){
  const int p=1+v;
  s[p]=(v==0)?1:((r()&1)?1:-1);
  if(v<49){const int q=99-v,prod=(p&1)?-1:1;s[q]=prod*s[p];}
 }
 return s;
}
static long long optimize_block(S&base,char which,unsigned long long&tested){
 std::vector<int>vars;
 if(which=='A'){for(int v=1;v<50;v+=2)vars.push_back(v);}
 else{for(int v=2;v<49;v+=2)vars.push_back(v);}
 const uint64_t total=1ULL<<vars.size();
 uint64_t prev=0;S s=base,bs=base;C c{};long long e=exact(s,&c),best=e;
 for(uint64_t i=1;i<total;i++){
  const uint64_t g=i^(i>>1),x=g^prev;prev=g;const int bit=__builtin_ctzll(x);
  flipcoord(s,c,e,vars[bit]);
  if((i&0x3fffffULL)==0){
   long long o=0;const long long chk=exact(s,nullptr,&o);
   if(chk!=e||o!=50||!nss(s))throw std::runtime_error("block incremental mismatch");
  }
  if(e<best){best=e;bs=s;}
 }
 base=bs;tested+=total;
 long long o=0;const long long chk=exact(base,nullptr,&o);
 if(chk!=best||o!=50||!nss(base))throw std::runtime_error("block winner mismatch");
 return best;
}

int main(int argc,char**argv){
 int cycles=6;uint64_t seed=1;long long target=574;
 for(int i=1;i<argc;i++){
  std::string a=argv[i];auto need=[&](){if(i+1>=argc)throw std::runtime_error("missing value");return std::string(argv[++i]);};
  if(a=="--cycles")cycles=std::stoi(need());
  else if(a=="--seed")seed=std::stoull(need());
  else if(a=="--target")target=std::stoll(need());
  else return 2;
 }
 std::mt19937_64 rng(seed);S s=random_nss(rng);long long odd=0,e=exact(s,nullptr,&odd);
 if(odd!=50||!nss(s))return 2;
 unsigned long long tested=0;const auto t0=std::chrono::steady_clock::now();
 std::cout<<"START seed="<<seed<<" energy="<<e<<"\n"<<std::flush;
 for(int c=0;c<cycles;c++){
  const long long before=e;
  e=optimize_block(s,'A',tested);
  std::cout<<"STEP cycle="<<c<<" block=A energy="<<e<<" tested="<<tested<<"\n"<<std::flush;
  if(e<=target)break;
  e=optimize_block(s,'B',tested);
  std::cout<<"STEP cycle="<<c<<" block=B energy="<<e<<" tested="<<tested<<"\n"<<std::flush;
  if(e<=target||e==before)break;
 }
 const long long chk=exact(s,nullptr,&odd);if(chk!=e||odd!=50)return 2;
 const double sec=std::chrono::duration<double>(std::chrono::steady_clock::now()-t0).count();
 std::cout<<"FINAL seed="<<seed<<" energy="<<e<<" tested="<<tested<<" seconds="<<sec<<" seq="<<fmt(s)<<"\n";
 return e<=target?0:1;
}
