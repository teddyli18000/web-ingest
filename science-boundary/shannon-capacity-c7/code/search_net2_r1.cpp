#include <algorithm>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <unordered_set>
#include <vector>

#ifdef _OPENMP
#include <omp.h>
#endif

namespace {
constexpr int D=10;
constexpr std::uint32_t P7[D+1]={1u,7u,49u,343u,2401u,16807u,117649u,823543u,5764801u,40353607u,282475249u};
constexpr std::uint32_t N=P7[D], GROUPS=N/7u;

enum class Op{Sum,Xor};
template<class T,Op op>
void transform(std::vector<T>&a,std::vector<T>&b,const char*name){
    for(int dim=0;dim<D;++dim){
        const auto s=P7[dim];const std::uint64_t block=std::uint64_t(s)*7u;
        #pragma omp parallel for schedule(static)
        for(std::int64_t gg=0;gg<(std::int64_t)GROUPS;++gg){
            const std::uint64_t g=gg,bn=g/s;const std::uint32_t off=g%s;const std::uint64_t base=bn*block+off;
            T v[7];for(int k=0;k<7;++k)v[k]=a[base+std::uint64_t(k)*s];
            for(int k=0;k<7;++k){
                if constexpr(op==Op::Sum)b[base+std::uint64_t(k)*s]=T(v[(k+6)%7]+v[k]+v[(k+1)%7]);
                else b[base+std::uint64_t(k)*s]=T(v[(k+6)%7]^v[k]^v[(k+1)%7]);
            }
        }
        a.swap(b);std::cerr<<name<<" dim="<<dim<<"\n";
    }
}
std::vector<std::uint32_t> load_ids(const std::string&p){
    std::ifstream in(p);if(!in)throw std::runtime_error("cannot open ids");std::vector<std::uint32_t>a;std::uint64_t x;
    while(in>>x){if(x>=N)throw std::runtime_error("id range");a.push_back((std::uint32_t)x);}
    if(a.empty())throw std::runtime_error("empty baseline");std::sort(a.begin(),a.end());if(std::adjacent_find(a.begin(),a.end())!=a.end())throw std::runtime_error("duplicate baseline");return a;
}
bool conflict(std::uint32_t a,std::uint32_t b){
    if(a==b)return true;
    for(int d=0;d<D;++d){int x=a%7u,y=b%7u;a/=7u;b/=7u;int z=(x-y+7)%7;if(z!=0&&z!=1&&z!=6)return false;}
    return true;
}
}

int main(int argc,char**argv){
    try{
        if(argc!=2){std::cerr<<"usage: search_net2_r1 BASELINE_IDS\n";return 2;}
        auto base=load_ids(argv[1]);std::unordered_set<std::uint32_t>bset(base.begin(),base.end());
        std::vector<std::uint16_t> cnt(N,0),tmp16(N,0);for(auto v:base)cnt[v]=1;transform<std::uint16_t,Op::Sum>(cnt,tmp16,"count");tmp16.clear();tmp16.shrink_to_fit();
        std::vector<std::uint32_t> freev;freev.reserve(2048);for(std::uint32_t v=0;v<N;++v)if(cnt[v]==0)freev.push_back(v);

        // First settle the stronger/easier direct +2 case exactly.
        for(std::size_t i=0;i<freev.size();++i)for(std::size_t j=i+1;j<freev.size();++j)if(!conflict(freev[i],freev[j])){
            std::cout<<"{\"kind\":\"add2\",\"baseline_size\":"<<base.size()<<",\"coverage0\":"<<freev.size()<<",\"add\":["<<freev[i]<<','<<freev[j]<<"]}\n";return 0;
        }
        // If no direct pair exists, freev is a conflict clique, so any independent
        // triple after deleting one owner contains at most one coverage-0 vertex.
        std::vector<std::uint32_t> xo(N,0),tmp32(N,0);for(std::uint32_t i=0;i<base.size();++i)xo[base[i]]=i+1u;transform<std::uint32_t,Op::Xor>(xo,tmp32,"xor");tmp32.clear();tmp32.shrink_to_fit();
        std::vector<std::vector<std::uint32_t>> g(base.size());std::uint64_t n1=0;
        for(std::uint32_t v=0;v<N;++v){if(cnt[v]!=1||bset.count(v))continue;auto o=xo[v];if(o==0||o>base.size())throw std::runtime_error("bad coverage1 owner");g[o-1].push_back(v);++n1;}
        cnt.clear();cnt.shrink_to_fit();xo.clear();xo.shrink_to_fit();
        std::size_t owners2=0,maxg=0;std::uint64_t pair_checks=0;
        for(std::uint32_t o=0;o<g.size();++o){auto &a=g[o];maxg=std::max(maxg,a.size());if(a.size()<2)continue;++owners2;
            for(std::size_t i=0;i<a.size();++i)for(std::size_t j=i+1;j<a.size();++j){++pair_checks;if(conflict(a[i],a[j]))continue;
                // Two owner-1 candidates plus one globally free candidate.
                for(auto z:freev)if(!conflict(a[i],z)&&!conflict(a[j],z)){
                    std::cout<<"{\"kind\":\"replace1add3\",\"method\":\"exact-unrestricted-r1-net2\",\"baseline_size\":"<<base.size()<<",\"coverage0\":"<<freev.size()<<",\"coverage1\":"<<n1<<",\"remove\":["<<base[o]<<"],\"add\":["<<a[i]<<','<<a[j]<<','<<z<<"]}\n";return 0;
                }
                // Or a third candidate owned by the same removed point.
                for(std::size_t k=j+1;k<a.size();++k)if(!conflict(a[i],a[k])&&!conflict(a[j],a[k])){
                    std::cout<<"{\"kind\":\"replace1add3\",\"method\":\"exact-unrestricted-r1-net2\",\"baseline_size\":"<<base.size()<<",\"coverage0\":"<<freev.size()<<",\"coverage1\":"<<n1<<",\"remove\":["<<base[o]<<"],\"add\":["<<a[i]<<','<<a[j]<<','<<a[k]<<"]}\n";return 0;
                }
            }
        }
        std::cout<<"{\"kind\":\"none\",\"method\":\"exact-unrestricted-r1-net2\",\"baseline_size\":"<<base.size()<<",\"coverage0\":"<<freev.size()<<",\"coverage1\":"<<n1<<",\"owners_with_ge2\":"<<owners2<<",\"max_group\":"<<maxg<<",\"pair_checks\":"<<pair_checks<<"}\n";
        return 0;
    }catch(const std::exception&e){std::cerr<<"error: "<<e.what()<<"\n";return 1;}
}
