// Probe the Packebusch/Mertens tight per-correlation bound on random partial
// assignments in the direct N=100 near-skew manifold.  For each even lag k,
// the graph of products s_i s_{i+k} is a disjoint union of chains.  Given a
// partial sign assignment, dynamic programming on those chains computes the
// exact set of attainable values of C_k if the still-free signs are relaxed
// independently of the near-skew mirror constraints.  Summing the resulting
// per-correlation minimum squares is therefore a rigorous LABS lower bound.
//
// This probe does not search for a record.  It measures when that expensive
// tight bound materially strengthens the cheap fixed-product interval bound,
// and validates it against random complete extensions before it is used for
// pruning in the main branch-and-bound.
#include <algorithm>
#include <array>
#include <bitset>
#include <cstdint>
#include <iostream>
#include <random>
#include <string>
#include <vector>

constexpr int N=100, OFF=100, W=201;
using S=std::array<int8_t,N>;
using A=std::array<uint8_t,N>;

struct P { S s{}; A used{}; };

static void assign_coord(P& p,int v,int val){
 int a=1+v;p.s[a]=val;p.used[a]=1;
 if(v!=49){int b=99-v, factor=(a&1)?-1:1;p.s[b]=factor*val;p.used[b]=1;}
}
static P random_partial(int depth,std::mt19937_64&rng){
 P p;p.s[0]=1;p.used[0]=1;assign_coord(p,0,1); // s1=+1 symmetry normalization
 for(int v=1;v<depth;v++)assign_coord(p,v,(rng()&1)?1:-1);
 return p;
}
static long long cheap_bound(const P&p){
 long long lb=0;
 for(int k=2;k<N;k+=2){
  int f=0,u=0;
  for(int i=0;i<N-k;i++){
   if(p.used[i]&&p.used[i+k]) f+=int(p.s[i])*int(p.s[i+k]);
   else u++;
  }
  int m=std::max(0,std::abs(f)-u);if(m&1)++m;lb+=1LL*m*m;
 }
 return lb;
}

// Exact attainable C_k set under the relaxation that every currently-free
// sign may be chosen independently.  This is exact for a single correlation.
static std::bitset<W> lag_values(const P&p,int k){
 std::bitset<W> global;global[OFF]=1;
 for(int start=0;start<k&&start<N;start++){
  std::vector<int> pos;for(int q=start;q<N;q+=k)pos.push_back(q);
  if(pos.size()<2)continue;
  std::array<std::bitset<W>,2> cur{},nxt{};
  auto allow=[&](int q,int sign){return !p.used[q]||int(p.s[q])==sign;};
  if(allow(pos[0],-1))cur[0][OFF]=1;
  if(allow(pos[0],+1))cur[1][OFF]=1;
  for(size_t j=1;j<pos.size();j++){
   nxt[0].reset();nxt[1].reset();
   for(int ps=0;ps<2;ps++)for(int ns=0;ns<2;ns++){
    int a=ps?1:-1,b=ns?1:-1;
    if(!allow(pos[j],b))continue;
    int d=a*b;
    if(d==1)nxt[ns] |= (cur[ps]<<1);
    else nxt[ns] |= (cur[ps]>>1);
   }
   cur=nxt;
  }
  std::bitset<W> chain=cur[0]|cur[1],combined;
  for(int a=0;a<W;a++)if(global[a])for(int b=0;b<W;b++)if(chain[b]){
   int z=(a-OFF)+(b-OFF);if(z>=-OFF&&z<=OFF)combined[z+OFF]=1;
  }
  global=combined;
 }
 return global;
}
static long long tight_bound(const P&p){
 long long lb=0;
 for(int k=2;k<N;k+=2){
  auto vals=lag_values(p,k);int m=1000;
  for(int c=-(N-k);c<=N-k;c+=2)if(vals[c+OFF])m=std::min(m,std::abs(c));
  if(m==1000){std::cerr<<"empty lag set k="<<k<<"\n";std::abort();}
  lb+=1LL*m*m;
 }
 return lb;
}
static S complete_nearskew(P p,std::mt19937_64&rng){
 for(int v=0;v<50;v++)if(!p.used[1+v])assign_coord(p,v,(rng()&1)?1:-1);
 return p.s;
}
static long long even_energy(const S&s){
 long long e=0;
 for(int k=2;k<N;k+=2){int c=0;for(int i=0;i<N-k;i++)c+=int(s[i])*int(s[i+k]);e+=1LL*c*c;}
 return e;
}

int main(int argc,char**argv){
 int samples=200;uint64_t seed=1;if(argc>1)samples=std::stoi(argv[1]);if(argc>2)seed=std::stoull(argv[2]);
 std::mt19937_64 rng(seed);std::vector<int> depths={8,12,16,20,24,28,32,36,40,44};
 for(int d:depths){
  long long sumc=0,sumt=0;int stronger=0,prune=0,cheapprune=0;long long maxgain=0;
  for(int n=0;n<samples;n++){
   P p=random_partial(d,rng);long long c=cheap_bound(p),t=tight_bound(p);
   if(t<c){std::cerr<<"tight below cheap depth="<<d<<" c="<<c<<" t="<<t<<"\n";return 2;}
   // Random-completion soundness check.
   for(int q=0;q<3;q++){S s=complete_nearskew(p,rng);long long ee=even_energy(s);if(ee<t){std::cerr<<"unsound tight bound depth="<<d<<" bound="<<t<<" completion="<<ee<<"\n";return 2;}}
   sumc+=c;sumt+=t;if(t>c)stronger++;if(c>524)cheapprune++;if(c<=524&&t>524)prune++;maxgain=std::max(maxgain,t-c);
  }
  std::cout<<"DEPTH "<<d<<" samples="<<samples<<" avgCheap="<<double(sumc)/samples<<" avgTight="<<double(sumt)/samples<<" stronger="<<stronger<<" tightOnlyPrune="<<prune<<" cheapPrune="<<cheapprune<<" maxGain="<<maxgain<<"\n";
 }
 // Full-assignment exactness regression.
 P p=random_partial(50,rng);long long t=tight_bound(p),ee=even_energy(p.s);
 std::cout<<"FULL tight="<<t<<" even="<<ee<<" exact="<<(t==ee)<<"\n";
 return t==ee?0:2;
}
