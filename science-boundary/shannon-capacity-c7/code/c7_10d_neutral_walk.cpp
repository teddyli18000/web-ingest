// Heuristic long-range neutral walk on an independent set in C7^10.
//
// Maintain exact conflict coverage count and owner XOR on all 7^10 ambient
// vertices.  An outside vertex with coverage exactly one is a legal neutral
// replacement for its unique owner.  Before taking a neutral move x->y, scan
// the current coverage-one candidates for a second candidate z with the same
// owner x and nonconfusable with y.  If one exists, x->{y,z} is an immediate
// +1 improvement.  Otherwise perform x->y and update only the two 3^10 closed
// neighborhoods.  This can travel arbitrarily far on the 134753 plateau and is
// therefore not contained in any fixed remove-r/add-(r+1) ball.
//
// Negative runs are heuristic evidence only. Any emitted +1 set is replayed by
// the Few Shots verifier in the workflow.
#include <algorithm>
#include <array>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <limits>
#include <random>
#include <stdexcept>
#include <unordered_set>
#include <vector>
#ifdef _OPENMP
#include <omp.h>
#endif

namespace {
constexpr int D=10;
constexpr std::uint32_t P7[D+1]={1u,7u,49u,343u,2401u,16807u,117649u,823543u,5764801u,40353607u,282475249u};
constexpr std::uint32_t N=P7[D];
constexpr std::uint32_t GROUPS=N/7u;
constexpr std::uint32_t NONE=std::numeric_limits<std::uint32_t>::max();

std::vector<std::uint32_t> load_ids(const char* p){
 std::ifstream in(p);if(!in)throw std::runtime_error("cannot open ids");
 std::vector<std::uint32_t>a;std::uint64_t z;while(in>>z){if(z>=N)throw std::runtime_error("id range");a.push_back((std::uint32_t)z);}
 if(a.empty())throw std::runtime_error("empty baseline");std::sort(a.begin(),a.end());
 if(std::adjacent_find(a.begin(),a.end())!=a.end())throw std::runtime_error("duplicate baseline");return a;
}
inline bool bitget(const std::vector<std::uint64_t>&b,std::uint32_t x){return (b[x>>6]>>(x&63))&1u;}
inline void bitsetv(std::vector<std::uint64_t>&b,std::uint32_t x,bool v){auto&m=b[x>>6];auto q=std::uint64_t(1)<<(x&63);if(v)m|=q;else m&=~q;}
bool conflict(std::uint32_t a,std::uint32_t b){if(a==b)return true;for(int d=0;d<D;++d){int x=a%7u,y=b%7u;a/=7u;b/=7u;int z=(x-y+7)%7;if(z!=0&&z!=1&&z!=6)return false;}return true;}
void neighborhood(std::uint32_t p,std::vector<std::uint32_t>&out){
 std::array<unsigned,D>d{};for(int i=0;i<D;++i){d[i]=p%7u;p/=7u;}
 out.resize(1);out[0]=0;
 std::size_t n=1;
 for(int dim=0;dim<D;++dim){std::array<unsigned,3>v{(d[dim]+6)%7,d[dim],(d[dim]+1)%7};
  for(std::size_t i=0;i<n;++i){auto base=out[i];out[i]=base+v[0]*P7[dim];out.push_back(base+v[1]*P7[dim]);out.push_back(base+v[2]*P7[dim]);}
  n*=3;
 }
}
void write_ids(const char*p,const std::vector<std::uint64_t>&sel,std::uint32_t rem,std::uint32_t a,std::uint32_t b){
 std::ofstream out(p);if(!out)throw std::runtime_error("cannot write result");std::uint64_t n=0;
 for(std::uint32_t v=0;v<N;++v)if(bitget(sel,v)&&v!=rem){out<<v<<'\n';++n;}
 out<<a<<'\n'<<b<<'\n';n+=2;if(n!=134754)throw std::runtime_error("result size drift");
}
}

int main(int argc,char**argv)try{
 if(argc!=5){std::cerr<<"usage: c7_10d_neutral_walk BASELINE_IDS RESULT_IDS STEPS SEED\n";return 2;}
 auto base=load_ids(argv[1]);auto steps=std::stoull(argv[3]);auto seed=std::stoull(argv[4]);
 if(base.size()!=134753)throw std::runtime_error("expected 134753 baseline");
 std::vector<std::uint16_t>cnt(N);std::vector<std::uint32_t>xo(N);
 std::vector<std::uint64_t>sel((N+63)/64);
 for(auto v:base){cnt[v]=1;xo[v]=v+1;bitsetv(sel,v,true);}
 // Exact separable count/XOR transforms. Each source-target pair has one path.
 for(int dim=0;dim<D;++dim){const std::uint32_t s=P7[dim];const std::uint64_t block=std::uint64_t(s)*7u;
#pragma omp parallel for schedule(static)
  for(std::int64_t gg=0;gg<(std::int64_t)GROUPS;++gg){const std::uint64_t g=(std::uint64_t)gg,bn=g/s;const std::uint32_t off=g%s,b0=(std::uint32_t)(bn*block+off);std::uint16_t oc[7];std::uint32_t ox[7];for(int k=0;k<7;++k){auto v=b0+k*s;oc[k]=cnt[v];ox[k]=xo[v];}for(int k=0;k<7;++k){unsigned sum=unsigned(oc[(k+6)%7])+oc[k]+oc[(k+1)%7];if(sum>65535)throw std::runtime_error("coverage overflow");auto v=b0+k*s;cnt[v]=(std::uint16_t)sum;xo[v]=ox[(k+6)%7]^ox[k]^ox[(k+1)%7];}}
  std::cerr<<"init dim="<<dim<<"\n";
 }
 // Dense position index gives O(1) exact maintenance of the outside coverage-1 list.
 std::vector<std::uint32_t>pos(N,NONE),cand;cand.reserve(100000);
 auto addcand=[&](std::uint32_t v){if(pos[v]!=NONE)return;pos[v]=(std::uint32_t)cand.size();cand.push_back(v);};
 auto delcand=[&](std::uint32_t v){auto i=pos[v];if(i==NONE)return;auto w=cand.back();cand[i]=w;pos[w]=i;cand.pop_back();pos[v]=NONE;};
 auto refresh=[&](std::uint32_t v){if(!bitget(sel,v)&&cnt[v]==1)addcand(v);else delcand(v);};
 std::uint64_t free0=0;for(std::uint32_t v=0;v<N;++v){if(!bitget(sel,v)){if(cnt[v]==0)++free0;else if(cnt[v]==1)addcand(v);}}
 if(free0)throw std::runtime_error("baseline has coverage0");
 std::cerr<<"initial candidates="<<cand.size()<<"\n";
 std::mt19937_64 rng(seed);std::vector<std::uint32_t>nx,ny;nx.reserve(59049);ny.reserve(59049);
 std::array<std::uint32_t,64>tabu{};tabu.fill(NONE);unsigned tp=0;
 for(std::uint64_t step=0;step<steps;++step){
  if(cand.empty())break;
  // Pick a non-tabu neutral candidate when possible.
  std::uint32_t y=NONE;
  for(unsigned trial=0;trial<128;++trial){auto q=cand[rng()%cand.size()];bool bad=false;for(auto t:tabu)if(q==t){bad=true;break;}if(!bad){y=q;break;}}
  if(y==NONE)y=cand[rng()%cand.size()];
  if(bitget(sel,y)||cnt[y]!=1||xo[y]==0)throw std::runtime_error("candidate invariant");
  std::uint32_t x=xo[y]-1;if(!bitget(sel,x)||!conflict(x,y))throw std::runtime_error("owner invariant");
  // Exact immediate +1 test for the chosen owner: another private candidate z
  // nonconfusable with y gives x->{y,z}.
  for(auto z:cand)if(z!=y&&xo[z]==x+1&&!conflict(y,z)){
    write_ids(argv[2],sel,x,y,z);
    std::cout<<"{\"kind\":\"replace1add2\",\"step\":"<<step<<",\"seed\":"<<seed<<",\"neutral_candidates\":"<<cand.size()<<",\"remove\":"<<x<<",\"add\":["<<y<<','<<z<<"]}\n";
    return 0;
  }
  neighborhood(x,nx);neighborhood(y,ny);
  // Change membership first; coverage is then updated exactly.
  bitsetv(sel,x,false);bitsetv(sel,y,true);
  for(auto v:nx){if(!cnt[v])throw std::runtime_error("remove underflow");--cnt[v];xo[v]^=x+1;}
  for(auto v:ny){if(cnt[v]==65535)throw std::runtime_error("add overflow");++cnt[v];xo[v]^=y+1;}
  for(auto v:nx)refresh(v);for(auto v:ny)refresh(v);
  tabu[tp++%tabu.size()]=x; // discourage the immediate reverse move
  if((step+1)%1000==0)std::cerr<<"progress step="<<(step+1)<<" candidates="<<cand.size()<<"\n";
 }
 std::cout<<"{\"kind\":\"none\",\"method\":\"heuristic-10d-neutral-walk\",\"steps_requested\":"<<steps<<",\"seed\":"<<seed<<",\"neutral_candidates_final\":"<<cand.size()<<"}\n";
 return 0;
}catch(const std::exception&e){std::cerr<<"error: "<<e.what()<<"\n";return 1;}
