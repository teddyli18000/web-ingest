// Exact stage-A unrestricted remove-6/add-8 net-+2 search for C7^10.
//
// This stage is complete for every witness containing at least one outside
// vertex whose blocker support against the 134752-point baseline has size 6.
// The in-place support-list transform recovers every exact support of sizes
// 1..6.  For each distinct exact size-6 owner set U, reconstruct the COMPLETE
// outside candidate pool P(U) by looking up all 63 nonempty support subsets of
// U, then search that small induced pool exactly for eight pairwise
// nonconfusable additions.  If found, deleting the six owners and adding the
// eight vertices gives a verifier-checkable 134754-point set.
//
// No lower-radius negative result is used for pruning in this stage; its
// completeness is therefore independent of the connected-support arguments
// used by the complementary lower-support radius-6 stage.
#include <algorithm>
#include <array>
#include <atomic>
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
constexpr std::uint32_t N=P7[D], GROUPS=N/7u, OVER=0xffffffffu;
constexpr unsigned K=6;
struct Rec{std::uint32_t x[K];};
struct Key{std::array<std::uint32_t,K>a{};bool operator==(const Key&o)const{return a==o.a;}bool operator<(const Key&o)const{return a<o.a;}};
struct KeyHash{std::size_t operator()(const Key&q)const noexcept{std::size_t h=0;for(auto x:q.a)h^=std::size_t(x)+0x9e3779b97f4a7c15ULL+(h<<6)+(h>>2);return h;}};
struct CRec{Key k;std::uint32_t v;};
struct Range{std::uint32_t lo,hi;};
struct SixGroup{Key k;std::uint32_t lo,hi;};

std::vector<std::uint32_t>load_ids(const char*p){std::ifstream in(p);if(!in)throw std::runtime_error("cannot open ids");std::vector<std::uint32_t>a;std::uint64_t z;while(in>>z){if(z>=N)throw std::runtime_error("id range");a.push_back((std::uint32_t)z);}if(a.empty())throw std::runtime_error("empty baseline");std::sort(a.begin(),a.end());if(std::adjacent_find(a.begin(),a.end())!=a.end())throw std::runtime_error("duplicate baseline");return a;}
inline bool overflow(const Rec&r){return r.x[0]==OVER;}
inline unsigned rsize(const Rec&r){if(overflow(r))return K+1;unsigned n=0;while(n<K&&r.x[n])++n;return n;}
inline Rec unite3(const Rec&a,const Rec&b,const Rec&c){if(overflow(a)||overflow(b)||overflow(c)){Rec r{};r.x[0]=OVER;return r;}unsigned ia=0,ib=0,ic=0,m=0;std::uint32_t last=0;Rec out{};for(;;){auto va=ia<K?a.x[ia]:0u,vb=ib<K?b.x[ib]:0u,vc=ic<K?c.x[ic]:0u;std::uint32_t v=0;if(va)v=va;if(vb&&(!v||vb<v))v=vb;if(vc&&(!v||vc<v))v=vc;if(!v)break;if(va==v)++ia;if(vb==v)++ib;if(vc==v)++ic;if(v==last)continue;if(m==K){Rec r{};r.x[0]=OVER;return r;}out.x[m++]=v;last=v;}return out;}
bool conflict(std::uint32_t a,std::uint32_t b){if(a==b)return true;for(int d=0;d<D;++d){int x=a%7u,y=b%7u;a/=7u;b/=7u;int z=(x-y+7)%7;if(z!=0&&z!=1&&z!=6)return false;}return true;}
bool find_rec(const std::vector<std::uint32_t>&p,std::size_t s,unsigned need,std::vector<std::uint32_t>&ch){if(ch.size()==need)return true;if(ch.size()+(p.size()-s)<need)return false;for(std::size_t i=s;i<p.size();++i){bool ok=true;for(auto z:ch)if(conflict(z,p[i])){ok=false;break;}if(!ok)continue;ch.push_back(p[i]);if(find_rec(p,i+1,need,ch))return true;ch.pop_back();}return false;}
bool find8(std::vector<std::uint32_t>p,std::vector<std::uint32_t>&out){std::sort(p.begin(),p.end());p.erase(std::unique(p.begin(),p.end()),p.end());out.clear();if(p.size()<8)return false;return find_rec(p,0,8,out);}
Key subset_key(const Key&u,unsigned mask){Key q{};unsigned j=0;for(unsigned i=0;i<K;++i)if(mask&(1u<<i))q.a[j++]=u.a[i];return q;}
}

int main(int argc,char**argv)try{
 if(argc!=2){std::cerr<<"usage: search_net2_r6_direct BASELINE_IDS\n";return 2;}
 auto base=load_ids(argv[1]);std::unordered_set<std::uint32_t>bset;base.size();bset.reserve(base.size()*2);for(auto v:base)bset.insert(v);
 std::vector<Rec>a(N);for(std::uint32_t i=0;i<base.size();++i)a[base[i]].x[0]=i+1;
 for(int dim=0;dim<D;++dim){const std::uint32_t s=P7[dim];const std::uint64_t block=std::uint64_t(s)*7u;
#pragma omp parallel for schedule(static)
  for(std::int64_t gg=0;gg<(std::int64_t)GROUPS;++gg){const std::uint64_t g=(std::uint64_t)gg,bn=g/s;const std::uint32_t off=g%s;const std::uint64_t b0=bn*block+off;Rec old[7],nw[7];for(int k=0;k<7;++k)old[k]=a[b0+std::uint64_t(k)*s];for(int k=0;k<7;++k)nw[k]=unite3(old[(k+6)%7],old[k],old[(k+1)%7]);for(int k=0;k<7;++k)a[b0+std::uint64_t(k)*s]=nw[k];}
  std::cerr<<"support dim="<<dim<<"\n";
 }
 std::vector<CRec>lower,six;lower.reserve(6000000);six.reserve(3300000);std::uint64_t c0=0;
 for(std::uint32_t v=0;v<N;++v){unsigned n=rsize(a[v]);if(n==0){if(!bset.count(v))++c0;continue;}if(n>K||bset.count(v))continue;Key k{};for(unsigned j=0;j<n;++j)k.a[j]=a[v].x[j];if(n<K)lower.push_back({k,v});else six.push_back({k,v});}
 if(c0)throw std::runtime_error("coverage0 nonzero");
 a.clear();a.shrink_to_fit();bset.clear();bset.rehash(0);
 auto less=[](const CRec&x,const CRec&y){if(x.k<y.k)return true;if(y.k<x.k)return false;return x.v<y.v;};std::sort(lower.begin(),lower.end(),less);std::sort(six.begin(),six.end(),less);
 std::unordered_map<Key,Range,KeyHash>idx;idx.reserve(lower.size());for(std::uint32_t i=0;i<lower.size();){std::uint32_t j=i+1;while(j<lower.size()&&lower[j].k==lower[i].k)++j;idx.emplace(lower[i].k,Range{i,j});i=j;}
 std::vector<SixGroup>groups;groups.reserve(six.size());for(std::uint32_t i=0;i<six.size();){std::uint32_t j=i+1;while(j<six.size()&&six[j].k==six[i].k)++j;groups.push_back({six[i].k,i,j});i=j;}
 std::atomic<bool>found(false);std::array<std::uint32_t,6>wrem{};std::vector<std::uint32_t>wadd;std::atomic<std::uint64_t>eligible(0),tested(0);std::atomic<std::uint32_t>maxpool(0);
#pragma omp parallel for schedule(dynamic,256)
 for(std::int64_t gi=0;gi<(std::int64_t)groups.size();++gi){if(found.load(std::memory_order_relaxed))continue;const auto&g=groups[gi];std::vector<std::uint32_t>pool;pool.reserve(40);for(std::uint32_t i=g.lo;i<g.hi;++i)pool.push_back(six[i].v);for(unsigned mask=1;mask<63;++mask){Key q=subset_key(g.k,mask);auto it=idx.find(q);if(it==idx.end())continue;for(std::uint32_t i=it->second.lo;i<it->second.hi;++i)pool.push_back(lower[i].v);}auto ps=(std::uint32_t)pool.size();auto old=maxpool.load();while(ps>old&&!maxpool.compare_exchange_weak(old,ps)){}if(ps<8)continue;++eligible;std::vector<std::uint32_t>ch;++tested;if(find8(pool,ch)){bool expected=false;if(found.compare_exchange_strong(expected,true)){
#pragma omp critical
   {for(unsigned j=0;j<K;++j)wrem[j]=base[g.k.a[j]-1];wadd=ch;}
  }} }
 if(found.load()){std::cout<<"{\"kind\":\"replace6add8\",\"method\":\"exact-unrestricted-r6-direct-support\",\"baseline_size\":"<<base.size()<<",\"coverage0\":0,\"lower_candidates\":"<<lower.size()<<",\"coverage6_candidates\":"<<six.size()<<",\"coverage6_groups\":"<<groups.size()<<",\"eligible_owner6\":"<<eligible.load()<<",\"tested_owner6\":"<<tested.load()<<",\"max_supported_pool\":"<<maxpool.load()<<",\"remove\":[";for(unsigned i=0;i<6;++i)std::cout<<(i?",":"")<<wrem[i];std::cout<<"],\"add\":[";for(unsigned i=0;i<wadd.size();++i)std::cout<<(i?",":"")<<wadd[i];std::cout<<"]}\n";return 0;}
 std::cout<<"{\"kind\":\"none\",\"method\":\"exact-unrestricted-r6-direct-support\",\"baseline_size\":"<<base.size()<<",\"coverage0\":0,\"lower_candidates\":"<<lower.size()<<",\"coverage6_candidates\":"<<six.size()<<",\"lower_support_groups\":"<<idx.size()<<",\"coverage6_groups\":"<<groups.size()<<",\"eligible_owner6\":"<<eligible.load()<<",\"tested_owner6\":"<<tested.load()<<",\"max_supported_pool\":"<<maxpool.load()<<"}\n";return 0;
}catch(const std::exception&e){std::cerr<<"error: "<<e.what()<<"\n";return 1;}
