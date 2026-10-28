// Stage-A exact unrestricted remove-5/add-7 search for C7^10.
//
// This stage is COMPLETE for every 5-owner set that occurs as the exact blocker
// support of at least one coverage-5 outside vertex. It is intentionally not
// yet the full radius-5 search: connected five-owner support hypergraphs made
// only from supports of size <=4 are handled by the next stage.
//
// Exact support recovery:
//   c1: min
//   c2: min,max
//   c3: min,max,sum
//   c4: min,max,sum,sumsq
//   c5: min,max,sum,sumsq,sumcube
// For c5 the three middle owner labels are roots of the monic cubic determined
// by Newton identities. Roots are isolated on the three monotone intervals of
// that cubic and found by integer binary search; all recovered moments are then
// replayed exactly. Any recovery drift aborts the run.
#include <algorithm>
#include <array>
#include <cmath>
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
enum class Op{Sum,Min,Max};

template<class T,Op op>void transform(std::vector<T>&a,std::vector<T>&b,const char*name){
 for(int dim=0;dim<D;++dim){const auto s=P7[dim];const std::uint64_t block=std::uint64_t(s)*7u;
  #pragma omp parallel for schedule(static)
  for(std::int64_t gg=0;gg<(std::int64_t)GROUPS;++gg){const std::uint64_t g=gg,bn=g/s;const std::uint32_t off=g%s;const std::uint64_t base=bn*block+off;T v[7];for(int k=0;k<7;++k)v[k]=a[base+std::uint64_t(k)*s];for(int k=0;k<7;++k){T l=v[(k+6)%7],m=v[k],r=v[(k+1)%7],z{};if constexpr(op==Op::Sum)z=T(l+m+r);else if constexpr(op==Op::Min)z=std::min(l,std::min(m,r));else z=std::max(l,std::max(m,r));b[base+std::uint64_t(k)*s]=z;}}
  a.swap(b);std::cerr<<name<<" dim="<<dim<<"\n";
 }
}
std::vector<std::uint32_t>load_ids(const std::string&p){std::ifstream in(p);if(!in)throw std::runtime_error("cannot open ids");std::vector<std::uint32_t>a;std::uint64_t x;while(in>>x){if(x>=N)throw std::runtime_error("id range");a.push_back((std::uint32_t)x);}if(a.empty())throw std::runtime_error("empty baseline");std::sort(a.begin(),a.end());if(std::adjacent_find(a.begin(),a.end())!=a.end())throw std::runtime_error("duplicate baseline");return a;}
bool conflict(std::uint32_t a,std::uint32_t b){if(a==b)return true;for(int d=0;d<D;++d){int x=a%7u,y=b%7u;a/=7u;b/=7u;int z=(x-y+7)%7;if(z!=0&&z!=1&&z!=6)return false;}return true;}
std::uint64_t key2(std::uint32_t a,std::uint32_t b){if(a>b)std::swap(a,b);return(std::uint64_t(a)<<BITS)|b;}
std::uint64_t key3(std::uint32_t a,std::uint32_t b,std::uint32_t c){std::array<std::uint32_t,3>x{a,b,c};std::sort(x.begin(),x.end());return(std::uint64_t(x[0])<<(2*BITS))|(std::uint64_t(x[1])<<BITS)|x[2];}
struct Quad{std::uint32_t a,b,c,d;bool operator==(const Quad&o)const{return a==o.a&&b==o.b&&c==o.c&&d==o.d;}};
struct QuadHash{std::size_t operator()(const Quad&q)const noexcept{std::size_t h=q.a;for(auto x:{q.b,q.c,q.d})h^=std::size_t(x)+0x9e3779b97f4a7c15ULL+(h<<6)+(h>>2);return h;}};
Quad quad(std::uint32_t a,std::uint32_t b,std::uint32_t c,std::uint32_t d){std::array<std::uint32_t,4>x{a,b,c,d};std::sort(x.begin(),x.end());return{x[0],x[1],x[2],x[3]};}
struct Quint{std::uint32_t a,b,c,d,e;bool operator==(const Quint&o)const{return a==o.a&&b==o.b&&c==o.c&&d==o.d&&e==o.e;}bool operator<(const Quint&o)const{return std::array<std::uint32_t,5>{a,b,c,d,e}<std::array<std::uint32_t,5>{o.a,o.b,o.c,o.d,o.e};}};
struct Entry5{Quint q;std::uint32_t v;};

std::uint64_t isqrt_u64(std::uint64_t x){std::uint64_t r=(std::uint64_t)std::sqrt((long double)x);while((r+1)>r&&(r+1)<=x/(r+1))++r;while(r&&r>x/r)--r;return r;}
__int128 poly3(std::int64_t t,std::int64_t e1,std::int64_t e2,std::int64_t e3){__int128 z=t;return z*z*z-(__int128)e1*z*z+(__int128)e2*z-e3;}
std::int64_t first_ge_zero(std::int64_t l,std::int64_t r,std::int64_t e1,std::int64_t e2,std::int64_t e3){while(l<r){auto m=l+(r-l)/2;if(poly3(m,e1,e2,e3)>=0)r=m;else l=m+1;}return l;}
std::int64_t first_le_zero(std::int64_t l,std::int64_t r,std::int64_t e1,std::int64_t e2,std::int64_t e3){while(l<r){auto m=l+(r-l)/2;if(poly3(m,e1,e2,e3)<=0)r=m;else l=m+1;}return l;}
std::array<std::uint32_t,3> recover_middle3(std::uint64_t p1,std::uint64_t p2,std::uint64_t p3,std::uint32_t lower,std::uint32_t upper){
 __int128 n2=(__int128)p1*p1-p2;if(n2<0||(n2&1))throw std::runtime_error("c5 Newton e2");std::int64_t e1=(std::int64_t)p1,e2=(std::int64_t)(n2/2);
 __int128 n3=(__int128)p3-(__int128)e1*p2+(__int128)e2*e1;if(n3<0||n3%3)throw std::runtime_error("c5 Newton e3");std::int64_t e3=(std::int64_t)(n3/3);
 __int128 dd=(__int128)e1*e1-3*(__int128)e2;if(dd<=0||dd>std::numeric_limits<std::uint64_t>::max())throw std::runtime_error("c5 derivative discriminant");long double sd=std::sqrt((long double)(std::uint64_t)dd);long double x1=((long double)e1-sd)/3.0L,x2=((long double)e1+sd)/3.0L;
 std::int64_t L1=(std::int64_t)lower+1,R1=(std::int64_t)std::floor(x1);std::int64_t L2=(std::int64_t)std::ceil(x1),R2=(std::int64_t)std::floor(x2);std::int64_t L3=(std::int64_t)std::ceil(x2),R3=(std::int64_t)upper-1;
 if(L1>R1||L2>R2||L3>R3)throw std::runtime_error("c5 root brackets");auto b=first_ge_zero(L1,R1,e1,e2,e3);auto c=first_le_zero(L2,R2,e1,e2,e3);auto d=first_ge_zero(L3,R3,e1,e2,e3);
 if(poly3(b,e1,e2,e3)||poly3(c,e1,e2,e3)||poly3(d,e1,e2,e3)||!(lower<(std::uint64_t)b&&(std::uint64_t)b<(std::uint64_t)c&&(std::uint64_t)c<(std::uint64_t)d&&(std::uint64_t)d<upper))throw std::runtime_error("c5 integer roots");
 __int128 q1=(__int128)b+c+d,q2=(__int128)b*b+(__int128)c*c+(__int128)d*d,q3=(__int128)b*b*b+(__int128)c*c*c+(__int128)d*d*d;if(q1!=p1||q2!=p2||q3!=p3)throw std::runtime_error("c5 moment replay");return{(std::uint32_t)b,(std::uint32_t)c,(std::uint32_t)d};
}
bool find_k_rec(const std::vector<std::uint32_t>&p,std::size_t start,unsigned k,std::vector<std::uint32_t>&chosen){if(chosen.size()==k)return true;if(chosen.size()+(p.size()-start)<k)return false;for(std::size_t i=start;i<p.size();++i){bool ok=true;for(auto z:chosen)if(conflict(z,p[i])){ok=false;break;}if(!ok)continue;chosen.push_back(p[i]);if(find_k_rec(p,i+1,k,chosen))return true;chosen.pop_back();}return false;}
bool find_k(std::vector<std::uint32_t>p,unsigned k,std::vector<std::uint32_t>&out){std::sort(p.begin(),p.end());p.erase(std::unique(p.begin(),p.end()),p.end());out.clear();return find_k_rec(p,0,k,out);}
}

int main(int argc,char**argv){try{
 if(argc!=2){std::cerr<<"usage: search_net2_r5_direct BASELINE_IDS\n";return 2;}auto base=load_ids(argv[1]);std::unordered_set<std::uint32_t>bset(base.begin(),base.end());
 std::vector<std::uint16_t>cnt(N,0),t16(N,0);for(auto v:base)cnt[v]=1;transform<std::uint16_t,Op::Sum>(cnt,t16,"count");t16.clear();t16.shrink_to_fit();std::vector<std::uint32_t>c1,c2,c3,c4,c5;c1.reserve(10000);c2.reserve(200000);c3.reserve(1100000);c4.reserve(2300000);c5.reserve(4000000);std::uint64_t c0=0;for(std::uint32_t v=0;v<N;++v){if(cnt[v]==0)++c0;else if(cnt[v]==1&&!bset.count(v))c1.push_back(v);else if(cnt[v]==2)c2.push_back(v);else if(cnt[v]==3)c3.push_back(v);else if(cnt[v]==4)c4.push_back(v);else if(cnt[v]==5)c5.push_back(v);}if(c0)throw std::runtime_error("coverage0 nonzero");cnt.clear();cnt.shrink_to_fit();
 std::vector<std::uint32_t>mn(N,INF),tm(N,INF);for(std::uint32_t i=0;i<base.size();++i)mn[base[i]]=i+1;transform<std::uint32_t,Op::Min>(mn,tm,"min");tm.clear();tm.shrink_to_fit();std::vector<std::vector<std::uint32_t>>g1(base.size());for(auto v:c1){auto a=mn[v];if(!a||a==INF||a>base.size())throw std::runtime_error("c1 owner");g1[a-1].push_back(v);}std::vector<std::uint32_t>lo2,lo3,lo4,lo5;for(auto v:c2)lo2.push_back(mn[v]);for(auto v:c3)lo3.push_back(mn[v]);for(auto v:c4)lo4.push_back(mn[v]);for(auto v:c5)lo5.push_back(mn[v]);mn.clear();mn.shrink_to_fit();
 std::vector<std::uint32_t>mx(N,0),tx(N,0);for(std::uint32_t i=0;i<base.size();++i)mx[base[i]]=i+1;transform<std::uint32_t,Op::Max>(mx,tx,"max");tx.clear();tx.shrink_to_fit();std::vector<std::uint32_t>hi2,hi3,hi4,hi5;for(auto v:c2)hi2.push_back(mx[v]);for(auto v:c3)hi3.push_back(mx[v]);for(auto v:c4)hi4.push_back(mx[v]);for(auto v:c5)hi5.push_back(mx[v]);mx.clear();mx.shrink_to_fit();
 std::vector<std::uint64_t>su(N,0),ts(N,0);for(std::uint32_t i=0;i<base.size();++i)su[base[i]]=std::uint64_t(i+1);transform<std::uint64_t,Op::Sum>(su,ts,"sum");ts.clear();ts.shrink_to_fit();std::vector<std::uint64_t>s3,s4,s5;for(auto v:c3)s3.push_back(su[v]);for(auto v:c4)s4.push_back(su[v]);for(auto v:c5)s5.push_back(su[v]);su.clear();su.shrink_to_fit();
 std::vector<std::uint64_t>sq(N,0),tq(N,0);for(std::uint32_t i=0;i<base.size();++i){std::uint64_t z=i+1;sq[base[i]]=z*z;}transform<std::uint64_t,Op::Sum>(sq,tq,"sumsq");tq.clear();tq.shrink_to_fit();std::vector<std::uint64_t>q4,q5;for(auto v:c4)q4.push_back(sq[v]);for(auto v:c5)q5.push_back(sq[v]);sq.clear();sq.shrink_to_fit();
 // For a target c5 cell the dependency cone contains exactly its five blockers,
 // so target sumcube cannot overflow uint64_t. Exact moment replay is mandatory.
 std::vector<std::uint64_t>cu(N,0),tu(N,0);for(std::uint32_t i=0;i<base.size();++i){std::uint64_t z=i+1;cu[base[i]]=z*z*z;}transform<std::uint64_t,Op::Sum>(cu,tu,"sumcube");tu.clear();tu.shrink_to_fit();std::vector<std::uint64_t>r5;for(auto v:c5)r5.push_back(cu[v]);cu.clear();cu.shrink_to_fit();
 std::unordered_map<std::uint64_t,std::vector<std::uint32_t>>g2,g3;g2.reserve(180000);g3.reserve(1100000);for(std::size_t i=0;i<c2.size();++i){auto a=lo2[i],b=hi2[i];if(!a||a==INF||!b||a>=b||b>base.size())throw std::runtime_error("c2 support");g2[key2(a-1,b-1)].push_back(c2[i]);}for(std::size_t i=0;i<c3.size();++i){std::uint64_t a=lo3[i],c=hi3[i],s=s3[i];if(!a||a==INF||!c||a>=c||s<=a+c)throw std::runtime_error("c3 support");std::uint64_t b=s-a-c;if(!(a<b&&b<c&&c<=base.size()))throw std::runtime_error("c3 middle");g3[key3(a-1,b-1,c-1)].push_back(c3[i]);}
 std::unordered_map<Quad,std::vector<std::uint32_t>,QuadHash>g4;g4.reserve(c4.size()*2+1);for(std::size_t i=0;i<c4.size();++i){std::uint64_t a=lo4[i],d=hi4[i],s=s4[i];if(!a||a==INF||!d||a>=d||s<=a+d)throw std::runtime_error("c4 support");std::uint64_t mids=s-a-d,edge=a*a+d*d;if(q4[i]<edge)throw std::runtime_error("c4 sumsq");std::uint64_t qm=q4[i]-edge;if(2*qm<mids*mids)throw std::runtime_error("c4 disc sign");std::uint64_t disc=2*qm-mids*mids,r=isqrt_u64(disc);if(r*r!=disc||mids<r||((mids-r)&1))throw std::runtime_error("c4 disc");std::uint64_t b=(mids-r)/2,c=(mids+r)/2;if(!(a<b&&b<c&&c<d&&d<=base.size()))throw std::runtime_error("c4 roots");g4[quad(a-1,b-1,c-1,d-1)].push_back(c4[i]);}
 std::vector<Entry5>e5;e5.reserve(c5.size());for(std::size_t i=0;i<c5.size();++i){std::uint64_t a=lo5[i],e=hi5[i];if(!a||a==INF||!e||a>=e||e>base.size())throw std::runtime_error("c5 extrema");if(s5[i]<=a+e||q5[i]<a*a+e*e||r5[i]<a*a*a+e*e*e)throw std::runtime_error("c5 moments edge");auto mid=recover_middle3(s5[i]-a-e,q5[i]-a*a-e*e,r5[i]-a*a*a-e*e*e,(std::uint32_t)a,(std::uint32_t)e);Quint q{(std::uint32_t)(a-1),mid[0]-1,mid[1]-1,mid[2]-1,(std::uint32_t)(e-1)};if(!(q.a<q.b&&q.b<q.c&&q.c<q.d&&q.d<q.e))throw std::runtime_error("c5 order");e5.push_back({q,c5[i]});}
 std::sort(e5.begin(),e5.end(),[](const Entry5&x,const Entry5&y){return x.q<y.q||(x.q==y.q&&x.v<y.v);});
 std::uint64_t groups=0,eligible=0;std::size_t maxpool=0;std::vector<std::uint32_t>chosen;Quint win{};bool found=false;auto append=[&](std::vector<std::uint32_t>&p,const auto&v){p.insert(p.end(),v.begin(),v.end());};
 for(std::size_t at=0;at<e5.size()&&!found;){std::size_t ed=at+1;while(ed<e5.size()&&e5[ed].q==e5[at].q)++ed;++groups;auto q=e5[at].q;std::array<std::uint32_t,5>x{q.a,q.b,q.c,q.d,q.e};std::vector<std::uint32_t>p;for(auto a:x)append(p,g1[a]);for(int i=0;i<5;++i)for(int j=i+1;j<5;++j){auto it=g2.find(key2(x[i],x[j]));if(it!=g2.end())append(p,it->second);}for(int i=0;i<5;++i)for(int j=i+1;j<5;++j)for(int k=j+1;k<5;++k){auto it=g3.find(key3(x[i],x[j],x[k]));if(it!=g3.end())append(p,it->second);}for(int omit=0;omit<5;++omit){std::array<std::uint32_t,4>y{};int z=0;for(int i=0;i<5;++i)if(i!=omit)y[z++]=x[i];auto it=g4.find(quad(y[0],y[1],y[2],y[3]));if(it!=g4.end())append(p,it->second);}for(std::size_t i=at;i<ed;++i)p.push_back(e5[i].v);std::sort(p.begin(),p.end());p.erase(std::unique(p.begin(),p.end()),p.end());maxpool=std::max(maxpool,p.size());if(p.size()>=7){++eligible;if(find_k(p,7,chosen)){win=q;found=true;break;}}at=ed;}
 if(found){std::cout<<"{\"kind\":\"replace5add7\",\"method\":\"exact-unrestricted-r5-direct-c5\",\"baseline_size\":"<<base.size()<<",\"remove\":["<<base[win.a]<<','<<base[win.b]<<','<<base[win.c]<<','<<base[win.d]<<','<<base[win.e]<<"],\"add\":[";for(std::size_t i=0;i<chosen.size();++i)std::cout<<(i?",":"")<<chosen[i];std::cout<<"],\"coverage5_groups_checked\":"<<groups<<"}\n";return 0;}
 std::cout<<"{\"kind\":\"none\",\"method\":\"exact-unrestricted-r5-direct-c5\",\"baseline_size\":"<<base.size()<<",\"coverage0\":0,\"coverage1\":"<<c1.size()<<",\"coverage2\":"<<c2.size()<<",\"coverage3\":"<<c3.size()<<",\"coverage4\":"<<c4.size()<<",\"coverage5\":"<<c5.size()<<",\"coverage2_groups\":"<<g2.size()<<",\"coverage3_groups\":"<<g3.size()<<",\"coverage4_groups\":"<<g4.size()<<",\"coverage5_groups_checked\":"<<groups<<",\"eligible_groups\":"<<eligible<<",\"max_supported_pool\":"<<maxpool<<"}\n";return 0;
}catch(const std::exception&e){std::cerr<<"error: "<<e.what()<<"\n";return 1;}}
