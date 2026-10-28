// Heuristic plateau walk on a verified 134753-point C7^10 independent set.
//
// Unlike the unguided neutral walk, this walk optimizes the exact precursor of
// a radius-1 improvement: multiple coverage-one (private) outside vertices
// owned by the same selected point.  At every plateau state it globally scans
// all current private-owner groups.  If any group contains two pairwise
// nonconfusable vertices, removing that owner and adding the pair gives a
// 134754-point certificate immediately.
//
// Otherwise the lexicographic potential is
//   (sum_x choose(|C1(x)|,2), |C1|).
// Legal neutral 1-for-1 moves that improve this potential are accepted;
// downhill moves are accepted with a small configurable probability to escape
// local maxima.  Coverage counts and unique owners are maintained exactly.
// Negative runs are heuristic only; any emitted winner is replayed by the
// Few Shots verifier in the workflow.
#include <algorithm>
#include <array>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <random>
#include <stdexcept>
#include <utility>
#include <vector>
#ifdef _OPENMP
#include <omp.h>
#endif
namespace {
constexpr int D=10;
constexpr std::uint32_t P7[D+1]={1u,7u,49u,343u,2401u,16807u,117649u,823543u,5764801u,40353607u,282475249u};
constexpr std::uint32_t N=P7[D],GROUPS=N/7u;
enum class Op{Sum,Xor};
template<class T,Op op>void trans(std::vector<T>&a,std::vector<T>&b){
 for(int d=0;d<D;++d){auto s=P7[d];std::uint64_t block=std::uint64_t(s)*7u;
#pragma omp parallel for schedule(static)
  for(std::int64_t gg=0;gg<(std::int64_t)GROUPS;++gg){std::uint64_t g=gg,bn=g/s;std::uint32_t off=g%s;std::uint64_t base=bn*block+off;T v[7];for(int k=0;k<7;++k)v[k]=a[base+std::uint64_t(k)*s];for(int k=0;k<7;++k){T l=v[(k+6)%7],m=v[k],r=v[(k+1)%7];b[base+std::uint64_t(k)*s]=op==Op::Sum?T(l+m+r):T(l^m^r);}}a.swap(b);
 }
}
std::vector<std::uint32_t>load(const char*p){std::ifstream in(p);if(!in)throw std::runtime_error("ids");std::vector<std::uint32_t>a;std::uint64_t z;while(in>>z){if(z>=N)throw std::runtime_error("range");a.push_back((std::uint32_t)z);}std::sort(a.begin(),a.end());if(a.size()!=134753||std::adjacent_find(a.begin(),a.end())!=a.end())throw std::runtime_error("baseline");return a;}
inline bool bg(const std::vector<std::uint64_t>&b,std::uint32_t x){return(b[x>>6]>>(x&63))&1u;}
inline void bs(std::vector<std::uint64_t>&b,std::uint32_t x,bool v){auto&m=b[x>>6];auto q=std::uint64_t(1)<<(x&63);if(v)m|=q;else m&=~q;}
bool cf(std::uint32_t a,std::uint32_t b){if(a==b)return true;for(int d=0;d<D;++d){int x=a%7u,y=b%7u;a/=7u;b/=7u;int z=(x-y+7)%7;if(z!=0&&z!=1&&z!=6)return false;}return true;}
void nb(std::uint32_t p,std::vector<std::uint32_t>&o){std::array<unsigned,D>d{};for(int i=0;i<D;++i){d[i]=p%7u;p/=7u;}o.clear();o.push_back(0);for(int k=0;k<D;++k){auto old=o;o.clear();o.reserve(old.size()*3);for(auto q:old){o.push_back(q+((d[k]+6)%7)*P7[k]);o.push_back(q+d[k]*P7[k]);o.push_back(q+((d[k]+1)%7)*P7[k]);}}}
void writewinner(const char*p,const std::vector<std::uint64_t>&sel,std::uint32_t rem,std::uint32_t a,std::uint32_t b){std::ofstream out(p);if(!out)throw std::runtime_error("write");std::uint64_t n=0;for(std::uint32_t v=0;v<N;++v)if(bg(sel,v)&&v!=rem){out<<v<<'\n';++n;}out<<a<<'\n'<<b<<'\n';n+=2;if(n!=134754)throw std::runtime_error("winner size");}
struct Pot{std::uint64_t rawpairs=0;std::uint32_t c1=0;};
bool better(const Pot&a,const Pot&b){return a.rawpairs>b.rawpairs||(a.rawpairs==b.rawpairs&&a.c1>b.c1);}
}
int main(int argc,char**argv)try{
 if(argc!=6){std::cerr<<"usage: c7_10d_private_guided_walk BASELINE_IDS RESULT_IDS STEPS SEED DOWN_RATE\n";return 2;}
 auto base=load(argv[1]);std::uint64_t steps=std::stoull(argv[3]),seed=std::stoull(argv[4]);unsigned down_rate=std::stoul(argv[5]);if(!down_rate)throw std::runtime_error("down_rate");
 std::vector<std::uint16_t>cnt(N),tmp16(N);std::vector<std::uint32_t>xo(N),tmp32(N);std::vector<std::uint64_t>sel((N+63)/64);
 for(auto v:base){cnt[v]=1;xo[v]=v+1;bs(sel,v,true);}trans<std::uint16_t,Op::Sum>(cnt,tmp16);tmp16.clear();tmp16.shrink_to_fit();trans<std::uint32_t,Op::Xor>(xo,tmp32);tmp32.clear();tmp32.shrink_to_fit();
 std::vector<std::int32_t>pos(N);std::vector<std::uint32_t>c1;c1.reserve(20000);
 auto erase=[&](std::uint32_t v){auto p=pos[v];if(!p)return;auto i=(std::uint32_t)(p-1),w=c1.back();c1[i]=w;pos[w]=(std::int32_t)i+1;c1.pop_back();pos[v]=0;};
 auto refresh=[&](std::uint32_t v){bool want=!bg(sel,v)&&cnt[v]==1;bool have=pos[v]!=0;if(want==have)return;if(have)erase(v);else{pos[v]=(std::int32_t)c1.size()+1;c1.push_back(v);}};
 for(std::uint32_t v=0;v<N;++v){if(!bg(sel,v)&&cnt[v]==0)throw std::runtime_error("coverage0 baseline");refresh(v);}
 std::vector<std::uint32_t>work;work.reserve(2*59049);std::vector<std::uint32_t>z;z.reserve(59049);
 auto apply=[&](std::uint32_t rem,std::uint32_t add){work.clear();bs(sel,rem,false);nb(rem,z);for(auto v:z){if(!cnt[v])throw std::runtime_error("underflow");--cnt[v];xo[v]^=rem+1;work.push_back(v);}bs(sel,add,true);nb(add,z);for(auto v:z){++cnt[v];xo[v]^=add+1;work.push_back(v);}for(auto v:work)refresh(v);};
 std::uint32_t winowner=N,wina=N,winb=N;
 auto potential=[&](){Pot p{};p.c1=(std::uint32_t)c1.size();std::vector<std::pair<std::uint32_t,std::uint32_t>>q;q.reserve(c1.size());for(auto v:c1){if(cnt[v]!=1||!xo[v])throw std::runtime_error("c1 invariant");q.push_back({xo[v]-1,v});}std::sort(q.begin(),q.end());for(std::size_t i=0;i<q.size();){std::size_t j=i+1;while(j<q.size()&&q[j].first==q[i].first)++j;auto n=j-i;p.rawpairs+=std::uint64_t(n)*(n-1)/2;for(std::size_t a=i;a<j&&wina==N;++a)for(std::size_t b=a+1;b<j;++b)if(!cf(q[a].second,q[b].second)){winowner=q[i].first;wina=q[a].second;winb=q[b].second;break;}i=j;}return p;};
 auto cur=potential();if(wina!=N){writewinner(argv[2],sel,winowner,wina,winb);std::cout<<"{\"kind\":\"replace1add2\",\"step\":0,\"seed\":"<<seed<<",\"remove\":"<<winowner<<",\"add\":["<<wina<<','<<winb<<"]}\n";return 0;}
 std::cerr<<"init c1="<<cur.c1<<" raw_private_pairs="<<cur.rawpairs<<"\n";
 std::mt19937_64 rng(seed);std::uint64_t accepted=0,uphill=0,downhill=0,rejected=0;Pot best=cur;
 for(std::uint64_t step=0;step<steps;++step){if(c1.empty())break;auto y=c1[rng()%c1.size()];if(cnt[y]!=1||!xo[y])throw std::runtime_error("chosen c1 invariant");auto x=xo[y]-1;if(!bg(sel,x))throw std::runtime_error("owner not selected");apply(x,y);winowner=wina=winb=N;auto nxt=potential();if(wina!=N){writewinner(argv[2],sel,winowner,wina,winb);std::cout<<"{\"kind\":\"replace1add2\",\"step\":"<<(step+1)<<",\"seed\":"<<seed<<",\"remove\":"<<winowner<<",\"add\":["<<wina<<','<<winb<<"],\"raw_private_pairs\":"<<nxt.rawpairs<<"}\n";return 0;}
  bool acc=false;if(better(nxt,cur)||(!better(cur,nxt)&&!better(nxt,cur))){acc=true;++uphill;}else if((rng()%down_rate)==0){acc=true;++downhill;}if(acc){cur=nxt;++accepted;if(better(cur,best))best=cur;}else{apply(y,x);++rejected;winowner=wina=winb=N;auto chk=potential();if(chk.rawpairs!=cur.rawpairs||chk.c1!=cur.c1)throw std::runtime_error("revert drift");}
  if((step+1)%1000==0)std::cerr<<"step="<<(step+1)<<" accepted="<<accepted<<" rejected="<<rejected<<" c1="<<cur.c1<<" raw="<<cur.rawpairs<<" best_c1="<<best.c1<<" best_raw="<<best.rawpairs<<" downhill="<<downhill<<"\n";
 }
 std::cout<<"{\"kind\":\"none\",\"method\":\"heuristic-private-pair-guided-neutral1\",\"steps_requested\":"<<steps<<",\"seed\":"<<seed<<",\"down_rate\":"<<down_rate<<",\"accepted\":"<<accepted<<",\"up_or_equal\":"<<uphill<<",\"downhill\":"<<downhill<<",\"rejected\":"<<rejected<<",\"c1_final\":"<<cur.c1<<",\"raw_private_pairs_final\":"<<cur.rawpairs<<",\"c1_best\":"<<best.c1<<",\"raw_private_pairs_best\":"<<best.rawpairs<<"}\n";return 0;
}catch(const std::exception&e){std::cerr<<"error: "<<e.what()<<"\n";return 1;}
