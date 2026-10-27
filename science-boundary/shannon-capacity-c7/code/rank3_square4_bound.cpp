#include <algorithm>
#include <array>
#include <cstdint>
#include <fstream>
#include <functional>
#include <iostream>
#include <map>
#include <stdexcept>
#include <string>
#include <tuple>
#include <unordered_map>
#include <unordered_set>
#include <utility>
#include <vector>

namespace {
constexpr int Q=7,D=5,U=16807,N=367;
using Dig=std::array<int,D>;
using Sq=std::pair<int,int>;
using Key=std::vector<int>; // encoded square vertices a*N+b, sorted
struct Port{char o;int i,e;bool operator<(Port const&z)const{return std::tie(o,i,e)<std::tie(z.o,z.i,z.e);}bool operator==(Port const&z)const{return o==z.o&&i==z.i&&e==z.e;}};
struct VLess{bool operator()(Key const&a,Key const&b)const{return a<b;}};
struct A3Hash{size_t operator()(std::array<int,3> const&a)const noexcept{size_t h=1469598103934665603ull;for(int x:a){h^=(uint32_t)x;h*=1099511628211ull;}return h;}};
struct A4Hash{size_t operator()(std::array<int,4> const&a)const noexcept{size_t h=1469598103934665603ull;for(int x:a){h^=(uint32_t)x;h*=1099511628211ull;}return h;}};
Dig dec(int v){Dig d{};for(int i=D-1;i>=0;--i){d[i]=v%Q;v/=Q;}return d;}
int enc(const Dig&d){int v=0;for(int x:d)v=v*Q+x;return v;}
bool conf(const Dig&a,const Dig&b){for(int i=0;i<D;++i){int z=(a[i]-b[i]+Q)%Q;if(z!=0&&z!=1&&z!=Q-1)return false;}return true;}
std::vector<int> load_r(const std::string&p){std::ifstream in(p);if(!in)throw std::runtime_error("cannot open R367");std::vector<int> r;int a,b,c,d,e;while(in>>a>>b>>c>>d>>e)r.push_back(enc(Dig{a,b,c,d,e}));if(r.size()!=N)throw std::runtime_error("bad R367 size");return r;}
Key norm(Key k){std::sort(k.begin(),k.end());k.erase(std::unique(k.begin(),k.end()),k.end());return k;}
Key uni(const Key&a,const Key&b){Key z=a;z.insert(z.end(),b.begin(),b.end());return norm(std::move(z));}
std::array<int,4> a4(const Key&k){if(k.size()!=4)throw std::runtime_error("not four");return {k[0],k[1],k[2],k[3]};}
std::array<int,3> a3(const Key&k){if(k.size()!=3)throw std::runtime_error("not three");return {k[0],k[1],k[2]};}
uint64_t paircode(int a,int b){if(a>b)std::swap(a,b);return (uint64_t(uint32_t(a))<<32)|uint32_t(b);}
void print_sq(int s){std::cout<<'['<<(s/N)<<','<<(s%N)<<']';}
}

int main(int argc,char**argv){try{
 if(argc!=2){std::cerr<<"usage: rank3_square4_bound R367.txt\n";return 2;}
 std::vector<Dig>d(U);for(int v=0;v<U;++v)d[v]=dec(v);
 auto r0=load_r(argv[1]);auto r=r0;r[267]=15083;r[294]=16388;
 const std::array<int,9>K{60,160,231,244,250,267,330,344,364};std::array<char,N>isK{};for(int i:K)isK[i]=1;
 std::vector<int>B;std::array<char,U>isB{};for(int i=0;i<N;++i)if(!isK[i]){B.push_back(i);isB[r[i]]=1;}
 std::vector<int>x(N);for(int i=0;i<N;++i){auto a=d[r0[i]];x[i]=enc(Dig{(2-a[1]+Q)%Q,a[3],a[0],(2-a[2]+Q)%Q,a[4]});}x[267]=enc(Dig{1,5,6,3,5});
 auto pconf=[&](Port a,Port b){if(a.o=='H'&&b.o=='H')return conf(d[a.e],d[b.e])&&conf(d[x[a.i]],d[x[b.i]]);if(a.o=='V'&&b.o=='V')return conf(d[x[a.i]],d[x[b.i]])&&conf(d[a.e],d[b.e]);if(a.o=='H')return conf(d[a.e],d[x[b.i]])&&conf(d[x[a.i]],d[b.e]);return conf(d[x[b.i]],d[a.e])&&conf(d[b.e],d[x[a.i]]);};

 std::map<std::vector<int>,std::vector<int>> eg,xg;
 for(int v=0;v<U;++v){if(isB[v])continue;std::vector<int>o;for(int i:B)if(conf(d[v],d[r[i]])){o.push_back(i);if(o.size()>4)break;}if(o.size()<=4)eg[o].push_back(v);}
 for(int xi=0;xi<N;++xi){std::vector<int>o;for(int i:B)if(conf(d[x[xi]],d[r[i]])){o.push_back(i);if(o.size()>4)break;}if(o.size()<=4)xg[o].push_back(xi);}

 std::map<Key,std::vector<Port>,VLess> groups[5];std::uint64_t ports[5]{};
 for(auto &[eo,es]:eg){if(eo.empty())continue;for(auto &[xo,xis]:xg){if(xo.empty())continue;int cost=int(eo.size()*xo.size());if(cost<1||cost>4)continue;for(int e:es)for(int xi:xis){Key h,v;h.reserve(cost);v.reserve(cost);for(int a:eo)for(int b:xo){h.push_back(a*N+b);v.push_back(b*N+a);}h=norm(std::move(h));v=norm(std::move(v));if((int)h.size()!=cost||(int)v.size()!=cost)throw std::runtime_error("bad cost support");groups[cost][h].push_back({'H',xi,e});groups[cost][v].push_back({'V',xi,e});ports[cost]+=2;}}}
 if(groups[1].size()!=3520||groups[2].size()!=21184||groups[3].size()!=97712||ports[1]!=3520||ports[2]!=24896||ports[3]!=103216)throw std::runtime_error("threshold-3 support census drift");

 std::vector<Key> k2,k3; k2.reserve(groups[2].size());k3.reserve(groups[3].size());
 for(auto const&z:groups[2])k2.push_back(z.first);for(auto const&z:groups[3])k3.push_back(z.first);
 std::vector<std::vector<int>> inc2(N*N);
 for(int i=0;i<(int)k2.size();++i)for(int s:k2[i])inc2[s].push_back(i);
 std::unordered_map<uint64_t,std::vector<int>> inc3pair;inc3pair.reserve(k3.size()*3);
 for(int i=0;i<(int)k3.size();++i)for(int a=0;a<3;++a)for(int b=a+1;b<3;++b)inc3pair[paircode(k3[i][a],k3[i][b])].push_back(i);

 std::unordered_set<std::array<int,4>,A4Hash> quads;quads.reserve(groups[4].size()*2+2000000);
 std::uint64_t from4=0,from32=0,from33=0,from222=0,wedge_raw=0;
 auto addq=[&](const Key&z,std::uint64_t &ctr){if(z.size()==4){quads.insert(a4(z));++ctr;}};
 for(auto const&z:groups[4]){quads.insert(a4(z.first));++from4;}

 // If a compatible 5-set contains a cost-3 support T, threshold-3 says at
 // least two selected ports must use the fourth square. Two singleton ports on
 // that square are impossible by threshold-1, so one such port has cost 2 or 3.
 // Hence S is generated by T union a cost-2/3 support.
 for(int i=0;i<(int)k3.size();++i){auto const&T=k3[i];
   for(int s:T)for(int j:inc2[s])addq(uni(T,k2[j]),from32);
   for(int a=0;a<3;++a)for(int b=a+1;b<3;++b){auto it=inc3pair.find(paircode(T[a],T[b]));if(it==inc3pair.end())continue;for(int j:it->second)if(j!=i)addq(uni(T,k3[j]),from33);}
 }

 // If all selected supports have cost <=2, five compatible ports on four
 // squares require at least three distinct cost-2 supports spanning all four.
 // Otherwise threshold-2/3 plus at most one singleton on a new square gives <=4.
 // Generate each such four-set from a cost-2 wedge (union size 3) plus a third
 // cost-2 support that reaches the fourth square.
 std::unordered_set<std::array<int,3>,A3Hash> wedges;wedges.reserve(100000);
 for(int pivot=0;pivot<N*N;++pivot){auto const&ks=inc2[pivot];for(size_t a=0;a<ks.size();++a)for(size_t b=a+1;b<ks.size();++b){if(ks[a]==ks[b])continue;auto z=uni(k2[ks[a]],k2[ks[b]]);if(z.size()==3){wedges.insert(a3(z));++wedge_raw;}}}
 for(auto const&A:wedges){Key T{A[0],A[1],A[2]};for(int s:T)for(int j:inc2[s])addq(uni(T,k2[j]),from222);}

 std::uint64_t scanned=0,dfs_nodes=0;size_t max_pool=0;std::array<Port,5>witness{};std::array<int,4>witnessS{};
 for(auto const&Sarr:quads){Key S{Sarr[0],Sarr[1],Sarr[2],Sarr[3]};std::vector<Port>pool;
   for(unsigned mask=1;mask<16;++mask){Key k;for(int b=0;b<4;++b)if(mask&(1u<<b))k.push_back(S[b]);int c=k.size();auto it=groups[c].find(k);if(it!=groups[c].end())pool.insert(pool.end(),it->second.begin(),it->second.end());}
   std::sort(pool.begin(),pool.end());pool.erase(std::unique(pool.begin(),pool.end()),pool.end());++scanned;max_pool=std::max(max_pool,pool.size());if(pool.size()<5)continue;
   std::vector<int>chosen;bool found=false;std::function<void(int)>dfs=[&](int start){if(found)return;if(chosen.size()==5){found=true;return;}if((int)chosen.size()+(int)pool.size()-start<5)return;for(int i=start;i<(int)pool.size()&&!found;++i){bool ok=true;for(int q:chosen)if(pconf(pool[i],pool[q])){ok=false;break;}if(!ok)continue;chosen.push_back(i);++dfs_nodes;dfs(i+1);if(!found)chosen.pop_back();}};dfs(0);
   if(found){for(int q=0;q<5;++q)witness[q]=pool[chosen[q]];witnessS=Sarr;std::cout<<"{\"threshold4_reduces_to_threshold0\":false,\"witness_square_quad\":[";for(int q=0;q<4;++q){if(q)std::cout<<',';print_sq(witnessS[q]);}std::cout<<"],\"witness_ports\":[";for(int q=0;q<5;++q){if(q)std::cout<<',';auto p=witness[q];std::cout<<"[\""<<p.o<<"\","<<p.i<<','<<p.e<<']';}std::cout<<"],\"raw_pool\":"<<pool.size()<<",\"candidate_four_square_sets\":"<<quads.size()<<"}\n";return 0;}
 }
 std::cout<<"{\"state\":18,\"k9\":[60,160,231,244,250,267,330,344,364],\"cost1_groups\":"<<groups[1].size()<<",\"cost2_groups\":"<<groups[2].size()<<",\"cost3_groups\":"<<groups[3].size()<<",\"cost4_groups\":"<<groups[4].size()<<",\"cost1_ports\":"<<ports[1]<<",\"cost2_ports\":"<<ports[2]<<",\"cost3_ports\":"<<ports[3]<<",\"cost4_ports\":"<<ports[4]<<",\"candidate_four_square_sets\":"<<quads.size()<<",\"generated_from_cost4\":"<<from4<<",\"generated_from_cost3_cost2\":"<<from32<<",\"generated_from_cost3_cost3\":"<<from33<<",\"cost2_wedges_unique\":"<<wedges.size()<<",\"cost2_wedges_raw\":"<<wedge_raw<<",\"generated_from_three_cost2\":"<<from222<<",\"candidate_sets_scanned\":"<<scanned<<",\"max_raw_ports_unlocked_by_four_deletions\":"<<max_pool<<",\"dfs_nodes\":"<<dfs_nodes<<",\"max_pairwise_compatible_ports_unlocked_by_four_deletions\":4,\"threshold4_reduces_to_threshold0\":true}\n";
 return 0;
}catch(const std::exception&e){std::cerr<<"error: "<<e.what()<<"\n";return 1;}}
