// Exact radius-6 stage for connected witnesses whose maximum selected blocker
// support is exactly 2.
//
// Earlier exact stages cover selected support sizes 6,5,4,3.  In this final
// stratum every selected support is a singleton or a pair.  Since all radius-6
// witness support hypergraphs are known to be connected, the selected size-2
// supports form a connected graph on the six owners and therefore contain a
// spanning tree.  Starting from any selected pair edge, the other four owners
// admit an ordering in which each new owner is adjacent by an OBSERVED exact
// c2 support to the current owner set.  Four boundary expansions are therefore
// a complete generator.
//
// Each owner-six set is assigned to its lexicographically smallest observed c2
// edge and to a deterministic greedy expansion order.  The complete P_{<=2}(U)
// (all six singleton groups and fifteen pair groups) is reconstructed and
// searched exactly for an independent eight-set.  A hit gives remove-6/add-8.
#include <algorithm>
#include <array>
#include <atomic>
#include <bit>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <unordered_map>
#include <vector>
#ifdef _OPENMP
#include <omp.h>
#endif
namespace{
constexpr int D=10;
constexpr std::uint32_t P7[D+1]={1u,7u,49u,343u,2401u,16807u,117649u,823543u,5764801u,40353607u,282475249u};
constexpr std::uint32_t N=P7[D],GROUPS=N/7u,OVER=0xffffffffu;
constexpr unsigned K=2;
struct Rec{std::uint32_t x[K];};
struct Key{std::array<std::uint32_t,K>a{};bool operator==(const Key&o)const{return a==o.a;}bool operator<(const Key&o)const{return a<o.a;}};
struct KH{std::size_t operator()(const Key&q)const noexcept{std::size_t h=0;for(auto x:q.a)h^=std::size_t(x)+0x9e3779b97f4a7c15ULL+(h<<6)+(h>>2);return h;}};
struct CR{Key k;std::uint32_t v;};struct Range{std::uint32_t lo,hi;};
struct U6{std::array<std::uint32_t,6>a{};};
std::vector<std::uint32_t>load(const char*p){std::ifstream in(p);if(!in)throw std::runtime_error("ids");std::vector<std::uint32_t>a;std::uint64_t z;while(in>>z){if(z>=N)throw std::runtime_error("range");a.push_back((std::uint32_t)z);}std::sort(a.begin(),a.end());if(a.size()!=134752||std::adjacent_find(a.begin(),a.end())!=a.end())throw std::runtime_error("baseline");return a;}
inline bool ov(const Rec&r){return r.x[0]==OVER;}inline unsigned rs(const Rec&r){if(ov(r))return K+1;unsigned n=0;while(n<K&&r.x[n])++n;return n;}
inline Rec un3(const Rec&a,const Rec&b,const Rec&c){if(ov(a)||ov(b)||ov(c)){Rec r{};r.x[0]=OVER;return r;}unsigned ia=0,ib=0,ic=0,m=0;std::uint32_t last=0;Rec o{};for(;;){auto va=ia<K?a.x[ia]:0u,vb=ib<K?b.x[ib]:0u,vc=ic<K?c.x[ic]:0u;std::uint32_t v=0;if(va)v=va;if(vb&&(!v||vb<v))v=vb;if(vc&&(!v||vc<v))v=vc;if(!v)break;if(va==v)++ia;if(vb==v)++ib;if(vc==v)++ic;if(v==last)continue;if(m==K){Rec r{};r.x[0]=OVER;return r;}o.x[m++]=v;last=v;}return o;}
bool cf(std::uint32_t a,std::uint32_t b){if(a==b)return true;for(int d=0;d<D;++d){int x=a%7u,y=b%7u;a/=7u;b/=7u;int z=(x-y+7)%7;if(z!=0&&z!=1&&z!=6)return false;}return true;}
bool rec8(const std::vector<std::uint32_t>&p,std::size_t s,std::vector<std::uint32_t>&ch){if(ch.size()==8)return true;if(ch.size()+p.size()-s<8)return false;for(std::size_t i=s;i<p.size();++i){bool ok=true;for(auto z:ch)if(cf(z,p[i])){ok=false;break;}if(!ok)continue;ch.push_back(p[i]);if(rec8(p,i+1,ch))return true;ch.pop_back();}return false;}
bool find8(std::vector<std::uint32_t>p,std::vector<std::uint32_t>&out){std::sort(p.begin(),p.end());p.erase(std::unique(p.begin(),p.end()),p.end());out.clear();return p.size()>=8&&rec8(p,0,out);}
Key pairkey(std::uint32_t a,std::uint32_t b){if(a>b)std::swap(a,b);return Key{{a,b}};}
Key singlekey(std::uint32_t a){return Key{{a,0}};}
}
int main(int argc,char**argv)try{
 if(argc!=4){std::cerr<<"usage: search_net2_r6_c2_graph BASELINE_IDS SHARD SHARD_COUNT\n";return 2;}unsigned shard=std::stoul(argv[2]),shards=std::stoul(argv[3]);if(!shards||shard>=shards)throw std::runtime_error("shard");auto base=load(argv[1]);
 std::vector<std::uint8_t>inbase(N);for(auto v:base)inbase[v]=1;std::vector<Rec>a(N);for(std::uint32_t i=0;i<base.size();++i)a[base[i]].x[0]=i+1;
 for(int d=0;d<D;++d){auto s=P7[d];std::uint64_t block=std::uint64_t(s)*7u;
#pragma omp parallel for schedule(static)
  for(std::int64_t gg=0;gg<(std::int64_t)GROUPS;++gg){std::uint64_t g=gg,bn=g/s;std::uint32_t off=g%s,b0=(std::uint32_t)(bn*block+off);Rec old[7],nw[7];for(int k=0;k<7;++k)old[k]=a[b0+k*s];for(int k=0;k<7;++k)nw[k]=un3(old[(k+6)%7],old[k],old[(k+1)%7]);for(int k=0;k<7;++k)a[b0+k*s]=nw[k];}
 }
 std::vector<CR>lo;lo.reserve(170000);std::uint64_t c0=0;for(std::uint32_t v=0;v<N;++v){if(inbase[v])continue;auto n=rs(a[v]);if(n==0){++c0;continue;}if(n>2)continue;Key k{};for(unsigned j=0;j<n;++j)k.a[j]=a[v].x[j];lo.push_back({k,v});}if(c0)throw std::runtime_error("coverage0");a.clear();a.shrink_to_fit();inbase.clear();inbase.shrink_to_fit();
 auto less=[](const CR&x,const CR&y){if(x.k<y.k)return true;if(y.k<x.k)return false;return x.v<y.v;};std::sort(lo.begin(),lo.end(),less);
 std::unordered_map<Key,Range,KH>idx;idx.reserve(170000);std::vector<Key>edges;edges.reserve(150000);
 for(std::uint32_t i=0;i<lo.size();){std::uint32_t j=i+1;while(j<lo.size()&&lo[j].k==lo[i].k)++j;auto k=lo[i].k;idx.emplace(k,Range{i,j});if(!k.a[1]){for(std::uint32_t x=i;x<j;++x)for(std::uint32_t y=x+1;y<j;++y)if(!cf(lo[x].v,lo[y].v))throw std::runtime_error("one-owner alpha>1");}else edges.push_back(k);i=j;}
 std::vector<std::uint32_t>deg(base.size());for(auto e:edges){++deg[e.a[0]-1];++deg[e.a[1]-1];}std::vector<std::uint64_t>off(base.size()+1);for(std::size_t i=0;i<base.size();++i)off[i+1]=off[i]+deg[i];std::vector<std::uint32_t>adj(off.back()),cur(base.size());for(std::size_t i=0;i<base.size();++i)cur[i]=off[i];for(auto e:edges){auto u=e.a[0]-1,v=e.a[1]-1;adj[cur[u]++]=v;adj[cur[v]++]=u;}deg.clear();deg.shrink_to_fit();cur.clear();cur.shrink_to_fit();
 auto linked=[&](const std::vector<std::uint32_t>&owners,std::uint32_t lab){auto v=lab-1;for(auto qlab:owners){auto u=qlab-1;for(std::uint64_t t=off[u];t<off[u+1];++t)if(adj[t]==v)return true;}return false;};
 auto neigh=[&](const std::vector<std::uint32_t>&owners){std::vector<std::uint32_t>z;for(auto lab:owners){auto u=lab-1;for(std::uint64_t q=off[u];q<off[u+1];++q){auto x=adj[q]+1;if(std::find(owners.begin(),owners.end(),x)==owners.end())z.push_back(x);}}std::sort(z.begin(),z.end());z.erase(std::unique(z.begin(),z.end()),z.end());return z;};
 auto canonical_order=[&](const Key&A,const U6&U,std::array<std::uint32_t,4>&ord){std::vector<std::uint32_t>cv={A.a[0],A.a[1]},out;for(auto x:U.a)if(x!=A.a[0]&&x!=A.a[1])out.push_back(x);if(out.size()!=4)return false;for(unsigned s=0;s<4;++s){std::uint32_t best=0;for(auto x:out)if(x&&linked(cv,x)&&(!best||x<best))best=x;if(!best)return false;ord[s]=best;cv.push_back(best);std::sort(cv.begin(),cv.end());for(auto&x:out)if(x==best){x=0;break;}}return true;};
 std::atomic<bool>found(false);std::array<std::uint32_t,6>wrem{};std::vector<std::uint32_t>wadd;std::atomic<std::uint64_t>anchors(0),l1(0),l2(0),l3(0),generated(0),canonical(0),eligible(0),tested(0);std::atomic<std::uint32_t>maxpool(0),maxdeg(0);
#pragma omp parallel for schedule(dynamic,16)
 for(std::int64_t ai=0;ai<(std::int64_t)edges.size();++ai){if((unsigned(ai)%shards)!=shard||found.load(std::memory_order_relaxed))continue;++anchors;auto A=edges[ai];std::vector<std::uint32_t>c2={A.a[0],A.a[1]};auto xs=neigh(c2);for(auto x:xs){if(found.load(std::memory_order_relaxed))break;++l1;auto c3=c2;c3.push_back(x);std::sort(c3.begin(),c3.end());auto ys=neigh(c3);for(auto y:ys){if(y==x)continue;++l2;auto c4=c3;c4.push_back(y);std::sort(c4.begin(),c4.end());if(std::adjacent_find(c4.begin(),c4.end())!=c4.end())continue;auto zs=neigh(c4);for(auto z:zs){if(z==x||z==y)continue;++l3;auto c5=c4;c5.push_back(z);std::sort(c5.begin(),c5.end());if(std::adjacent_find(c5.begin(),c5.end())!=c5.end())continue;auto ws=neigh(c5);for(auto w:ws){if(found.load(std::memory_order_relaxed))break;if(w==x||w==y||w==z)continue;++generated;U6 U{{A.a[0],A.a[1],x,y,z,w}};std::sort(U.a.begin(),U.a.end());if(std::adjacent_find(U.a.begin(),U.a.end())!=U.a.end())continue;
      Key minedge{};bool have=false;for(unsigned i=0;i<6;++i)for(unsigned j=i+1;j<6;++j){auto e=pairkey(U.a[i],U.a[j]);if(idx.find(e)==idx.end())continue;if(!have||e<minedge){minedge=e;have=true;}}if(!have||!(minedge==A))continue;std::array<std::uint32_t,4>ord{};if(!canonical_order(A,U,ord)||ord[0]!=x||ord[1]!=y||ord[2]!=z||ord[3]!=w)continue;++canonical;
      std::vector<std::uint32_t>pool;pool.reserve(32);for(unsigned i=0;i<6;++i){auto it=idx.find(singlekey(U.a[i]));if(it!=idx.end())for(std::uint32_t q=it->second.lo;q<it->second.hi;++q)pool.push_back(lo[q].v);}for(unsigned i=0;i<6;++i)for(unsigned j=i+1;j<6;++j){auto it=idx.find(pairkey(U.a[i],U.a[j]));if(it!=idx.end())for(std::uint32_t q=it->second.lo;q<it->second.hi;++q)pool.push_back(lo[q].v);}auto ps=(std::uint32_t)pool.size(),old=maxpool.load();while(ps>old&&!maxpool.compare_exchange_weak(old,ps)){}if(ps<8)continue;++eligible;std::vector<std::uint32_t>ch;++tested;if(find8(pool,ch)){bool ex=false;if(found.compare_exchange_strong(ex,true)){
#pragma omp critical
        {for(unsigned h=0;h<6;++h)wrem[h]=base[U.a[h]-1];wadd=ch;}
       }}
     }
    }
   }
  }
 }
 if(found.load()){std::cout<<"{\"kind\":\"replace6add8\",\"method\":\"exact-r6-c2-graph\",\"baseline_size\":"<<base.size()<<",\"shard\":"<<shard<<",\"shards\":"<<shards<<",\"c2_groups\":"<<edges.size()<<",\"anchors\":"<<anchors.load()<<",\"level1\":"<<l1.load()<<",\"level2\":"<<l2.load()<<",\"level3\":"<<l3.load()<<",\"generated\":"<<generated.load()<<",\"canonical_owner6\":"<<canonical.load()<<",\"eligible\":"<<eligible.load()<<",\"tested\":"<<tested.load()<<",\"max_supported_pool\":"<<maxpool.load()<<",\"remove\":[";for(unsigned i=0;i<6;++i)std::cout<<(i?",":"")<<wrem[i];std::cout<<"],\"add\":[";for(unsigned i=0;i<wadd.size();++i)std::cout<<(i?",":"")<<wadd[i];std::cout<<"]}\n";return 0;}
 std::cout<<"{\"kind\":\"none\",\"method\":\"exact-r6-c2-graph\",\"baseline_size\":"<<base.size()<<",\"shard\":"<<shard<<",\"shards\":"<<shards<<",\"c2_groups\":"<<edges.size()<<",\"anchors\":"<<anchors.load()<<",\"level1\":"<<l1.load()<<",\"level2\":"<<l2.load()<<",\"level3\":"<<l3.load()<<",\"generated\":"<<generated.load()<<",\"canonical_owner6\":"<<canonical.load()<<",\"eligible\":"<<eligible.load()<<",\"tested\":"<<tested.load()<<",\"max_supported_pool\":"<<maxpool.load()<<"}\n";return 0;
}catch(const std::exception&e){std::cerr<<"error: "<<e.what()<<"\n";return 1;}
