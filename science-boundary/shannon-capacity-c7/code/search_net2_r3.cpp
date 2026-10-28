// Exact unrestricted net-+2 search around a C7^10 independent set with coverage0=0.
//
// Finds, if present, a replacement of at most 3 old vertices by 5 arbitrary
// C7^10 vertices.  The search is complete for the stated baseline, not tied to
// the BPZ product template.  It first re-proves the radius-1 and radius-2
// negatives internally.  This lets the radius-3 enumeration use a complete
// support decomposition without the historical "only triples that occur as a
// coverage-3 vertex" gap:
//   * a selected coverage-3 vertex determines its owner triple;
//   * two distinct selected coverage-2 supports must share an owner and
//     determine their three-owner union;
//   * with exactly one coverage-2 support, radius-2 negativity forces the
//     third owner to contribute >=2 mutually compatible coverage-1 vertices;
//   * with coverage-1 vertices only, radius-1 negativity forces at least two
//     of the three owners to contribute >=2 mutually compatible vertices.
#include <algorithm>
#include <array>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>
#ifdef _OPENMP
#include <omp.h>
#endif
namespace {
constexpr int D=10;
constexpr std::uint32_t P7[D+1]={1u,7u,49u,343u,2401u,16807u,117649u,823543u,5764801u,40353607u,282475249u};
constexpr std::uint32_t N=P7[D], GROUPS=N/7u, INF=0xffffffffu;
constexpr unsigned BITS=18;
enum class Op{Sum,Xor,Min,Max};

template<class T,Op op>void transform(std::vector<T>&a,std::vector<T>&b,const char*name){
 for(int dim=0;dim<D;++dim){const auto s=P7[dim];const std::uint64_t block=std::uint64_t(s)*7u;
  #pragma omp parallel for schedule(static)
  for(std::int64_t gg=0;gg<(std::int64_t)GROUPS;++gg){const std::uint64_t g=gg,bn=g/s;const std::uint32_t off=g%s;const std::uint64_t base=bn*block+off;T v[7];for(int k=0;k<7;++k)v[k]=a[base+std::uint64_t(k)*s];for(int k=0;k<7;++k){T l=v[(k+6)%7],m=v[k],r=v[(k+1)%7],z{};if constexpr(op==Op::Sum)z=T(l+m+r);else if constexpr(op==Op::Xor)z=T(l^m^r);else if constexpr(op==Op::Min)z=std::min(l,std::min(m,r));else z=std::max(l,std::max(m,r));b[base+std::uint64_t(k)*s]=z;}}
  a.swap(b);std::cerr<<name<<" dim="<<dim<<"\n";
 }
}
std::vector<std::uint32_t>load_ids(const std::string&p){std::ifstream in(p);if(!in)throw std::runtime_error("cannot open ids");std::vector<std::uint32_t>a;std::uint64_t x;while(in>>x){if(x>=N)throw std::runtime_error("id range");a.push_back((std::uint32_t)x);}if(a.empty())throw std::runtime_error("empty baseline");std::sort(a.begin(),a.end());if(std::adjacent_find(a.begin(),a.end())!=a.end())throw std::runtime_error("duplicate baseline");return a;}
bool conflict(std::uint32_t a,std::uint32_t b){if(a==b)return true;for(int d=0;d<D;++d){int x=a%7u,y=b%7u;a/=7u;b/=7u;int z=(x-y+7)%7;if(z!=0&&z!=1&&z!=6)return false;}return true;}
std::uint64_t key2(std::uint32_t a,std::uint32_t b){if(a>b)std::swap(a,b);return(std::uint64_t(a)<<BITS)|b;}
std::pair<std::uint32_t,std::uint32_t>unkey2(std::uint64_t k){return{std::uint32_t(k>>BITS),std::uint32_t(k&((1u<<BITS)-1))};}
std::uint64_t key3(std::uint32_t a,std::uint32_t b,std::uint32_t c){std::array<std::uint32_t,3>x{a,b,c};std::sort(x.begin(),x.end());return(std::uint64_t(x[0])<<(2*BITS))|(std::uint64_t(x[1])<<BITS)|x[2];}
std::array<std::uint32_t,3>unkey3(std::uint64_t k){const std::uint64_t mask=(1ull<<BITS)-1;return{std::uint32_t(k>>(2*BITS)),std::uint32_t((k>>BITS)&mask),std::uint32_t(k&mask)};}

bool find_k_rec(const std::vector<std::uint32_t>&p,std::size_t start,unsigned k,std::vector<std::uint32_t>&chosen){
 if(chosen.size()==k)return true;
 if(chosen.size()+(p.size()-start)<k)return false;
 for(std::size_t i=start;i<p.size();++i){bool ok=true;for(auto z:chosen)if(conflict(z,p[i])){ok=false;break;}if(!ok)continue;chosen.push_back(p[i]);if(find_k_rec(p,i+1,k,chosen))return true;chosen.pop_back();}
 return false;
}
bool find_k(std::vector<std::uint32_t> p,unsigned k,std::vector<std::uint32_t>&out){std::sort(p.begin(),p.end());p.erase(std::unique(p.begin(),p.end()),p.end());out.clear();return find_k_rec(p,0,k,out);}
bool has_ind2(const std::vector<std::uint32_t>&p){for(std::size_t i=0;i<p.size();++i)for(std::size_t j=i+1;j<p.size();++j)if(!conflict(p[i],p[j]))return true;return false;}
}

int main(int argc,char**argv){try{
 if(argc!=2){std::cerr<<"usage: search_net2_r3 BASELINE_IDS\n";return 2;}auto base=load_ids(argv[1]);if(base.size()>((1u<<BITS)-1))throw std::runtime_error("baseline owner id exceeds packing");std::unordered_set<std::uint32_t>bset(base.begin(),base.end());
 // Exact coverage count over all 7^10 vertices.
 std::vector<std::uint16_t>cnt(N,0),t16(N,0);for(auto v:base)cnt[v]=1;transform<std::uint16_t,Op::Sum>(cnt,t16,"count");t16.clear();t16.shrink_to_fit();
 std::vector<std::uint32_t>freev,c1,c2,c3;freev.reserve(128);c1.reserve(10000);c2.reserve(200000);c3.reserve(1200000);
 for(std::uint32_t v=0;v<N;++v){if(cnt[v]==0)freev.push_back(v);else if(cnt[v]==1&&!bset.count(v))c1.push_back(v);else if(cnt[v]==2)c2.push_back(v);else if(cnt[v]==3)c3.push_back(v);}
 // This solver's exact decomposition assumes maximality; fail loudly otherwise.
 if(!freev.empty())throw std::runtime_error("search_net2_r3 requires coverage0=0; run add2/r1 general solver first");
 cnt.clear();cnt.shrink_to_fit();
 // XOR owner labels: unique owner for c1, and one ingredient for c3 recovery.
 std::vector<std::uint32_t>xo(N,0),tx(N,0);for(std::uint32_t i=0;i<base.size();++i)xo[base[i]]=i+1;transform<std::uint32_t,Op::Xor>(xo,tx,"xor");tx.clear();tx.shrink_to_fit();
 std::vector<std::vector<std::uint32_t>>g1(base.size());for(auto v:c1){auto o=xo[v];if(!o||o>base.size())throw std::runtime_error("bad c1 owner");g1[o-1].push_back(v);}std::vector<std::uint32_t>x3;x3.reserve(c3.size());for(auto v:c3)x3.push_back(xo[v]);xo.clear();xo.shrink_to_fit();
 // Min owner labels for c2/c3.
 std::vector<std::uint32_t>mn(N,INF),tm(N,INF);for(std::uint32_t i=0;i<base.size();++i)mn[base[i]]=i+1;transform<std::uint32_t,Op::Min>(mn,tm,"min");tm.clear();tm.shrink_to_fit();std::vector<std::uint32_t>lo2,lo3;lo2.reserve(c2.size());lo3.reserve(c3.size());for(auto v:c2)lo2.push_back(mn[v]);for(auto v:c3)lo3.push_back(mn[v]);mn.clear();mn.shrink_to_fit();
 // Max labels complete exact c2/c3 support recovery.
 std::vector<std::uint32_t>mx(N,0),tmax(N,0);for(std::uint32_t i=0;i<base.size();++i)mx[base[i]]=i+1;transform<std::uint32_t,Op::Max>(mx,tmax,"max");tmax.clear();tmax.shrink_to_fit();
 std::unordered_map<std::uint64_t,std::vector<std::uint32_t>>g2,g3;g2.reserve(180000);g3.reserve(1100000);
 for(std::size_t i=0;i<c2.size();++i){auto a=lo2[i],b=mx[c2[i]];if(!a||a==INF||!b||a>=b||b>base.size())throw std::runtime_error("bad c2 owners");g2[key2(a-1,b-1)].push_back(c2[i]);}
 for(std::size_t i=0;i<c3.size();++i){auto lo=lo3[i],hi=mx[c3[i]],xx=x3[i];if(!lo||lo==INF||!hi||hi>base.size())throw std::runtime_error("bad c3 extrema");auto mid=xx^lo^hi;if(!(lo<mid&&mid<hi&&mid<=base.size()))throw std::runtime_error("bad c3 middle owner");g3[key3(lo-1,mid-1,hi-1)].push_back(c3[i]);}
 mx.clear();mx.shrink_to_fit();lo2.clear();lo2.shrink_to_fit();lo3.clear();lo3.shrink_to_fit();x3.clear();x3.shrink_to_fit();c1.clear();c1.shrink_to_fit();c2.clear();c2.shrink_to_fit();c3.clear();c3.shrink_to_fit();

 std::vector<std::uint32_t>chosen;
 auto emit=[&](const char*kind,const std::vector<std::uint32_t>&owners,const std::vector<std::uint32_t>&add){std::cout<<"{\"kind\":\""<<kind<<"\",\"method\":\"exact-unrestricted-r3-net2\",\"baseline_size\":"<<base.size()<<",\"coverage0\":0,\"remove\":[";for(std::size_t i=0;i<owners.size();++i)std::cout<<(i?",":"")<<base[owners[i]];std::cout<<"],\"add\":[";for(std::size_t i=0;i<add.size();++i)std::cout<<(i?",":"")<<add[i];std::cout<<"]}\n";};
 // Re-prove radius 1 exactly. Any independent 3-set in one g1 group is a net+2 witness.
 std::vector<std::uint32_t>active,heavy;for(std::uint32_t a=0;a<g1.size();++a)if(!g1[a].empty()){active.push_back(a);if(find_k(g1[a],3,chosen)){emit("replace1add3",{a},chosen);return 0;}if(has_ind2(g1[a]))heavy.push_back(a);}
 // Re-prove radius 2 exactly and build g2 incidence.  Pairs without c2 are relevant only when their g1 union has at least four vertices.
 std::unordered_set<std::uint64_t>done2;done2.reserve(g2.size()*2+1024);std::vector<std::vector<std::uint32_t>>inc(base.size());
 auto pool2=[&](std::uint32_t a,std::uint32_t b){std::vector<std::uint32_t>p;p.reserve(g1[a].size()+g1[b].size()+8);p.insert(p.end(),g1[a].begin(),g1[a].end());p.insert(p.end(),g1[b].begin(),g1[b].end());auto it=g2.find(key2(a,b));if(it!=g2.end())p.insert(p.end(),it->second.begin(),it->second.end());return p;};
 for(const auto&kv:g2){auto [a,b]=unkey2(kv.first);inc[a].push_back(b);inc[b].push_back(a);done2.insert(kv.first);auto p=pool2(a,b);if(find_k(p,4,chosen)){emit("replace2add4",{a,b},chosen);return 0;}}
 for(std::size_t i=0;i<active.size();++i)for(std::size_t j=i+1;j<active.size();++j){auto a=active[i],b=active[j];if(g1[a].size()+g1[b].size()<4)continue;auto k=key2(a,b);if(!done2.insert(k).second)continue;auto p=pool2(a,b);if(find_k(p,4,chosen)){emit("replace2add4",{a,b},chosen);return 0;}}
 for(auto&v:inc){std::sort(v.begin(),v.end());v.erase(std::unique(v.begin(),v.end()),v.end());}

 std::unordered_set<std::uint64_t>done3;done3.reserve(g3.size()*2+4000000);std::uint64_t triples_checked=0,eligible=0;std::size_t maxpool=0;
 auto pool3=[&](std::uint32_t a,std::uint32_t b,std::uint32_t c){std::array<std::uint32_t,3>x{a,b,c};std::sort(x.begin(),x.end());std::vector<std::uint32_t>p;for(auto q:x)p.insert(p.end(),g1[q].begin(),g1[q].end());for(int i=0;i<3;++i)for(int j=i+1;j<3;++j){auto it=g2.find(key2(x[i],x[j]));if(it!=g2.end())p.insert(p.end(),it->second.begin(),it->second.end());}auto it3=g3.find(key3(x[0],x[1],x[2]));if(it3!=g3.end())p.insert(p.end(),it3->second.begin(),it3->second.end());std::sort(p.begin(),p.end());p.erase(std::unique(p.begin(),p.end()),p.end());return p;};
 auto check3=[&](std::uint32_t a,std::uint32_t b,std::uint32_t c)->bool{if(a==b||a==c||b==c)return false;auto k=key3(a,b,c);if(!done3.insert(k).second)return false;auto x=unkey3(k);auto p=pool3(x[0],x[1],x[2]);++triples_checked;maxpool=std::max(maxpool,p.size());if(p.size()<5)return false;++eligible;if(find_k(p,5,chosen)){emit("replace3add5",{x[0],x[1],x[2]},chosen);return true;}return false;};
 // Case A: at least one selected coverage-3 vertex.
 for(const auto&kv:g3){auto x=unkey3(kv.first);if(check3(x[0],x[1],x[2]))return 0;}
 // Case B: at least two distinct selected coverage-2 supports. Their pair keys must share an owner.
 for(std::uint32_t a=0;a<inc.size();++a){auto&v=inc[a];for(std::size_t i=0;i<v.size();++i)for(std::size_t j=i+1;j<v.size();++j)if(check3(a,v[i],v[j]))return 0;}
 // Case C: exactly one selected coverage-2 support. Since every two-owner pool has alpha<=3 above, the third owner must supply an independent pair from g1.
 for(const auto&kv:g2){auto [a,b]=unkey2(kv.first);for(auto c:heavy)if(c!=a&&c!=b)if(check3(a,b,c))return 0;}
 // Case D: selected candidates have coverage one only. Radius-1 negativity gives alpha(g1[a])<=2, so at least two owners must be heavy to reach five vertices.
 for(std::size_t i=0;i<heavy.size();++i)for(std::size_t j=i+1;j<heavy.size();++j){auto a=heavy[i],b=heavy[j];for(auto c:active)if(c!=a&&c!=b)if(check3(a,b,c))return 0;}
 std::cout<<"{\"kind\":\"none\",\"method\":\"exact-unrestricted-r3-net2\",\"baseline_size\":"<<base.size()<<",\"coverage0\":0,\"coverage1\":";std::uint64_t n1=0;for(auto&g:g1)n1+=g.size();std::uint64_t n2=0;for(auto&kv:g2)n2+=kv.second.size();std::uint64_t n3=0;for(auto&kv:g3)n3+=kv.second.size();std::cout<<n1<<",\"coverage2\":"<<n2<<",\"coverage3\":"<<n3<<",\"coverage2_groups\":"<<g2.size()<<",\"coverage3_groups\":"<<g3.size()<<",\"active_c1_owners\":"<<active.size()<<",\"heavy_c1_owners\":"<<heavy.size()<<",\"triples_checked\":"<<triples_checked<<",\"eligible_triples\":"<<eligible<<",\"max_supported_pool\":"<<maxpool<<"}\n";
 return 0;
}catch(const std::exception&e){std::cerr<<"error: "<<e.what()<<"\n";return 1;}}
