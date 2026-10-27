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

enum class Op{Sum,Min,Max};
template<class T,Op op>void transform(std::vector<T>&a,std::vector<T>&b,const char*name){
 for(int dim=0;dim<D;++dim){auto s=P7[dim];std::uint64_t block=std::uint64_t(s)*7u;
  #pragma omp parallel for schedule(static)
  for(std::int64_t gg=0;gg<(std::int64_t)GROUPS;++gg){std::uint64_t g=gg,bn=g/s;std::uint32_t off=g%s;std::uint64_t base=bn*block+off;T v[7];for(int k=0;k<7;++k)v[k]=a[base+std::uint64_t(k)*s];for(int k=0;k<7;++k){T l=v[(k+6)%7],m=v[k],r=v[(k+1)%7],z{};if constexpr(op==Op::Sum)z=static_cast<T>(l+m+r);else if constexpr(op==Op::Min)z=std::min(l,std::min(m,r));else z=std::max(l,std::max(m,r));b[base+std::uint64_t(k)*s]=z;}}
  a.swap(b);std::cerr<<name<<" dim="<<dim<<"\n";
 }
}
std::vector<std::uint32_t>load(const std::string&p){std::ifstream in(p);if(!in)throw std::runtime_error("cannot open ids");std::vector<std::uint32_t>a;std::uint64_t x;while(in>>x){if(x>=U)throw std::runtime_error("id range");a.push_back(x);}if(a.size()!=134753u)throw std::runtime_error("baseline size");return a;}
bool adj(std::uint32_t a,std::uint32_t b){if(a==b)return true;for(int d=0;d<D;++d){int x=a%7u,y=b%7u;a/=7u;b/=7u;int z=(x-y+7)%7;if(z!=0&&z!=1&&z!=6)return false;}return true;}
std::uint64_t pk(std::uint32_t a,std::uint32_t b){if(a>b)std::swap(a,b);return(std::uint64_t(a)<<BITS)|b;}
std::uint64_t tk(std::uint32_t a,std::uint32_t b,std::uint32_t c){std::array<std::uint32_t,3>v{a,b,c};std::sort(v.begin(),v.end());return(std::uint64_t(v[0])<<(2*BITS))|(std::uint64_t(v[1])<<BITS)|v[2];}
using U128=unsigned __int128;
U128 qk(std::uint32_t a,std::uint32_t b,std::uint32_t c,std::uint32_t d){std::array<std::uint32_t,4>v{a,b,c,d};std::sort(v.begin(),v.end());return(U128(v[0])<<(3*BITS))|(U128(v[1])<<(2*BITS))|(U128(v[2])<<BITS)|v[3];}
std::array<std::uint32_t,4>qun(U128 k){return{std::uint32_t((k>>(3*BITS))&MASK),std::uint32_t((k>>(2*BITS))&MASK),std::uint32_t((k>>BITS)&MASK),std::uint32_t(k&MASK)};}
std::uint64_t isqrt(std::uint64_t n){std::uint64_t x=std::sqrt((long double)n);while((x+1)*(unsigned __int128)(x+1)<=n)++x;while(x*(unsigned __int128)x>n)--x;return x;}

bool independent5(const std::vector<std::uint32_t>&p,std::array<std::uint32_t,5>&out){
 if(p.size()<5)return false;std::array<int,5>ch{};
 std::function<bool(int,int)>dfs=[&](int start,int n){if(n==5){for(int i=0;i<5;++i)out[i]=p[ch[i]];return true;}if((int)p.size()-start<5-n)return false;for(int i=start;i<(int)p.size();++i){bool ok=true;for(int j=0;j<n;++j)if(adj(p[i],p[ch[j]])){ok=false;break;}if(!ok)continue;ch[n]=i;if(dfs(i+1,n+1))return true;}return false;};return dfs(0,0);
}
void append2(std::vector<std::uint32_t>&p,const std::unordered_map<std::uint64_t,std::vector<std::uint32_t>>&m,std::uint64_t k){auto it=m.find(k);if(it!=m.end())p.insert(p.end(),it->second.begin(),it->second.end());}
void append3(std::vector<std::uint32_t>&p,const std::unordered_map<std::uint64_t,std::vector<std::uint32_t>>&m,std::uint64_t k){auto it=m.find(k);if(it!=m.end())p.insert(p.end(),it->second.begin(),it->second.end());}
struct QItem{U128 key;std::uint32_t id;};
}
int main(int argc,char**argv){try{
 if(argc!=2){std::cerr<<"usage: search4 BASELINE_IDS\n";return 2;}auto base=load(argv[1]);std::unordered_set<std::uint32_t>bset(base.begin(),base.end());
 std::vector<std::uint16_t>cnt(U,0),tmp16(U,0);for(auto id:base)cnt[id]=1;transform<std::uint16_t,Op::Sum>(cnt,tmp16,"count");tmp16.clear();tmp16.shrink_to_fit();
 std::vector<std::uint32_t>mn(U,INF),tm32(U,INF);for(std::uint32_t i=0;i<base.size();++i)mn[base[i]]=i+1;transform<std::uint32_t,Op::Min>(mn,tm32,"min");tm32.clear();tm32.shrink_to_fit();
 std::vector<std::uint32_t>mx(U,0),tx(U,0);for(std::uint32_t i=0;i<base.size();++i)mx[base[i]]=i+1;transform<std::uint32_t,Op::Max>(mx,tx,"max");tx.clear();tx.shrink_to_fit();
 std::vector<std::uint32_t>sum(U,0),ts(U,0);for(std::uint32_t i=0;i<base.size();++i)sum[base[i]]=i+1;transform<std::uint32_t,Op::Sum>(sum,ts,"sum");ts.clear();ts.shrink_to_fit();
 std::vector<std::uint64_t>sq(U,0),tq(U,0);for(std::uint64_t i=0;i<base.size();++i)sq[base[i]]=(i+1)*(i+1);transform<std::uint64_t,Op::Sum>(sq,tq,"sumsq");tq.clear();tq.shrink_to_fit();

 std::vector<std::vector<std::uint32_t>>c1(base.size());std::unordered_map<std::uint64_t,std::vector<std::uint32_t>>c2,c3;c2.reserve(160000);c3.reserve(1100000);std::vector<QItem>c4;c4.reserve(2300000);std::uint64_t n1=0,n2=0,n3=0,n4=0;
 for(std::uint32_t id=0;id<U;++id){int c=cnt[id];if(c<1||c>4)continue;auto lo=mn[id],hi=mx[id];if(c==1){if(bset.count(id))continue;if(lo==0||lo==INF||lo>base.size())throw std::runtime_error("bad c1");c1[lo-1].push_back(id);++n1;}else if(c==2){if(lo==0||lo==INF||hi<=lo||hi>base.size())throw std::runtime_error("bad c2");c2[pk(lo-1,hi-1)].push_back(id);++n2;}else if(c==3){std::uint64_t mid=std::uint64_t(sum[id])-lo-hi;if(mid==0||mid>base.size()||mid==lo||mid==hi)throw std::runtime_error("bad c3");c3[tk(lo-1,mid-1,hi-1)].push_back(id);++n3;}else{
   std::uint64_t mids=std::uint64_t(sum[id])-lo-hi;std::uint64_t midq=sq[id]-std::uint64_t(lo)*lo-std::uint64_t(hi)*hi;std::uint64_t disc=2*midq-mids*mids;auto dif=isqrt(disc);if(dif*dif!=disc||(mids<dif)||((mids-dif)&1))throw std::runtime_error("bad c4 discriminant");std::uint64_t b=(mids-dif)/2,cx=(mids+dif)/2;if(b==0||cx==0||b>=cx||cx>=hi||b<=lo||cx>base.size())throw std::runtime_error("bad c4 middle");c4.push_back({qk(lo-1,b-1,cx-1,hi-1),id});++n4;
 }}
 std::cerr<<"coverage low: "<<n1<<","<<n2<<","<<n3<<","<<n4<<"\n";cnt.clear();cnt.shrink_to_fit();mn.clear();mn.shrink_to_fit();mx.clear();mx.shrink_to_fit();sum.clear();sum.shrink_to_fit();sq.clear();sq.shrink_to_fit();
 std::sort(c4.begin(),c4.end(),[](const QItem&a,const QItem&b){return a.key<b.key||(a.key==b.key&&a.id<b.id);});
 std::size_t pos=0,maxpool=0;std::uint64_t groups=0,eligible=0;
 while(pos<c4.size()){auto key=c4[pos].key;size_t end=pos+1;while(end<c4.size()&&c4[end].key==key)++end;++groups;auto o=qun(key);std::vector<std::uint32_t>pool;pool.reserve(32);for(size_t i=pos;i<end;++i)pool.push_back(c4[i].id);
  for(int omit=0;omit<4;++omit){std::array<std::uint32_t,3>t{};int q=0;for(int i=0;i<4;++i)if(i!=omit)t[q++]=o[i];append3(pool,c3,tk(t[0],t[1],t[2]));}
  for(int i=0;i<4;++i)for(int j=i+1;j<4;++j)append2(pool,c2,pk(o[i],o[j]));
  for(auto a:o)pool.insert(pool.end(),c1[a].begin(),c1[a].end());std::sort(pool.begin(),pool.end());pool.erase(std::unique(pool.begin(),pool.end()),pool.end());maxpool=std::max(maxpool,pool.size());if(pool.size()>=5){++eligible;std::array<std::uint32_t,5>add{};if(independent5(pool,add)){std::cerr<<"FOUND groups="<<groups<<" pool="<<pool.size()<<"\n";std::cout<<"{\"kind\":\"bulk\",\"method\":\"exact-4-for-5\",\"baseline_size\":"<<base.size()<<",\"remove\":["<<base[o[0]]<<','<<base[o[1]]<<','<<base[o[2]]<<','<<base[o[3]]<<"],\"add\":["<<add[0]<<','<<add[1]<<','<<add[2]<<','<<add[3]<<','<<add[4]<<"],\"owner_indices\":["<<o[0]<<','<<o[1]<<','<<o[2]<<','<<o[3]<<"]}\n";return 0;}}
  pos=end;
 }
 std::cerr<<"NONE groups="<<groups<<" eligible="<<eligible<<" maxpool="<<maxpool<<"\n";std::cout<<"{\"kind\":\"none\",\"method\":\"exact-4-for-5\",\"baseline_size\":"<<base.size()<<",\"cov1\":"<<n1<<",\"cov2\":"<<n2<<",\"cov3\":"<<n3<<",\"cov4\":"<<n4<<",\"quad_groups\":"<<groups<<",\"eligible_groups\":"<<eligible<<",\"max_pool\":"<<maxpool<<"}\n";return 0;
}catch(const std::exception&e){std::cerr<<"error: "<<e.what()<<"\n";return 1;}}
