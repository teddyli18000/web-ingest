// Exact radius-6 stage for connected witnesses with maximum selected support 3.
//
// Earlier exact work proves every remove-6/add-8 witness on the FunSearch
// deletion seeds has a connected support hypergraph.  Fix an observed size-3
// anchor A contained in the six-owner union U.  Starting from ANY nonempty
// proper owner subset of a connected selected hypergraph, some selected support
// crosses the cut.  With maximum support size 3, that crossing support can
// introduce either one or two new owners, never more.  Therefore the remaining
// three owners are introduced in exactly one of the patterns
//
//   1+1+1,  1+2,  or  2+1.
//
// We index REAL exact support groups as (core -> one new owner) and
// (core -> two new owners), enumerate only these support extensions, assign each
// final U to its lexicographically smallest observed size-3 anchor, deduplicate
// U by exact equality, reconstruct the COMPLETE P_{<=3}(U), and decide exactly
// whether it contains eight pairwise nonconfusable additions.
#include <algorithm>
#include <array>
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
constexpr unsigned K=3;
struct Rec{std::uint32_t x[K];};
struct Key{std::array<std::uint32_t,K>a{};bool operator==(const Key&o)const{return a==o.a;}bool operator<(const Key&o)const{return a<o.a;}};
struct KH{std::size_t operator()(const Key&q)const noexcept{std::size_t h=0;for(auto x:q.a)h^=std::size_t(x)+0x9e3779b97f4a7c15ULL+(h<<6)+(h>>2);return h;}};
struct U6{std::array<std::uint32_t,6>a{};bool operator==(const U6&o)const{return a==o.a;}};
struct U6H{std::size_t operator()(const U6&q)const noexcept{std::size_t h=0;for(auto x:q.a)h^=std::size_t(x)+0x9e3779b97f4a7c15ULL+(h<<6)+(h>>2);return h;}};
struct CR{Key k;std::uint32_t v;}; struct Range{std::uint32_t lo,hi;}; struct G3{Key k;Range r;};
struct E1{Key core;std::uint32_t x;}; struct E2{Key core;std::uint32_t x,y;};
std::vector<std::uint32_t>load(const char*p){std::ifstream in(p);if(!in)throw std::runtime_error("ids");std::vector<std::uint32_t>a;std::uint64_t z;while(in>>z){if(z>=N)throw std::runtime_error("range");a.push_back((std::uint32_t)z);}std::sort(a.begin(),a.end());if(a.size()!=134752||std::adjacent_find(a.begin(),a.end())!=a.end())throw std::runtime_error("baseline");return a;}
inline bool ov(const Rec&r){return r.x[0]==OVER;} inline unsigned rs(const Rec&r){if(ov(r))return K+1;unsigned n=0;while(n<K&&r.x[n])++n;return n;}
inline Rec un3(const Rec&a,const Rec&b,const Rec&c){if(ov(a)||ov(b)||ov(c)){Rec r{};r.x[0]=OVER;return r;}unsigned ia=0,ib=0,ic=0,m=0;std::uint32_t last=0;Rec o{};for(;;){auto va=ia<K?a.x[ia]:0u,vb=ib<K?b.x[ib]:0u,vc=ic<K?c.x[ic]:0u;std::uint32_t v=0;if(va)v=va;if(vb&&(!v||vb<v))v=vb;if(vc&&(!v||vc<v))v=vc;if(!v)break;if(va==v)++ia;if(vb==v)++ib;if(vc==v)++ic;if(v==last)continue;if(m==K){Rec r{};r.x[0]=OVER;return r;}o.x[m++]=v;last=v;}return o;}
bool cf(std::uint32_t a,std::uint32_t b){if(a==b)return true;for(int d=0;d<D;++d){int x=a%7u,y=b%7u;a/=7u;b/=7u;int z=(x-y+7)%7;if(z!=0&&z!=1&&z!=6)return false;}return true;}
unsigned ksize(const Key&q){unsigned n=0;while(n<K&&q.a[n])++n;return n;}
Key remove1(const Key&q,unsigned n,unsigned t){Key r{};unsigned j=0;for(unsigned i=0;i<n;++i)if(i!=t)r.a[j++]=q.a[i];return r;}
Key remove2(const Key&q,unsigned n,unsigned s,unsigned t){Key r{};unsigned j=0;for(unsigned i=0;i<n;++i)if(i!=s&&i!=t)r.a[j++]=q.a[i];return r;}
Key subset(const std::vector<std::uint32_t>&v,unsigned mask){Key q{};unsigned j=0;for(unsigned i=0;i<v.size();++i)if(mask&(1u<<i))q.a[j++]=v[i];return q;}
Key subset6(const U6&u,unsigned mask){Key q{};unsigned j=0;for(unsigned i=0;i<6;++i)if(mask&(1u<<i))q.a[j++]=u.a[i];return q;}
bool find8(const std::vector<std::uint32_t>&p,std::vector<std::uint32_t>&out){unsigned n=p.size();if(n<8)return false;if(n<=63){std::vector<std::uint64_t>ok(n);for(unsigned i=0;i<n;++i)for(unsigned j=i+1;j<n;++j)if(!cf(p[i],p[j]))ok[i]|=1ull<<j;std::array<unsigned,8>ch{};auto dfs=[&](auto&&self,std::uint64_t m,unsigned d)->bool{if(d==8){out.clear();for(unsigned t=0;t<8;++t)out.push_back(p[ch[t]]);return true;}if(std::popcount(m)<8-d)return false;while(m){unsigned v=std::countr_zero(m);m&=m-1;ch[d]=v;if(self(self,m&ok[v],d+1))return true;if(std::popcount(m)<7-d)break;}return false;};return dfs(dfs,(1ull<<n)-1,0);}std::vector<std::uint32_t>ch;auto dfs=[&](auto&&self,std::size_t s)->bool{if(ch.size()==8){out=ch;return true;}if(ch.size()+p.size()-s<8)return false;for(std::size_t i=s;i<p.size();++i){bool good=true;for(auto z:ch)if(cf(z,p[i])){good=false;break;}if(!good)continue;ch.push_back(p[i]);if(self(self,i+1))return true;ch.pop_back();}return false;};return dfs(dfs,0);}
}
int main(int argc,char**argv)try{
 if(argc!=4){std::cerr<<"usage: search_net2_r6_c3_extensions BASELINE_IDS SHARD SHARD_COUNT\n";return 2;}unsigned shard=std::stoul(argv[2]),shards=std::stoul(argv[3]);if(!shards||shard>=shards)throw std::runtime_error("shard");auto base=load(argv[1]);
 std::vector<std::uint8_t>inbase(N);for(auto v:base)inbase[v]=1;std::vector<Rec>a(N);for(std::uint32_t i=0;i<base.size();++i)a[base[i]].x[0]=i+1;
 for(int d=0;d<D;++d){auto s=P7[d];std::uint64_t block=std::uint64_t(s)*7u;
#pragma omp parallel for schedule(static)
  for(std::int64_t gg=0;gg<(std::int64_t)GROUPS;++gg){std::uint64_t g=gg,bn=g/s;std::uint32_t off=g%s,b0=(std::uint32_t)(bn*block+off);Rec old[7],nw[7];for(int k=0;k<7;++k)old[k]=a[b0+k*s];for(int k=0;k<7;++k)nw[k]=un3(old[(k+6)%7],old[k],old[(k+1)%7]);for(int k=0;k<7;++k)a[b0+k*s]=nw[k];}}
 std::vector<CR>lo;lo.reserve(1200000);std::uint64_t c0=0;for(std::uint32_t v=0;v<N;++v){if(inbase[v])continue;auto n=rs(a[v]);if(n==0){++c0;continue;}if(n>3)continue;Key k{};for(unsigned j=0;j<n;++j)k.a[j]=a[v].x[j];lo.push_back({k,v});}if(c0)throw std::runtime_error("coverage0");a.clear();a.shrink_to_fit();inbase.clear();inbase.shrink_to_fit();
 auto less=[](const CR&x,const CR&y){if(x.k<y.k)return true;if(y.k<x.k)return false;return x.v<y.v;};std::sort(lo.begin(),lo.end(),less);std::unordered_map<Key,Range,KH>idx;idx.reserve(lo.size()*2);std::vector<G3>g3;g3.reserve(1000000);std::vector<E1>e1;std::vector<E2>e2;e1.reserve(3200000);e2.reserve(3000000);
 for(std::uint32_t i=0;i<lo.size();){std::uint32_t j=i+1;while(j<lo.size()&&lo[j].k==lo[i].k)++j;auto k=lo[i].k,n=ksize(k);idx.emplace(k,Range{i,j});if(n==1){for(std::uint32_t x=i;x<j;++x)for(std::uint32_t y=x+1;y<j;++y)if(!cf(lo[x].v,lo[y].v))throw std::runtime_error("one-owner alpha>1");}if(n==3)g3.push_back({k,{i,j}});if(n>=2)for(unsigned t=0;t<n;++t)e1.push_back({remove1(k,n,t),k.a[t]});if(n==3)for(unsigned s=0;s<3;++s)for(unsigned t=s+1;t<3;++t){auto x=k.a[s],y=k.a[t];if(x>y)std::swap(x,y);e2.push_back({remove2(k,3,s,t),x,y});}i=j;}
 auto e1less=[](const E1&a,const E1&b){if(a.core<b.core)return true;if(b.core<a.core)return false;return a.x<b.x;};auto e2less=[](const E2&a,const E2&b){if(a.core<b.core)return true;if(b.core<a.core)return false;if(a.x!=b.x)return a.x<b.x;return a.y<b.y;};std::sort(e1.begin(),e1.end(),e1less);e1.erase(std::unique(e1.begin(),e1.end(),[](const E1&a,const E1&b){return a.core==b.core&&a.x==b.x;}),e1.end());std::sort(e2.begin(),e2.end(),e2less);e2.erase(std::unique(e2.begin(),e2.end(),[](const E2&a,const E2&b){return a.core==b.core&&a.x==b.x&&a.y==b.y;}),e2.end());
 auto ext1=[&](const std::vector<std::uint32_t>&cur){std::vector<std::uint32_t>out;unsigned m=cur.size();for(unsigned mask=1;mask<(1u<<m);++mask){if(std::popcount(mask)>2)continue;auto core=subset(cur,mask);E1 p{core,0};auto it=std::lower_bound(e1.begin(),e1.end(),p,e1less);for(;it!=e1.end()&&it->core==core;++it)if(!std::binary_search(cur.begin(),cur.end(),it->x))out.push_back(it->x);}std::sort(out.begin(),out.end());out.erase(std::unique(out.begin(),out.end()),out.end());return out;};
 auto ext2=[&](const std::vector<std::uint32_t>&cur){std::vector<std::uint64_t>out;for(auto lab:cur){Key core{};core.a[0]=lab;E2 p{core,0,0};auto it=std::lower_bound(e2.begin(),e2.end(),p,e2less);for(;it!=e2.end()&&it->core==core;++it)if(!std::binary_search(cur.begin(),cur.end(),it->x)&&!std::binary_search(cur.begin(),cur.end(),it->y))out.push_back((std::uint64_t(it->x)<<32)|it->y);}std::sort(out.begin(),out.end());out.erase(std::unique(out.begin(),out.end()),out.end());return out;};
 std::unordered_set<U6,U6H>seen;seen.reserve(4000000);std::uint64_t anchors=0,e1a=0,e1b=0,e1c=0,e2a=0,e2b=0,generated=0,canonical=0,eligible=0,tested=0;std::uint32_t maxpool=0,maxe1=0,maxe2=0;bool found=false;std::array<std::uint32_t,6>wrem{};std::vector<std::uint32_t>wadd;
 auto testU=[&](const Key&A,std::uint32_t x,std::uint32_t y,std::uint32_t z){U6 U{{A.a[0],A.a[1],A.a[2],x,y,z}};std::sort(U.a.begin(),U.a.end());if(std::adjacent_find(U.a.begin(),U.a.end())!=U.a.end())return false;++generated;Key mina{};bool have=false;for(unsigned mask=0;mask<64;++mask){if(std::popcount(mask)!=3)continue;auto q=subset6(U,mask);if(idx.find(q)==idx.end())continue;if(!have||q<mina){mina=q;have=true;}}if(!have||!(mina==A))return false;++canonical;if(!seen.insert(U).second)return false;std::vector<std::uint32_t>pool;pool.reserve(48);for(unsigned mask=1;mask<64;++mask){if(std::popcount(mask)>3)continue;auto it=idx.find(subset6(U,mask));if(it==idx.end())continue;for(std::uint32_t t=it->second.lo;t<it->second.hi;++t)pool.push_back(lo[t].v);}std::sort(pool.begin(),pool.end());pool.erase(std::unique(pool.begin(),pool.end()),pool.end());maxpool=std::max(maxpool,(std::uint32_t)pool.size());if(pool.size()<8)return false;++eligible;std::vector<std::uint32_t>ch;++tested;if(!find8(pool,ch))return false;found=true;for(unsigned i=0;i<6;++i)wrem[i]=base[U.a[i]-1];wadd=ch;return true;};
 for(std::size_t ai=0;ai<g3.size()&&!found;++ai){if(ai%shards!=shard)continue;++anchors;auto A=g3[ai].k;std::vector<std::uint32_t>a3={A.a[0],A.a[1],A.a[2]};
  auto xs=ext1(a3);e1a+=xs.size();maxe1=std::max(maxe1,(std::uint32_t)xs.size());
  for(auto x:xs){if(found)break;auto a4=a3;a4.push_back(x);std::sort(a4.begin(),a4.end());auto ys=ext1(a4);e1b+=ys.size();maxe1=std::max(maxe1,(std::uint32_t)ys.size());for(auto y:ys){if(y==x)continue;auto a5=a4;a5.push_back(y);std::sort(a5.begin(),a5.end());if(std::adjacent_find(a5.begin(),a5.end())!=a5.end())continue;auto zs=ext1(a5);e1c+=zs.size();maxe1=std::max(maxe1,(std::uint32_t)zs.size());for(auto z:zs){if(z==x||z==y)continue;if(testU(A,x,y,z))break;}}if(found)break;auto yz=ext2(a4);e2b+=yz.size();maxe2=std::max(maxe2,(std::uint32_t)yz.size());for(auto e:yz){auto y=(std::uint32_t)(e>>32),z=(std::uint32_t)e;if(y==x||z==x)continue;if(testU(A,x,y,z))break;}}
  if(found)break;auto xy=ext2(a3);e2a+=xy.size();maxe2=std::max(maxe2,(std::uint32_t)xy.size());for(auto e:xy){auto x=(std::uint32_t)(e>>32),y=(std::uint32_t)e;auto a5=a3;a5.push_back(x);a5.push_back(y);std::sort(a5.begin(),a5.end());if(std::adjacent_find(a5.begin(),a5.end())!=a5.end())continue;auto zs=ext1(a5);e1c+=zs.size();maxe1=std::max(maxe1,(std::uint32_t)zs.size());for(auto z:zs){if(z==x||z==y)continue;if(testU(A,x,y,z))break;}if(found)break;}
 }
 if(found){std::cout<<"{\"kind\":\"replace6add8\",\"method\":\"exact-r6-c3-support-extensions\",\"baseline_size\":"<<base.size()<<",\"shard\":"<<shard<<",\"shards\":"<<shards<<",\"c3_groups\":"<<g3.size()<<",\"e1_records\":"<<e1.size()<<",\"e2_records\":"<<e2.size()<<",\"anchors\":"<<anchors<<",\"e1_a\":"<<e1a<<",\"e1_b\":"<<e1b<<",\"e1_c\":"<<e1c<<",\"e2_a\":"<<e2a<<",\"e2_b\":"<<e2b<<",\"generated\":"<<generated<<",\"canonical_owner6\":"<<canonical<<",\"unique_owner6\":"<<seen.size()<<",\"eligible\":"<<eligible<<",\"tested\":"<<tested<<",\"max_e1\":"<<maxe1<<",\"max_e2\":"<<maxe2<<",\"max_supported_pool\":"<<maxpool<<",\"remove\":[";for(unsigned i=0;i<6;++i)std::cout<<(i?",":"")<<wrem[i];std::cout<<"],\"add\":[";for(unsigned i=0;i<wadd.size();++i)std::cout<<(i?",":"")<<wadd[i];std::cout<<"]}\n";return 0;}
 std::cout<<"{\"kind\":\"none\",\"method\":\"exact-r6-c3-support-extensions\",\"baseline_size\":"<<base.size()<<",\"shard\":"<<shard<<",\"shards\":"<<shards<<",\"c3_groups\":"<<g3.size()<<",\"e1_records\":"<<e1.size()<<",\"e2_records\":"<<e2.size()<<",\"anchors\":"<<anchors<<",\"e1_a\":"<<e1a<<",\"e1_b\":"<<e1b<<",\"e1_c\":"<<e1c<<",\"e2_a\":"<<e2a<<",\"e2_b\":"<<e2b<<",\"generated\":"<<generated<<",\"canonical_owner6\":"<<canonical<<",\"unique_owner6\":"<<seen.size()<<",\"eligible\":"<<eligible<<",\"tested\":"<<tested<<",\"max_e1\":"<<maxe1<<",\"max_e2\":"<<maxe2<<",\"max_supported_pool\":"<<maxpool<<"}\n";return 0;
}catch(const std::exception&e){std::cerr<<"error: "<<e.what()<<"\n";return 1;}
