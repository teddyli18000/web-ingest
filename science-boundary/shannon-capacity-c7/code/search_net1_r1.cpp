#include <algorithm>
#include <array>
#include <chrono>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <unordered_set>
#include <vector>

#ifdef _OPENMP
#include <omp.h>
#endif

namespace {
constexpr int D=10;
constexpr std::uint32_t POW7[D+1]={1u,7u,49u,343u,2401u,16807u,117649u,823543u,5764801u,40353607u,282475249u};
constexpr std::uint32_t N=POW7[D], GROUPS=N/7u;
using Clock=std::chrono::steady_clock;
enum class Op { Sum, Xor };

double sec(Clock::time_point t){return std::chrono::duration<double>(Clock::now()-t).count();}

template<class T,Op op>
void transform(std::vector<T>&a,std::vector<T>&b,const char*label){
 for(int dim=0;dim<D;++dim){
  const std::uint32_t stride=POW7[dim]; const std::uint64_t block=(std::uint64_t)stride*7u;
  auto t=Clock::now();
  #pragma omp parallel for schedule(static)
  for(std::int64_t gg=0;gg<(std::int64_t)GROUPS;++gg){
   std::uint64_t g=(std::uint64_t)gg, block_no=g/stride; std::uint32_t off=(std::uint32_t)(g%stride);
   std::uint64_t base=block_no*block+off; T v[7];
   for(int k=0;k<7;++k)v[k]=a[base+(std::uint64_t)k*stride];
   for(int k=0;k<7;++k){
    T l=v[(k+6)%7],m=v[k],r=v[(k+1)%7];
    if constexpr(op==Op::Sum)b[base+(std::uint64_t)k*stride]=(T)(l+m+r);
    else b[base+(std::uint64_t)k*stride]=l^m^r;
   }
  }
  a.swap(b); std::cerr<<label<<" dim="<<dim<<" sec="<<sec(t)<<"\n";
 }
}

std::vector<std::uint32_t> load_ids(const std::string&path){
 std::ifstream in(path); if(!in)throw std::runtime_error("cannot open baseline ids");
 std::vector<std::uint32_t> v; std::uint64_t x;
 while(in>>x){if(x>=N)throw std::runtime_error("id out of range");v.push_back((std::uint32_t)x);}
 if(v.empty())throw std::runtime_error("empty baseline");
 std::unordered_set<std::uint32_t>s; s.reserve(v.size()*2);
 for(auto x:v)if(!s.insert(x).second)throw std::runtime_error("duplicate baseline id");
 return v;
}

bool adjacent(std::uint32_t a,std::uint32_t b){
 if(a==b)return true;
 for(int d=0;d<D;++d){int da=a%7u,db=b%7u;a/=7u;b/=7u;int z=(da-db+7)%7;if(z!=0&&z!=1&&z!=6)return false;}
 return true;
}
}

int main(int argc,char**argv){
 try{
  if(argc!=2){std::cerr<<"usage: search_net1_r1 BASELINE_IDS\n";return 2;}
  auto all=Clock::now(); auto base=load_ids(argv[1]);
  std::cerr<<"vertices="<<N<<" baseline="<<base.size();
#ifdef _OPENMP
  std::cerr<<" omp_threads="<<omp_get_max_threads();
#endif
  std::cerr<<"\n";
  std::unordered_set<std::uint32_t> bset; bset.reserve(base.size()*2); for(auto x:base)bset.insert(x);

  std::vector<std::uint16_t> count(N,0), scratch16(N,0); for(auto x:base)count[x]=1;
  transform<std::uint16_t,Op::Sum>(count,scratch16,"count"); scratch16.clear();scratch16.shrink_to_fit();
  std::uint64_t cov0=0,cov1n=0;
  for(std::uint32_t id=0;id<N;++id){
   if(bset.contains(id))continue;
   if(count[id]==0){++cov0;std::cout<<"{\"kind\":\"direct\",\"add\":"<<id<<",\"baseline_size\":"<<base.size()<<"}\n";return 0;}
   if(count[id]==1)++cov1n;
  }

  std::vector<std::uint32_t>xors(N,0),scratch32(N,0); for(std::uint32_t i=0;i<base.size();++i)xors[base[i]]=i+1u;
  transform<std::uint32_t,Op::Xor>(xors,scratch32,"xor"); scratch32.clear();scratch32.shrink_to_fit();
  std::vector<std::vector<std::uint32_t>> groups(base.size());
  for(std::uint32_t id=0;id<N;++id){
   if(count[id]!=1||bset.contains(id))continue;
   auto o=xors[id]; if(o==0||o>base.size())throw std::runtime_error("bad coverage1 owner"); groups[o-1].push_back(id);
  }
  std::uint64_t pairs=0; std::size_t maxg=0; std::uint32_t best_owner=0;
  for(std::uint32_t o=0;o<groups.size();++o){
   auto&g=groups[o]; if(g.size()>maxg){maxg=g.size();best_owner=o;}
   for(std::size_t i=0;i<g.size();++i)for(std::size_t j=i+1;j<g.size();++j){
    ++pairs; if(adjacent(g[i],g[j]))continue;
    std::cout<<"{\"kind\":\"replace1\",\"remove_index\":"<<o<<",\"remove\":"<<base[o]
             <<",\"add\":["<<g[i]<<","<<g[j]<<"],\"baseline_size\":"<<base.size()<<"}\n";return 0;
   }
  }
  std::cout<<"{\"kind\":\"none\",\"baseline_size\":"<<base.size()<<",\"outside_coverage0\":"<<cov0
           <<",\"outside_coverage1\":"<<cov1n<<",\"max_coverage1_group\":"<<maxg
           <<",\"max_group_owner_index\":"<<best_owner<<",\"coverage1_pairs_checked\":"<<pairs
           <<",\"seconds\":"<<sec(all)<<"}\n";
  return 0;
 }catch(const std::exception&e){std::cerr<<"error: "<<e.what()<<"\n";return 1;}
}
