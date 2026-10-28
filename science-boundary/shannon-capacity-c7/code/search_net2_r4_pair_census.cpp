// Census productive two-owner pools for a future exact remove4/add6 search.
// Assumes/validates coverage0=0 and records which genuine coverage-2 owner
// edges have a two-owner candidate pool containing an independent triple.
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
constexpr int D=10; constexpr std::uint32_t P7[D+1]={1u,7u,49u,343u,2401u,16807u,117649u,823543u,5764801u,40353607u,282475249u}; constexpr std::uint32_t N=P7[D],GROUPS=N/7u,INF=0xffffffffu; constexpr unsigned BITS=18; enum class Op{Sum,Xor,Min,Max};
template<class T,Op op>void transform(std::vector<T>&a,std::vector<T>&b,const char*name){for(int dim=0;dim<D;++dim){const auto s=P7[dim];const std::uint64_t block=std::uint64_t(s)*7u;
#pragma omp parallel for schedule(static)
for(std::int64_t gg=0;gg<(std::int64_t)GROUPS;++gg){const std::uint64_t g=gg,bn=g/s;const std::uint32_t off=g%s;const std::uint64_t base=bn*block+off;T v[7];for(int k=0;k<7;++k)v[k]=a[base+std::uint64_t(k)*s];for(int k=0;k<7;++k){T l=v[(k+6)%7],m=v[k],r=v[(k+1)%7],z{};if constexpr(op==Op::Sum)z=T(l+m+r);else if constexpr(op==Op::Xor)z=T(l^m^r);else if constexpr(op==Op::Min)z=std::min(l,std::min(m,r));else z=std::max(l,std::max(m,r));b[base+std::uint64_t(k)*s]=z;}}a.swap(b);std::cerr<<name<<" dim="<<dim<<"\n";}}
std::vector<std::uint32_t>load(const std::string&p){std::ifstream in(p);if(!in)throw std::runtime_error("ids");std::vector<std::uint32_t>a;std::uint64_t x;while(in>>x){if(x>=N)throw std::runtime_error("range");a.push_back((std::uint32_t)x);}std::sort(a.begin(),a.end());if(std::adjacent_find(a.begin(),a.end())!=a.end())throw std::runtime_error("dup");return a;}
bool conflict(std::uint32_t a,std::uint32_t b){if(a==b)return true;for(int d=0;d<D;++d){int x=a%7u,y=b%7u;a/=7u;b/=7u;int z=(x-y+7)%7;if(z!=0&&z!=1&&z!=6)return false;}return true;}
std::uint64_t key(std::uint32_t a,std::uint32_t b){if(a>b)std::swap(a,b);return(std::uint64_t(a)<<BITS)|b;}
std::pair<std::uint32_t,std::uint32_t>unkey(std::uint64_t k){return{std::uint32_t(k>>BITS),std::uint32_t(k&((1u<<BITS)-1))};}
}
int main(int argc,char**argv){try{if(argc!=2){std::cerr<<"usage: census IDS\n";return 2;}auto base=load(argv[1]);std::unordered_set<std::uint32_t>bset(base.begin(),base.end());std::vector<std::uint16_t>cnt(N,0),t16(N,0);for(auto v:base)cnt[v]=1;transform<std::uint16_t,Op::Sum>(cnt,t16,"count");t16.clear();t16.shrink_to_fit();std::vector<std::uint32_t>c1,c2;c1.reserve(10000);c2.reserve(200000);std::uint64_t c0=0;for(std::uint32_t v=0;v<N;++v){if(cnt[v]==0)++c0;else if(cnt[v]==1&&!bset.count(v))c1.push_back(v);else if(cnt[v]==2)c2.push_back(v);}if(c0)throw std::runtime_error("coverage0 nonzero");cnt.clear();cnt.shrink_to_fit();
std::vector<std::uint32_t>xo(N,0),tx(N,0);for(std::uint32_t i=0;i<base.size();++i)xo[base[i]]=i+1;transform<std::uint32_t,Op::Xor>(xo,tx,"xor");tx.clear();tx.shrink_to_fit();std::vector<std::vector<std::uint32_t>>g1(base.size());for(auto v:c1){auto o=xo[v];if(!o||o>base.size())throw std::runtime_error("c1 owner");g1[o-1].push_back(v);}xo.clear();xo.shrink_to_fit();
std::vector<std::uint32_t>mn(N,INF),tm(N,INF);for(std::uint32_t i=0;i<base.size();++i)mn[base[i]]=i+1;transform<std::uint32_t,Op::Min>(mn,tm,"min");tm.clear();tm.shrink_to_fit();std::vector<std::uint32_t>lo;lo.reserve(c2.size());for(auto v:c2)lo.push_back(mn[v]);mn.clear();mn.shrink_to_fit();std::vector<std::uint32_t>mx(N,0),tt(N,0);for(std::uint32_t i=0;i<base.size();++i)mx[base[i]]=i+1;transform<std::uint32_t,Op::Max>(mx,tt,"max");tt.clear();tt.shrink_to_fit();std::unordered_map<std::uint64_t,std::vector<std::uint32_t>>g2;g2.reserve(180000);for(std::size_t i=0;i<c2.size();++i){auto a=lo[i],b=mx[c2[i]];if(!a||a==INF||!b||a>=b||b>base.size())throw std::runtime_error("c2 owner");g2[key(a-1,b-1)].push_back(c2[i]);}mx.clear();mx.shrink_to_fit();lo.clear();lo.shrink_to_fit();
std::uint64_t productive=0,total_triples=0;std::size_t max_pool=0,max_triples=0;std::vector<std::uint64_t>examples;
for(const auto&kv:g2){auto [a,b]=unkey(kv.first);std::vector<std::uint32_t>p;p.reserve(g1[a].size()+g1[b].size()+kv.second.size());p.insert(p.end(),g1[a].begin(),g1[a].end());p.insert(p.end(),g1[b].begin(),g1[b].end());p.insert(p.end(),kv.second.begin(),kv.second.end());std::sort(p.begin(),p.end());p.erase(std::unique(p.begin(),p.end()),p.end());max_pool=std::max(max_pool,p.size());std::size_t triples=0;for(std::size_t i=0;i<p.size();++i)for(std::size_t j=i+1;j<p.size();++j){if(conflict(p[i],p[j]))continue;for(std::size_t k=j+1;k<p.size();++k)if(!conflict(p[i],p[k])&&!conflict(p[j],p[k]))++triples;}if(triples){++productive;total_triples+=triples;max_triples=std::max(max_triples,triples);if(examples.size()<20)examples.push_back(kv.first);}}
std::cout<<"{\"method\":\"r4-productive-two-owner-census\",\"baseline_size\":"<<base.size()<<",\"coverage0\":0,\"coverage1\":"<<c1.size()<<",\"coverage2\":"<<c2.size()<<",\"coverage2_groups\":"<<g2.size()<<",\"productive_edges_alpha3\":"<<productive<<",\"independent_triples_total\":"<<total_triples<<",\"max_pool\":"<<max_pool<<",\"max_triples_per_edge\":"<<max_triples<<",\"example_edge_keys\":[";for(std::size_t i=0;i<examples.size();++i)std::cout<<(i?",":"")<<examples[i];std::cout<<"]}\n";return 0;}catch(const std::exception&e){std::cerr<<"error: "<<e.what()<<"\n";return 1;}}
