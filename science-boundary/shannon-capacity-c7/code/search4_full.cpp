#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <fstream>
#include <functional>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <utility>
#include <vector>

#ifdef _OPENMP
#include <omp.h>
#endif

namespace {
constexpr int D=10;
constexpr std::uint32_t P7[D+1]={1u,7u,49u,343u,2401u,16807u,117649u,823543u,5764801u,40353607u,282475249u};
constexpr std::uint32_t U=P7[D], GROUPS=U/7u, INF=0xffffffffu;
constexpr unsigned BITS=18;
constexpr std::uint64_t MASK=(1ull<<BITS)-1;
using U128=unsigned __int128;

enum class Op{Sum,Min,Max};
template<class T,Op op>void transform(std::vector<T>&a,std::vector<T>&b,const char*name){
 for(int dim=0;dim<D;++dim){auto s=P7[dim];std::uint64_t block=std::uint64_t(s)*7u;
  #pragma omp parallel for schedule(static)
  for(std::int64_t gg=0;gg<(std::int64_t)GROUPS;++gg){std::uint64_t g=gg,bn=g/s;std::uint32_t off=g%s;std::uint64_t base=bn*block+off;T v[7];for(int k=0;k<7;++k)v[k]=a[base+std::uint64_t(k)*s];for(int k=0;k<7;++k){T l=v[(k+6)%7],m=v[k],r=v[(k+1)%7],z{};if constexpr(op==Op::Sum)z=static_cast<T>(l+m+r);else if constexpr(op==Op::Min)z=std::min(l,std::min(m,r));else z=std::max(l,std::max(m,r));b[base+std::uint64_t(k)*s]=z;}}
  a.swap(b);std::cerr<<name<<" dim="<<dim<<"\n";
 }
}

std::vector<std::uint32_t>load(const std::string&p){std::ifstream in(p);if(!in)throw std::runtime_error("cannot open ids");std::vector<std::uint32_t>a;std::uint64_t x;while(in>>x){if(x>=U)throw std::runtime_error("id range");a.push_back(static_cast<std::uint32_t>(x));}if(a.size()!=134753u)throw std::runtime_error("baseline size");return a;}
bool adj(std::uint32_t a,std::uint32_t b){if(a==b)return true;for(int d=0;d<D;++d){int x=a%7u,y=b%7u;a/=7u;b/=7u;int z=(x-y+7)%7;if(z!=0&&z!=1&&z!=6)return false;}return true;}
std::uint64_t pk(std::uint32_t a,std::uint32_t b){if(a>b)std::swap(a,b);return(std::uint64_t(a)<<BITS)|b;}
std::array<std::uint32_t,2>pun(std::uint64_t k){return{std::uint32_t((k>>BITS)&MASK),std::uint32_t(k&MASK)};}
std::uint64_t tk(std::uint32_t a,std::uint32_t b,std::uint32_t c){std::array<std::uint32_t,3>v{a,b,c};std::sort(v.begin(),v.end());return(std::uint64_t(v[0])<<(2*BITS))|(std::uint64_t(v[1])<<BITS)|v[2];}
std::array<std::uint32_t,3>tun(std::uint64_t k){return{std::uint32_t((k>>(2*BITS))&MASK),std::uint32_t((k>>BITS)&MASK),std::uint32_t(k&MASK)};}
U128 qk(std::uint32_t a,std::uint32_t b,std::uint32_t c,std::uint32_t d){std::array<std::uint32_t,4>v{a,b,c,d};std::sort(v.begin(),v.end());return(U128(v[0])<<(3*BITS))|(U128(v[1])<<(2*BITS))|(U128(v[2])<<BITS)|v[3];}
std::array<std::uint32_t,4>qun(U128 k){return{std::uint32_t((k>>(3*BITS))&MASK),std::uint32_t((k>>(2*BITS))&MASK),std::uint32_t((k>>BITS)&MASK),std::uint32_t(k&MASK)};}
std::uint64_t isqrt(std::uint64_t n){std::uint64_t x=std::sqrt((long double)n);while((x+1)*(unsigned __int128)(x+1)<=n)++x;while(x*(unsigned __int128)x>n)--x;return x;}

struct Low{std::uint32_t id;std::uint8_t c;std::uint32_t lo=0,hi=0,sum=0;std::uint64_t sq=0;};
struct QItem{U128 key;std::uint32_t id;};
struct PairThird{std::uint64_t pair;std::uint32_t third;};

bool independent5(const std::vector<std::uint32_t>&p,std::array<std::uint32_t,5>&out){
 if(p.size()<5)return false;std::array<int,5>ch{};
 std::function<bool(int,int)>dfs=[&](int start,int n){if(n==5){for(int i=0;i<5;++i)out[i]=p[ch[i]];return true;}if((int)p.size()-start<5-n)return false;for(int i=start;i<(int)p.size();++i){bool ok=true;for(int j=0;j<n;++j)if(adj(p[i],p[ch[j]])){ok=false;break;}if(!ok)continue;ch[n]=i;if(dfs(i+1,n+1))return true;}return false;};return dfs(0,0);
}
void append2(std::vector<std::uint32_t>&p,const std::unordered_map<std::uint64_t,std::vector<std::uint32_t>>&m,std::uint64_t k){auto it=m.find(k);if(it!=m.end())p.insert(p.end(),it->second.begin(),it->second.end());}
void append3(std::vector<std::uint32_t>&p,const std::unordered_map<std::uint64_t,std::vector<std::uint32_t>>&m,std::uint64_t k){auto it=m.find(k);if(it!=m.end())p.insert(p.end(),it->second.begin(),it->second.end());}
void append4(std::vector<std::uint32_t>&p,const std::vector<QItem>&v,U128 k){auto it=std::lower_bound(v.begin(),v.end(),k,[](const QItem&a,U128 b){return a.key<b;});while(it!=v.end()&&it->key==k){p.push_back(it->id);++it;}}
void addq(std::vector<U128>&qs,std::uint32_t a,std::uint32_t b,std::uint32_t c,std::uint32_t d){if(a==b||a==c||a==d||b==c||b==d||c==d)return;qs.push_back(qk(a,b,c,d));}
void print_bulk(const std::vector<std::uint32_t>&base,const std::array<std::uint32_t,4>&o,const std::array<std::uint32_t,5>&add){std::cout<<"{\"kind\":\"bulk\",\"method\":\"exact-4-for-5-connected-union4\",\"baseline_size\":"<<base.size()<<",\"remove\":["<<base[o[0]]<<','<<base[o[1]]<<','<<base[o[2]]<<','<<base[o[3]]<<"],\"add\":["<<add[0]<<','<<add[1]<<','<<add[2]<<','<<add[3]<<','<<add[4]<<"],\"owner_indices\":["<<o[0]<<','<<o[1]<<','<<o[2]<<','<<o[3]<<"]}\n";}
}

int main(int argc,char**argv){try{
 if(argc!=2){std::cerr<<"usage: search4_full BASELINE_IDS\n";return 2;}
 auto base=load(argv[1]);std::unordered_set<std::uint32_t>bset(base.begin(),base.end());

 // Count first, retain only vertices of coverage 1..4, then release the dense
 // array before the owner-moment transforms.  This keeps peak RAM well below
 // the older search4 implementation.
 std::vector<std::uint16_t>cnt(U,0),tmp16(U,0);for(auto id:base)cnt[id]=1;transform<std::uint16_t,Op::Sum>(cnt,tmp16,"count");tmp16.clear();tmp16.shrink_to_fit();
 std::vector<Low>low;low.reserve(4000000);for(std::uint32_t id=0;id<U;++id){auto c=cnt[id];if(c==0){std::cout<<"{\"kind\":\"bulk\",\"method\":\"exact-direct\",\"baseline_size\":"<<base.size()<<",\"remove\":[],\"add\":["<<id<<"]}\n";return 0;}if(c>=1&&c<=4)low.push_back({id,static_cast<std::uint8_t>(c)});}std::cerr<<"low_vertices="<<low.size()<<"\n";cnt.clear();cnt.shrink_to_fit();

 std::vector<std::uint32_t>a32(U,INF),b32(U,INF);for(std::uint32_t i=0;i<base.size();++i)a32[base[i]]=i+1;transform<std::uint32_t,Op::Min>(a32,b32,"min");for(auto&x:low)x.lo=a32[x.id];a32.clear();a32.shrink_to_fit();b32.clear();b32.shrink_to_fit();
 a32.assign(U,0);b32.assign(U,0);for(std::uint32_t i=0;i<base.size();++i)a32[base[i]]=i+1;transform<std::uint32_t,Op::Max>(a32,b32,"max");for(auto&x:low)x.hi=a32[x.id];a32.clear();a32.shrink_to_fit();b32.clear();b32.shrink_to_fit();
 a32.assign(U,0);b32.assign(U,0);for(std::uint32_t i=0;i<base.size();++i)a32[base[i]]=i+1;transform<std::uint32_t,Op::Sum>(a32,b32,"sum");for(auto&x:low)x.sum=a32[x.id];a32.clear();a32.shrink_to_fit();b32.clear();b32.shrink_to_fit();
 std::vector<std::uint64_t>a64(U,0),b64(U,0);for(std::uint64_t i=0;i<base.size();++i)a64[base[i]]=(i+1)*(i+1);transform<std::uint64_t,Op::Sum>(a64,b64,"sumsq");for(auto&x:low)x.sq=a64[x.id];a64.clear();a64.shrink_to_fit();b64.clear();b64.shrink_to_fit();

 std::vector<std::vector<std::uint32_t>>c1(base.size());std::unordered_map<std::uint64_t,std::vector<std::uint32_t>>c2,c3;c2.reserve(160000);c3.reserve(1100000);std::vector<QItem>c4;c4.reserve(2400000);std::uint64_t n1=0,n2=0,n3=0,n4=0;
 for(const auto&x:low){auto lo=x.lo,hi=x.hi;if(lo==0||lo==INF||hi==0||hi==INF||lo>base.size()||hi>base.size())throw std::runtime_error("bad extrema");if(x.c==1){if(bset.count(x.id))continue;if(lo!=hi)throw std::runtime_error("bad c1 extrema");c1[lo-1].push_back(x.id);++n1;}else if(x.c==2){if(lo>=hi)throw std::runtime_error("bad c2");c2[pk(lo-1,hi-1)].push_back(x.id);++n2;}else if(x.c==3){std::uint64_t mid=std::uint64_t(x.sum)-lo-hi;if(mid==0||mid>base.size()||mid==lo||mid==hi)throw std::runtime_error("bad c3");c3[tk(lo-1,static_cast<std::uint32_t>(mid-1),hi-1)].push_back(x.id);++n3;}else{std::uint64_t mids=std::uint64_t(x.sum)-lo-hi;std::uint64_t midq=x.sq-std::uint64_t(lo)*lo-std::uint64_t(hi)*hi;std::uint64_t disc=2*midq-mids*mids;auto dif=isqrt(disc);if(dif*dif!=disc||mids<dif||((mids-dif)&1))throw std::runtime_error("bad c4 discriminant");std::uint64_t m1=(mids-dif)/2,m2=(mids+dif)/2;if(m1==0||m2==0||lo>=m1||m1>=m2||m2>=hi||m2>base.size())throw std::runtime_error("bad c4 middle");c4.push_back({qk(lo-1,static_cast<std::uint32_t>(m1-1),static_cast<std::uint32_t>(m2-1),hi-1),x.id});++n4;}}
 low.clear();low.shrink_to_fit();std::cerr<<"coverage low: "<<n1<<","<<n2<<","<<n3<<","<<n4<<" groups2="<<c2.size()<<" groups3="<<c3.size()<<"\n";
 std::sort(c4.begin(),c4.end(),[](const QItem&a,const QItem&b){return a.key<b.key||(a.key==b.key&&a.id<b.id);});

 // Necessary condition for alpha(P(T)) >= 5 on four owners T: the hypergraph
 // of non-singleton owner supports inside T must be connected.  Otherwise its
 // connected components are proper owner subsets; the already-closed <=3
 // owner radii give alpha <= sum |component| = 4.  Generate every connected
 // T from: a cov4 edge; a cov3 edge joined to cov2; two cov3 edges sharing a
 // pair; or a connected cov2-only graph.
 std::vector<std::vector<std::uint32_t>>oadj(base.size());for(const auto&kv:c2){auto e=pun(kv.first);oadj[e[0]].push_back(e[1]);oadj[e[1]].push_back(e[0]);}for(auto&v:oadj){std::sort(v.begin(),v.end());v.erase(std::unique(v.begin(),v.end()),v.end());}
 std::vector<U128>qs;qs.reserve(16000000);
 std::uint64_t cov4_groups=0;for(std::size_t i=0;i<c4.size();){qs.push_back(c4[i].key);++cov4_groups;std::size_t j=i+1;while(j<c4.size()&&c4[j].key==c4[i].key)++j;i=j;}

 std::vector<PairThird>pt;pt.reserve(c3.size()*3ull);std::uint64_t raw32=0;
 for(const auto&kv:c3){auto t=tun(kv.first);pt.push_back({pk(t[0],t[1]),t[2]});pt.push_back({pk(t[0],t[2]),t[1]});pt.push_back({pk(t[1],t[2]),t[0]});for(auto x:t)for(auto d:oadj[x])if(d!=t[0]&&d!=t[1]&&d!=t[2]){addq(qs,t[0],t[1],t[2],d);++raw32;}}
 std::sort(pt.begin(),pt.end(),[](const PairThird&a,const PairThird&b){return a.pair<b.pair||(a.pair==b.pair&&a.third<b.third);});
 std::uint64_t raw33=0;for(std::size_t i=0;i<pt.size();){std::size_t j=i+1;while(j<pt.size()&&pt[j].pair==pt[i].pair)++j;std::vector<std::uint32_t>third;third.reserve(j-i);for(std::size_t z=i;z<j;++z)if(third.empty()||third.back()!=pt[z].third)third.push_back(pt[z].third);auto ab=pun(pt[i].pair);for(std::size_t x=0;x<third.size();++x)for(std::size_t y=x+1;y<third.size();++y){addq(qs,ab[0],ab[1],third[x],third[y]);++raw33;}i=j;}pt.clear();pt.shrink_to_fit();

 std::uint64_t raw22=0,wedge=0;for(std::uint32_t a=0;a<oadj.size();++a){const auto&nb=oadj[a];for(std::size_t i=0;i<nb.size();++i)for(std::size_t j=i+1;j<nb.size();++j){auto b=nb[i],c=nb[j];++wedge;std::array<std::uint32_t,3>t{a,b,c};for(auto x:t)for(auto d:oadj[x])if(d!=a&&d!=b&&d!=c){addq(qs,a,b,c,d);++raw22;}}}
 std::cerr<<"quad_generation cov4_groups="<<cov4_groups<<" raw_c3_c2="<<raw32<<" raw_c3_c3="<<raw33<<" cov2_wedges="<<wedge<<" raw_c2_connected="<<raw22<<" raw_total="<<qs.size()<<"\n";
 std::sort(qs.begin(),qs.end());qs.erase(std::unique(qs.begin(),qs.end()),qs.end());

 std::size_t maxpool=0;std::uint64_t checked=0,eligible=0,no4=0;
 for(auto key:qs){auto o=qun(key);std::vector<std::uint32_t>pool;pool.reserve(40);append4(pool,c4,key);bool has4=!pool.empty();if(!has4)++no4;for(int omit=0;omit<4;++omit){std::array<std::uint32_t,3>t{};int z=0;for(int i=0;i<4;++i)if(i!=omit)t[z++]=o[i];append3(pool,c3,tk(t[0],t[1],t[2]));}for(int i=0;i<4;++i)for(int j=i+1;j<4;++j)append2(pool,c2,pk(o[i],o[j]));for(auto a:o)pool.insert(pool.end(),c1[a].begin(),c1[a].end());std::sort(pool.begin(),pool.end());pool.erase(std::unique(pool.begin(),pool.end()),pool.end());++checked;maxpool=std::max(maxpool,pool.size());if(pool.size()<5)continue;++eligible;std::array<std::uint32_t,5>add{};if(independent5(pool,add)){std::cerr<<"FOUND checked="<<checked<<" pool="<<pool.size()<<" has_cov4="<<has4<<"\n";print_bulk(base,o,add);return 0;}}
 std::cerr<<"NONE candidate_quads="<<qs.size()<<" checked="<<checked<<" eligible="<<eligible<<" no_cov4="<<no4<<" maxpool="<<maxpool<<"\n";
 std::cout<<"{\"kind\":\"none\",\"method\":\"exact-4-for-5-connected-union4\",\"baseline_size\":"<<base.size()<<",\"cov1\":"<<n1<<",\"cov2\":"<<n2<<",\"cov3\":"<<n3<<",\"cov4\":"<<n4<<",\"cov2_groups\":"<<c2.size()<<",\"cov3_groups\":"<<c3.size()<<",\"cov4_groups\":"<<cov4_groups<<",\"candidate_quads\":"<<qs.size()<<",\"no_cov4_quads\":"<<no4<<",\"eligible_quads\":"<<eligible<<",\"raw_c3_c2\":"<<raw32<<",\"raw_c3_c3\":"<<raw33<<",\"raw_c2_connected\":"<<raw22<<",\"max_pool\":"<<maxpool<<"}\n";return 0;
}catch(const std::exception&e){std::cerr<<"error: "<<e.what()<<"\n";return 1;}}
