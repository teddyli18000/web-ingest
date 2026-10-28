// Target-guided heuristic plateau walk on the verified 134753 C7^10 baseline.
//
// Uses legal neutral 1-for-1 and genuine 2-for-2 moves, but unlike the random
// neutral12 walker accepts moves according to the exact precursor of a radius-1
// breakthrough: raw same-owner private-candidate pairs
//     sum_x choose(|C1(x)|,2),
// with |C1| as tie-breaker.  Every evaluated state globally checks whether any
// same-owner pair is nonconfusable, which would give remove1/add2 = 134754.
// Before each sampled neutral2 proposal, its complete current two-owner pool is
// checked exactly for an independent triple, which would give remove2/add3.
// Negative runs are heuristic only; winners are replayed by Few Shots verifier.
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
namespace{
constexpr int D=10;constexpr std::uint32_t P7[D+1]={1u,7u,49u,343u,2401u,16807u,117649u,823543u,5764801u,40353607u,282475249u};constexpr std::uint32_t N=P7[D],GROUPS=N/7u;enum class Op{Sum,Xor};
template<class T,Op op>void trans(std::vector<T>&a,std::vector<T>&b){for(int d=0;d<D;++d){auto s=P7[d];std::uint64_t block=std::uint64_t(s)*7u;
#pragma omp parallel for schedule(static)
 for(std::int64_t gg=0;gg<(std::int64_t)GROUPS;++gg){std::uint64_t g=gg,bn=g/s;std::uint32_t off=g%s;std::uint64_t base=bn*block+off;T v[7];for(int k=0;k<7;++k)v[k]=a[base+std::uint64_t(k)*s];for(int k=0;k<7;++k){T l=v[(k+6)%7],m=v[k],r=v[(k+1)%7];b[base+std::uint64_t(k)*s]=op==Op::Sum?T(l+m+r):T(l^m^r);}}a.swap(b);}}
std::vector<std::uint32_t>load(const char*p){std::ifstream in(p);if(!in)throw std::runtime_error("ids");std::vector<std::uint32_t>a;std::uint64_t z;while(in>>z){if(z>=N)throw std::runtime_error("range");a.push_back((std::uint32_t)z);}std::sort(a.begin(),a.end());if(a.size()!=134753||std::adjacent_find(a.begin(),a.end())!=a.end())throw std::runtime_error("baseline");return a;}
inline bool bg(const std::vector<std::uint64_t>&b,std::uint32_t x){return(b[x>>6]>>(x&63))&1u;}inline void bs(std::vector<std::uint64_t>&b,std::uint32_t x,bool v){auto&m=b[x>>6];auto q=std::uint64_t(1)<<(x&63);if(v)m|=q;else m&=~q;}
bool cf(std::uint32_t a,std::uint32_t b){if(a==b)return true;for(int d=0;d<D;++d){int x=a%7u,y=b%7u;a/=7u;b/=7u;int z=(x-y+7)%7;if(z!=0&&z!=1&&z!=6)return false;}return true;}
void nb(std::uint32_t p,std::vector<std::uint32_t>&o){std::array<unsigned,D>d{};for(int i=0;i<D;++i){d[i]=p%7u;p/=7u;}o.clear();o.push_back(0);for(int k=0;k<D;++k){auto old=o;o.clear();o.reserve(old.size()*3);for(auto q:old){o.push_back(q+((d[k]+6)%7)*P7[k]);o.push_back(q+d[k]*P7[k]);o.push_back(q+((d[k]+1)%7)*P7[k]);}}}
void writewinner(const char*p,const std::vector<std::uint64_t>&sel,const std::vector<std::uint32_t>&rem,const std::vector<std::uint32_t>&add){std::ofstream out(p);if(!out)throw std::runtime_error("write");std::uint64_t n=0;for(std::uint32_t v=0;v<N;++v)if(bg(sel,v)&&std::find(rem.begin(),rem.end(),v)==rem.end()){out<<v<<'\n';++n;}for(auto v:add){out<<v<<'\n';++n;}if(n!=134754)throw std::runtime_error("winner size");}
bool independent3(const std::vector<std::uint32_t>&p,std::array<std::uint32_t,3>&o){for(std::size_t i=0;i<p.size();++i)for(std::size_t j=i+1;j<p.size();++j){if(cf(p[i],p[j]))continue;for(std::size_t k=j+1;k<p.size();++k)if(!cf(p[i],p[k])&&!cf(p[j],p[k])){o={p[i],p[j],p[k]};return true;}}return false;}
struct Pot{std::uint64_t raw=0;std::uint32_t c1=0;};bool better(const Pot&a,const Pot&b){return a.raw>b.raw||(a.raw==b.raw&&a.c1>b.c1);}
}
int main(int argc,char**argv)try{
 if(argc!=7){std::cerr<<"usage: guided12 BASELINE_IDS RESULT_IDS STEPS SEED TWO_RATE DOWN_RATE\n";return 2;}auto base=load(argv[1]);std::uint64_t steps=std::stoull(argv[3]),seed=std::stoull(argv[4]);unsigned two_rate=std::stoul(argv[5]),down_rate=std::stoul(argv[6]);if(!two_rate||!down_rate)throw std::runtime_error("rates");
 std::vector<std::uint16_t>cnt(N),tmp16(N);std::vector<std::uint32_t>xo(N),tmp32(N);std::vector<std::uint64_t>sel((N+63)/64);for(auto v:base){cnt[v]=1;xo[v]=v+1;bs(sel,v,true);}trans<std::uint16_t,Op::Sum>(cnt,tmp16);tmp16.clear();tmp16.shrink_to_fit();trans<std::uint32_t,Op::Xor>(xo,tmp32);tmp32.clear();tmp32.shrink_to_fit();
 std::vector<std::int32_t>pos(N);std::vector<std::uint32_t>c1,c2;c1.reserve(20000);c2.reserve(300000);
 auto erase=[&](std::uint32_t v){auto p=pos[v];if(!p)return;if(p>0){auto i=(std::uint32_t)(p-1),w=c1.back();c1[i]=w;pos[w]=(std::int32_t)i+1;c1.pop_back();}else{auto i=(std::uint32_t)(-p-1),w=c2.back();c2[i]=w;pos[w]=-((std::int32_t)i+1);c2.pop_back();}pos[v]=0;};
 auto refresh=[&](std::uint32_t v){unsigned want=bg(sel,v)?0:(cnt[v]==1?1:cnt[v]==2?2:0);auto p=pos[v];unsigned have=p>0?1:p<0?2:0;if(want==have)return;erase(v);if(want==1){pos[v]=(std::int32_t)c1.size()+1;c1.push_back(v);}else if(want==2){pos[v]=-((std::int32_t)c2.size()+1);c2.push_back(v);}};
 for(std::uint32_t v=0;v<N;++v){if(!bg(sel,v)&&cnt[v]==0)throw std::runtime_error("coverage0 baseline");refresh(v);}
 std::vector<std::uint32_t>work,z;work.reserve(4*59049);z.reserve(59049);
 auto apply=[&](const std::vector<std::uint32_t>&rem,const std::vector<std::uint32_t>&add){work.clear();for(auto x:rem){bs(sel,x,false);nb(x,z);for(auto v:z){if(!cnt[v])throw std::runtime_error("underflow");--cnt[v];xo[v]^=x+1;work.push_back(v);}}for(auto y:add){bs(sel,y,true);nb(y,z);for(auto v:z){++cnt[v];xo[v]^=y+1;work.push_back(v);}}for(auto v:work)refresh(v);};
 std::uint32_t winowner=N,wina=N,winb=N;
 auto potential=[&](){Pot p{};p.c1=(std::uint32_t)c1.size();std::vector<std::pair<std::uint32_t,std::uint32_t>>q;q.reserve(c1.size());for(auto v:c1){if(cnt[v]!=1||!xo[v])throw std::runtime_error("c1 invariant");q.push_back({xo[v]-1,v});}std::sort(q.begin(),q.end());for(std::size_t i=0;i<q.size();){std::size_t j=i+1;while(j<q.size()&&q[j].first==q[i].first)++j;auto n=j-i;p.raw+=std::uint64_t(n)*(n-1)/2;for(std::size_t a=i;a<j&&wina==N;++a)for(std::size_t b=a+1;b<j;++b)if(!cf(q[a].second,q[b].second)){winowner=q[i].first;wina=q[a].second;winb=q[b].second;break;}i=j;}return p;};
 auto cur=potential();if(wina!=N){writewinner(argv[2],sel,{winowner},{wina,winb});std::cout<<"{\"kind\":\"replace1add2\",\"step\":0}\n";return 0;}Pot best=cur;std::cerr<<"init c1="<<cur.c1<<" c2="<<c2.size()<<" raw="<<cur.raw<<"\n";
 std::mt19937_64 rng(seed);std::uint64_t acc1=0,acc2=0,rej1=0,rej2=0,down=0,fail2=0;
 for(std::uint64_t step=0;step<steps;++step){bool proposed=false,is2=false;std::vector<std::uint32_t>rem,add;
  if(step%two_rate==0&&!c2.empty())for(unsigned tr=0;tr<64&&!proposed;++tr){auto y=c2[rng()%c2.size()];if(bg(sel,y)||cnt[y]!=2)continue;nb(y,z);std::uint32_t a=N,b=N;for(auto q:z)if(bg(sel,q)){if(a==N)a=q;else if(b==N)b=q;else throw std::runtime_error("c2 owners >2");}if(a==N||b==N)throw std::runtime_error("c2 owners <2");std::vector<std::uint32_t>pool;pool.reserve(16);for(auto q:c1){auto o=xo[q];if(o==a+1||o==b+1)pool.push_back(q);}auto target=(a+1)^(b+1);for(auto q:c2)if(xo[q]==target&&cf(q,a)&&cf(q,b))pool.push_back(q);std::sort(pool.begin(),pool.end());pool.erase(std::unique(pool.begin(),pool.end()),pool.end());std::array<std::uint32_t,3>w{};if(independent3(pool,w)){writewinner(argv[2],sel,{a,b},{w[0],w[1],w[2]});std::cout<<"{\"kind\":\"replace2add3\",\"step\":"<<step<<",\"seed\":"<<seed<<",\"remove\":["<<a<<','<<b<<"],\"add\":["<<w[0]<<','<<w[1]<<','<<w[2]<<"]}\n";return 0;}std::shuffle(pool.begin(),pool.end(),rng);for(auto q:pool)if(q!=y&&!cf(y,q)){rem={a,b};add={y,q};proposed=true;is2=true;break;}}
  if(!proposed){if(c1.empty())break;auto y=c1[rng()%c1.size()];if(cnt[y]!=1||!xo[y])throw std::runtime_error("c1 choose");auto x=xo[y]-1;if(!bg(sel,x))throw std::runtime_error("owner");rem={x};add={y};proposed=true;is2=false;}
  apply(rem,add);winowner=wina=winb=N;auto nxt=potential();if(wina!=N){writewinner(argv[2],sel,{winowner},{wina,winb});std::cout<<"{\"kind\":\"replace1add2\",\"step\":"<<(step+1)<<",\"seed\":"<<seed<<",\"remove\":"<<winowner<<",\"add\":["<<wina<<','<<winb<<"],\"raw\":"<<nxt.raw<<"}\n";return 0;}
  bool accept=better(nxt,cur)||(!better(cur,nxt)&&!better(nxt,cur));if(!accept&&(rng()%down_rate)==0){accept=true;++down;}if(accept){cur=nxt;if(is2)++acc2;else ++acc1;if(better(cur,best))best=cur;}else{apply(add,rem);winowner=wina=winb=N;auto chk=potential();if(chk.raw!=cur.raw||chk.c1!=cur.c1)throw std::runtime_error("revert drift");if(is2)++rej2;else ++rej1;}if(is2&&!accept){}if(step%two_rate==0&&!is2)++fail2;
  if((step+1)%1000==0)std::cerr<<"step="<<(step+1)<<" c1="<<cur.c1<<" c2="<<c2.size()<<" raw="<<cur.raw<<" best_raw="<<best.raw<<" best_c1="<<best.c1<<" acc1="<<acc1<<" acc2="<<acc2<<" rej1="<<rej1<<" rej2="<<rej2<<" down="<<down<<"\n";
 }
 std::cout<<"{\"kind\":\"none\",\"method\":\"heuristic-private-guided-neutral12\",\"steps_requested\":"<<steps<<",\"seed\":"<<seed<<",\"two_rate\":"<<two_rate<<",\"down_rate\":"<<down_rate<<",\"accepted1\":"<<acc1<<",\"accepted2\":"<<acc2<<",\"rejected1\":"<<rej1<<",\"rejected2\":"<<rej2<<",\"failed2\":"<<fail2<<",\"downhill\":"<<down<<",\"c1_final\":"<<cur.c1<<",\"c2_final\":"<<c2.size()<<",\"raw_final\":"<<cur.raw<<",\"c1_best\":"<<best.c1<<",\"raw_best\":"<<best.raw<<"}\n";return 0;
}catch(const std::exception&e){std::cerr<<"error: "<<e.what()<<"\n";return 1;}
