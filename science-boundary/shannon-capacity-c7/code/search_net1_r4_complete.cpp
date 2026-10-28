// Complete unrestricted net-+1 search through radius 4 around a maximal C7^10
// independent set, assuming nothing from external artifacts: lower radii are
// re-proved on the same baseline before radius 4 is searched.
//
// After r1/r2/r3 are negative, alpha(P(U)) <= |U| for every |U|<=3.
// Hence five additions on four owners cannot have a disconnected support
// hypergraph: partitions 3+1 and 2+2 support at most 4, and finer partitions
// are smaller.  Every r4 witness is connected.
//
// Complete owner-four generation:
//   A) an exact support-4 group gives U directly;
//   B) if a selected support-3 group A exists, connectivity supplies a real
//      support-2/3 crossing A that introduces the fourth owner.  We enumerate
//      exact support extensions core->x with core subset A;
//   C) if all selected supports have size <=2, their support-2 graph is
//      connected on four owners.  We enumerate every connected four-owner set
//      by growing two boundary edges from each exact support-2 edge.
// For every generated U, the complete exact P_{<=4}(U) is reconstructed and
// tested for five pairwise nonconfusable additions.
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
namespace{
constexpr int D=10;
constexpr std::uint32_t P7[D+1]={1u,7u,49u,343u,2401u,16807u,117649u,823543u,5764801u,40353607u,282475249u};
constexpr std::uint32_t N=P7[D],GROUPS=N/7u,OVER=0xffffffffu;
constexpr unsigned K=4;
struct Rec{std::uint32_t x[K];};
struct Key{std::array<std::uint32_t,K>a{};bool operator==(const Key&o)const{return a==o.a;}bool operator<(const Key&o)const{return a<o.a;}};
struct KH{std::size_t operator()(const Key&q)const noexcept{std::size_t h=0;for(auto x:q.a)h^=std::size_t(x)+0x9e3779b97f4a7c15ULL+(h<<6)+(h>>2);return h;}};
struct CR{Key k;std::uint32_t v;};struct Range{std::uint32_t lo,hi;};struct E1{Key core;std::uint32_t x;};
std::vector<std::uint32_t>load(const char*p){std::ifstream in(p);if(!in)throw std::runtime_error("ids");std::vector<std::uint32_t>a;std::uint64_t z;while(in>>z){if(z>=N)throw std::runtime_error("range");a.push_back((std::uint32_t)z);}std::sort(a.begin(),a.end());if(a.empty()||std::adjacent_find(a.begin(),a.end())!=a.end())throw std::runtime_error("baseline");return a;}
inline bool ov(const Rec&r){return r.x[0]==OVER;}inline unsigned rs(const Rec&r){if(ov(r))return K+1;unsigned n=0;while(n<K&&r.x[n])++n;return n;}
inline Rec un3(const Rec&a,const Rec&b,const Rec&c){if(ov(a)||ov(b)||ov(c)){Rec r{};r.x[0]=OVER;return r;}unsigned ia=0,ib=0,ic=0,m=0;std::uint32_t last=0;Rec o{};for(;;){auto va=ia<K?a.x[ia]:0u,vb=ib<K?b.x[ib]:0u,vc=ic<K?c.x[ic]:0u;std::uint32_t v=0;if(va)v=va;if(vb&&(!v||vb<v))v=vb;if(vc&&(!v||vc<v))v=vc;if(!v)break;if(va==v)++ia;if(vb==v)++ib;if(vc==v)++ic;if(v==last)continue;if(m==K){Rec r{};r.x[0]=OVER;return r;}o.x[m++]=v;last=v;}return o;}
bool cf(std::uint32_t a,std::uint32_t b){if(a==b)return true;for(int d=0;d<D;++d){int x=a%7u,y=b%7u;a/=7u;b/=7u;int z=(x-y+7)%7;if(z!=0&&z!=1&&z!=6)return false;}return true;}
unsigned ks(const Key&q){unsigned n=0;while(n<K&&q.a[n])++n;return n;}
Key rem1(const Key&q,unsigned n,unsigned t){Key r{};unsigned j=0;for(unsigned i=0;i<n;++i)if(i!=t)r.a[j++]=q.a[i];return r;}
Key key1(std::uint32_t a){return Key{{a,0,0,0}};}Key key2(std::uint32_t a,std::uint32_t b){if(a>b)std::swap(a,b);return Key{{a,b,0,0}};}Key key3(std::uint32_t a,std::uint32_t b,std::uint32_t c){std::array<std::uint32_t,3>x{a,b,c};std::sort(x.begin(),x.end());return Key{{x[0],x[1],x[2],0}};}Key key4(std::uint32_t a,std::uint32_t b,std::uint32_t c,std::uint32_t d){std::array<std::uint32_t,4>x{a,b,c,d};std::sort(x.begin(),x.end());return Key{x};}
Key subset(const Key&U,unsigned mask){Key q{};unsigned n=ks(U),j=0;for(unsigned i=0;i<n;++i)if(mask&(1u<<i))q.a[j++]=U.a[i];return q;}
bool findk(const std::vector<std::uint32_t>&p,unsigned k,std::vector<std::uint32_t>&out){if(p.size()<k)return false;std::vector<std::uint32_t>q=p;std::sort(q.begin(),q.end());q.erase(std::unique(q.begin(),q.end()),q.end());std::vector<std::uint32_t>ch;auto dfs=[&](auto&&self,std::size_t s)->bool{if(ch.size()==k){out=ch;return true;}if(ch.size()+q.size()-s<k)return false;for(std::size_t i=s;i<q.size();++i){bool ok=true;for(auto z:ch)if(cf(z,q[i])){ok=false;break;}if(!ok)continue;ch.push_back(q[i]);if(self(self,i+1))return true;ch.pop_back();}return false;};return dfs(dfs,0);}
}
int main(int argc,char**argv)try{
 if(argc!=2){std::cerr<<"usage: search_net1_r4_complete BASELINE_IDS\n";return 2;}auto base=load(argv[1]);
 std::vector<std::uint8_t>inbase(N);for(auto v:base)inbase[v]=1;std::vector<Rec>a(N);for(std::uint32_t i=0;i<base.size();++i)a[base[i]].x[0]=i+1;
 for(int d=0;d<D;++d){auto s=P7[d];std::uint64_t block=std::uint64_t(s)*7u;
#pragma omp parallel for schedule(static)
  for(std::int64_t gg=0;gg<(std::int64_t)GROUPS;++gg){std::uint64_t g=gg,bn=g/s;std::uint32_t off=g%s,b0=(std::uint32_t)(bn*block+off);Rec old[7],nw[7];for(int k=0;k<7;++k)old[k]=a[b0+k*s];for(int k=0;k<7;++k)nw[k]=un3(old[(k+6)%7],old[k],old[(k+1)%7]);for(int k=0;k<7;++k)a[b0+k*s]=nw[k];}}
 std::vector<std::uint32_t>freev;std::vector<CR>lo;freev.reserve(16);lo.reserve(3400000);for(std::uint32_t v=0;v<N;++v){if(inbase[v])continue;auto n=rs(a[v]);if(n==0)freev.push_back(v);else if(n<=4){Key k{};for(unsigned j=0;j<n;++j)k.a[j]=a[v].x[j];lo.push_back({k,v});}}a.clear();a.shrink_to_fit();inbase.clear();inbase.shrink_to_fit();
 if(!freev.empty()){std::cout<<"{\"kind\":\"add1\",\"method\":\"exact-unrestricted-net1-r4-complete\",\"baseline_size\":"<<base.size()<<",\"remove\":[],\"add\":["<<freev[0]<<"]}\n";return 0;}
 auto less=[](const CR&x,const CR&y){if(x.k<y.k)return true;if(y.k<x.k)return false;return x.v<y.v;};std::sort(lo.begin(),lo.end(),less);std::unordered_map<Key,Range,KH>idx;idx.reserve(lo.size()*2);std::vector<Key>g2,g3,g4;g2.reserve(200000);g3.reserve(1000000);g4.reserve(2200000);std::vector<E1>e1;e1.reserve(3300000);std::uint64_t c1=0,c2=0,c3=0,c4=0;
 for(std::uint32_t i=0;i<lo.size();){std::uint32_t j=i+1;while(j<lo.size()&&lo[j].k==lo[i].k)++j;auto k=lo[i].k,n=ks(k);idx.emplace(k,Range{i,j});if(n==1)c1+=j-i;else if(n==2){c2+=j-i;g2.push_back(k);}else if(n==3){c3+=j-i;g3.push_back(k);}else{c4+=j-i;g4.push_back(k);}if(n>=2&&n<=3)for(unsigned t=0;t<n;++t)e1.push_back({rem1(k,n,t),k.a[t]});i=j;}
 auto e1less=[](const E1&a,const E1&b){if(a.core<b.core)return true;if(b.core<a.core)return false;return a.x<b.x;};std::sort(e1.begin(),e1.end(),e1less);e1.erase(std::unique(e1.begin(),e1.end(),[](const E1&a,const E1&b){return a.core==b.core&&a.x==b.x;}),e1.end());
 auto pool=[&](const Key&U,unsigned maxs){std::vector<std::uint32_t>p;unsigned n=ks(U);for(unsigned mask=1;mask<(1u<<n);++mask){if(std::popcount(mask)>maxs)continue;auto it=idx.find(subset(U,mask));if(it!=idx.end())for(std::uint32_t z=it->second.lo;z<it->second.hi;++z)p.push_back(lo[z].v);}std::sort(p.begin(),p.end());p.erase(std::unique(p.begin(),p.end()),p.end());return p;};
 std::vector<std::uint32_t>chosen;auto emit=[&](const char*kind,const Key&U,const std::vector<std::uint32_t>&add){std::cout<<"{\"kind\":\""<<kind<<"\",\"method\":\"exact-unrestricted-net1-r4-complete\",\"baseline_size\":"<<base.size()<<",\"remove\":[";unsigned n=ks(U);for(unsigned i=0;i<n;++i)std::cout<<(i?",":"")<<base[U.a[i]-1];std::cout<<"],\"add\":[";for(unsigned i=0;i<add.size();++i)std::cout<<(i?",":"")<<add[i];std::cout<<"]}\n";};
 // Re-prove r1.
 for(std::uint32_t o=1;o<=base.size();++o){auto it=idx.find(key1(o));if(it==idx.end())continue;std::vector<std::uint32_t>p;for(std::uint32_t z=it->second.lo;z<it->second.hi;++z)p.push_back(lo[z].v);if(findk(p,2,chosen)){emit("replace1add2",key1(o),chosen);return 0;}}
 // Re-prove r2 on every exact support2 owner pair; without support2, two
 // singleton pools have alpha at most 2 after r1 negativity.
 for(auto U:g2)if(findk(pool(U,2),3,chosen)){emit("replace2add3",U,chosen);return 0;}
 // Re-prove complete r3: exact support3 plus wedges of exact support2 edges.
 std::vector<std::vector<std::uint32_t>>adj2(base.size());for(auto U:g2){auto a0=U.a[0]-1,b0=U.a[1]-1;adj2[a0].push_back(b0);adj2[b0].push_back(a0);}for(auto&v:adj2){std::sort(v.begin(),v.end());v.erase(std::unique(v.begin(),v.end()),v.end());}
 std::unordered_set<Key,KH>done3;done3.reserve(g3.size()*2+3000000);auto check3=[&](Key U){if(!done3.insert(U).second)return false;auto p=pool(U,3);return findk(p,4,chosen);};for(auto U:g3)if(check3(U)){emit("replace3add4",U,chosen);return 0;}for(std::uint32_t a0=0;a0<adj2.size();++a0){auto&v=adj2[a0];for(std::size_t i=0;i<v.size();++i)for(std::size_t j=i+1;j<v.size();++j){auto U=key3(a0+1,v[i]+1,v[j]+1);if(check3(U)){emit("replace3add4",U,chosen);return 0;}}}
 // r4 complete connected owner-set generation.
 std::unordered_set<Key,KH>done4;done4.reserve(g4.size()*2+5000000);std::uint64_t owner4_checked=0,eligible=0;std::uint32_t maxpool=0;auto check4=[&](Key U)->bool{if(!done4.insert(U).second)return false;auto p=pool(U,4);++owner4_checked;maxpool=std::max(maxpool,(std::uint32_t)p.size());if(p.size()<5)return false;++eligible;if(findk(p,5,chosen)){emit("replace4add5",U,chosen);return true;}return false;};
 // A: direct exact support4.
 for(auto U:g4)if(check4(U))return 0;
 // B: exact support3 anchor plus one REAL support2/3 extension.
 for(auto A:g3){std::vector<std::uint32_t>cur={A.a[0],A.a[1],A.a[2]};std::vector<std::uint32_t>xs;for(unsigned mask=1;mask<8;++mask){if(std::popcount(mask)>2)continue;Key core{};unsigned q=0;for(unsigned t=0;t<3;++t)if(mask&(1u<<t))core.a[q++]=cur[t];E1 probe{core,0};auto it=std::lower_bound(e1.begin(),e1.end(),probe,e1less);for(;it!=e1.end()&&it->core==core;++it)if(!std::binary_search(cur.begin(),cur.end(),it->x))xs.push_back(it->x);}std::sort(xs.begin(),xs.end());xs.erase(std::unique(xs.begin(),xs.end()),xs.end());for(auto x:xs)if(check4(key4(A.a[0],A.a[1],A.a[2],x)))return 0;}
 // C: support2-only connected graph on four owners. Starting from each exact
 // support2 edge, grow two boundary edges in the exact support2 graph.
 for(auto A:g2){std::vector<std::uint32_t>s={A.a[0]-1,A.a[1]-1};std::vector<std::uint32_t>f1;for(auto u:s)for(auto x:adj2[u])if(x!=s[0]&&x!=s[1])f1.push_back(x);std::sort(f1.begin(),f1.end());f1.erase(std::unique(f1.begin(),f1.end()),f1.end());for(auto x:f1){std::vector<std::uint32_t>s3={s[0],s[1],x};std::vector<std::uint32_t>f2;for(auto u:s3)for(auto y:adj2[u])if(std::find(s3.begin(),s3.end(),y)==s3.end())f2.push_back(y);std::sort(f2.begin(),f2.end());f2.erase(std::unique(f2.begin(),f2.end()),f2.end());for(auto y:f2)if(check4(key4(s[0]+1,s[1]+1,x+1,y+1)))return 0;}}
 std::cout<<"{\"kind\":\"none\",\"method\":\"exact-unrestricted-net1-r4-complete\",\"baseline_size\":"<<base.size()<<",\"coverage0\":0,\"coverage1\":"<<c1<<",\"coverage2\":"<<c2<<",\"coverage3\":"<<c3<<",\"coverage4\":"<<c4<<",\"support2_groups\":"<<g2.size()<<",\"support3_groups\":"<<g3.size()<<",\"support4_groups\":"<<g4.size()<<",\"owner4_checked\":"<<owner4_checked<<",\"eligible_owner4\":"<<eligible<<",\"max_supported_pool\":"<<maxpool<<"}\n";return 0;
}catch(const std::exception&e){std::cerr<<"error: "<<e.what()<<"\n";return 1;}
