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
constexpr std::uint32_t N=P7[D],GROUPS=N/7u,INF=0xffffffffu;
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
std::uint64_t key(std::uint32_t a,std::uint32_t b){if(a>b)std::swap(a,b);return(std::uint64_t(a)<<BITS)|b;}
std::pair<std::uint32_t,std::uint32_t> unkey(std::uint64_t k){return{std::uint32_t(k>>BITS),std::uint32_t(k&((1u<<BITS)-1))};}

bool find4(const std::vector<std::uint32_t>&supp,const std::vector<std::uint32_t>&freev,std::array<std::uint32_t,4>&out){
 // Caller has already proved freev contains no compatible pair, so an
 // independent four-set uses either four supported vertices or three plus one free.
 for(std::size_t i=0;i<supp.size();++i)for(std::size_t j=i+1;j<supp.size();++j){if(conflict(supp[i],supp[j]))continue;
  for(std::size_t k=j+1;k<supp.size();++k){if(conflict(supp[i],supp[k])||conflict(supp[j],supp[k]))continue;
   for(auto z:freev)if(!conflict(supp[i],z)&&!conflict(supp[j],z)&&!conflict(supp[k],z)){out={supp[i],supp[j],supp[k],z};return true;}
   for(std::size_t l=k+1;l<supp.size();++l)if(!conflict(supp[i],supp[l])&&!conflict(supp[j],supp[l])&&!conflict(supp[k],supp[l])){out={supp[i],supp[j],supp[k],supp[l]};return true;}
  }
 }
 return false;
}
}

int main(int argc,char**argv){try{
 if(argc!=2){std::cerr<<"usage: search_net2_r2 BASELINE_IDS\n";return 2;}auto base=load_ids(argv[1]);std::unordered_set<std::uint32_t>bset(base.begin(),base.end());
 // Coverage classes.
 std::vector<std::uint16_t>cnt(N,0),t16(N,0);for(auto v:base)cnt[v]=1;transform<std::uint16_t,Op::Sum>(cnt,t16,"count");t16.clear();t16.shrink_to_fit();
 std::vector<std::uint32_t>freev,c1ids,c2ids;freev.reserve(2048);c1ids.reserve(10000);c2ids.reserve(200000);
 for(std::uint32_t v=0;v<N;++v){if(cnt[v]==0)freev.push_back(v);else if(cnt[v]==1&&!bset.count(v))c1ids.push_back(v);else if(cnt[v]==2)c2ids.push_back(v);}
 // Direct +2 settles support-union size zero.
 for(std::size_t i=0;i<freev.size();++i)for(std::size_t j=i+1;j<freev.size();++j)if(!conflict(freev[i],freev[j])){std::cout<<"{\"kind\":\"add2\",\"baseline_size\":"<<base.size()<<",\"coverage0\":"<<freev.size()<<",\"add\":["<<freev[i]<<','<<freev[j]<<"]}\n";return 0;}
 cnt.clear();cnt.shrink_to_fit();
 // Unique owner of coverage-one vertices.
 std::vector<std::uint32_t>xo(N,0),tx(N,0);for(std::uint32_t i=0;i<base.size();++i)xo[base[i]]=i+1;transform<std::uint32_t,Op::Xor>(xo,tx,"xor");tx.clear();tx.shrink_to_fit();
 std::vector<std::vector<std::uint32_t>>g1(base.size());for(auto v:c1ids){auto o=xo[v];if(!o||o>base.size())throw std::runtime_error("bad c1 owner");g1[o-1].push_back(v);}xo.clear();xo.shrink_to_fit();
 // Exact owner pairs of coverage-two vertices, materializing extrema one pass at a time.
 std::vector<std::uint32_t>mn(N,INF),tm(N,INF);for(std::uint32_t i=0;i<base.size();++i)mn[base[i]]=i+1;transform<std::uint32_t,Op::Min>(mn,tm,"min");tm.clear();tm.shrink_to_fit();std::vector<std::uint32_t>lo;lo.reserve(c2ids.size());for(auto v:c2ids)lo.push_back(mn[v]);mn.clear();mn.shrink_to_fit();
 std::vector<std::uint32_t>mx(N,0),tmax(N,0);for(std::uint32_t i=0;i<base.size();++i)mx[base[i]]=i+1;transform<std::uint32_t,Op::Max>(mx,tmax,"max");tmax.clear();tmax.shrink_to_fit();
 std::unordered_map<std::uint64_t,std::vector<std::uint32_t>>g2;g2.reserve(180000);for(std::size_t i=0;i<c2ids.size();++i){auto a=lo[i],b=mx[c2ids[i]];if(!a||a==INF||!b||b==INF||a>=b||b>base.size())throw std::runtime_error("bad c2 owners");g2[key(a-1,b-1)].push_back(c2ids[i]);}mx.clear();mx.shrink_to_fit();lo.clear();lo.shrink_to_fit();

 // Before radius two, settle support-union size one exactly. Since freev is a
 // clique, a 1-remove/3-add witness requires >=2 owner-one candidates.
 for(std::uint32_t a=0;a<g1.size();++a){auto &g=g1[a];if(g.size()<2)continue;for(std::size_t i=0;i<g.size();++i)for(std::size_t j=i+1;j<g.size();++j){if(conflict(g[i],g[j]))continue;for(auto z:freev)if(!conflict(g[i],z)&&!conflict(g[j],z)){std::cout<<"{\"kind\":\"replace1add3\",\"baseline_size\":"<<base.size()<<",\"remove\":["<<base[a]<<"],\"add\":["<<g[i]<<','<<g[j]<<','<<z<<"]}\n";return 0;}for(std::size_t k=j+1;k<g.size();++k)if(!conflict(g[i],g[k])&&!conflict(g[j],g[k])){std::cout<<"{\"kind\":\"replace1add3\",\"baseline_size\":"<<base.size()<<",\"remove\":["<<base[a]<<"],\"add\":["<<g[i]<<','<<g[j]<<','<<g[k]<<"]}\n";return 0;}}}

 std::unordered_set<std::uint64_t>done;done.reserve(g2.size()*2+1024);std::uint64_t pairs_checked=0,eligible_pairs=0;std::size_t maxsupp=0;std::array<std::uint32_t,4>add{};
 auto check_pair=[&](std::uint32_t a,std::uint32_t b)->bool{if(a==b)return false;auto k=key(a,b);if(!done.insert(k).second)return false;auto [x,y]=unkey(k);std::vector<std::uint32_t>supp;supp.reserve(g1[x].size()+g1[y].size()+8);supp.insert(supp.end(),g1[x].begin(),g1[x].end());supp.insert(supp.end(),g1[y].begin(),g1[y].end());auto it=g2.find(k);if(it!=g2.end())supp.insert(supp.end(),it->second.begin(),it->second.end());std::sort(supp.begin(),supp.end());supp.erase(std::unique(supp.begin(),supp.end()),supp.end());++pairs_checked;maxsupp=std::max(maxsupp,supp.size());if(supp.size()<3)return false;++eligible_pairs;if(find4(supp,freev,add)){std::cout<<"{\"kind\":\"replace2add4\",\"method\":\"exact-unrestricted-r2-net2\",\"baseline_size\":"<<base.size()<<",\"coverage0\":"<<freev.size()<<",\"coverage1\":"<<c1ids.size()<<",\"coverage2\":"<<c2ids.size()<<",\"remove\":["<<base[x]<<','<<base[y]<<"],\"add\":["<<add[0]<<','<<add[1]<<','<<add[2]<<','<<add[3]<<"]}\n";return true;}return false;};
 // Every coverage-two support induces its owner pair.
 for(const auto&kv:g2){auto [a,b]=unkey(kv.first);if(check_pair(a,b))return 0;}
 // If no coverage-two candidate is selected, a genuine two-owner witness must
 // draw supported candidates from both nonempty coverage-one owner groups.
 std::vector<std::uint32_t>active;for(std::uint32_t a=0;a<g1.size();++a)if(!g1[a].empty())active.push_back(a);
 for(std::size_t i=0;i<active.size();++i)for(std::size_t j=i+1;j<active.size();++j){auto a=active[i],b=active[j];if(g1[a].size()+g1[b].size()<3)continue;if(check_pair(a,b))return 0;}
 std::cout<<"{\"kind\":\"none\",\"method\":\"exact-unrestricted-r2-net2\",\"baseline_size\":"<<base.size()<<",\"coverage0\":"<<freev.size()<<",\"coverage1\":"<<c1ids.size()<<",\"coverage2\":"<<c2ids.size()<<",\"owner_pairs_checked\":"<<pairs_checked<<",\"eligible_pairs\":"<<eligible_pairs<<",\"max_supported_pool\":"<<maxsupp<<"}\n";return 0;
}catch(const std::exception&e){std::cerr<<"error: "<<e.what()<<"\n";return 1;}}
