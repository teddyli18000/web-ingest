// Exact C7^10 radius-7 net+1 search, maximum selected blocker support = 5.
//
// Baseline: the verified Few Shots 134753-point record. We seek eight pairwise
// nonconfusable outside vertices whose blocker-owner union has size seven.
// Exact negativity through radius 6 implies that any radius-7 improving support
// hypergraph is connected: otherwise one connected component would contain
// more additions than owners and would itself be a smaller-radius improvement.
//
// This stratum contains an exact support-5 anchor A and no selected support of
// size 6 or 7. Relative to A, the two remaining owners are introduced either
// (i) together by one real crossing support, or (ii) one at a time by two real
// crossing supports. We pre-index every observed support<=5 as core+one-owner
// and core+two-owner extensions, enumerate only those real support crossings,
// canonicalize each seven-owner set by its least observed c5 anchor, reconstruct
// COMPLETE P_5(U), and decide alpha(P_5(U)) >= 8 exactly.
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
namespace{
constexpr int D=10;
constexpr std::uint32_t P7[D+1]={1u,7u,49u,343u,2401u,16807u,117649u,823543u,5764801u,40353607u,282475249u};
constexpr std::uint32_t N=P7[D],GROUPS=N/7u,OVER=0xffffffffu;
constexpr unsigned K=5;
struct Rec{std::uint32_t x[K];};
struct Key{std::array<std::uint32_t,K>a{};bool operator==(const Key&o)const{return a==o.a;}bool operator<(const Key&o)const{return a<o.a;}};
struct KH{std::size_t operator()(const Key&q)const noexcept{std::size_t h=0;for(auto x:q.a)h^=std::size_t(x)+0x9e3779b97f4a7c15ULL+(h<<6)+(h>>2);return h;}};
struct Owner7{std::array<std::uint32_t,7>a{};bool operator==(const Owner7&o)const{return a==o.a;}};
struct O7H{std::size_t operator()(const Owner7&q)const noexcept{std::size_t h=0;for(auto x:q.a)h^=std::size_t(x)+0x9e3779b97f4a7c15ULL+(h<<6)+(h>>2);return h;}};
struct CR{Key k;std::uint32_t v;};struct Range{std::uint32_t lo,hi;};struct G5{Key k;Range r;};
struct E1{Key core;std::uint32_t x;};
struct E2{Key core;std::uint32_t x,y;};
std::vector<std::uint32_t>load(const char*p){std::ifstream in(p);if(!in)throw std::runtime_error("ids");std::vector<std::uint32_t>a;std::uint64_t z;while(in>>z){if(z>=N)throw std::runtime_error("range");a.push_back((std::uint32_t)z);}std::sort(a.begin(),a.end());if(a.size()!=134753||std::adjacent_find(a.begin(),a.end())!=a.end())throw std::runtime_error("baseline");return a;}
inline bool ov(const Rec&r){return r.x[0]==OVER;}inline unsigned rs(const Rec&r){if(ov(r))return K+1;unsigned n=0;while(n<K&&r.x[n])++n;return n;}
inline Rec un3(const Rec&a,const Rec&b,const Rec&c){if(ov(a)||ov(b)||ov(c)){Rec r{};r.x[0]=OVER;return r;}unsigned ia=0,ib=0,ic=0,m=0;std::uint32_t last=0;Rec o{};for(;;){auto va=ia<K?a.x[ia]:0u,vb=ib<K?b.x[ib]:0u,vc=ic<K?c.x[ic]:0u;std::uint32_t v=0;if(va)v=va;if(vb&&(!v||vb<v))v=vb;if(vc&&(!v||vc<v))v=vc;if(!v)break;if(va==v)++ia;if(vb==v)++ib;if(vc==v)++ic;if(v==last)continue;if(m==K){Rec r{};r.x[0]=OVER;return r;}o.x[m++]=v;last=v;}return o;}
bool cf(std::uint32_t a,std::uint32_t b){if(a==b)return true;for(int d=0;d<D;++d){int x=a%7u,y=b%7u;a/=7u;b/=7u;int z=(x-y+7)%7;if(z!=0&&z!=1&&z!=6)return false;}return true;}
unsigned ksize(const Key&q){unsigned n=0;while(n<K&&q.a[n])++n;return n;}
Key remove1(const Key&q,unsigned n,unsigned t){Key r{};unsigned j=0;for(unsigned i=0;i<n;++i)if(i!=t)r.a[j++]=q.a[i];return r;}
Key remove2(const Key&q,unsigned n,unsigned s,unsigned t){Key r{};unsigned j=0;for(unsigned i=0;i<n;++i)if(i!=s&&i!=t)r.a[j++]=q.a[i];return r;}
Key subset(const std::vector<std::uint32_t>&v,unsigned mask){Key q{};unsigned j=0;for(unsigned i=0;i<v.size();++i)if(mask&(1u<<i))q.a[j++]=v[i];return q;}
Key subset7(const std::array<std::uint32_t,7>&v,unsigned mask){Key q{};unsigned j=0;for(unsigned i=0;i<7;++i)if(mask&(1u<<i))q.a[j++]=v[i];return q;}
bool find8(const std::vector<std::uint32_t>&p,std::vector<std::uint32_t>&out){unsigned n=p.size();if(n<8)return false;if(n<=63){std::vector<std::uint64_t>ok(n);for(unsigned i=0;i<n;++i)for(unsigned j=i+1;j<n;++j)if(!cf(p[i],p[j]))ok[i]|=1ull<<j;std::array<unsigned,8>ch{};auto dfs=[&](auto&&self,std::uint64_t m,unsigned d)->bool{if(d==8){out.clear();for(unsigned t=0;t<8;++t)out.push_back(p[ch[t]]);return true;}if(std::popcount(m)<8-d)return false;while(m){unsigned v=std::countr_zero(m);m&=m-1;ch[d]=v;if(self(self,m&ok[v],d+1))return true;if(std::popcount(m)<7-d)break;}return false;};return dfs(dfs,n==64?~0ull:((1ull<<n)-1),0);}std::vector<std::uint32_t>ch;auto dfs=[&](auto&&self,std::size_t s)->bool{if(ch.size()==8){out=ch;return true;}if(ch.size()+p.size()-s<8)return false;for(std::size_t i=s;i<p.size();++i){bool good=true;for(auto z:ch)if(cf(z,p[i])){good=false;break;}if(!good)continue;ch.push_back(p[i]);if(self(self,i+1))return true;ch.pop_back();}return false;};return dfs(dfs,0);}
}
int main(int argc,char**argv)try{
 if(argc!=4){std::cerr<<"usage: search_net1_r7_c5_extensions BASELINE_IDS SHARD SHARDS\n";return 2;}unsigned shard=std::stoul(argv[2]),shards=std::stoul(argv[3]);if(!shards||shard>=shards)throw std::runtime_error("shard");auto base=load(argv[1]);
 std::vector<std::uint8_t>inbase(N);for(auto v:base)inbase[v]=1;std::vector<Rec>a(N);for(std::uint32_t i=0;i<base.size();++i)a[base[i]].x[0]=i+1;
 for(int d=0;d<D;++d){auto s=P7[d];std::uint64_t block=std::uint64_t(s)*7u;
#pragma omp parallel for schedule(static)
  for(std::int64_t gg=0;gg<(std::int64_t)GROUPS;++gg){std::uint64_t g=gg,bn=g/s;std::uint32_t off=g%s,b0=(std::uint32_t)(bn*block+off);Rec old[7],nw[7];for(int k=0;k<7;++k)old[k]=a[b0+k*s];for(int k=0;k<7;++k)nw[k]=un3(old[(k+6)%7],old[k],old[(k+1)%7]);for(int k=0;k<7;++k)a[b0+k*s]=nw[k];}}
 std::vector<CR>lo;lo.reserve(6000000);std::uint64_t c0=0;for(std::uint32_t v=0;v<N;++v){if(inbase[v])continue;auto n=rs(a[v]);if(n==0){++c0;continue;}if(n>5)continue;Key k{};for(unsigned j=0;j<n;++j)k.a[j]=a[v].x[j];lo.push_back({k,v});}if(c0)throw std::runtime_error("coverage0");a.clear();a.shrink_to_fit();inbase.clear();inbase.shrink_to_fit();
 auto less=[](const CR&x,const CR&y){if(x.k<y.k)return true;if(y.k<x.k)return false;return x.v<y.v;};std::sort(lo.begin(),lo.end(),less);std::unordered_map<Key,Range,KH>idx;idx.reserve(lo.size());std::vector<G5>g5;g5.reserve(2600000);std::vector<E1>e1;std::vector<E2>e2;e1.reserve(16000000);e2.reserve(30000000);
 for(std::uint32_t i=0;i<lo.size();){std::uint32_t j=i+1;while(j<lo.size()&&lo[j].k==lo[i].k)++j;auto k=lo[i].k,n=ksize(k);idx.emplace(k,Range{i,j});if(n==1){for(std::uint32_t x=i;x<j;++x)for(std::uint32_t y=x+1;y<j;++y)if(!cf(lo[x].v,lo[y].v))throw std::runtime_error("one-owner alpha>1");}if(n==5)g5.push_back({k,{i,j}});if(n>=2)for(unsigned t=0;t<n;++t)e1.push_back({remove1(k,n,t),k.a[t]});if(n>=3)for(unsigned s=0;s<n;++s)for(unsigned t=s+1;t<n;++t){auto x=k.a[s],y=k.a[t];if(x>y)std::swap(x,y);e2.push_back({remove2(k,n,s,t),x,y});}i=j;}
 auto e1less=[](const E1&a,const E1&b){if(a.core<b.core)return true;if(b.core<a.core)return false;return a.x<b.x;};auto e2less=[](const E2&a,const E2&b){if(a.core<b.core)return true;if(b.core<a.core)return false;if(a.x!=b.x)return a.x<b.x;return a.y<b.y;};std::sort(e1.begin(),e1.end(),e1less);std::sort(e2.begin(),e2.end(),e2less);
 auto add_e1=[&](const std::vector<std::uint32_t>&cur,std::vector<std::uint32_t>&out){unsigned m=cur.size();for(unsigned mask=1;mask<(1u<<m);++mask){if(std::popcount(mask)>4)continue;auto core=subset(cur,mask);E1 probe{core,0};auto it=std::lower_bound(e1.begin(),e1.end(),probe,e1less);for(;it!=e1.end()&&it->core==core;++it)if(!std::binary_search(cur.begin(),cur.end(),it->x))out.push_back(it->x);}std::sort(out.begin(),out.end());out.erase(std::unique(out.begin(),out.end()),out.end());};
 auto add_e2=[&](const std::vector<std::uint32_t>&cur,std::vector<std::uint64_t>&out){unsigned m=cur.size();for(unsigned mask=1;mask<(1u<<m);++mask){if(std::popcount(mask)>3)continue;auto core=subset(cur,mask);E2 probe{core,0,0};auto it=std::lower_bound(e2.begin(),e2.end(),probe,e2less);for(;it!=e2.end()&&it->core==core;++it)if(!std::binary_search(cur.begin(),cur.end(),it->x)&&!std::binary_search(cur.begin(),cur.end(),it->y))out.push_back((std::uint64_t(it->x)<<32)|it->y);}std::sort(out.begin(),out.end());out.erase(std::unique(out.begin(),out.end()),out.end());};
 std::atomic<bool>found(false);std::array<std::uint32_t,7>wrem{};std::vector<std::uint32_t>wadd;std::atomic<std::uint64_t>anchors(0),one_ext(0),second_ext(0),direct_pairs(0),generated(0),canonical(0),eligible(0),tested(0);std::atomic<std::uint32_t>maxe1(0),maxe2(0),maxpool(0);
#pragma omp parallel for schedule(dynamic,8)
 for(std::int64_t ai=0;ai<(std::int64_t)g5.size();++ai){if((std::uint64_t(ai)%shards)!=shard||found.load(std::memory_order_relaxed))continue;++anchors;auto A=g5[ai].k;std::vector<std::uint32_t>av={A.a[0],A.a[1],A.a[2],A.a[3],A.a[4]};std::unordered_set<Owner7,O7H>seen;seen.reserve(256);
  auto testU=[&](std::uint32_t x,std::uint32_t y){if(x==y)return false;Owner7 O{{A.a[0],A.a[1],A.a[2],A.a[3],A.a[4],x,y}};std::sort(O.a.begin(),O.a.end());if(std::adjacent_find(O.a.begin(),O.a.end())!=O.a.end())return false;if(!seen.insert(O).second)return false;++generated;Key best{};bool have=false;for(unsigned mask=0;mask<128;++mask){if(std::popcount(mask)!=5)continue;auto q=subset7(O.a,mask);if(idx.find(q)==idx.end())continue;if(!have||q<best){best=q;have=true;}}if(!have||!(best==A))return false;++canonical;std::vector<std::uint32_t>pool;pool.reserve(80);for(unsigned mask=1;mask<128;++mask){if(std::popcount(mask)>5)continue;auto it=idx.find(subset7(O.a,mask));if(it==idx.end())continue;for(std::uint32_t z=it->second.lo;z<it->second.hi;++z)pool.push_back(lo[z].v);}std::sort(pool.begin(),pool.end());pool.erase(std::unique(pool.begin(),pool.end()),pool.end());auto ps=(std::uint32_t)pool.size(),old=maxpool.load();while(ps>old&&!maxpool.compare_exchange_weak(old,ps)){}if(ps<8)return false;++eligible;std::vector<std::uint32_t>ch;++tested;if(!find8(pool,ch))return false;bool ex=false;if(found.compare_exchange_strong(ex,true)){
#pragma omp critical
   {for(unsigned h=0;h<7;++h)wrem[h]=base[O.a[h]-1];wadd=ch;}}
   return true;};
  std::vector<std::uint32_t>xs;add_e1(av,xs);one_ext+=xs.size();auto me=(std::uint32_t)xs.size(),old=maxe1.load();while(me>old&&!maxe1.compare_exchange_weak(old,me)){}for(auto x:xs){if(found.load(std::memory_order_relaxed))break;std::vector<std::uint32_t>b=av;b.push_back(x);std::sort(b.begin(),b.end());std::vector<std::uint32_t>ys;add_e1(b,ys);second_ext+=ys.size();auto my=(std::uint32_t)ys.size();old=maxe2.load();while(my>old&&!maxe2.compare_exchange_weak(old,my)){}for(auto y:ys)if(testU(x,y))break;}
  if(found.load(std::memory_order_relaxed))continue;std::vector<std::uint64_t>ps;add_e2(av,ps);direct_pairs+=ps.size();for(auto e:ps){auto x=(std::uint32_t)(e>>32),y=(std::uint32_t)e;if(testU(x,y))break;}
 }
 if(found.load()){std::cout<<"{\"kind\":\"replace7add8\",\"method\":\"exact-net1-r7-c5-support-extensions\",\"baseline_size\":"<<base.size()<<",\"shard\":"<<shard<<",\"shards\":"<<shards<<",\"lower_candidates\":"<<lo.size()<<",\"support_groups\":"<<idx.size()<<",\"coverage5_groups\":"<<g5.size()<<",\"anchors\":"<<anchors.load()<<",\"one_extensions\":"<<one_ext.load()<<",\"second_extensions\":"<<second_ext.load()<<",\"direct_two_extensions\":"<<direct_pairs.load()<<",\"generated_owner7\":"<<generated.load()<<",\"canonical_owner7\":"<<canonical.load()<<",\"eligible_owner7\":"<<eligible.load()<<",\"tested_owner7\":"<<tested.load()<<",\"max_e1\":"<<maxe1.load()<<",\"max_e2\":"<<maxe2.load()<<",\"max_supported_pool\":"<<maxpool.load()<<",\"remove\":[";for(unsigned i=0;i<7;++i)std::cout<<(i?",":"")<<wrem[i];std::cout<<"],\"add\":[";for(unsigned i=0;i<wadd.size();++i)std::cout<<(i?",":"")<<wadd[i];std::cout<<"]}\n";return 0;}
 std::cout<<"{\"kind\":\"none\",\"method\":\"exact-net1-r7-c5-support-extensions\",\"baseline_size\":"<<base.size()<<",\"shard\":"<<shard<<",\"shards\":"<<shards<<",\"lower_candidates\":"<<lo.size()<<",\"support_groups\":"<<idx.size()<<",\"coverage5_groups\":"<<g5.size()<<",\"anchors\":"<<anchors.load()<<",\"one_extensions\":"<<one_ext.load()<<",\"second_extensions\":"<<second_ext.load()<<",\"direct_two_extensions\":"<<direct_pairs.load()<<",\"generated_owner7\":"<<generated.load()<<",\"canonical_owner7\":"<<canonical.load()<<",\"eligible_owner7\":"<<eligible.load()<<",\"tested_owner7\":"<<tested.load()<<",\"max_e1\":"<<maxe1.load()<<",\"max_e2\":"<<maxe2.load()<<",\"max_supported_pool\":"<<maxpool.load()<<"}\n";return 0;
}catch(const std::exception&e){std::cerr<<"error: "<<e.what()<<"\n";return 1;}
