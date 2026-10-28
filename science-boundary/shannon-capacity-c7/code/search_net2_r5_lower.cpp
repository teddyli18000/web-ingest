// Stage-B exact unrestricted remove-5/add-7 search for C7^10.
//
// This stage covers witnesses whose seven selected additions all have blocker
// support size <=4.  It is complete PROVIDED the same baseline has certified:
//   * exact radius-3 negative: alpha(P(U)) <= 4 for |U|<=3;
//   * exact radius-4 negative: alpha(P(U)) <= 5 for |U|<=4;
// and this program's internal checks establish alpha(P(U))<=1 for one-owner
// pools and <=2 for every genuine two-owner pool.
// These bounds rule out every disconnected support-hypergraph partition of five
// owners.  Hence the selected multi-owner supports must connect all five.
//
// Connected five-owner sets are generated completely by maximum selected
// support size:
//   4: a c4 support plus one crossing c2/c3/c4 support exposing owner five;
//   3: either two c3 supports intersect in one owner (union size five), or a
//      c3-rooted connected four-set is extended by a crossing c2/c3 support;
//   2: a connected c2 graph contains a spanning tree, generated as a wedge,
//      then one edge to owner four, then one edge to owner five.
// Each unique five-owner set is replayed with the COMPLETE pool of c1..c4
// candidates supported inside it and searched exactly for an independent 7-set.
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
template<class T,Op op>void transform(std::vector<T>&a,std::vector<T>&b,const char*name){for(int dim=0;dim<D;++dim){const auto s=P7[dim];const std::uint64_t block=std::uint64_t(s)*7u;
#pragma omp parallel for schedule(static)
for(std::int64_t gg=0;gg<(std::int64_t)GROUPS;++gg){const std::uint64_t g=gg,bn=g/s;const std::uint32_t off=g%s;const std::uint64_t base=bn*block+off;T v[7];for(int k=0;k<7;++k)v[k]=a[base+std::uint64_t(k)*s];for(int k=0;k<7;++k){T l=v[(k+6)%7],m=v[k],r=v[(k+1)%7],z{};if constexpr(op==Op::Sum)z=T(l+m+r);else if constexpr(op==Op::Min)z=std::min(l,std::min(m,r));else z=std::max(l,std::max(m,r));b[base+std::uint64_t(k)*s]=z;}}a.swap(b);std::cerr<<name<<" dim="<<dim<<"\n";}}
std::vector<std::uint32_t>load_ids(const std::string&p){std::ifstream in(p);if(!in)throw std::runtime_error("cannot open ids");std::vector<std::uint32_t>a;std::uint64_t x;while(in>>x){if(x>=N)throw std::runtime_error("id range");a.push_back((std::uint32_t)x);}if(a.empty())throw std::runtime_error("empty baseline");std::sort(a.begin(),a.end());if(std::adjacent_find(a.begin(),a.end())!=a.end())throw std::runtime_error("duplicate baseline");return a;}
bool conflict(std::uint32_t a,std::uint32_t b){if(a==b)return true;for(int d=0;d<D;++d){int x=a%7u,y=b%7u;a/=7u;b/=7u;int z=(x-y+7)%7;if(z!=0&&z!=1&&z!=6)return false;}return true;}
std::uint64_t key2(std::uint32_t a,std::uint32_t b){if(a>b)std::swap(a,b);return(std::uint64_t(a)<<BITS)|b;}
std::pair<std::uint32_t,std::uint32_t>unkey2(std::uint64_t k){return{std::uint32_t(k>>BITS),std::uint32_t(k&((1u<<BITS)-1))};}
std::uint64_t key3(std::uint32_t a,std::uint32_t b,std::uint32_t c){std::array<std::uint32_t,3>x{a,b,c};std::sort(x.begin(),x.end());return(std::uint64_t(x[0])<<(2*BITS))|(std::uint64_t(x[1])<<BITS)|x[2];}
std::array<std::uint32_t,3>unkey3(std::uint64_t k){const auto m=(1ull<<BITS)-1;return{std::uint32_t(k>>(2*BITS)),std::uint32_t((k>>BITS)&m),std::uint32_t(k&m)};}
struct Quad{std::uint32_t a,b,c,d;bool operator==(const Quad&o)const{return a==o.a&&b==o.b&&c==o.c&&d==o.d;}};
struct QuadHash{std::size_t operator()(const Quad&q)const noexcept{std::size_t h=q.a;for(auto x:{q.b,q.c,q.d})h^=std::size_t(x)+0x9e3779b97f4a7c15ULL+(h<<6)+(h>>2);return h;}};
Quad quad(std::uint32_t a,std::uint32_t b,std::uint32_t c,std::uint32_t d){std::array<std::uint32_t,4>x{a,b,c,d};std::sort(x.begin(),x.end());return{x[0],x[1],x[2],x[3]};}
struct Quint{std::uint32_t a,b,c,d,e;bool operator==(const Quint&o)const{return a==o.a&&b==o.b&&c==o.c&&d==o.d&&e==o.e;}};
struct QuintHash{std::size_t operator()(const Quint&q)const noexcept{std::size_t h=q.a;for(auto x:{q.b,q.c,q.d,q.e})h^=std::size_t(x)+0x9e3779b97f4a7c15ULL+(h<<6)+(h>>2);return h;}};
Quint quint(std::uint32_t a,std::uint32_t b,std::uint32_t c,std::uint32_t d,std::uint32_t e){std::array<std::uint32_t,5>x{a,b,c,d,e};std::sort(x.begin(),x.end());return{x[0],x[1],x[2],x[3],x[4]};}
bool distinct5(const Quint&q){return q.a<q.b&&q.b<q.c&&q.c<q.d&&q.d<q.e;}
std::uint64_t isqrt_u64(std::uint64_t x){std::uint64_t r=(std::uint64_t)std::sqrt((long double)x);while((r+1)>r&&(r+1)<=x/(r+1))++r;while(r&&r>x/r)--r;return r;}
bool find_k_rec(const std::vector<std::uint32_t>&p,std::size_t start,unsigned k,std::vector<std::uint32_t>&chosen){if(chosen.size()==k)return true;if(chosen.size()+(p.size()-start)<k)return false;for(std::size_t i=start;i<p.size();++i){bool ok=true;for(auto z:chosen)if(conflict(z,p[i])){ok=false;break;}if(!ok)continue;chosen.push_back(p[i]);if(find_k_rec(p,i+1,k,chosen))return true;chosen.pop_back();}return false;}
bool find_k(std::vector<std::uint32_t>p,unsigned k,std::vector<std::uint32_t>&out){std::sort(p.begin(),p.end());p.erase(std::unique(p.begin(),p.end()),p.end());out.clear();return find_k_rec(p,0,k,out);}
}
int main(int argc,char**argv){try{
 if(argc!=2){std::cerr<<"usage: search_net2_r5_lower BASELINE_IDS\n";return 2;}auto base=load_ids(argv[1]);std::unordered_set<std::uint32_t>bset(base.begin(),base.end());
 std::vector<std::uint16_t>cnt(N,0),t16(N,0);for(auto v:base)cnt[v]=1;transform<std::uint16_t,Op::Sum>(cnt,t16,"count");t16.clear();t16.shrink_to_fit();std::vector<std::uint32_t>c1,c2,c3,c4;c1.reserve(10000);c2.reserve(200000);c3.reserve(1100000);c4.reserve(2300000);std::uint64_t c0=0;for(std::uint32_t v=0;v<N;++v){if(cnt[v]==0)++c0;else if(cnt[v]==1&&!bset.count(v))c1.push_back(v);else if(cnt[v]==2)c2.push_back(v);else if(cnt[v]==3)c3.push_back(v);else if(cnt[v]==4)c4.push_back(v);}if(c0)throw std::runtime_error("coverage0 nonzero");cnt.clear();cnt.shrink_to_fit();
 std::vector<std::uint32_t>mn(N,INF),tm(N,INF);for(std::uint32_t i=0;i<base.size();++i)mn[base[i]]=i+1;transform<std::uint32_t,Op::Min>(mn,tm,"min");tm.clear();tm.shrink_to_fit();std::vector<std::vector<std::uint32_t>>g1(base.size());for(auto v:c1){auto a=mn[v];if(!a||a==INF||a>base.size())throw std::runtime_error("c1");g1[a-1].push_back(v);}std::vector<std::uint32_t>lo2,lo3,lo4;for(auto v:c2)lo2.push_back(mn[v]);for(auto v:c3)lo3.push_back(mn[v]);for(auto v:c4)lo4.push_back(mn[v]);mn.clear();mn.shrink_to_fit();
 std::vector<std::uint32_t>mx(N,0),tx(N,0);for(std::uint32_t i=0;i<base.size();++i)mx[base[i]]=i+1;transform<std::uint32_t,Op::Max>(mx,tx,"max");tx.clear();tx.shrink_to_fit();std::vector<std::uint32_t>hi2,hi3,hi4;for(auto v:c2)hi2.push_back(mx[v]);for(auto v:c3)hi3.push_back(mx[v]);for(auto v:c4)hi4.push_back(mx[v]);mx.clear();mx.shrink_to_fit();
 std::vector<std::uint64_t>su(N,0),ts(N,0);for(std::uint32_t i=0;i<base.size();++i)su[base[i]]=i+1;transform<std::uint64_t,Op::Sum>(su,ts,"sum");ts.clear();ts.shrink_to_fit();std::vector<std::uint64_t>s3,s4;for(auto v:c3)s3.push_back(su[v]);for(auto v:c4)s4.push_back(su[v]);su.clear();su.shrink_to_fit();
 std::vector<std::uint64_t>sq(N,0),tq(N,0);for(std::uint32_t i=0;i<base.size();++i){std::uint64_t z=i+1;sq[base[i]]=z*z;}transform<std::uint64_t,Op::Sum>(sq,tq,"sumsq");tq.clear();tq.shrink_to_fit();std::vector<std::uint64_t>q4;for(auto v:c4)q4.push_back(sq[v]);sq.clear();sq.shrink_to_fit();
 std::unordered_map<std::uint64_t,std::vector<std::uint32_t>>g2,g3;g2.reserve(180000);g3.reserve(1100000);for(std::size_t i=0;i<c2.size();++i){auto a=lo2[i],b=hi2[i];if(!a||a==INF||!b||a>=b||b>base.size())throw std::runtime_error("c2 support");g2[key2(a-1,b-1)].push_back(c2[i]);}for(std::size_t i=0;i<c3.size();++i){std::uint64_t a=lo3[i],c=hi3[i],s=s3[i];if(!a||a==INF||!c||a>=c||s<=a+c)throw std::runtime_error("c3 support");std::uint64_t b=s-a-c;if(!(a<b&&b<c&&c<=base.size()))throw std::runtime_error("c3 roots");g3[key3(a-1,b-1,c-1)].push_back(c3[i]);}
 std::unordered_map<Quad,std::vector<std::uint32_t>,QuadHash>g4;g4.reserve(c4.size()*2+1);for(std::size_t i=0;i<c4.size();++i){std::uint64_t a=lo4[i],d=hi4[i],s=s4[i];if(!a||a==INF||!d||a>=d||s<=a+d)throw std::runtime_error("c4 support");std::uint64_t mids=s-a-d,edge=a*a+d*d;if(q4[i]<edge)throw std::runtime_error("c4 sumsq");std::uint64_t qm=q4[i]-edge;if(2*qm<mids*mids)throw std::runtime_error("c4 disc sign");std::uint64_t disc=2*qm-mids*mids,r=isqrt_u64(disc);if(r*r!=disc||mids<r||((mids-r)&1))throw std::runtime_error("c4 disc");std::uint64_t b=(mids-r)/2,c=(mids+r)/2;if(!(a<b&&b<c&&c<d&&d<=base.size()))throw std::runtime_error("c4 roots");g4[quad(a-1,b-1,c-1,d-1)].push_back(c4[i]);}
 // Internal structural checks used by the disconnected-component bound.
 std::vector<std::uint32_t>scratch;for(std::uint32_t a=0;a<g1.size();++a)if(find_k(g1[a],2,scratch))throw std::runtime_error("one-owner alpha>1");for(const auto&kv:g2){auto [a,b]=unkey2(kv.first);std::vector<std::uint32_t>p=g1[a];p.insert(p.end(),g1[b].begin(),g1[b].end());p.insert(p.end(),kv.second.begin(),kv.second.end());if(find_k(p,3,scratch))throw std::runtime_error("two-owner alpha>2");}
 // Support incidence indices.
 std::vector<std::vector<std::uint32_t>>inc2(base.size());for(const auto&kv:g2){auto [a,b]=unkey2(kv.first);inc2[a].push_back(b);inc2[b].push_back(a);}for(auto&v:inc2){std::sort(v.begin(),v.end());v.erase(std::unique(v.begin(),v.end()),v.end());}
 std::unordered_map<std::uint64_t,std::vector<std::uint32_t>>tri_by_pair;tri_by_pair.reserve(g3.size()*2);std::vector<std::vector<std::uint64_t>>tri_by_owner(base.size());for(const auto&kv:g3){auto x=unkey3(kv.first);tri_by_pair[key2(x[0],x[1])].push_back(x[2]);tri_by_pair[key2(x[0],x[2])].push_back(x[1]);tri_by_pair[key2(x[1],x[2])].push_back(x[0]);tri_by_owner[x[0]].push_back(key2(x[1],x[2]));tri_by_owner[x[1]].push_back(key2(x[0],x[2]));tri_by_owner[x[2]].push_back(key2(x[0],x[1]));}
 for(auto&kv:tri_by_pair){auto&v=kv.second;std::sort(v.begin(),v.end());v.erase(std::unique(v.begin(),v.end()),v.end());}
 for(auto&v:tri_by_owner){std::sort(v.begin(),v.end());v.erase(std::unique(v.begin(),v.end()),v.end());}
 std::unordered_map<std::uint64_t,std::vector<std::uint32_t>>quad_by_triple;quad_by_triple.reserve(g4.size()*2);for(const auto&kv:g4){auto q=kv.first;std::array<std::uint32_t,4>x{q.a,q.b,q.c,q.d};for(int omit=0;omit<4;++omit){std::array<std::uint32_t,3>y{};int z=0;for(int i=0;i<4;++i)if(i!=omit)y[z++]=x[i];quad_by_triple[key3(y[0],y[1],y[2])].push_back(x[omit]);}}
 for(auto&kv:quad_by_triple){auto&v=kv.second;std::sort(v.begin(),v.end());v.erase(std::unique(v.begin(),v.end()),v.end());}
 std::unordered_set<Quint,QuintHash>done;done.reserve(20000000);std::uint64_t generated=0,unique=0,eligible=0;std::size_t maxpool=0;std::vector<std::uint32_t>chosen;Quint win{};bool found=false;auto append=[&](std::vector<std::uint32_t>&p,const auto&v){p.insert(p.end(),v.begin(),v.end());};
 auto check5=[&](Quint q)->bool{++generated;if(!distinct5(q)||!done.insert(q).second)return false;++unique;std::array<std::uint32_t,5>x{q.a,q.b,q.c,q.d,q.e};std::vector<std::uint32_t>p;for(auto a:x)append(p,g1[a]);for(int i=0;i<5;++i)for(int j=i+1;j<5;++j){auto it=g2.find(key2(x[i],x[j]));if(it!=g2.end())append(p,it->second);}for(int i=0;i<5;++i)for(int j=i+1;j<5;++j)for(int k=j+1;k<5;++k){auto it=g3.find(key3(x[i],x[j],x[k]));if(it!=g3.end())append(p,it->second);}for(int omit=0;omit<5;++omit){std::array<std::uint32_t,4>y{};int z=0;for(int i=0;i<5;++i)if(i!=omit)y[z++]=x[i];auto it=g4.find(quad(y[0],y[1],y[2],y[3]));if(it!=g4.end())append(p,it->second);}std::sort(p.begin(),p.end());p.erase(std::unique(p.begin(),p.end()),p.end());maxpool=std::max(maxpool,p.size());if(p.size()<7)return false;++eligible;if(find_k(p,7,chosen)){win=q;found=true;return true;}return false;};
 auto outside4=[](const Quad&q,std::uint32_t d){return d!=q.a&&d!=q.b&&d!=q.c&&d!=q.d;};
 auto extend234=[&](const Quad&q){std::array<std::uint32_t,4>x{q.a,q.b,q.c,q.d};for(auto u:x)for(auto d:inc2[u])if(outside4(q,d)&&check5(quint(q.a,q.b,q.c,q.d,d)))return true;for(int i=0;i<4;++i)for(int j=i+1;j<4;++j){auto it=tri_by_pair.find(key2(x[i],x[j]));if(it!=tri_by_pair.end())for(auto d:it->second)if(outside4(q,d)&&check5(quint(q.a,q.b,q.c,q.d,d)))return true;}for(int omit=0;omit<4;++omit){std::array<std::uint32_t,3>y{};int z=0;for(int i=0;i<4;++i)if(i!=omit)y[z++]=x[i];auto it=quad_by_triple.find(key3(y[0],y[1],y[2]));if(it!=quad_by_triple.end())for(auto d:it->second)if(outside4(q,d)&&check5(quint(q.a,q.b,q.c,q.d,d)))return true;}return false;};
 auto extend23=[&](const Quad&q){std::array<std::uint32_t,4>x{q.a,q.b,q.c,q.d};for(auto u:x)for(auto d:inc2[u])if(outside4(q,d)&&check5(quint(q.a,q.b,q.c,q.d,d)))return true;for(int i=0;i<4;++i)for(int j=i+1;j<4;++j){auto it=tri_by_pair.find(key2(x[i],x[j]));if(it!=tri_by_pair.end())for(auto d:it->second)if(outside4(q,d)&&check5(quint(q.a,q.b,q.c,q.d,d)))return true;}return false;};
 // Max selected support size 4.
 for(const auto&kv:g4){if(extend234(kv.first)){found=true;break;}}
 // Max selected support size <=3: two c3 supports intersecting in exactly one owner directly span five owners.
 if(!found)for(std::uint32_t u=0;u<tri_by_owner.size();++u){auto&v=tri_by_owner[u];for(std::size_t i=0;i<v.size()&&!found;++i){auto [a,b]=unkey2(v[i]);for(std::size_t j=i+1;j<v.size();++j){auto [c,d]=unkey2(v[j]);if(a==c||a==d||b==c||b==d)continue;if(check5(quint(u,a,b,c,d))){found=true;break;}}}}
 // Connected c3-rooted four-sets: two c3 supports sharing a pair.
 if(!found)for(const auto&kv:tri_by_pair){auto [a,b]=unkey2(kv.first);auto&v=kv.second;for(std::size_t i=0;i<v.size()&&!found;++i)for(std::size_t j=i+1;j<v.size();++j){if(extend23(quad(a,b,v[i],v[j]))){found=true;break;}}}
 // Connected c3 + c2 four-sets.
 if(!found)for(const auto&kv:g3){auto x=unkey3(kv.first);for(int i=0;i<3&&!found;++i)for(auto d:inc2[x[i]]){if(d==x[0]||d==x[1]||d==x[2])continue;if(extend23(quad(x[0],x[1],x[2],d))){found=true;break;}}}
 // c2-only connected four-sets (tree wedge plus extending edge), then one more c2/c3 extension.
 if(!found)for(std::uint32_t b=0;b<inc2.size();++b){auto&nb=inc2[b];for(std::size_t i=0;i<nb.size()&&!found;++i)for(std::size_t j=i+1;j<nb.size();++j){auto a=nb[i],c=nb[j];if(a==c)continue;std::array<std::uint32_t,3>t{a,b,c};for(auto u:t){for(auto d:inc2[u]){if(d==a||d==b||d==c)continue;if(extend23(quad(a,b,c,d))){found=true;break;}}if(found)break;}}if(found)break;}
 if(found){std::cout<<"{\"kind\":\"replace5add7\",\"method\":\"exact-unrestricted-r5-connected-lower-support\",\"baseline_size\":"<<base.size()<<",\"remove\":["<<base[win.a]<<','<<base[win.b]<<','<<base[win.c]<<','<<base[win.d]<<','<<base[win.e]<<"],\"add\":[";for(std::size_t i=0;i<chosen.size();++i)std::cout<<(i?",":"")<<chosen[i];std::cout<<"],\"generated_calls\":"<<generated<<",\"unique_owner5_checked\":"<<unique<<"}\n";return 0;}
 std::cout<<"{\"kind\":\"none\",\"method\":\"exact-unrestricted-r5-connected-lower-support\",\"baseline_size\":"<<base.size()<<",\"coverage0\":0,\"coverage1\":"<<c1.size()<<",\"coverage2\":"<<c2.size()<<",\"coverage3\":"<<c3.size()<<",\"coverage4\":"<<c4.size()<<",\"coverage2_groups\":"<<g2.size()<<",\"coverage3_groups\":"<<g3.size()<<",\"coverage4_groups\":"<<g4.size()<<",\"generated_calls\":"<<generated<<",\"unique_owner5_checked\":"<<unique<<",\"eligible_owner5\":"<<eligible<<",\"max_supported_pool\":"<<maxpool<<"}\n";return 0;
}catch(const std::exception&e){std::cerr<<"error: "<<e.what()<<"\n";return 1;}}
