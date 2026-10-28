// Exact radius-6 stage for connected witnesses whose selected blocker supports
// all have size <=3 and at least one selected support has size exactly 3.
//
// Lower-radius exact results on the four FunSearch C5 representatives imply
// every radius-6 remove-6/add-8 witness has a connected support hypergraph.
// In this stratum choose any selected exact support-3 hyperedge A. The 2-section
// graph of the selected support hypergraph is connected, so starting from A one
// can add the remaining three owners one at a time along crossing edges. Every
// such edge occurs in an observed exact support-2/3 group. We therefore enumerate
// graph-connected six-owner sets from every observed support-3 anchor, assign
// each final U to its lexicographically smallest observed support-3 subset, then
// reconstruct the COMPLETE candidate pool with supports <=3 inside U and decide
// exactly whether it contains eight pairwise nonconfusable vertices.
//
// This stage is complementary to the r6 direct/c5/c4/support1-2 stages.
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
struct CR{Key k;std::uint32_t v;};struct Range{std::uint32_t lo,hi;};struct G3{Key k;Range r;};
std::vector<std::uint32_t>load(const char*p){std::ifstream in(p);if(!in)throw std::runtime_error("ids");std::vector<std::uint32_t>a;std::uint64_t z;while(in>>z){if(z>=N)throw std::runtime_error("range");a.push_back((std::uint32_t)z);}std::sort(a.begin(),a.end());if(a.size()!=134752||std::adjacent_find(a.begin(),a.end())!=a.end())throw std::runtime_error("baseline");return a;}
inline bool ov(const Rec&r){return r.x[0]==OVER;}inline unsigned rs(const Rec&r){if(ov(r))return K+1;unsigned n=0;while(n<K&&r.x[n])++n;return n;}
inline Rec un3(const Rec&a,const Rec&b,const Rec&c){if(ov(a)||ov(b)||ov(c)){Rec r{};r.x[0]=OVER;return r;}unsigned ia=0,ib=0,ic=0,m=0;std::uint32_t last=0;Rec o{};for(;;){auto va=ia<K?a.x[ia]:0u,vb=ib<K?b.x[ib]:0u,vc=ic<K?c.x[ic]:0u;std::uint32_t v=0;if(va)v=va;if(vb&&(!v||vb<v))v=vb;if(vc&&(!v||vc<v))v=vc;if(!v)break;if(va==v)++ia;if(vb==v)++ib;if(vc==v)++ic;if(v==last)continue;if(m==K){Rec r{};r.x[0]=OVER;return r;}o.x[m++]=v;last=v;}return o;}
bool conflict(std::uint32_t a,std::uint32_t b){if(a==b)return true;for(int d=0;d<D;++d){int x=a%7u,y=b%7u;a/=7u;b/=7u;int z=(x-y+7)%7;if(z!=0&&z!=1&&z!=6)return false;}return true;}
bool find8(const std::vector<std::uint32_t>&p,std::vector<std::uint32_t>&out){const unsigned n=p.size();if(n<8)return false;if(n<=63){std::vector<std::uint64_t>compat(n,0);for(unsigned i=0;i<n;++i)for(unsigned j=i+1;j<n;++j)if(!conflict(p[i],p[j]))compat[i]|=1ull<<j;std::array<unsigned,8>ch{};auto rec=[&](auto&&self,std::uint64_t mask,unsigned d)->bool{if(d==8){out.clear();for(unsigned t=0;t<8;++t)out.push_back(p[ch[t]]);return true;}if(std::popcount(mask)<8-d)return false;while(mask){unsigned v=std::countr_zero(mask);mask&=mask-1;ch[d]=v;if(self(self,mask&compat[v],d+1))return true;if(std::popcount(mask)<7-d)break;}return false;};return rec(rec,(1ull<<n)-1,0);}std::vector<std::uint32_t>ch;auto rec=[&](auto&&self,std::size_t s)->bool{if(ch.size()==8){out=ch;return true;}if(ch.size()+p.size()-s<8)return false;for(std::size_t i=s;i<p.size();++i){bool ok=true;for(auto z:ch)if(conflict(z,p[i])){ok=false;break;}if(!ok)continue;ch.push_back(p[i]);if(self(self,i+1))return true;ch.pop_back();}return false;};return rec(rec,0);}
Key sub3(const U6&u,unsigned i,unsigned j,unsigned k){Key q{};q.a={u.a[i],u.a[j],u.a[k]};return q;}
}
int main(int argc,char**argv)try{
 if(argc!=4){std::cerr<<"usage: search_net2_r6_c3_connected BASELINE_IDS SHARD SHARD_COUNT\n";return 2;}unsigned shard=std::stoul(argv[2]),shards=std::stoul(argv[3]);if(!shards||shard>=shards)throw std::runtime_error("shard");auto base=load(argv[1]);
 std::vector<std::uint8_t>inbase(N);for(auto v:base)inbase[v]=1;std::vector<Rec>a(N);for(std::uint32_t i=0;i<base.size();++i)a[base[i]].x[0]=i+1;
 for(int d=0;d<D;++d){auto s=P7[d];std::uint64_t block=std::uint64_t(s)*7u;
#pragma omp parallel for schedule(static)
  for(std::int64_t gg=0;gg<(std::int64_t)GROUPS;++gg){std::uint64_t g=gg,bn=g/s;std::uint32_t off=g%s,b0=(std::uint32_t)(bn*block+off);Rec old[7],nw[7];for(int k=0;k<7;++k)old[k]=a[b0+k*s];for(int k=0;k<7;++k)nw[k]=un3(old[(k+6)%7],old[k],old[(k+1)%7]);for(int k=0;k<7;++k)a[b0+k*s]=nw[k];}}
 std::vector<CR>lo;lo.reserve(1200000);std::uint64_t c0=0;for(std::uint32_t v=0;v<N;++v){if(inbase[v])continue;auto n=rs(a[v]);if(n==0){++c0;continue;}if(n>3)continue;Key k{};for(unsigned j=0;j<n;++j)k.a[j]=a[v].x[j];lo.push_back({k,v});}if(c0)throw std::runtime_error("coverage0");a.clear();a.shrink_to_fit();inbase.clear();inbase.shrink_to_fit();
 auto less=[](const CR&x,const CR&y){if(x.k<y.k)return true;if(y.k<x.k)return false;return x.v<y.v;};std::sort(lo.begin(),lo.end(),less);std::unordered_map<Key,Range,KH>idx;idx.reserve(lo.size()*2);std::vector<G3>g3;g3.reserve(1000000);std::vector<std::uint64_t>edges;edges.reserve(6000000);
 for(std::uint32_t i=0;i<lo.size();){std::uint32_t j=i+1;while(j<lo.size()&&lo[j].k==lo[i].k)++j;auto k=lo[i].k;idx.emplace(k,Range{i,j});unsigned n=k.a[2]?3:(k.a[1]?2:1);if(n==1){for(std::uint32_t x=i;x<j;++x)for(std::uint32_t y=x+1;y<j;++y)if(!conflict(lo[x].v,lo[y].v))throw std::runtime_error("one-owner alpha>1");}if(n==3)g3.push_back({k,{i,j}});if(n>=2)for(unsigned x=0;x<n;++x)for(unsigned y=x+1;y<n;++y){auto u=k.a[x]-1,v=k.a[y]-1;if(u>v)std::swap(u,v);edges.push_back((std::uint64_t(u)<<32)|v);}i=j;}
 std::sort(edges.begin(),edges.end());edges.erase(std::unique(edges.begin(),edges.end()),edges.end());std::vector<std::uint32_t>deg(base.size());for(auto e:edges){++deg[e>>32];++deg[(std::uint32_t)e];}std::vector<std::uint64_t>off(base.size()+1);for(std::size_t i=0;i<base.size();++i)off[i+1]=off[i]+deg[i];std::vector<std::uint32_t>adj(off.back()),cur(base.size());for(std::size_t i=0;i<base.size();++i)cur[i]=off[i];for(auto e:edges){auto u=(std::uint32_t)(e>>32),v=(std::uint32_t)e;adj[cur[u]++]=v;adj[cur[v]++]=u;}edges.clear();edges.shrink_to_fit();deg.clear();deg.shrink_to_fit();cur.clear();cur.shrink_to_fit();
 std::unordered_set<U6,U6H>seen;seen.reserve(2000000);std::uint64_t anchors=0,expansions=0,finals=0,canonical=0,eligible=0,tested=0;std::uint32_t maxpool=0,maxfrontier=0;bool found=false;std::array<std::uint32_t,6>wrem{};std::vector<std::uint32_t>wadd;
 auto pool_for=[&](const U6&U){std::vector<std::uint32_t>p;p.reserve(96);for(unsigned i=0;i<6;++i){Key q{};q.a[0]=U.a[i];auto it=idx.find(q);if(it!=idx.end())for(std::uint32_t z=it->second.lo;z<it->second.hi;++z)p.push_back(lo[z].v);}for(unsigned i=0;i<6;++i)for(unsigned j=i+1;j<6;++j){Key q{};q.a={U.a[i],U.a[j],0};auto it=idx.find(q);if(it!=idx.end())for(std::uint32_t z=it->second.lo;z<it->second.hi;++z)p.push_back(lo[z].v);}for(unsigned i=0;i<6;++i)for(unsigned j=i+1;j<6;++j)for(unsigned k=j+1;k<6;++k){auto q=sub3(U,i,j,k);auto it=idx.find(q);if(it!=idx.end())for(std::uint32_t z=it->second.lo;z<it->second.hi;++z)p.push_back(lo[z].v);}std::sort(p.begin(),p.end());p.erase(std::unique(p.begin(),p.end()),p.end());return p;};
 for(std::size_t ai=0;ai<g3.size()&&!found;++ai){if(ai%shards!=shard)continue;++anchors;Key anchor=g3[ai].k;std::vector<std::uint32_t>start={anchor.a[0],anchor.a[1],anchor.a[2]};
  std::unordered_set<std::uint64_t>seen4,seen5;seen4.reserve(256);seen5.reserve(4096);
  auto smallkey=[](const std::vector<std::uint32_t>&v){std::vector<std::uint32_t>x=v;std::sort(x.begin(),x.end());std::uint64_t h=1469598103934665603ULL;for(auto z:x){h^=z;h*=1099511628211ULL;}return h;};
  auto dfs=[&](auto&&self,std::vector<std::uint32_t>&curv)->void{if(found)return;if(curv.size()==6){++finals;U6 U{};for(unsigned i=0;i<6;++i)U.a[i]=curv[i];std::sort(U.a.begin(),U.a.end());Key mina{};bool have=false;for(unsigned i=0;i<6;++i)for(unsigned j=i+1;j<6;++j)for(unsigned k=j+1;k<6;++k){auto q=sub3(U,i,j,k);if(idx.find(q)==idx.end())continue;if(!have||q<mina){mina=q;have=true;}}if(!have||!(mina==anchor))return;++canonical;if(!seen.insert(U).second)return;auto p=pool_for(U);maxpool=std::max(maxpool,(std::uint32_t)p.size());if(p.size()<8)return;++eligible;std::vector<std::uint32_t>ch;++tested;if(find8(p,ch)){found=true;for(unsigned i=0;i<6;++i)wrem[i]=base[U.a[i]-1];wadd=ch;}return;}
   std::vector<std::uint32_t>front;for(auto lab:curv){auto u=lab-1;for(std::uint64_t q=off[u];q<off[u+1];++q){auto x=adj[q]+1;if(std::find(curv.begin(),curv.end(),x)==curv.end())front.push_back(x);}}std::sort(front.begin(),front.end());front.erase(std::unique(front.begin(),front.end()),front.end());maxfrontier=std::max(maxfrontier,(std::uint32_t)front.size());for(auto x:front){++expansions;curv.push_back(x);auto hk=smallkey(curv);bool fresh=curv.size()==4?seen4.insert(hk).second:seen5.insert(hk).second;if(fresh)self(self,curv);curv.pop_back();if(found)return;}
  };dfs(dfs,start);
 }
 if(found){std::cout<<"{\"kind\":\"replace6add8\",\"method\":\"exact-r6-support123-connected\",\"baseline_size\":"<<base.size()<<",\"shard\":"<<shard<<",\"shards\":"<<shards<<",\"coverage123_candidates\":"<<lo.size()<<",\"support3_groups\":"<<g3.size()<<",\"anchors\":"<<anchors<<",\"expansions\":"<<expansions<<",\"final_sequences\":"<<finals<<",\"canonical_sequences\":"<<canonical<<",\"unique_owner6\":"<<seen.size()<<",\"eligible\":"<<eligible<<",\"tested\":"<<tested<<",\"max_supported_pool\":"<<maxpool<<",\"max_frontier\":"<<maxfrontier<<",\"remove\":[";for(unsigned i=0;i<6;++i)std::cout<<(i?",":"")<<wrem[i];std::cout<<"],\"add\":[";for(unsigned i=0;i<wadd.size();++i)std::cout<<(i?",":"")<<wadd[i];std::cout<<"]}\n";return 0;}
 std::cout<<"{\"kind\":\"none\",\"method\":\"exact-r6-support123-connected\",\"baseline_size\":"<<base.size()<<",\"shard\":"<<shard<<",\"shards\":"<<shards<<",\"coverage123_candidates\":"<<lo.size()<<",\"support3_groups\":"<<g3.size()<<",\"anchors\":"<<anchors<<",\"expansions\":"<<expansions<<",\"final_sequences\":"<<finals<<",\"canonical_sequences\":"<<canonical<<",\"unique_owner6\":"<<seen.size()<<",\"eligible\":"<<eligible<<",\"tested\":"<<tested<<",\"max_supported_pool\":"<<maxpool<<",\"max_frontier\":"<<maxfrontier<<"}\n";return 0;
}catch(const std::exception&e){std::cerr<<"error: "<<e.what()<<"\n";return 1;}
