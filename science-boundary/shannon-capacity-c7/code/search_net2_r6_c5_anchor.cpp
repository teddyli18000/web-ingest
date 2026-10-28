// Exact radius-6 lower-support stage for witnesses containing a size-5 support.
//
// Baseline: a verified 134752-point independent set in C7^10. We seek eight
// pairwise nonconfusable outside vertices whose blocker-owner union has size 6.
// This file handles the complete subfamily in which at least one selected
// addition has blocker support size exactly 5, while no size-6 support is
// needed (the latter is handled by search_net2_r6_direct.cpp).
//
// Let A be a selected size-5 support and x the sixth owner. The exact one-owner
// replay below checks alpha(P({x}))<=1. Hall/radius-5 constraints require x to
// occur in at least two selected additions, so they cannot both be singleton
// support {x}. Hence one selected support contains x and some owner of A. Thus x
// occurs as a real co-owner neighbor of A in an observed support group. We
// enumerate exactly those neighbors, reconstruct the COMPLETE P(A union {x})
// from all support groups of sizes 1..5, and decide independent-set size >=8.
#include <algorithm>
#include <array>
#include <atomic>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <unordered_map>
#include <vector>
#ifdef _OPENMP
#include <omp.h>
#endif
namespace{
constexpr int D=10;constexpr std::uint32_t P7[D+1]={1u,7u,49u,343u,2401u,16807u,117649u,823543u,5764801u,40353607u,282475249u};constexpr std::uint32_t N=P7[D],GROUPS=N/7u,OVER=0xffffffffu;constexpr unsigned K=6;
struct Rec{std::uint32_t x[K];};struct Key{std::array<std::uint32_t,K>a{};bool operator==(const Key&o)const{return a==o.a;}bool operator<(const Key&o)const{return a<o.a;}};struct KH{std::size_t operator()(const Key&q)const noexcept{std::size_t h=0;for(auto x:q.a)h^=std::size_t(x)+0x9e3779b97f4a7c15ULL+(h<<6)+(h>>2);return h;}};struct CR{Key k;std::uint32_t v;};struct Range{std::uint32_t lo,hi;};struct G5{Key k;Range r;};
std::vector<std::uint32_t>load(const char*p){std::ifstream in(p);if(!in)throw std::runtime_error("ids");std::vector<std::uint32_t>a;std::uint64_t z;while(in>>z){if(z>=N)throw std::runtime_error("range");a.push_back(z);}std::sort(a.begin(),a.end());if(a.size()!=134752||std::adjacent_find(a.begin(),a.end())!=a.end())throw std::runtime_error("baseline");return a;}
inline bool ov(const Rec&r){return r.x[0]==OVER;}inline unsigned rs(const Rec&r){if(ov(r))return K+1;unsigned n=0;while(n<K&&r.x[n])++n;return n;}inline Rec un3(const Rec&a,const Rec&b,const Rec&c){if(ov(a)||ov(b)||ov(c)){Rec r{};r.x[0]=OVER;return r;}unsigned ia=0,ib=0,ic=0,m=0;std::uint32_t last=0;Rec o{};for(;;){auto va=ia<K?a.x[ia]:0u,vb=ib<K?b.x[ib]:0u,vc=ic<K?c.x[ic]:0u;std::uint32_t v=0;if(va)v=va;if(vb&&(!v||vb<v))v=vb;if(vc&&(!v||vc<v))v=vc;if(!v)break;if(va==v)++ia;if(vb==v)++ib;if(vc==v)++ic;if(v==last)continue;if(m==K){Rec r{};r.x[0]=OVER;return r;}o.x[m++]=v;last=v;}return o;}
bool cf(std::uint32_t a,std::uint32_t b){if(a==b)return true;for(int d=0;d<D;++d){int x=a%7u,y=b%7u;a/=7u;b/=7u;int z=(x-y+7)%7;if(z!=0&&z!=1&&z!=6)return false;}return true;}
unsigned ksize(const Key&q){unsigned n=0;while(n<K&&q.a[n])++n;return n;}
Key subkey(const Key&u,unsigned mask){Key q{};unsigned j=0;for(unsigned i=0;i<K;++i)if(mask&(1u<<i))q.a[j++]=u.a[i];return q;}
bool rec8(const std::vector<std::uint32_t>&p,std::size_t s,std::vector<std::uint32_t>&ch){if(ch.size()==8)return true;if(ch.size()+p.size()-s<8)return false;for(std::size_t i=s;i<p.size();++i){bool ok=true;for(auto z:ch)if(cf(z,p[i])){ok=false;break;}if(!ok)continue;ch.push_back(p[i]);if(rec8(p,i+1,ch))return true;ch.pop_back();}return false;}
bool find8(std::vector<std::uint32_t>p,std::vector<std::uint32_t>&ch){std::sort(p.begin(),p.end());p.erase(std::unique(p.begin(),p.end()),p.end());ch.clear();return p.size()>=8&&rec8(p,0,ch);}
}
int main(int argc,char**argv)try{
 if(argc!=2){std::cerr<<"usage: search_net2_r6_c5_anchor BASELINE_IDS\n";return 2;}auto base=load(argv[1]);
 std::vector<std::uint8_t>inbase(N);for(auto v:base)inbase[v]=1;std::vector<Rec>a(N);for(std::uint32_t i=0;i<base.size();++i)a[base[i]].x[0]=i+1;
 for(int d=0;d<D;++d){auto s=P7[d];std::uint64_t block=std::uint64_t(s)*7u;
#pragma omp parallel for schedule(static)
  for(std::int64_t gg=0;gg<(std::int64_t)GROUPS;++gg){std::uint64_t g=gg,bn=g/s;std::uint32_t off=g%s,b0=(std::uint32_t)(bn*block+off);Rec old[7],nw[7];for(int k=0;k<7;++k)old[k]=a[b0+k*s];for(int k=0;k<7;++k)nw[k]=un3(old[(k+6)%7],old[k],old[(k+1)%7]);for(int k=0;k<7;++k)a[b0+k*s]=nw[k];}}
 std::vector<CR>lo;lo.reserve(6000000);std::uint64_t c0=0;for(std::uint32_t v=0;v<N;++v){if(inbase[v])continue;auto n=rs(a[v]);if(n==0){++c0;continue;}if(n>5)continue;Key k{};for(unsigned j=0;j<n;++j)k.a[j]=a[v].x[j];lo.push_back({k,v});}if(c0)throw std::runtime_error("coverage0");a.clear();a.shrink_to_fit();inbase.clear();inbase.shrink_to_fit();
 auto less=[](const CR&x,const CR&y){if(x.k<y.k)return true;if(y.k<x.k)return false;return x.v<y.v;};std::sort(lo.begin(),lo.end(),less);
 std::unordered_map<Key,Range,KH>idx;idx.reserve(lo.size());std::vector<G5>g5;g5.reserve(3000000);std::vector<std::uint64_t>edges;edges.reserve(50000000);
 for(std::uint32_t i=0;i<lo.size();){std::uint32_t j=i+1;while(j<lo.size()&&lo[j].k==lo[i].k)++j;auto k=lo[i].k;idx.emplace(k,Range{i,j});auto n=ksize(k);if(n==1){for(std::uint32_t x=i;x<j;++x)for(std::uint32_t y=x+1;y<j;++y)if(!cf(lo[x].v,lo[y].v))throw std::runtime_error("one-owner alpha>1; c5-anchor completeness precondition failed");}if(n==5)g5.push_back({k,{i,j}});if(n>=2)for(unsigned x=0;x<n;++x)for(unsigned y=x+1;y<n;++y){auto u=k.a[x]-1,v=k.a[y]-1;if(u>v)std::swap(u,v);edges.push_back((std::uint64_t(u)<<32)|v);}i=j;}
 std::sort(edges.begin(),edges.end());edges.erase(std::unique(edges.begin(),edges.end()),edges.end());std::vector<std::uint32_t>deg(base.size());for(auto e:edges){++deg[e>>32];++deg[(std::uint32_t)e];}std::vector<std::uint64_t>off(base.size()+1);for(std::size_t i=0;i<base.size();++i)off[i+1]=off[i]+deg[i];std::vector<std::uint32_t>adj(off.back()),cur(base.size());for(std::size_t i=0;i<base.size();++i)cur[i]=off[i];for(auto e:edges){auto u=(std::uint32_t)(e>>32),v=(std::uint32_t)e;adj[cur[u]++]=v;adj[cur[v]++]=u;}edges.clear();edges.shrink_to_fit();deg.clear();deg.shrink_to_fit();cur.clear();cur.shrink_to_fit();
 std::atomic<bool>found(false);std::array<std::uint32_t,6>wrem{};std::vector<std::uint32_t>wadd;std::atomic<std::uint64_t>generated(0),eligible(0),tested(0);std::atomic<std::uint32_t>maxpool(0),maxneighbors(0);
#pragma omp parallel for schedule(dynamic,64)
 for(std::int64_t ai=0;ai<(std::int64_t)g5.size();++ai){if(found.load(std::memory_order_relaxed))continue;auto A=g5[ai].k;std::vector<std::uint32_t>xs;for(unsigned t=0;t<5;++t){auto u=A.a[t]-1;for(std::uint64_t q=off[u];q<off[u+1];++q){auto x=adj[q]+1;bool inside=false;for(unsigned h=0;h<5;++h)if(A.a[h]==x){inside=true;break;}if(!inside)xs.push_back(x);}}std::sort(xs.begin(),xs.end());xs.erase(std::unique(xs.begin(),xs.end()),xs.end());auto xn=(std::uint32_t)xs.size();auto mo=maxneighbors.load();while(xn>mo&&!maxneighbors.compare_exchange_weak(mo,xn)){}for(auto x:xs){if(found.load(std::memory_order_relaxed))break;++generated;Key U{};std::array<std::uint32_t,6>z{A.a[0],A.a[1],A.a[2],A.a[3],A.a[4],x};std::sort(z.begin(),z.end());U.a=z;std::vector<std::uint32_t>pool;pool.reserve(48);for(unsigned m=1;m<63;++m){auto it=idx.find(subkey(U,m));if(it==idx.end())continue;for(std::uint32_t q=it->second.lo;q<it->second.hi;++q)pool.push_back(lo[q].v);}auto ps=(std::uint32_t)pool.size();auto mp=maxpool.load();while(ps>mp&&!maxpool.compare_exchange_weak(mp,ps)){}if(ps<8)continue;++eligible;std::vector<std::uint32_t>ch;++tested;if(find8(pool,ch)){bool ex=false;if(found.compare_exchange_strong(ex,true)){
#pragma omp critical
 {for(unsigned h=0;h<6;++h)wrem[h]=base[U.a[h]-1];wadd=ch;}
 }}}}
 if(found.load()){std::cout<<"{\"kind\":\"replace6add8\",\"method\":\"exact-r6-c5-anchor\",\"baseline_size\":"<<base.size()<<",\"lower_candidates\":"<<lo.size()<<",\"support_groups\":"<<idx.size()<<",\"coverage5_groups\":"<<g5.size()<<",\"generated_owner6_with_duplicates\":"<<generated.load()<<",\"eligible_owner6_with_duplicates\":"<<eligible.load()<<",\"tested_owner6_with_duplicates\":"<<tested.load()<<",\"max_supported_pool\":"<<maxpool.load()<<",\"max_anchor_neighbor_owners\":"<<maxneighbors.load()<<",\"remove\":[";for(unsigned i=0;i<6;++i)std::cout<<(i?",":"")<<wrem[i];std::cout<<"],\"add\":[";for(unsigned i=0;i<wadd.size();++i)std::cout<<(i?",":"")<<wadd[i];std::cout<<"]}\n";return 0;}
 std::cout<<"{\"kind\":\"none\",\"method\":\"exact-r6-c5-anchor\",\"baseline_size\":"<<base.size()<<",\"lower_candidates\":"<<lo.size()<<",\"support_groups\":"<<idx.size()<<",\"coverage5_groups\":"<<g5.size()<<",\"generated_owner6_with_duplicates\":"<<generated.load()<<",\"eligible_owner6_with_duplicates\":"<<eligible.load()<<",\"tested_owner6_with_duplicates\":"<<tested.load()<<",\"max_supported_pool\":"<<maxpool.load()<<",\"max_anchor_neighbor_owners\":"<<maxneighbors.load()<<"}\n";return 0;
}catch(const std::exception&e){std::cerr<<"error: "<<e.what()<<"\n";return 1;}
