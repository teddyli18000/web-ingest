#include <array>
#include <chrono>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

using S=std::array<int8_t,100>;
using C=std::array<int,100>;

static S parse(const std::string&z){
 if(z.size()!=100)throw std::runtime_error("length must be 100");
 S s{};
 for(int i=0;i<100;i++){
  if(z[i]=='+')s[i]=1;
  else if(z[i]=='-')s[i]=-1;
  else throw std::runtime_error("bad char");
 }
 return s;
}
static std::string fmt(const S&s){std::string z;z.reserve(100);for(auto v:s)z+=v>0?'+':'-';return z;}
static long long exact(const S&s,C*out=nullptr,long long*odd=nullptr){
 C c{};long long e=0,o=0;
 for(int k=1;k<100;k++){
  int x=0;for(int i=0;i<100-k;i++)x+=int(s[i])*int(s[i+k]);
  c[k]=x;long long q=1LL*x*x;e+=q;if(k&1)o+=q;
 }
 if(out)*out=c;if(odd)*odd=o;return e;
}
static bool nss(const S&s){
 if(s[0]!=1||s[1]!=1)return false;
 for(int p=1;p<=49;p++){
  int w=(p&1)?-1:1;
  if(int(s[p])*int(s[100-p])!=w)return false;
 }
 return true;
}
static void flipcoord(S&s,C&c,long long&e,int v){
 int p=1+v,q=v==49?-1:99-v,sp=s[p],sq=q>=0?s[q]:0;
 int dist=q>=0?std::abs(q-p):-1,pq=q>=0?sp*sq:0;
 for(int k=1;k<100;k++){
  int t=0;
  if(p+k<100)t+=sp*int(s[p+k]);
  if(p-k>=0)t+=int(s[p-k])*sp;
  if(q>=0){
   if(q+k<100)t+=sq*int(s[q+k]);
   if(q-k>=0)t+=int(s[q-k])*sq;
   if(k==dist)t-=2*pq;
  }
  int nc=c[k]-2*t;e+=1LL*nc*nc-1LL*c[k]*c[k];c[k]=nc;
 }
 s[p]=-s[p];if(q>=0)s[q]=-s[q];
}

int main(int argc,char**argv){
 if(argc!=3){std::cerr<<"usage: nearskew_block <sequence> <A|B>\n";return 2;}
 S base=parse(argv[1]);std::string which=argv[2];long long odd=0,be=exact(base,nullptr,&odd);
 if(!nss(base)||odd!=50){std::cerr<<"seed must be canonical near-skew with s0=s1=+\n";return 2;}
 std::vector<int> vars;
 if(which=="A"){for(int v=1;v<50;v+=2)vars.push_back(v);}
 else if(which=="B"){for(int v=2;v<49;v+=2)vars.push_back(v);}
 else return 2;
 uint64_t total=1ULL<<vars.size(),prev=0,count=1;
 S s=base,bs=base;C c{};long long e=exact(s,&c),best=e;
 auto t0=std::chrono::steady_clock::now();
 for(uint64_t i=1;i<total;i++){
  uint64_t g=i^(i>>1),x=g^prev;prev=g;int bit=__builtin_ctzll(x);
  flipcoord(s,c,e,vars[bit]);
  if((i&0x3fffffULL)==0){
   long long o=0,chk=exact(s,nullptr,&o);
   if(chk!=e||o!=50||!nss(s)){std::cerr<<"mismatch at "<<i<<"\n";return 2;}
  }
  if(e<best){best=e;bs=s;count=1;}else if(e==best)count++;
 }
 long long o=0,chk=exact(bs,nullptr,&o);if(chk!=best||o!=50)return 2;
 double sec=std::chrono::duration<double>(std::chrono::steady_clock::now()-t0).count();
 std::cout<<"BLOCK block="<<which<<" vars="<<vars.size()<<" tested="<<total<<" seed="<<be<<" best="<<best<<" count="<<count<<" seconds="<<sec<<"\n";
 std::cout<<"BESTSEQ "<<fmt(bs)<<"\n";
}
