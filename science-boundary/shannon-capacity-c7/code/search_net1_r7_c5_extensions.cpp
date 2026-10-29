// Exact C7^10 radius-7 net+1 search, maximum selected blocker support = 5.
//
// Baseline: the verified Few Shots 134753-point record. We seek eight pairwise
// nonconfusable outside vertices whose blocker-owner union has size seven.
// Lower radii 1..6 are already exactly negative for net+1. Therefore the
// support hypergraph of any radius-7 witness must be connected: otherwise one
// connected component would contain more additions than owners and would be a
// smaller-radius improvement.
//
// This stratum assumes at least one selected addition has support exactly 5 and
// none has support 6 or 7. Anchor an observed five-owner support A. The 2-section
// (co-owner graph) of a connected support hypergraph is connected, so the two
// owners outside A can be ordered x,y such that x is a real co-owner neighbor
// of A and y is a real co-owner neighbor of A union {x}. We enumerate exactly
// this superset using all observed support groups of sizes 2..5, canonicalize on
// the lexicographically least contained c5 support, reconstruct COMPLETE P(U)
// from all support groups of sizes 1..5, and decide alpha(P(U)) >= 8 exactly.
#include <algorithm>
#include <array>
#include <atomic>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <limits>
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
constexpr unsigned K=7;
struct Rec{std::uint32_t x[K];};
struct Key{std::array<std::uint32_t,K>a{};bool operator==(const Key&o)const{return a==o.a;}bool operator<(const Key&o)const{return a<o.a;}};
struct KH{std::size_t operator()(const Key&q)const noexcept{std::size_t h=0;for(auto x:q.a)h^=std::size_t(x)+0x9e3779b97f4a7c15ULL+(h<<6)+(h>>2);return h;}};
struct CR{Key k;std::uint32_t v;};
struct Range{std::uint32_t lo,hi;};
struct G5{Key k;Range r;};
std::vector<std::uint32_t> load(const char*p){std::ifstream in(p);if(!in)throw std::runtime_error("ids");std::vector<std::uint32_t>a;std::uint64_t z;while(in>>z){if(z>=N)throw std::runtime_error("range");a.push_back((std::uint32_t)z);}std::sort(a.begin(),a.end());if(a.size()!=134753||std::adjacent_find(a.begin(),a.end())!=a.end())throw std::runtime_error("baseline");return a;}
inline bool ov(const Rec&r){return r.x[0]==OVER;}
inline unsigned rs(const Rec&r){if(ov(r))return K+1;unsigned n=0;while(n<K&&r.x[n])++n;return n;}
inline Rec un3(const Rec&a,const Rec&b,const Rec&c){if(ov(a)||ov(b)||ov(c)){Rec r{};r.x[0]=OVER;return r;}unsigned ia=0,ib=0,ic=0,m=0;std::uint32_t last=0;Rec o{};for(;;){auto va=ia<K?a.x[ia]:0u,vb=ib<K?b.x[ib]:0u,vc=ic<K?c.x[ic]:0u;std::uint32_t v=0;if(va)v=va;if(vb&&(!v||vb<v))v=vb;if(vc&&(!v||vc<v))v=vc;if(!v)break;if(va==v)++ia;if(vb==v)++ib;if(vc==v)++ic;if(v==last)continue;if(m==K){Rec r{};r.x[0]=OVER;return r;}o.x[m++]=v;last=v;}return o;}
bool cf(std::uint32_t a,std::uint32_t b){if(a==b)return true;for(int d=0;d<D;++d){int x=a%7u,y=b%7u;a/=7u;b/=7u;int z=(x-y+7)%7;if(z!=0&&z!=1&&z!=6)return false;}return true;}
unsigned ksize(const Key&q){unsigned n=0;while(n<K&&q.a[n])++n;return n;}
Key subkey(const Key&u,unsigned mask){Key q{};unsigned j=0;for(unsigned i=0;i<K;++i)if(mask&(1u<<i))q.a[j++]=u.a[i];return q;}
bool rec8(const std::vector<std::uint32_t>&p,std::size_t s,std::vector<std::uint32_t>&ch){if(ch.size()==8)return true;if(ch.size()+p.size()-s<8)return false;for(std::size_t i=s;i<p.size();++i){bool ok=true;for(auto z:ch)if(cf(z,p[i])){ok=false;break;}if(!ok)continue;ch.push_back(p[i]);if(rec8(p,i+1,ch))return true;ch.pop_back();}return false;}
bool find8(std::vector<std::uint32_t>p,std::vector<std::uint32_t>&ch){std::sort(p.begin(),p.end());p.erase(std::unique(p.begin(),p.end()),p.end());ch.clear();return p.size()>=8&&rec8(p,0,ch);}
bool inside(const Key&u,std::uint32_t x,unsigned n){for(unsigned i=0;i<n;++i)if(u.a[i]==x)return true;return false;}
Key make7(const Key&A,std::uint32_t x,std::uint32_t y){Key U{};std::array<std::uint32_t,7>z{A.a[0],A.a[1],A.a[2],A.a[3],A.a[4],x,y};std::sort(z.begin(),z.end());U.a=z;return U;}
}
int main(int argc,char**argv)try{
 if(argc!=4){std::cerr<<"usage: search_net1_r7_c5_extensions BASELINE_IDS SHARD SHARDS\n";return 2;}
 auto base=load(argv[1]);unsigned shard=std::stoul(argv[2]),shards=std::stoul(argv[3]);if(!shards||shard>=shards)throw std::runtime_error("shard");
 std::vector<std::uint8_t>inbase(N);for(auto v:base)inbase[v]=1;
 std::vector<Rec>a(N);for(std::uint32_t i=0;i<base.size();++i)a[base[i]].x[0]=i+1;
 for(int d=0;d<D;++d){auto s=P7[d];std::uint64_t block=std::uint64_t(s)*7u;
#pragma omp parallel for schedule(static)
  for(std::int64_t gg=0;gg<(std::int64_t)GROUPS;++gg){std::uint64_t g=gg,bn=g/s;std::uint32_t off0=g%s,b0=(std::uint32_t)(bn*block+off0);Rec old[7],nw[7];for(int k=0;k<7;++k)old[k]=a[b0+k*s];for(int k=0;k<7;++k)nw[k]=un3(old[(k+6)%7],old[k],old[(k+1)%7]);for(int k=0;k<7;++k)a[b0+k*s]=nw[k];}}
 std::vector<CR>lo;lo.reserve(6000000);std::uint64_t c0=0;for(std::uint32_t v=0;v<N;++v){if(inbase[v])continue;auto n=rs(a[v]);if(n==0){++c0;continue;}if(n>5)continue;Key k{};for(unsigned j=0;j<n;++j)k.a[j]=a[v].x[j];lo.push_back({k,v});}if(c0)throw std::runtime_error("coverage0");a.clear();a.shrink_to_fit();inbase.clear();inbase.shrink_to_fit();
 auto less=[](const CR&x,const CR&y){if(x.k<y.k)return true;if(y.k<x.k)return false;return x.v<y.v;};std::sort(lo.begin(),lo.end(),less);
 std::unordered_map<Key,Range,KH>idx;idx.reserve(lo.size());std::vector<G5>g5;g5.reserve(3000000);std::vector<std::uint64_t>edges;edges.reserve(50000000);
 for(std::uint32_t i=0;i<lo.size();){std::uint32_t j=i+1;while(j<lo.size()&&lo[j].k==lo[i].k)++j;auto k=lo[i].k;idx.emplace(k,Range{i,j});auto n=ksize(k);if(n==1){for(std::uint32_t x=i;x<j;++x)for(std::uint32_t y=x+1;y<j;++y)if(!cf(lo[x].v,lo[y].v))throw std::runtime_error("one-owner alpha>1");}if(n==5)g5.push_back({k,{i,j}});if(n>=2)for(unsigned x=0;x<n;++x)for(unsigned y=x+1;y<n;++y){auto u=k.a[x]-1,v=k.a[y]-1;if(u>v)std::swap(u,v);edges.push_back((std::uint64_t(u)<<32)|v);}i=j;}
 std::sort(edges.begin(),edges.end());edges.erase(std::unique(edges.begin(),edges.end()),edges.end());
 std::vector<std::uint32_t>deg(base.size());for(auto e:edges){++deg[e>>32];++deg[(std::uint32_t)e];}std::vector<std::uint64_t>off(base.size()+1);for(std::size_t i=0;i<base.size();++i)off[i+1]=off[i]+deg[i];std::vector<std::uint32_t>adj(off.back()),cur(base.size());for(std::size_t i=0;i<base.size();++i)cur[i]=off[i];for(auto e:edges){auto u=(std::uint32_t)(e>>32),v=(std::uint32_t)e;adj[cur[u]++]=v;adj[cur[v]++]=u;}edges.clear();edges.shrink_to_fit();deg.clear();deg.shrink_to_fit();cur.clear();cur.shrink_to_fit();
 std::atomic<bool>found(false);std::array<std::uint32_t,7>wrem{};std::vector<std::uint32_t>wadd;std::atomic<std::uint64_t>generated(0),canonical(0),eligible(0),tested(0);std::atomic<std::uint32_t>maxpool(0),maxx(0),maxy(0);
#pragma omp parallel for schedule(dynamic,8)
 for(std::int64_t ai=0;ai<(std::int64_t)g5.size();++ai){if(found.load(std::memory_order_relaxed)||((std::uint64_t)ai%shards)!=shard)continue;auto A=g5[ai].k;
  std::vector<std::uint32_t>xs;for(unsigned t=0;t<5;++t){auto u=A.a[t]-1;for(std::uint64_t q=off[u];q<off[u+1];++q){auto x=adj[q]+1;if(!inside(A,x,5))xs.push_back(x);}}std::sort(xs.begin(),xs.end());xs.erase(std::unique(xs.begin(),xs.end()),xs.end());auto xn=(std::uint32_t)xs.size();auto mx=maxx.load();while(xn>mx&&!maxx.compare_exchange_weak(mx,xn)){}
  std::unordered_set<Key,KH>seen;seen.reserve(xs.size()*8+16);
  for(auto x:xs){if(found.load(std::memory_order_relaxed))break;Key U6{};std::array<std::uint32_t,6>z6{A.a[0],A.a[1],A.a[2],A.a[3],A.a[4],x};std::sort(z6.begin(),z6.end());for(unsigned h=0;h<6;++h)U6.a[h]=z6[h];
   std::vector<std::uint32_t>ys;for(unsigned t=0;t<6;++t){auto u=U6.a[t]-1;for(std::uint64_t q=off[u];q<off[u+1];++q){auto y=adj[q]+1;if(!inside(U6,y,6))ys.push_back(y);}}std::sort(ys.begin(),ys.end());ys.erase(std::unique(ys.begin(),ys.end()),ys.end());auto yn=(std::uint32_t)ys.size();auto my=maxy.load();while(yn>my&&!maxy.compare_exchange_weak(my,yn)){}
   for(auto y:ys){if(found.load(std::memory_order_relaxed))break;++generated;auto U=make7(A,x,y);if(!seen.insert(U).second)continue;
    // Canonical anchor: A must be the lexicographically least observed c5 support contained in U.
    Key best{};bool have=false;for(unsigned m=0;m<(1u<<7);++m){if(__builtin_popcount(m)!=5)continue;auto q=subkey(U,m);if(idx.find(q)==idx.end())continue;if(!have||q<best){best=q;have=true;}}if(!have||!(best==A))continue;++canonical;
    std::vector<std::uint32_t>pool;pool.reserve(64);for(unsigned m=1;m<(1u<<7);++m){if(__builtin_popcount(m)>5)continue;auto it=idx.find(subkey(U,m));if(it==idx.end())continue;for(std::uint32_t q=it->second.lo;q<it->second.hi;++q)pool.push_back(lo[q].v);}auto ps=(std::uint32_t)pool.size();auto mp=maxpool.load();while(ps>mp&&!maxpool.compare_exchange_weak(mp,ps)){}if(ps<8)continue;++eligible;std::vector<std::uint32_t>ch;++tested;if(find8(pool,ch)){bool ex=false;if(found.compare_exchange_strong(ex,true)){
#pragma omp critical
      {for(unsigned h=0;h<7;++h)wrem[h]=base[U.a[h]-1];wadd=ch;}
    }}
   }
  }
 }
 if(found.load()){std::cout<<"{\"kind\":\"replace7add8\",\"method\":\"exact-net1-r7-maxsupport5\",\"baseline_size\":"<<base.size()<<",\"shard\":"<<shard<<",\"shards\":"<<shards<<",\"lower_candidates\":"<<lo.size()<<",\"support_groups\":"<<idx.size()<<",\"coverage5_groups\":"<<g5.size()<<",\"generated_paths\":"<<generated.load()<<",\"canonical_owner7\":"<<canonical.load()<<",\"eligible_owner7\":"<<eligible.load()<<",\"tested_owner7\":"<<tested.load()<<",\"max_supported_pool\":"<<maxpool.load()<<",\"max_first_neighbors\":"<<maxx.load()<<",\"max_second_neighbors\":"<<maxy.load()<<",\"remove\":[";for(unsigned i=0;i<7;++i)std::cout<<(i?",":"")<<wrem[i];std::cout<<"],\"add\":[";for(unsigned i=0;i<wadd.size();++i)std::cout<<(i?",":"")<<wadd[i];std::cout<<"]}\n";return 0;}
 std::cout<<"{\"kind\":\"none\",\"method\":\"exact-net1-r7-maxsupport5\",\"baseline_size\":"<<base.size()<<",\"shard\":"<<shard<<",\"shards\":"<<shards<<",\"lower_candidates\":"<<lo.size()<<",\"support_groups\":"<<idx.size()<<",\"coverage5_groups\":"<<g5.size()<<",\"generated_paths\":"<<generated.load()<<",\"canonical_owner7\":"<<canonical.load()<<",\"eligible_owner7\":"<<eligible.load()<<",\"tested_owner7\":"<<tested.load()<<",\"max_supported_pool\":"<<maxpool.load()<<",\"max_first_neighbors\":"<<maxx.load()<<",\"max_second_neighbors\":"<<maxy.load()<<"}\n";return 0;
}catch(const std::exception&e){std::cerr<<"error: "<<e.what()<<"\n";return 1;}
