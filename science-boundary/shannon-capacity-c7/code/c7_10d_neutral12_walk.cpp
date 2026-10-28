// Heuristic plateau walk on a 134753-point independent set in C7^10 using
// both neutral 1-for-1 and genuinely two-owner 2-for-2 exchanges.
//
// The 1-for-1 move uses an outside coverage-one vertex y and replaces its
// unique owner x. Before moving, the whole one-owner pool is checked exactly
// for a compatible pair, which would give x->{y,z} and score 134754.
//
// The 2-for-2 move starts from an outside coverage-two vertex y with owners
// {a,b}. The complete current two-owner pool P({a,b}) is reconstructed from
// coverage-one candidates owned by a/b and coverage-two candidates whose two
// blockers are exactly a,b. Before any neutral move, that small pool is checked
// exactly for an independent triple; such a triple gives {a,b}->3 additions
// and score 134754. Otherwise an independent pair containing y yields a legal
// neutral 2-for-2 plateau move. Because y has coverage two before deletion,
// these moves need not factor through legal 1-for-1 plateau states.
//
// All coverage counts and owner XORs are maintained exactly and incrementally.
// Negative walks are heuristic evidence only. Any emitted candidate is replayed
// by the Few Shots verifier in the workflow.
#include <algorithm>
#include <array>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <limits>
#include <random>
#include <stdexcept>
#include <vector>
#ifdef _OPENMP
#include <omp.h>
#endif
namespace{
constexpr int D=10;constexpr std::uint32_t P7[D+1]={1u,7u,49u,343u,2401u,16807u,117649u,823543u,5764801u,40353607u,282475249u};constexpr std::uint32_t N=P7[D],GROUPS=N/7u;enum class Op{Sum,Xor};
template<class T,Op op>void trans(std::vector<T>&a,std::vector<T>&b){for(int d=0;d<D;++d){auto s=P7[d];std::uint64_t block=std::uint64_t(s)*7u;
#pragma omp parallel for schedule(static)
 for(std::int64_t gg=0;gg<(std::int64_t)GROUPS;++gg){std::uint64_t g=gg,bn=g/s;std::uint32_t off=g%s;std::uint64_t base=bn*block+off;T v[7];for(int k=0;k<7;++k)v[k]=a[base+std::uint64_t(k)*s];for(int k=0;k<7;++k){T l=v[(k+6)%7],m=v[k],r=v[(k+1)%7];b[base+std::uint64_t(k)*s]=op==Op::Sum?T(l+m+r):T(l^m^r);}}a.swap(b);}}
std::vector<std::uint32_t>load(const char*p){std::ifstream in(p);if(!in)throw std::runtime_error("ids");std::vector<std::uint32_t>a;std::uint64_t z;while(in>>z){if(z>=N)throw std::runtime_error("range");a.push_back(z);}std::sort(a.begin(),a.end());if(a.size()!=134753||std::adjacent_find(a.begin(),a.end())!=a.end())throw std::runtime_error("baseline");return a;}
inline bool bg(const std::vector<std::uint64_t>&b,std::uint32_t x){return(b[x>>6]>>(x&63))&1u;}inline void bs(std::vector<std::uint64_t>&b,std::uint32_t x,bool v){auto&m=b[x>>6];auto q=std::uint64_t(1)<<(x&63);if(v)m|=q;else m&=~q;}
bool cf(std::uint32_t a,std::uint32_t b){if(a==b)return true;for(int d=0;d<D;++d){int x=a%7u,y=b%7u;a/=7u;b/=7u;int z=(x-y+7)%7;if(z!=0&&z!=1&&z!=6)return false;}return true;}
void nb(std::uint32_t p,std::vector<std::uint32_t>&o){std::array<unsigned,D>d{};for(int i=0;i<D;++i){d[i]=p%7u;p/=7u;}o.clear();o.push_back(0);std::size_t n=1;for(int k=0;k<D;++k){auto old=o; o.clear();o.reserve(n*3);for(auto q:old){o.push_back(q+((d[k]+6)%7)*P7[k]);o.push_back(q+d[k]*P7[k]);o.push_back(q+((d[k]+1)%7)*P7[k]);}n*=3;}}
void write(const char*p,const std::vector<std::uint64_t>&sel,const std::vector<std::uint32_t>&rem,const std::vector<std::uint32_t>&add){std::ofstream out(p);if(!out)throw std::runtime_error("write");std::uint64_t n=0;for(std::uint32_t v=0;v<N;++v)if(bg(sel,v)&&std::find(rem.begin(),rem.end(),v)==rem.end()){out<<v<<'\n';++n;}for(auto v:add){out<<v<<'\n';++n;}if(n!=134754)throw std::runtime_error("winner size");}
bool independent3(const std::vector<std::uint32_t>&p,std::array<std::uint32_t,3>&o){for(std::size_t i=0;i<p.size();++i)for(std::size_t j=i+1;j<p.size();++j){if(cf(p[i],p[j]))continue;for(std::size_t k=j+1;k<p.size();++k)if(!cf(p[i],p[k])&&!cf(p[j],p[k])){o={p[i],p[j],p[k]};return true;}}return false;}
}
int main(int argc,char**argv)try{
 if(argc!=6){std::cerr<<"usage: c7_10d_neutral12_walk BASELINE_IDS RESULT_IDS STEPS SEED TWO_RATE\n";return 2;}auto base=load(argv[1]);std::uint64_t steps=std::stoull(argv[3]),seed=std::stoull(argv[4]);unsigned two_rate=std::stoul(argv[5]);if(!two_rate)throw std::runtime_error("two_rate");
 std::vector<std::uint16_t>cnt(N),tmp16(N);std::vector<std::uint32_t>xo(N),tmp32(N);std::vector<std::uint64_t>sel((N+63)/64);for(auto v:base){cnt[v]=1;xo[v]=v+1;bs(sel,v,true);}trans<std::uint16_t,Op::Sum>(cnt,tmp16);tmp16.clear();tmp16.shrink_to_fit();trans<std::uint32_t,Op::Xor>(xo,tmp32);tmp32.clear();tmp32.shrink_to_fit();
 // pos: >0 index+1 in c1, <0 -(index+1) in c2, 0 absent.
 std::vector<std::int32_t>pos(N);std::vector<std::uint32_t>c1,c2;c1.reserve(20000);c2.reserve(300000);
 auto erase=[&](std::uint32_t v){auto p=pos[v];if(!p)return;if(p>0){auto i=(std::uint32_t)(p-1),w=c1.back();c1[i]=w;pos[w]=i+1;c1.pop_back();}else{auto i=(std::uint32_t)(-p-1),w=c2.back();c2[i]=w;pos[w]=-(std::int32_t(i)-0+1);c2.pop_back();}pos[v]=0;};
 // Fix c2 swapped-position assignment explicitly rather than relying on signed arithmetic.
 auto erase2=[&](std::uint32_t v){auto p=pos[v];if(!p)return;if(p>0){auto i=(std::uint32_t)(p-1),w=c1.back();c1[i]=w;pos[w]=(std::int32_t)i+1;c1.pop_back();}else{auto i=(std::uint32_t)(-p-1),w=c2.back();c2[i]=w;pos[w]=-((std::int32_t)i+1);c2.pop_back();}pos[v]=0;};
 auto refresh=[&](std::uint32_t v){unsigned want=bg(sel,v)?0:(cnt[v]==1?1:cnt[v]==2?2:0);auto p=pos[v];unsigned have=p>0?1:p<0?2:0;if(want==have)return;erase2(v);if(want==1){pos[v]=(std::int32_t)c1.size()+1;c1.push_back(v);}else if(want==2){pos[v]=-((std::int32_t)c2.size()+1);c2.push_back(v);}};
 for(std::uint32_t v=0;v<N;++v){if(!bg(sel,v)&&cnt[v]==0)throw std::runtime_error("coverage0 baseline");refresh(v);}std::cerr<<"init c1="<<c1.size()<<" c2="<<c2.size()<<"\n";
 std::mt19937_64 rng(seed);std::vector<std::uint32_t>work;work.reserve(4*59049);std::array<std::uint32_t,128>tabu{};tabu.fill(N);unsigned tp=0;std::uint64_t n1=0,n2=0,failed2=0;
 auto apply=[&](const std::vector<std::uint32_t>&rem,const std::vector<std::uint32_t>&add){work.clear();std::vector<std::uint32_t>z;z.reserve(59049);for(auto x:rem){bs(sel,x,false);nb(x,z);for(auto v:z){if(!cnt[v])throw std::runtime_error("underflow");--cnt[v];xo[v]^=x+1;work.push_back(v);}}for(auto y:add){bs(sel,y,true);nb(y,z);for(auto v:z){++cnt[v];xo[v]^=y+1;work.push_back(v);}}for(auto v:work)refresh(v);for(auto v:rem)tabu[tp++%tabu.size()]=v;};
 for(std::uint64_t step=0;step<steps;++step){bool did=false;
  if(step%two_rate==0&&!c2.empty()){
   for(unsigned tr=0;tr<64&&!did;++tr){auto y=c2[rng()%c2.size()];if(bg(sel,y)||cnt[y]!=2)continue;std::vector<std::uint32_t>ny;nb(y,ny);std::uint32_t a=N,b=N;for(auto q:ny)if(bg(sel,q)){if(a==N)a=q;else if(b==N)b=q;else throw std::runtime_error("c2 owners >2");}if(a==N||b==N)throw std::runtime_error("c2 owners <2");
    std::vector<std::uint32_t>pool;pool.reserve(16);for(auto q:c1){auto o=xo[q];if(o==a+1||o==b+1)pool.push_back(q);}auto target=(a+1)^(b+1);for(auto q:c2)if(xo[q]==target&&cf(q,a)&&cf(q,b))pool.push_back(q);std::sort(pool.begin(),pool.end());pool.erase(std::unique(pool.begin(),pool.end()),pool.end());std::array<std::uint32_t,3>w{};if(independent3(pool,w)){write(argv[2],sel,{a,b},{w[0],w[1],w[2]});std::cout<<"{\"kind\":\"replace2add3\",\"step\":"<<step<<",\"seed\":"<<seed<<",\"remove\":["<<a<<','<<b<<"],\"add\":["<<w[0]<<','<<w[1]<<','<<w[2]<<"]}\n";return 0;}
    std::shuffle(pool.begin(),pool.end(),rng);for(auto z:pool)if(z!=y&&!cf(y,z)){apply({a,b},{y,z});++n2;did=true;break;}
   }if(!did)++failed2;
  }
  if(!did){if(c1.empty())break;std::uint32_t y=N;for(unsigned tr=0;tr<128;++tr){auto q=c1[rng()%c1.size()];bool bad=false;for(auto t:tabu)if(q==t){bad=true;break;}if(!bad){y=q;break;}}if(y==N)y=c1[rng()%c1.size()];if(cnt[y]!=1||!xo[y])throw std::runtime_error("c1 invariant");auto x=xo[y]-1;if(!bg(sel,x))throw std::runtime_error("c1 owner");for(auto z:c1)if(z!=y&&xo[z]==x+1&&!cf(y,z)){write(argv[2],sel,{x},{y,z});std::cout<<"{\"kind\":\"replace1add2\",\"step\":"<<step<<",\"seed\":"<<seed<<",\"remove\":"<<x<<",\"add\":["<<y<<','<<z<<"]}\n";return 0;}apply({x},{y});++n1;}
  if((step+1)%1000==0)std::cerr<<"step="<<(step+1)<<" c1="<<c1.size()<<" c2="<<c2.size()<<" n1="<<n1<<" n2="<<n2<<" failed2="<<failed2<<"\n";
 }
 std::cout<<"{\"kind\":\"none\",\"method\":\"heuristic-neutral1-neutral2-walk\",\"steps_requested\":"<<steps<<",\"seed\":"<<seed<<",\"neutral1_moves\":"<<n1<<",\"neutral2_moves\":"<<n2<<",\"failed_neutral2_attempts\":"<<failed2<<",\"c1_final\":"<<c1.size()<<",\"c2_final\":"<<c2.size()<<"}\n";return 0;
}catch(const std::exception&e){std::cerr<<"error: "<<e.what()<<"\n";return 1;}
