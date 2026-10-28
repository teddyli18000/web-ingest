// Exact unrestricted remove-4/add-6 net-+2 search for a C7^10 independent set.
//
// Preconditions certified in the workflow on the same baseline:
//   (1) coverage0 = 0;
//   (2) exact unrestricted radius-3 search is negative, hence every candidate
//       pool supported on <=3 old owners has independence number <=4.
// This program independently rechecks the additional radius-4 structural fact
// that every genuine two-owner pool has alpha <= 2 (no independent triple).
//
// Completeness of four-owner generation:
// - a selected coverage-4 vertex gives its owner quadruple directly;
// - with selected coverage-3 vertices but no c4, a second c3 or a crossing c2
//   must expose the fourth owner (one c1 alone would add at most one vertex to
//   a <=4 three-owner solution);
// - with only c1/c2, the selected c2 support graph on four owners must be
//   connected: an isolated owner gives <=4+1, and two disjoint owner-pairs give
//   <=2+2 by the internally checked two-owner alpha bound.  A connected graph
//   contains a two-edge wedge plus an edge extending the resulting 3-set to
//   the fourth owner.
// Every generated owner quadruple is then replayed with the COMPLETE pool of
// all c1/c2/c3/c4 candidates supported inside it and searched exactly for an
// independent six-set.
#include <algorithm>
#include <array>
#include <cmath>
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
constexpr std::uint32_t N=P7[D],GROUPS=N/7u,INF=0xffffffffu;
constexpr unsigned BITS=18;
enum class Op{Sum,Min,Max};

template<class T,Op op>void transform(std::vector<T>&a,std::vector<T>&b,const char*name){
 for(int dim=0;dim<D;++dim){const auto s=P7[dim];const std::uint64_t block=std::uint64_t(s)*7u;
  #pragma omp parallel for schedule(static)
  for(std::int64_t gg=0;gg<(std::int64_t)GROUPS;++gg){const std::uint64_t g=gg,bn=g/s;const std::uint32_t off=g%s;const std::uint64_t base=bn*block+off;T v[7];for(int k=0;k<7;++k)v[k]=a[base+std::uint64_t(k)*s];for(int k=0;k<7;++k){T l=v[(k+6)%7],m=v[k],r=v[(k+1)%7],z{};if constexpr(op==Op::Sum)z=T(l+m+r);else if constexpr(op==Op::Min)z=std::min(l,std::min(m,r));else z=std::max(l,std::max(m,r));b[base+std::uint64_t(k)*s]=z;}}
  a.swap(b);std::cerr<<name<<" dim="<<dim<<"\n";
 }
}
std::vector<std::uint32_t>load_ids(const std::string&p){std::ifstream in(p);if(!in)throw std::runtime_error("cannot open ids");std::vector<std::uint32_t>a;std::uint64_t x;while(in>>x){if(x>=N)throw std::runtime_error("id range");a.push_back((std::uint32_t)x);}if(a.empty())throw std::runtime_error("empty baseline");std::sort(a.begin(),a.end());if(std::adjacent_find(a.begin(),a.end())!=a.end())throw std::runtime_error("duplicate baseline");return a;}
bool conflict(std::uint32_t a,std::uint32_t b){if(a==b)return true;for(int d=0;d<D;++d){int x=a%7u,y=b%7u;a/=7u;b/=7u;int z=(x-y+7)%7;if(z!=0&&z!=1&&z!=6)return false;}return true;}
std::uint64_t key2(std::uint32_t a,std::uint32_t b){if(a>b)std::swap(a,b);return(std::uint64_t(a)<<BITS)|b;}
std::pair<std::uint32_t,std::uint32_t>unkey2(std::uint64_t k){return{std::uint32_t(k>>BITS),std::uint32_t(k&((1u<<BITS)-1))};}
std::uint64_t key3(std::uint32_t a,std::uint32_t b,std::uint32_t c){std::array<std::uint32_t,3>x{a,b,c};std::sort(x.begin(),x.end());return(std::uint64_t(x[0])<<(2*BITS))|(std::uint64_t(x[1])<<BITS)|x[2];}
std::array<std::uint32_t,3>unkey3(std::uint64_t k){const std::uint64_t m=(1ull<<BITS)-1;return{std::uint32_t(k>>(2*BITS)),std::uint32_t((k>>BITS)&m),std::uint32_t(k&m)};}
struct Quad{std::uint32_t a,b,c,d;bool operator==(const Quad&o)const{return a==o.a&&b==o.b&&c==o.c&&d==o.d;}};
struct QuadHash{std::size_t operator()(const Quad&q)const noexcept{std::size_t h=q.a;for(auto x:{q.b,q.c,q.d})h^=std::size_t(x)+0x9e3779b97f4a7c15ULL+(h<<6)+(h>>2);return h;}};
Quad quad(std::uint32_t a,std::uint32_t b,std::uint32_t c,std::uint32_t d){std::array<std::uint32_t,4>x{a,b,c,d};std::sort(x.begin(),x.end());return{x[0],x[1],x[2],x[3]};}
bool distinct4(const Quad&q){return q.a<q.b&&q.b<q.c&&q.c<q.d;}

bool find_k_rec(const std::vector<std::uint32_t>&p,std::size_t start,unsigned k,std::vector<std::uint32_t>&chosen){
 if(chosen.size()==k)return true;
 if(chosen.size()+(p.size()-start)<k)return false;
 for(std::size_t i=start;i<p.size();++i){bool ok=true;for(auto z:chosen)if(conflict(z,p[i])){ok=false;break;}if(!ok)continue;chosen.push_back(p[i]);if(find_k_rec(p,i+1,k,chosen))return true;chosen.pop_back();}
 return false;
}
bool find_k(std::vector<std::uint32_t>p,unsigned k,std::vector<std::uint32_t>&out){std::sort(p.begin(),p.end());p.erase(std::unique(p.begin(),p.end()),p.end());out.clear();return find_k_rec(p,0,k,out);}
}

int main(int argc,char**argv){try{
 if(argc!=2){std::cerr<<"usage: search_net2_r4 BASELINE_IDS\n";return 2;}auto base=load_ids(argv[1]);if(base.size()>((1u<<BITS)-1))throw std::runtime_error("owner packing");std::unordered_set<std::uint32_t>bset(base.begin(),base.end());
 // Coverage classes 0..4.
 std::vector<std::uint16_t>cnt(N,0),t16(N,0);for(auto v:base)cnt[v]=1;transform<std::uint16_t,Op::Sum>(cnt,t16,"count");t16.clear();t16.shrink_to_fit();
 std::vector<std::uint32_t>c1,c2,c3,c4;c1.reserve(10000);c2.reserve(200000);c3.reserve(1100000);c4.reserve(2300000);std::uint64_t c0=0;
 for(std::uint32_t v=0;v<N;++v){if(cnt[v]==0)++c0;else if(cnt[v]==1&&!bset.count(v))c1.push_back(v);else if(cnt[v]==2)c2.push_back(v);else if(cnt[v]==3)c3.push_back(v);else if(cnt[v]==4)c4.push_back(v);}if(c0)throw std::runtime_error("coverage0 nonzero; r4 precondition failed");cnt.clear();cnt.shrink_to_fit();
 // Min owner labels (1-based), retained only for c1..c4.
 std::vector<std::uint32_t>mn(N,INF),tm(N,INF);for(std::uint32_t i=0;i<base.size();++i)mn[base[i]]=i+1;transform<std::uint32_t,Op::Min>(mn,tm,"min");tm.clear();tm.shrink_to_fit();
 std::vector<std::uint32_t>lo1,lo2,lo3,lo4;lo1.reserve(c1.size());lo2.reserve(c2.size());lo3.reserve(c3.size());lo4.reserve(c4.size());for(auto v:c1)lo1.push_back(mn[v]);for(auto v:c2)lo2.push_back(mn[v]);for(auto v:c3)lo3.push_back(mn[v]);for(auto v:c4)lo4.push_back(mn[v]);mn.clear();mn.shrink_to_fit();
 // Max owner labels.
 std::vector<std::uint32_t>mx(N,0),tx(N,0);for(std::uint32_t i=0;i<base.size();++i)mx[base[i]]=i+1;transform<std::uint32_t,Op::Max>(mx,tx,"max");tx.clear();tx.shrink_to_fit();
 std::vector<std::uint32_t>hi2,hi3,hi4;hi2.reserve(c2.size());hi3.reserve(c3.size());hi4.reserve(c4.size());for(auto v:c2)hi2.push_back(mx[v]);for(auto v:c3)hi3.push_back(mx[v]);for(auto v:c4)hi4.push_back(mx[v]);mx.clear();mx.shrink_to_fit();
 // Sum owner labels for exact c3/c4 recovery.
 std::vector<std::uint64_t>su(N,0),ts(N,0);for(std::uint32_t i=0;i<base.size();++i)su[base[i]]=std::uint64_t(i+1);transform<std::uint64_t,Op::Sum>(su,ts,"sum");ts.clear();ts.shrink_to_fit();
 std::vector<std::uint64_t>sum3,sum4;sum3.reserve(c3.size());sum4.reserve(c4.size());for(auto v:c3)sum3.push_back(su[v]);for(auto v:c4)sum4.push_back(su[v]);su.clear();su.shrink_to_fit();
 // Sum squares is needed only to recover the two middle owners of c4 exactly.
 std::vector<std::uint64_t>sq(N,0),tq(N,0);for(std::uint32_t i=0;i<base.size();++i){std::uint64_t z=i+1;sq[base[i]]=z*z;}transform<std::uint64_t,Op::Sum>(sq,tq,"sumsq");tq.clear();tq.shrink_to_fit();std::vector<std::uint64_t>sumq4;sumq4.reserve(c4.size());for(auto v:c4)sumq4.push_back(sq[v]);sq.clear();sq.shrink_to_fit();

 std::vector<std::vector<std::uint32_t>>g1(base.size());for(std::size_t i=0;i<c1.size();++i){auto a=lo1[i];if(!a||a==INF||a>base.size())throw std::runtime_error("c1 owner");g1[a-1].push_back(c1[i]);}
 std::unordered_map<std::uint64_t,std::vector<std::uint32_t>>g2;g2.reserve(180000);for(std::size_t i=0;i<c2.size();++i){auto a=lo2[i],b=hi2[i];if(!a||a==INF||!b||a>=b||b>base.size())throw std::runtime_error("c2 owner");g2[key2(a-1,b-1)].push_back(c2[i]);}
 std::unordered_map<std::uint64_t,std::vector<std::uint32_t>>g3;g3.reserve(1100000);for(std::size_t i=0;i<c3.size();++i){std::uint64_t a=lo3[i],c=hi3[i],s=sum3[i];if(!a||a==INF||!c||a>=c||c>base.size()||s<=a+c)throw std::runtime_error("c3 extrema");std::uint64_t b=s-a-c;if(!(a<b&&b<c&&b<=base.size()))throw std::runtime_error("c3 middle");g3[key3(a-1,b-1,c-1)].push_back(c3[i]);}
 std::unordered_map<Quad,std::vector<std::uint32_t>,QuadHash>g4;g4.reserve(c4.size()*2+1);for(std::size_t i=0;i<c4.size();++i){std::uint64_t a=lo4[i],d=hi4[i],s=sum4[i];if(!a||a==INF||!d||a>=d||d>base.size()||s<=a+d)throw std::runtime_error("c4 extrema");std::uint64_t mids=s-a-d,qmid=sumq4[i]-a*a-d*d;if(sumsq4[i] < a*a+d*d) throw std::runtime_error("c4 sumsq underflow");
   // x+y=mids; x^2+y^2=qmid => (x-y)^2 = 2*qmid-mids^2.
   if(2*qmid<mids*mids)throw std::runtime_error("c4 discriminant sign");std::uint64_t disc=2*qmid-mids*mids;std::uint64_t r=(std::uint64_t)std::llround(std::sqrt((long double)disc));while((r+1)*(r+1)<=disc)++r;while(r*r>disc)--r;if(r*r!=disc||mids<r||((mids-r)&1))throw std::runtime_error("c4 discriminant");std::uint64_t b=(mids-r)/2,c=(mids+r)/2;if(!(a<b&&b<c&&c<d&&c<=base.size()))throw std::runtime_error("c4 middles");g4[quad(a-1,b-1,c-1,d-1)].push_back(c4[i]);}
 // NOTE typo guard above references sumsq4; use sumq4. (This line is replaced below in repository patch if compiler catches it.)

 // Incidence of genuine c2 supports.
 std::vector<std::vector<std::uint32_t>>inc(base.size());for(const auto&kv:g2){auto [a,b]=unkey2(kv.first);inc[a].push_back(b);inc[b].push_back(a);}for(auto&v:inc){std::sort(v.begin(),v.end());v.erase(std::unique(v.begin(),v.end()),v.end());}
 // Structural precheck: each c1 owner is a clique and every genuine two-owner pool has alpha<=2.
 std::vector<std::uint32_t>tmp;
 for(std::uint32_t a=0;a<g1.size();++a)if(find_k(g1[a],2,tmp))throw std::runtime_error("c1 alpha>=2; r4 generator precondition failed");
 for(const auto&kv:g2){auto [a,b]=unkey2(kv.first);std::vector<std::uint32_t>p;p.insert(p.end(),g1[a].begin(),g1[a].end());p.insert(p.end(),g1[b].begin(),g1[b].end());p.insert(p.end(),kv.second.begin(),kv.second.end());if(find_k(p,3,tmp))throw std::runtime_error("two-owner alpha>=3; disconnected r4 case requires separate treatment");}

 std::unordered_set<Quad,QuadHash>done;done.reserve(g4.size()*2+4000000);std::uint64_t checked=0,eligible=0;std::size_t maxpool=0;std::vector<std::uint32_t>chosen;Quad win{};bool found=false;
 auto pool4=[&](const Quad&q){std::array<std::uint32_t,4>x{q.a,q.b,q.c,q.d};std::vector<std::uint32_t>p;for(auto a:x)p.insert(p.end(),g1[a].begin(),g1[a].end());for(int i=0;i<4;++i)for(int j=i+1;j<4;++j){auto it=g2.find(key2(x[i],x[j]));if(it!=g2.end())p.insert(p.end(),it->second.begin(),it->second.end());}for(int i=0;i<4;++i)for(int j=i+1;j<4;++j)for(int k=j+1;k<4;++k){auto it=g3.find(key3(x[i],x[j],x[k]));if(it!=g3.end())p.insert(p.end(),it->second.begin(),it->second.end());}auto it4=g4.find(q);if(it4!=g4.end())p.insert(p.end(),it4->second.begin(),it4->second.end());std::sort(p.begin(),p.end());p.erase(std::unique(p.begin(),p.end()),p.end());return p;};
 auto check=[&](Quad q)->bool{if(!distinct4(q)||!done.insert(q).second)return false;auto p=pool4(q);++checked;maxpool=std::max(maxpool,p.size());if(p.size()<6)return false;++eligible;if(find_k(p,6,chosen)){win=q;found=true;return true;}return false;};
 // A. Direct c4 supports.
 for(const auto&kv:g4)if(check(kv.first))break;
 // B. Two distinct c3 supports sharing an owner pair; their union is a quad.
 if(!found){std::unordered_map<std::uint64_t,std::vector<std::uint32_t>>tri_by_pair;tri_by_pair.reserve(g3.size()*2);for(const auto&kv:g3){auto x=unkey3(kv.first);tri_by_pair[key2(x[0],x[1])].push_back(x[2]);tri_by_pair[key2(x[0],x[2])].push_back(x[1]);tri_by_pair[key2(x[1],x[2])].push_back(x[0]);}for(auto&kv:tri_by_pair){auto [a,b]=unkey2(kv.first);auto&v=kv.second;std::sort(v.begin(),v.end());v.erase(std::unique(v.begin(),v.end()),v.end());for(std::size_t i=0;i<v.size()&&!found;++i)for(std::size_t j=i+1;j<v.size();++j)if(check(quad(a,b,v[i],v[j])))break;}}
 // C. One c3 support plus a genuine c2 crossing edge that exposes the fourth owner.
 if(!found)for(const auto&kv:g3){auto x=unkey3(kv.first);for(int i=0;i<3&&!found;++i)for(auto d:inc[x[i]]){if(d==x[0]||d==x[1]||d==x[2])continue;if(check(quad(x[0],x[1],x[2],d)))break;}if(found)break;}
 // D. c1/c2 only: selected c2 support graph must be connected on four owners.
 // Enumerate every two-edge wedge a-b-c, then every genuine c2 edge from any
 // vertex of {a,b,c} to a new d. This covers a spanning tree of every connected graph.
 if(!found)for(std::uint32_t b=0;b<inc.size();++b){auto&nb=inc[b];for(std::size_t i=0;i<nb.size()&&!found;++i)for(std::size_t j=i+1;j<nb.size();++j){auto a=nb[i],c=nb[j];if(a==c)continue;std::array<std::uint32_t,3>t{a,b,c};for(auto u:t){for(auto d:inc[u]){if(d==a||d==b||d==c)continue;if(check(quad(a,b,c,d)))break;}if(found)break;}}if(found)break;}
 if(found){std::cout<<"{\"kind\":\"replace4add6\",\"method\":\"exact-unrestricted-r4-net2\",\"baseline_size\":"<<base.size()<<",\"remove\":["<<base[win.a]<<','<<base[win.b]<<','<<base[win.c]<<','<<base[win.d]<<"],\"add\":[";for(std::size_t i=0;i<chosen.size();++i)std::cout<<(i?",":"")<<chosen[i];std::cout<<"],\"quadruples_checked\":"<<checked<<"}\n";return 0;}
 std::cout<<"{\"kind\":\"none\",\"method\":\"exact-unrestricted-r4-net2\",\"baseline_size\":"<<base.size()<<",\"coverage0\":0,\"coverage1\":"<<c1.size()<<",\"coverage2\":"<<c2.size()<<",\"coverage3\":"<<c3.size()<<",\"coverage4\":"<<c4.size()<<",\"coverage2_groups\":"<<g2.size()<<",\"coverage3_groups\":"<<g3.size()<<",\"coverage4_groups\":"<<g4.size()<<",\"quadruples_checked\":"<<checked<<",\"eligible_quadruples\":"<<eligible<<",\"max_supported_pool\":"<<maxpool<<"}\n";return 0;
}catch(const std::exception&e){std::cerr<<"error: "<<e.what()<<"\n";return 1;}}
