#include <algorithm>
#include <array>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

#ifdef _OPENMP
#include <omp.h>
#endif

namespace {
constexpr int D=10;
constexpr std::uint32_t P7[D+1]={1u,7u,49u,343u,2401u,16807u,117649u,823543u,5764801u,40353607u,282475249u};
constexpr std::uint32_t N=P7[D], GROUPS=N/7u;

template<class T>
void sum_transform(std::vector<T>&a,std::vector<T>&b){
    for(int dim=0;dim<D;++dim){
        const auto s=P7[dim]; const std::uint64_t block=std::uint64_t(s)*7u;
        #pragma omp parallel for schedule(static)
        for(std::int64_t gg=0;gg<(std::int64_t)GROUPS;++gg){
            const std::uint64_t g=gg,bn=g/s; const std::uint32_t off=g%s; const std::uint64_t base=bn*block+off;
            T v[7]; for(int k=0;k<7;++k)v[k]=a[base+std::uint64_t(k)*s];
            for(int k=0;k<7;++k)b[base+std::uint64_t(k)*s]=T(v[(k+6)%7]+v[k]+v[(k+1)%7]);
        }
        a.swap(b); std::cerr<<"count dim="<<dim<<"\n";
    }
}

std::vector<std::uint32_t> load_ids(const std::string&p){
    std::ifstream in(p); if(!in)throw std::runtime_error("cannot open ids");
    std::vector<std::uint32_t>a; std::uint64_t x;
    while(in>>x){if(x>=N)throw std::runtime_error("id range");a.push_back((std::uint32_t)x);}
    if(a.empty())throw std::runtime_error("empty baseline");
    std::sort(a.begin(),a.end()); if(std::adjacent_find(a.begin(),a.end())!=a.end())throw std::runtime_error("duplicate baseline id");
    return a;
}

bool conflict(std::uint32_t a,std::uint32_t b){
    if(a==b)return true;
    for(int d=0;d<D;++d){int x=a%7u,y=b%7u;a/=7u;b/=7u;int z=(x-y+7)%7;if(z!=0&&z!=1&&z!=6)return false;}
    return true;
}
}

int main(int argc,char**argv){
    try{
        if(argc!=2){std::cerr<<"usage: search_add2 BASELINE_IDS\n";return 2;}
        auto base=load_ids(argv[1]);
        std::vector<std::uint16_t> cnt(N,0),tmp(N,0);
        for(auto v:base)cnt[v]=1;
        sum_transform(cnt,tmp); tmp.clear(); tmp.shrink_to_fit();
        std::vector<std::uint32_t> freev; freev.reserve(65536);
        for(std::uint32_t v=0;v<N;++v)if(cnt[v]==0)freev.push_back(v);
        cnt.clear();cnt.shrink_to_fit();
        std::cerr<<"baseline="<<base.size()<<" coverage0="<<freev.size()<<"\n";
        for(std::size_t i=0;i<freev.size();++i){
            for(std::size_t j=i+1;j<freev.size();++j){
                if(!conflict(freev[i],freev[j])){
                    std::cout<<"{\"kind\":\"add2\",\"baseline_size\":"<<base.size()<<",\"coverage0\":"<<freev.size()<<",\"add\":["<<freev[i]<<','<<freev[j]<<"]}\n";
                    return 0;
                }
            }
        }
        std::cout<<"{\"kind\":\"none\",\"baseline_size\":"<<base.size()<<",\"coverage0\":"<<freev.size()<<"}\n";
        return 0;
    }catch(const std::exception&e){std::cerr<<"error: "<<e.what()<<"\n";return 1;}
}
