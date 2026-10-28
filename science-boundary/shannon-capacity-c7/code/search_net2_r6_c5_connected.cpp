// Exact connected-support radius-6 stratum for C7^10.
//
// Baseline size is 134752.  A remove-6/add-8 improvement is equivalent to
// eight pairwise nonconfusable outside vertices whose blocker-support union has
// size at most six.  This stage is COMPLETE for witnesses satisfying:
//   * no selected candidate has support size 6 (the direct-support r6 stage
//     handles every witness that does), and
//   * at least one selected candidate has support size 5, and
//   * the selected support hypergraph on the six owners is connected.
//
// If S is the selected size-5 support and x is the sixth owner, connectedness
// forces another selected support E (size <=5) with x in E and
// E\{x} subset S, E\{x} nonempty.  We index every such exact support extension.
// For each resulting U=S union {x}, the COMPLETE candidate pool P(U), including
// all support sizes 1..6, is reconstructed and searched exactly for an
// independent 8-set.  Duplicate U tests are harmless and preserve completeness.
#include <algorithm>
#include <array>
#include <atomic>
#include <bit>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <unordered_map>
#include <unordered_set>
#include <vector>
#ifdef _OPENMP
#include <omp.h>
#endif
namespace {
constexpr int D=10;
constexpr std::uint32_t P7[D+1]={1u,7u,49u,343u,2401u,16807u,117649u,823543u,5764801u,40353607u,282475249u};
constexpr std::uint32_t N=P7[D],GROUPS=N/7u,OVER=0xffffffffu;
constexpr unsigned K=6;
struct Rec{std::uint32_t x[K];};
struct Key{std::array<std::uint32_t,K>a{};bool operator==(const Key&o)const{return a==o.a;}bool operator<(const Key&o)const{return a<o.a;}};
struct KeyHash{std::size_t operator()(const Key&q)const noexcept{std::size_t h=0;for(auto x:q.a)h^=std::size_t(x)+0x9e3779b97f4a7c15ULL+(h<<6)+(h>>2);return h;}};
struct CRec{Key k;std::uint32_t v;};
struct Range{std::uint32_t lo,hi;};
struct Group{Key k;std::uint32_t lo,hi;unsigned n;};
struct SubKey{std::array<std::uint32_t,4>a{};bool operator==(const SubKey&o)const{return a==o.a;}bool operator<(const SubKey&o)const{return a<o.a;}};
struct Ext{SubKey t;std::uint32_t x;std::uint32_t cnt;bool operator<(const Ext&o)const{if(t<o.t)return true;if(o.t<t)return false;return x<o.x;}};
std::vector<std::uint32_t>load_ids(const char*p){std::ifstream in(p);if(!in)throw std::runtime_error("cannot open ids");std::vector<std::uint32_t>a;std::uint64_t z;while(in>>z){if(z>=N)throw std::runtime_error("id range");a.push_back((std::uint32_t)z);}if(a.empty())throw std::runtime_error("empty baseline");std::sort(a.begin(),a.end());if(std::adjacent_find(a.begin(),a.end())!=a.end())throw std::runtime_error("duplicate baseline");return a;}
inline bool overflow(const Rec&r){return r.x[0]==OVER;}
inline unsigned rsize(const Rec&r){if(overflow(r))return K+1;unsigned n=0;while(n<K&&r.x[n])++n;return n;}
inline Rec unite3(const Rec&a,const Rec&b,const Rec&c){if(overflow(a)||overflow(b)||overflow(c)){Rec r{};r.x[0]=OVER;return r;}unsigned ia=0,ib=0,ic=0,m=0;std::uint32_t last=0;Rec out{};for(;;){auto va=ia<K?a.x[ia]:0u,vb=ib<K?b.x[ib]:0u,vc=ic<K?c.x[ic]:0u;std::uint32_t v=0;if(va)v=va;if(vb&&(!v||vb<v))v=vb;if(vc&&(!v||vc<v))v=vc;if(!v)break;if(va==v)++ia;if(vb==v)++ib;if(vc==v)++ic;if(v==last)continue;if(m==K){Rec r{};r.x[0]=OVER;return r;}out.x[m++]=v;last=v;}return out;}
bool conflict(std::uint32_t a,std::uint32_t b){if(a==b)return true;for(int d=0;d<D;++d){int x=a%7u,y=b%7u;a/=7u;b/=7u;int z=(x-y+7)%7;if(z!=0&&z!=1&&z!=6)return false;}return true;}
Key subset_key(const Key&u,unsigned mask){Key q{};unsigned j=0;for(unsigned i=0;i<K;++i)if(mask&(1u<<i))q.a[j++]=u.a[i];return q;}
SubKey subkey_from5(const Key&s,unsigned mask){SubKey q{};unsigned j=0;for(unsigned i=0;i<5;++i)if(mask&(1u<<i))q.a[j++]=s.a[i];return q;}
SubKey remove_one(const Key&e,unsigned n,unsigned drop){SubKey q{};unsigned j=0;for(unsigned i=0;i<n;++i)if(i!=drop)q.a[j++]=e.a[i];return q;}
bool has(const Key&s,unsigned n,std::uint32_t x){return std::binary_search(s.a.begin(),s.a.begin()+n,x);}
Key add_to5(const Key&s,std::uint32_t x){std::array<std::uint32_t,6>z{};for(unsigned i=0;i<5;++i)z[i]=s.a[i];z[5]=x;std::sort(z.begin(),z.end());Key q{};q.a=z;return q;}

bool find8_bits(const std::vector<std::uint32_t>&p,std::vector<std::uint32_t>&out){
 const unsigned n=p.size(); if(n<8)return false;
 if(n>63){ // Rare fallback, still exact.
  std::vector<std::uint32_t>ch;
  auto rec=[&](auto&&self,std::size_t s)->bool{if(ch.size()==8){out=ch;return true;}if(ch.size()+p.size()-s<8)return false;for(std::size_t i=s;i<p.size();++i){bool ok=true;for(auto z:ch)if(conflict(z,p[i])){ok=false;break;}if(!ok)continue;ch.push_back(p[i]);if(self(self,i+1))return true;ch.pop_back();}return false;};
  return rec(rec,0);
 }
 std::vector<std::uint64_t>compat(n,0);for(unsigned i=0;i<n;++i)for(unsigned j=i+1;j<n;++j)if(!conflict(p[i],p[j]))compat[i]|=(1ull<<j);
 std::array<unsigned,8>chosen{};
 auto rec=[&](auto&&self,std::uint64_t mask,unsigned depth)->bool{
  if(depth==8){out.clear();for(unsigned i=0;i<8;++i)out.push_back(p[chosen[i]]);return true;}
  if(std::popcount(mask)<8-depth)return false;
  while(mask){unsigned v=std::countr_zero(mask);mask&=mask-1;chosen[depth]=v;if(self(self,mask&compat[v],depth+1))return true;if(std::popcount(mask)<7-depth)break;}
  return false;
 };
 return rec(rec,n==64?~0ull:((1ull<<n)-1),0);
}
}
int main(int argc,char**argv)try{
 if(argc!=2){std::cerr<<"usage: search_net2_r6_c5_connected BASELINE_IDS\n";return 2;}
 auto base=load_ids(argv[1]);std::unordered_set<std::uint32_t>bset(base.begin(),base.end());
 std::vector<Rec>a(N);for(std::uint32_t i=0;i<base.size();++i)a[base[i]].x[0]=i+1;
 for(int dim=0;dim<D;++dim){const std::uint32_t s=P7[dim];const std::uint64_t block=std::uint64_t(s)*7u;
#pragma omp parallel for schedule(static)
  for(std::int64_t gg=0;gg<(std::int64_t)GROUPS;++gg){const std::uint64_t g=gg,bn=g/s;const std::uint32_t off=g%s;const std::uint64_t b0=bn*block+off;Rec old[7],nw[7];for(int k=0;k<7;++k)old[k]=a[b0+std::uint64_t(k)*s];for(int k=0;k<7;++k)nw[k]=unite3(old[(k+6)%7],old[k],old[(k+1)%7]);for(int k=0;k<7;++k)a[b0+std::uint64_t(k)*s]=nw[k];}
  std::cerr<<"support dim="<<dim<<"\n";
 }
 std::vector<CRec>cand;cand.reserve(9500000);std::uint64_t c0=0;std::array<std::uint64_t,7>hist{};
 for(std::uint32_t v=0;v<N;++v){unsigned n=rsize(a[v]);if(n==0){if(!bset.count(v))++c0;continue;}if(n>K||bset.count(v))continue;++hist[n];Key k{};for(unsigned j=0;j<n;++j)k.a[j]=a[v].x[j];cand.push_back({k,v});}
 if(c0)throw std::runtime_error("coverage0 nonzero");a.clear();a.shrink_to_fit();bset.clear();bset.rehash(0);
 auto less=[](const CRec&x,const CRec&y){if(x.k<y.k)return true;if(y.k<x.k)return false;return x.v<y.v;};std::sort(cand.begin(),cand.end(),less);
 std::vector<Group>groups;groups.reserve(cand.size());for(std::uint32_t i=0;i<cand.size();){std::uint32_t j=i+1;while(j<cand.size()&&cand[j].k==cand[i].k)++j;unsigned n=0;while(n<K&&cand[i].k.a[n])++n;groups.push_back({cand[i].k,i,j,n});i=j;}
 std::unordered_map<Key,Range,KeyHash>idx;idx.reserve(groups.size()*11/10+1);std::vector<std::uint32_t>g5;g5.reserve(3000000);std::vector<Ext>ext;ext.reserve(24000000);
 for(std::uint32_t gi=0;gi<groups.size();++gi){const auto&g=groups[gi];idx.emplace(g.k,Range{g.lo,g.hi});if(g.n==5)g5.push_back(gi);if(g.n>=2&&g.n<=5){for(unsigned d=0;d<g.n;++d)ext.push_back({remove_one(g.k,g.n,d),g.k.a[d],g.hi-g.lo});}}
 std::sort(ext.begin(),ext.end());
 auto erange=[&](const SubKey&q){Ext lo{q,0,0},hi{q,0xffffffffu,0};auto b=std::lower_bound(ext.begin(),ext.end(),lo);auto e=std::upper_bound(ext.begin(),ext.end(),hi);return std::pair{b,e};};
 std::atomic<bool>found(false);std::array<std::uint32_t,6>wrem{};std::vector<std::uint32_t>wadd;std::atomic<std::uint64_t>generated(0),hall1(0),tested(0),eligible(0);std::atomic<std::uint32_t>maxpool(0),maxext(0);
#pragma omp parallel for schedule(dynamic,64)
 for(std::int64_t zz=0;zz<(std::int64_t)g5.size();++zz){if(found.load(std::memory_order_relaxed))continue;const Group&sg=groups[g5[zz]];std::vector<std::pair<std::uint32_t,std::uint32_t>>xs;xs.reserve(256);
  for(unsigned mask=1;mask<31;++mask){SubKey q=subkey_from5(sg.k,mask);auto [b,e]=erange(q);for(auto it=b;it!=e;++it){if(has(sg.k,5,it->x))continue;xs.push_back({it->x,it->cnt});}}
  if(xs.empty())continue;std::sort(xs.begin(),xs.end());std::vector<std::pair<std::uint32_t,std::uint32_t>>ux;for(auto z:xs){if(ux.empty()||ux.back().first!=z.first)ux.push_back(z);else ux.back().second+=z.second;}auto m=(std::uint32_t)ux.size();auto old=maxext.load();while(m>old&&!maxext.compare_exchange_weak(old,m)){}
  for(auto [x,xc]:ux){if(found.load(std::memory_order_relaxed))break;++generated;Key u=add_to5(sg.k,x);
   // Singleton Hall condition for the sixth owner: at least two available
   // candidates in P(U) must contain x.  xc counts every size2..5 exact
   // crossing support.  Add the optional singleton support {x} and size6 U.
   std::uint32_t xavail=xc;Key qx{};qx.a[0]=x;auto ix=idx.find(qx);if(ix!=idx.end())xavail+=ix->second.hi-ix->second.lo;auto iu6=idx.find(u);if(iu6!=idx.end())xavail+=iu6->second.hi-iu6->second.lo;if(xavail<2)continue;++hall1;
   std::vector<std::uint32_t>pool;pool.reserve(64);for(unsigned mask=1;mask<64;++mask){Key q=subset_key(u,mask);auto it=idx.find(q);if(it==idx.end())continue;for(std::uint32_t i=it->second.lo;i<it->second.hi;++i)pool.push_back(cand[i].v);}auto ps=(std::uint32_t)pool.size();old=maxpool.load();while(ps>old&&!maxpool.compare_exchange_weak(old,ps)){}if(ps<8)continue;++eligible;++tested;std::vector<std::uint32_t>ch;if(find8_bits(pool,ch)){bool exp=false;if(found.compare_exchange_strong(exp,true)){
#pragma omp critical
    {for(unsigned j=0;j<6;++j)wrem[j]=base[u.a[j]-1];wadd=ch;}
   }}
  }
 }
 if(found.load()){std::cout<<"{\"kind\":\"replace6add8\",\"method\":\"exact-r6-connected-c5-stratum\",\"baseline_size\":"<<base.size()<<",\"coverage0\":0,\"c1\":"<<hist[1]<<",\"c2\":"<<hist[2]<<",\"c3\":"<<hist[3]<<",\"c4\":"<<hist[4]<<",\"c5\":"<<hist[5]<<",\"c6\":"<<hist[6]<<",\"support_groups\":"<<groups.size()<<",\"c5_groups\":"<<g5.size()<<",\"extension_records\":"<<ext.size()<<",\"generated_owner6\":"<<generated.load()<<",\"hall1_pass\":"<<hall1.load()<<",\"eligible_owner6\":"<<eligible.load()<<",\"tested_owner6\":"<<tested.load()<<",\"max_extensions_per_c5\":"<<maxext.load()<<",\"max_supported_pool\":"<<maxpool.load()<<",\"remove\":[";for(unsigned i=0;i<6;++i)std::cout<<(i?",":"")<<wrem[i];std::cout<<"],\"add\":[";for(unsigned i=0;i<wadd.size();++i)std::cout<<(i?",":"")<<wadd[i];std::cout<<"]}\n";return 0;}
 std::cout<<"{\"kind\":\"none\",\"method\":\"exact-r6-connected-c5-stratum\",\"baseline_size\":"<<base.size()<<",\"coverage0\":0,\"c1\":"<<hist[1]<<",\"c2\":"<<hist[2]<<",\"c3\":"<<hist[3]<<",\"c4\":"<<hist[4]<<",\"c5\":"<<hist[5]<<",\"c6\":"<<hist[6]<<",\"support_groups\":"<<groups.size()<<",\"c5_groups\":"<<g5.size()<<",\"extension_records\":"<<ext.size()<<",\"generated_owner6\":"<<generated.load()<<",\"hall1_pass\":"<<hall1.load()<<",\"eligible_owner6\":"<<eligible.load()<<",\"tested_owner6\":"<<tested.load()<<",\"max_extensions_per_c5\":"<<maxext.load()<<",\"max_supported_pool\":"<<maxpool.load()<<"}\n";return 0;
}catch(const std::exception&e){std::cerr<<"error: "<<e.what()<<"\n";return 1;}
