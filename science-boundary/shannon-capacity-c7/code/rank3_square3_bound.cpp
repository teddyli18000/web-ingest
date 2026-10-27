#include <algorithm>
#include <array>
#include <cstdint>
#include <fstream>
#include <functional>
#include <iostream>
#include <map>
#include <set>
#include <stdexcept>
#include <string>
#include <tuple>
#include <utility>
#include <vector>

namespace {
constexpr int Q=7,D=5,U=16807,N=367;
using Dig=std::array<int,D>;
using Sq=std::pair<int,int>;
struct Port{char o;int i,e;bool operator<(Port const&z)const{return std::tie(o,i,e)<std::tie(z.o,z.i,z.e);}bool operator==(Port const&z)const{return o==z.o&&i==z.i&&e==z.e;}};
struct VLess{bool operator()(std::vector<Sq> const&a,std::vector<Sq> const&b)const{return a<b;}};
Dig dec(int v){Dig d{};for(int i=D-1;i>=0;--i){d[i]=v%Q;v/=Q;}return d;}
int enc(const Dig&d){int v=0;for(int x:d)v=v*Q+x;return v;}
bool conf(const Dig&a,const Dig&b){for(int i=0;i<D;++i){int z=(a[i]-b[i]+Q)%Q;if(z!=0&&z!=1&&z!=Q-1)return false;}return true;}
std::vector<Sq> norm(std::vector<Sq> s){std::sort(s.begin(),s.end());s.erase(std::unique(s.begin(),s.end()),s.end());return s;}
std::vector<int> load_r(const std::string&p){std::ifstream in(p);if(!in)throw std::runtime_error("cannot open R367");std::vector<int> r;int a,b,c,d,e;while(in>>a>>b>>c>>d>>e)r.push_back(enc(Dig{a,b,c,d,e}));if(r.size()!=N)throw std::runtime_error("bad R367 size");return r;}
}

int main(int argc,char**argv){try{
 if(argc!=2){std::cerr<<"usage: rank3_square3_bound R367.txt\n";return 2;}
 std::vector<Dig>d(U);for(int v=0;v<U;++v)d[v]=dec(v);
 auto r0=load_r(argv[1]);auto r=r0;r[267]=15083;r[294]=16388;
 const std::array<int,9>K{60,160,231,244,250,267,330,344,364};std::array<char,N>isK{};for(int i:K)isK[i]=1;
 std::vector<int>B;std::array<char,U>isB{};for(int i=0;i<N;++i)if(!isK[i]){B.push_back(i);isB[r[i]]=1;}
 std::vector<int>x(N);for(int i=0;i<N;++i){auto a=d[r0[i]];x[i]=enc(Dig{(2-a[1]+Q)%Q,a[3],a[0],(2-a[2]+Q)%Q,a[4]});}x[267]=enc(Dig{1,5,6,3,5});
 auto pconf=[&](Port a,Port b){if(a.o=='H'&&b.o=='H')return conf(d[a.e],d[b.e])&&conf(d[x[a.i]],d[x[b.i]]);if(a.o=='V'&&b.o=='V')return conf(d[x[a.i]],d[x[b.i]])&&conf(d[a.e],d[b.e]);if(a.o=='H')return conf(d[a.e],d[x[b.i]])&&conf(d[x[a.i]],d[b.e]);return conf(d[x[b.i]],d[a.e])&&conf(d[b.e],d[x[a.i]]);};
 std::map<std::vector<int>,std::vector<int>> eg,xg;
 for(int v=0;v<U;++v){if(isB[v])continue;std::vector<int>o;for(int i:B)if(conf(d[v],d[r[i]])){o.push_back(i);if(o.size()>3)break;}if(o.size()<=3)eg[o].push_back(v);}
 for(int xi=0;xi<N;++xi){std::vector<int>o;for(int i:B)if(conf(d[x[xi]],d[r[i]])){o.push_back(i);if(o.size()>3)break;}if(o.size()<=3)xg[o].push_back(xi);}
 std::map<std::vector<Sq>,std::vector<Port>,VLess> groups[4];std::uint64_t ports[4]{};
 for(auto &[eo,es]:eg){if(eo.empty())continue;for(auto &[xo,xis]:xg){if(xo.empty())continue;int cost=eo.size()*xo.size();if(cost<1||cost>3)continue;for(int e:es)for(int xi:xis){std::vector<Sq>h,v;for(int a:eo)for(int b:xo){h.push_back({a,b});v.push_back({b,a});}h=norm(h);v=norm(v);if((int)h.size()!=cost||(int)v.size()!=cost)throw std::runtime_error("bad cost set");groups[cost][h].push_back({'H',xi,e});groups[cost][v].push_back({'V',xi,e});ports[cost]+=2;}}}
 // To exceed the deletion cost of 3, a three-square set must either contain an exact cost-3 group,
 // or contain at least two distinct exact cost-2 groups. If it contains at most one cost-2 group
 // and no cost-3 group, the already-certified threshold-2 bound contributes <=2 compatible ports
 // on that pair and the third singleton contributes <=1.
 std::set<std::vector<Sq>,VLess> triples;for(auto &[k,v]:groups[3])triples.insert(k);
 std::map<Sq,std::vector<std::vector<Sq>>> incident;for(auto &[k,v]:groups[2]){incident[k[0]].push_back(k);incident[k[1]].push_back(k);}
 std::uint64_t wedges=0;for(auto &[pivot,ks]:incident)for(size_t i=0;i<ks.size();++i)for(size_t j=i+1;j<ks.size();++j){auto u=ks[i];u.insert(u.end(),ks[j].begin(),ks[j].end());u=norm(u);if(u.size()==3){triples.insert(u);++wedges;}}
 int raw_best=0,compatible_best=0;std::uint64_t dfs_nodes=0;
 for(auto const&S:triples){std::vector<Port>pool;auto i3=groups[3].find(S);if(i3!=groups[3].end())pool.insert(pool.end(),i3->second.begin(),i3->second.end());for(int omit=0;omit<3;++omit){std::vector<Sq>k;for(int q=0;q<3;++q)if(q!=omit)k.push_back(S[q]);auto it=groups[2].find(k);if(it!=groups[2].end())pool.insert(pool.end(),it->second.begin(),it->second.end());}for(auto sq:S){std::vector<Sq>k{sq};auto it=groups[1].find(k);if(it!=groups[1].end())pool.insert(pool.end(),it->second.begin(),it->second.end());}std::sort(pool.begin(),pool.end());pool.erase(std::unique(pool.begin(),pool.end()),pool.end());raw_best=std::max(raw_best,(int)pool.size());if(pool.size()<=3){compatible_best=std::max(compatible_best,(int)pool.size());continue;}if(pool.size()>28)throw std::runtime_error("unexpected large pool");std::vector<int>chosen;bool found=false;std::function<void(int)>dfs=[&](int start){if(found)return;if(chosen.size()>=4){found=true;return;}if((int)chosen.size()+(int)pool.size()-start<4)return;for(int i=start;i<(int)pool.size()&&!found;++i){bool ok=true;for(int q:chosen)if(pconf(pool[i],pool[q])){ok=false;break;}if(!ok)continue;chosen.push_back(i);++dfs_nodes;dfs(i+1);chosen.pop_back();}};dfs(0);if(found){std::cout<<"{\"threshold3_reduces_to_threshold0\":false,\"witness_square_triple\":[";for(int i=0;i<3;++i){if(i)std::cout<<',';std::cout<<'['<<S[i].first<<','<<S[i].second<<']';}std::cout<<"],\"raw_pool\":"<<pool.size()<<"}\n";return 0;}compatible_best=std::max(compatible_best,3);}
 std::cout<<"{\"state\":18,\"k9\":[60,160,231,244,250,267,330,344,364],\"cost1_groups\":"<<groups[1].size()<<",\"cost2_groups\":"<<groups[2].size()<<",\"cost3_groups\":"<<groups[3].size()<<",\"cost1_ports\":"<<ports[1]<<",\"cost2_ports\":"<<ports[2]<<",\"cost3_ports\":"<<ports[3]<<",\"candidate_three_square_sets\":"<<triples.size()<<",\"cost2_wedges\":"<<wedges<<",\"max_raw_ports_unlocked_by_three_deletions\":"<<raw_best<<",\"max_pairwise_compatible_ports_unlocked_by_three_deletions\":"<<compatible_best<<",\"dfs_nodes\":"<<dfs_nodes<<",\"threshold3_reduces_to_threshold0\":true}\n";
 return 0;
}catch(const std::exception&e){std::cerr<<"error: "<<e.what()<<"\n";return 1;}}
