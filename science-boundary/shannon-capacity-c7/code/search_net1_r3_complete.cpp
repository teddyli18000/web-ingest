// Complete unrestricted net-+1 search through radius 3 around a C7^10
// independent set.  A witness gives a score improvement by one.
//
// Exact support-list transform recovers every outside blocker support of size
// <=3.  The search first proves lower radii on the same baseline:
//   r0: any support-0 outside vertex is directly addable;
//   r1: an independent pair in one support-1 owner pool is remove1/add2;
//   r2: after r1 is negative, a remove2/add3 witness must contain a support-2
//       vertex, so its two-owner set occurs as an exact support-2 group;
//   r3: after r2 is negative, a remove3/add4 witness either contains an exact
//       support-3 vertex, or contains at least two distinct support-2 pairs.
//       With owner union <=3 those two pairs share an owner.  If there were at
//       most one support-2 pair, P(pair) contributes at most 2 independent
//       vertices and the third singleton pool at most 1, so four additions are
//       impossible.  Pure singleton supports give at most 3.
//
// Thus exact support-3 groups plus wedges of exact support-2 groups are a
// COMPLETE radius-3 owner-triple generator; the complete P(U) is reconstructed
// before testing an independent four-set.
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
constexpr unsigned K=3,BITS=18;
struct Rec{std::uint32_t x[K];};
struct Key{std::array<std::uint32_t,K>a{};bool operator==(const Key&o)const{return a==o.a;}bool operator<(const Key&o)const{return a<o.a;}};
struct KH{std::size_t operator()(const Key&q)const noexcept{std::size_t h=0;for(auto x:q.a)h^=std::size_t(x)+0x9e3779b97f4a7c15ULL+(h<<6)+(h>>2);return h;}};
struct CR{Key k;std::uint32_t v;};struct Range{std::uint32_t lo,hi;};
std::vector<std::uint32_t>load(const char*p){std::ifstream in(p);if(!in)throw std::runtime_error("ids");std::vector<std::uint32_t>a;std::uint64_t z;while(in>>z){if(z>=N)throw std::runtime_error("range");a.push_back((std::uint32_t)z);}std::sort(a.begin(),a.end());if(a.empty()||std::adjacent_find(a.begin(),a.end())!=a.end())throw std::runtime_error("baseline");return a;}
inline bool ov(const Rec&r){return r.x[0]==OVER;}inline unsigned rs(const Rec&r){if(ov(r))return K+1;unsigned n=0;while(n<K&&r.x[n])++n;return n;}
inline Rec un3(const Rec&a,const Rec&b,const Rec&c){if(ov(a)||ov(b)||ov(c)){Rec r{};r.x[0]=OVER;return r;}unsigned ia=0,ib=0,ic=0,m=0;std::uint32_t last=0;Rec o{};for(;;){auto va=ia<K?a.x[ia]:0u,vb=ib<K?b.x[ib]:0u,vc=ic<K?c.x[ic]:0u;std::uint32_t v=0;if(va)v=va;if(vb&&(!v||vb<v))v=vb;if(vc&&(!v||vc<v))v=vc;if(!v)break;if(va==v)++ia;if(vb==v)++ib;if(vc==v)++ic;if(v==last)continue;if(m==K){Rec r{};r.x[0]=OVER;return r;}o.x[m++]=v;last=v;}return o;}
bool cf(std::uint32_t a,std::uint32_t b){if(a==b)return true;for(int d=0;d<D;++d){int x=a%7u,y=b%7u;a/=7u;b/=7u;int z=(x-y+7)%7;if(z!=0&&z!=1&&z!=6)return false;}return true;}
bool findk(const std::vector<std::uint32_t>&p,unsigned k,std::vector<std::uint32_t>&out){if(p.size()<k)return false;std::vector<std::uint32_t>q=p;std::sort(q.begin(),q.end());q.erase(std::unique(q.begin(),q.end()),q.end());std::vector<std::uint32_t>ch;auto dfs=[&](auto&&self,std::size_t s)->bool{if(ch.size()==k){out=ch;return true;}if(ch.size()+q.size()-s<k)return false;for(std::size_t i=s;i<q.size();++i){bool ok=true;for(auto z:ch)if(cf(z,q[i])){ok=false;break;}if(!ok)continue;ch.push_back(q[i]);if(self(self,i+1))return true;ch.pop_back();}return false;};return dfs(dfs,0);}
Key single(std::uint32_t a){return Key{{a,0,0}};}Key pairk(std::uint32_t a,std::uint32_t b){if(a>b)std::swap(a,b);return Key{{a,b,0}};}Key triple(std::uint32_t a,std::uint32_t b,std::uint32_t c){std::array<std::uint32_t,3>x{a,b,c};std::sort(x.begin(),x.end());return Key{x};}
}
int main(int argc,char**argv)try{
 if(argc!=2){std::cerr<<"usage: search_net1_r3_complete BASELINE_IDS\n";return 2;}auto base=load(argv[1]);if(base.size()>((1u<<BITS)-1))throw std::runtime_error("too many owners");
 std::vector<std::uint8_t>inbase(N);for(auto v:base)inbase[v]=1;std::vector<Rec>a(N);for(std::uint32_t i=0;i<base.size();++i)a[base[i]].x[0]=i+1;
 for(int d=0;d<D;++d){auto s=P7[d];std::uint64_t block=std::uint64_t(s)*7u;
#pragma omp parallel for schedule(static)
  for(std::int64_t gg=0;gg<(std::int64_t)GROUPS;++gg){std::uint64_t g=gg,bn=g/s;std::uint32_t off=g%s,b0=(std::uint32_t)(bn*block+off);Rec old[7],nw[7];for(int k=0;k<7;++k)old[k]=a[b0+k*s];for(int k=0;k<7;++k)nw[k]=un3(old[(k+6)%7],old[k],old[(k+1)%7]);for(int k=0;k<7;++k)a[b0+k*s]=nw[k];}}
 std::vector<std::uint32_t>freev;std::vector<CR>lo;freev.reserve(16);lo.reserve(1200000);for(std::uint32_t v=0;v<N;++v){if(inbase[v])continue;auto n=rs(a[v]);if(n==0)freev.push_back(v);else if(n<=3){Key k{};for(unsigned j=0;j<n;++j)k.a[j]=a[v].x[j];lo.push_back({k,v});}}a.clear();a.shrink_to_fit();inbase.clear();inbase.shrink_to_fit();
 if(!freev.empty()){std::cout<<"{\"kind\":\"add1\",\"method\":\"exact-unrestricted-net1-r3-complete\",\"baseline_size\":"<<base.size()<<",\"remove\":[],\"add\":["<<freev[0]<<"]}\n";return 0;}
 auto less=[](const CR&x,const CR&y){if(x.k<y.k)return true;if(y.k<x.k)return false;return x.v<y.v;};std::sort(lo.begin(),lo.end(),less);std::unordered_map<Key,Range,KH>idx;idx.reserve(lo.size()*2);std::vector<Key>g2,g3;g2.reserve(200000);g3.reserve(1000000);std::vector<std::vector<std::uint32_t>>inc(base.size());std::uint64_t c1=0,c2=0,c3=0;
 for(std::uint32_t i=0;i<lo.size();){std::uint32_t j=i+1;while(j<lo.size()&&lo[j].k==lo[i].k)++j;auto k=lo[i].k;idx.emplace(k,Range{i,j});unsigned n=k.a[2]?3:(k.a[1]?2:1);if(n==1)c1+=j-i;else if(n==2){c2+=j-i;g2.push_back(k);inc[k.a[0]-1].push_back(k.a[1]-1);inc[k.a[1]-1].push_back(k.a[0]-1);}else{c3+=j-i;g3.push_back(k);}i=j;}
 std::vector<std::uint32_t>chosen;
 auto vals=[&](const Key&U,unsigned maxs){std::vector<std::uint32_t>p;unsigned n=U.a[2]?3:(U.a[1]?2:1);for(unsigned mask=1;mask<(1u<<n);++mask){if(std::popcount(mask)>maxs)continue;Key q{};unsigned z=0;for(unsigned t=0;t<n;++t)if(mask&(1u<<t))q.a[z++]=U.a[t];auto it=idx.find(q);if(it!=idx.end())for(std::uint32_t w=it->second.lo;w<it->second.hi;++w)p.push_back(lo[w].v);}return p;};
 auto emit=[&](const char*kind,const Key&U,const std::vector<std::uint32_t>&add){std::cout<<"{\"kind\":\""<<kind<<"\",\"method\":\"exact-unrestricted-net1-r3-complete\",\"baseline_size\":"<<base.size()<<",\"remove\":[";unsigned n=U.a[2]?3:(U.a[1]?2:1);for(unsigned i=0;i<n;++i)std::cout<<(i?",":"")<<base[U.a[i]-1];std::cout<<"],\"add\":[";for(unsigned i=0;i<add.size();++i)std::cout<<(i?",":"")<<add[i];std::cout<<"]}\n";};
 // r1 exact: every single-owner pool.
 for(std::uint32_t o=1;o<=base.size();++o){auto it=idx.find(single(o));if(it==idx.end())continue;std::vector<std::uint32_t>p;for(std::uint32_t w=it->second.lo;w<it->second.hi;++w)p.push_back(lo[w].v);if(findk(p,2,chosen)){emit("replace1add2",single(o),chosen);return 0;}}
 // r2 exact: after r1 negative, any independent triple on two owners must use
 // an exact support-2 candidate, so its owner pair is in g2.
 std::uint64_t pairs_checked=0;for(auto U:g2){auto p=vals(U,2);++pairs_checked;if(findk(p,3,chosen)){emit("replace2add3",U,chosen);return 0;}}
 for(auto&v:inc){std::sort(v.begin(),v.end());v.erase(std::unique(v.begin(),v.end()),v.end());}
 // r3 complete owner triples: exact support3 or wedge of two exact support2s.
 std::unordered_set<Key,KH>done;done.reserve(g3.size()*2+3000000);std::uint64_t triples_checked=0,eligible=0;std::uint32_t maxpool=0;
 auto check3=[&](Key U)->bool{if(!done.insert(U).second)return false;auto p=vals(U,3);++triples_checked;maxpool=std::max(maxpool,(std::uint32_t)p.size());if(p.size()<4)return false;++eligible;if(findk(p,4,chosen)){emit("replace3add4",U,chosen);return true;}return false;};
 for(auto U:g3)if(check3(U))return 0;
 for(std::uint32_t a0=0;a0<inc.size();++a0){auto&v=inc[a0];for(std::size_t i=0;i<v.size();++i)for(std::size_t j=i+1;j<v.size();++j){if(v[i]==v[j])continue;if(check3(triple(a0+1,v[i]+1,v[j]+1)))return 0;}}
 std::cout<<"{\"kind\":\"none\",\"method\":\"exact-unrestricted-net1-r3-complete\",\"baseline_size\":"<<base.size()<<",\"coverage0\":0,\"coverage1\":"<<c1<<",\"coverage2\":"<<c2<<",\"coverage3\":"<<c3<<",\"support2_groups\":"<<g2.size()<<",\"support3_groups\":"<<g3.size()<<",\"pairs_checked\":"<<pairs_checked<<",\"triples_checked\":"<<triples_checked<<",\"eligible_triples\":"<<eligible<<",\"max_supported_pool\":"<<maxpool<<"}\n";return 0;
}catch(const std::exception&e){std::cerr<<"error: "<<e.what()<<"\n";return 1;}
