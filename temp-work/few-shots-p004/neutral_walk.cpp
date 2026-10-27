#include <algorithm>
#include <array>
#include <bit>
#include <cstdint>
#include <fstream>
#include <functional>
#include <iostream>
#include <limits>
#include <numeric>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>

namespace {
constexpr int Q=7,D=5,U=16807,N=367,K=9,XW=(N+63)/64,TOPN=30;
using Dig=std::array<std::uint8_t,D>;using Foot=std::array<std::uint64_t,XW>;
struct Pair{int c,a;};struct Rec{int ov,priv,centers,depth;std::vector<int>state;};
int enc(const Dig&d){int v=0;for(auto x:d)v=v*Q+x;return v;}Dig dec(int v){Dig d{};for(int i=D-1;i>=0;--i){d[i]=v%Q;v/=Q;}return d;}
bool confd(const Dig&a,const Dig&b){for(int i=0;i<D;++i){int z=(int(a[i])-int(b[i])+Q)%Q;if(z!=0&&z!=1&&z!=Q-1)return false;}return true;}
struct W{std::array<Dig,U>d{};std::vector<std::array<int,243>>nb;std::array<Foot,U>xf{};explicit W(const std::vector<int>&x):nb(U){for(int v=0;v<U;++v)d[v]=dec(v);for(int v=0;v<U;++v){int p=0;for(int m=0;m<243;++m){int t=m;auto z=d[v];for(int j=0;j<D;++j){int q=t%3-1;t/=3;z[j]=(z[j]+q+Q)%Q;}nb[v][p++]=enc(z);}std::sort(nb[v].begin(),nb[v].end());}for(int v=0;v<U;++v){xf[v].fill(0);for(int i=0;i<N;++i)if(confd(d[v],d[x[i]]))xf[v][i/64]|=1ull<<(i%64);}}};
bool conf(const W&w,int a,int b){return confd(w.d[a],w.d[b]);}
std::vector<int>load(const std::string&p){std::ifstream in(p);std::vector<int>r;int a,b,c,d,e;while(in>>a>>b>>c>>d>>e)r.push_back(enc(Dig{(uint8_t)a,(uint8_t)b,(uint8_t)c,(uint8_t)d,(uint8_t)e}));if(r.size()!=N||std::unordered_set<int>(r.begin(),r.end()).size()!=N)throw std::runtime_error("bad R");return r;}
std::vector<int>makex(const std::vector<int>&r,const std::array<Dig,U>&d){std::vector<int>x;for(int id:r){auto a=d[id];x.push_back(enc(Dig{(uint8_t)((2-a[1]+Q)%Q),a[3],a[0],(uint8_t)((2-a[2]+Q)%Q),a[4]}));}x[267]=enc(Dig{1,5,6,3,5});return x;}
struct Info{std::vector<Pair>priv;int centers;};
Info analyze(const W&w,const std::vector<int>&p){std::array<uint16_t,U>cnt{};std::array<char,U>in{};for(int z:p){in[z]=1;for(int q:w.nb[z])++cnt[q];}std::vector<Pair>v;std::unordered_set<int>cs;for(int q=0;q<U;++q)if(!in[q]&&cnt[q]==1){int c=-1;for(int z:w.nb[q])if(in[z]){c=z;break;}if(c<0)throw std::runtime_error("private without center");v.push_back({c,q});cs.insert(c);}return{std::move(v),(int)cs.size()};}
int overlap(const Foot&a,const Foot&b){int c=0;for(int i=0;i<XW;++i)c+=std::popcount(a[i]&b[i]);return c;}void OR(Foot&a,const Foot&b){for(int i=0;i<XW;++i)a[i]|=b[i];}
int best_overlap(const W&w,const Info&info){if(info.centers<K)return 1000000000;std::unordered_map<int,std::vector<int>>by;for(auto&p:info.priv)by[p.c].push_back(p.a);std::vector<int>cs;for(auto&[c,a]:by)cs.push_back(c);int bo=1000000000;std::vector<int>hs,vs;Foot hu{},vu{};hu.fill(0);vu.fill(0);int chosen=0;std::function<void(int)>dfs=[&](int pos){if(chosen==K){bo=std::min(bo,overlap(hu,vu));return;}if(pos>=(int)cs.size()||chosen+(int)cs.size()-pos<K)return;for(int ci=pos;ci<(int)cs.size();++ci){std::swap(cs[pos],cs[ci]);int c=cs[pos];for(int a:by[c])for(int s=0;s<2;++s){int h=s?a:c,v=s?c:a;bool ok=true;for(int z:hs)if(conf(w,h,z)){ok=false;break;}if(ok)for(int z:vs)if(conf(w,v,z)){ok=false;break;}if(!ok)continue;auto oh=hu,ov=vu;OR(hu,w.xf[h]);OR(vu,w.xf[v]);int lower=overlap(hu,vu);if(lower<bo){hs.push_back(h);vs.push_back(v);++chosen;dfs(pos+1);--chosen;vs.pop_back();hs.pop_back();}hu=oh;vu=ov;}std::swap(cs[pos],cs[ci]);}};dfs(0);return bo;}
std::string key(std::vector<int>p){std::sort(p.begin(),p.end());std::string s(2*p.size(),'\0');for(size_t i=0;i<p.size();++i){s[2*i]=p[i]&255;s[2*i+1]=(p[i]>>8)&255;}return s;}
bool better(const Rec&a,const Rec&b){if(a.ov!=b.ov)return a.ov<b.ov;if(a.centers!=b.centers)return a.centers>b.centers;if(a.priv!=b.priv)return a.priv>b.priv;return a.depth<b.depth;}
void keep(std::vector<Rec>&top,Rec&&r){top.push_back(std::move(r));std::sort(top.begin(),top.end(),better);if((int)top.size()>TOPN)top.resize(TOPN);}
}
int main(int argc,char**argv){try{if(argc!=4){std::cerr<<"usage: neutral_walk R367 OUT MAX_DEPTH\n";return 2;}int md=std::stoi(argv[3]);if(md<0||md>8)throw std::runtime_error("depth 0..8");std::array<Dig,U>d{};for(int i=0;i<U;++i)d[i]=dec(i);auto r0=load(argv[1]);auto x=makex(r0,d);W w(x);
 std::vector<std::vector<int>>front{r0};std::unordered_set<std::string>seen;seen.reserve(200000);seen.insert(key(r0));long long states=0,evaluated=0;int maxpriv=0,maxcent=0,bestov=1000000000;std::vector<Rec>top;
 for(int depth=0;depth<=md;++depth){std::cerr<<"walk depth="<<depth<<" frontier="<<front.size()<<" seen="<<seen.size()<<"\n";std::vector<std::vector<int>>next;for(const auto&st:front){++states;auto inf=analyze(w,st);maxpriv=std::max(maxpriv,(int)inf.priv.size());maxcent=std::max(maxcent,inf.centers);if(inf.centers>=K){++evaluated;int ov=best_overlap(w,inf);if(ov<bestov){bestov=ov;std::cerr<<"walk best depth="<<depth<<" state="<<states<<" private="<<inf.priv.size()<<" centers="<<inf.centers<<" overlap="<<ov<<"\n";}keep(top,Rec{ov,(int)inf.priv.size(),inf.centers,depth,st});}if(depth==md)continue;for(auto p:inf.priv){auto q=st;auto it=std::find(q.begin(),q.end(),p.c);if(it==q.end())throw std::runtime_error("center absent");*it=p.a;auto sk=key(q);if(seen.insert(sk).second)next.push_back(std::move(q));}}
  front=std::move(next);
 }
 std::ofstream out(argv[2]);if(!out)throw std::runtime_error("cannot write");out<<"{\"kind\":\"neutral-walk-states\",\"method\":\"exact-sequential-neutral-swap-walk\",\"max_depth\":"<<md<<",\"states\":"<<states<<",\"seen\":"<<seen.size()<<",\"evaluated\":"<<evaluated<<",\"max_private\":"<<maxpriv<<",\"max_private_centers\":"<<maxcent<<",\"best_overlap\":"<<(bestov==1000000000?-1:bestov)<<",\"top\":[";
 for(size_t z=0;z<top.size();++z){if(z)out<<',';auto&t=top[z];std::vector<int>ri,av;for(int i=0;i<N;++i)if(t.state[i]!=r0[i]){ri.push_back(i);av.push_back(t.state[i]);}out<<"{\"overlap\":"<<t.ov<<",\"private\":"<<t.priv<<",\"centers\":"<<t.centers<<",\"depth\":"<<t.depth<<",\"remove_indices\":[";for(size_t i=0;i<ri.size();++i){if(i)out<<',';out<<ri[i];}out<<"],\"add\":[";for(size_t i=0;i<av.size();++i){if(i)out<<',';out<<av[i];}out<<"],\"state\":[";for(size_t i=0;i<t.state.size();++i){if(i)out<<',';out<<t.state[i];}out<<"]}";}out<<"]}\n";
 std::cerr<<"walk DONE states="<<states<<" seen="<<seen.size()<<" evaluated="<<evaluated<<" maxpriv="<<maxpriv<<" maxcent="<<maxcent<<" bestov="<<(bestov==1000000000?-1:bestov)<<"\n";return 0;}catch(const std::exception&e){std::cerr<<"error: "<<e.what()<<"\n";return 1;}}
