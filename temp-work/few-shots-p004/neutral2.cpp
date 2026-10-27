#include <algorithm>
#include <array>
#include <bit>
#include <cstdint>
#include <fstream>
#include <functional>
#include <iostream>
#include <limits>
#include <numeric>
#include <set>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>

namespace {
constexpr int Q=7,D=5,U=16807,N=367,K=9,XW=(N+63)/64;
using Dig=std::array<std::uint8_t,D>;using Foot=std::array<std::uint64_t,XW>;
struct Pair{int c,a;};struct Port{int c,a,s;};
int enc(const Dig&d){int v=0;for(auto x:d)v=v*Q+x;return v;}
Dig dec(int v){Dig d{};for(int i=D-1;i>=0;--i){d[i]=v%Q;v/=Q;}return d;}
bool confd(const Dig&a,const Dig&b){for(int i=0;i<D;++i){int z=(int(a[i])-int(b[i])+Q)%Q;if(z!=0&&z!=1&&z!=Q-1)return false;}return true;}
struct W{std::array<Dig,U>d{};std::vector<std::array<int,243>>nb;std::array<Foot,U>xf{};explicit W(const std::vector<int>&x):nb(U){for(int v=0;v<U;++v)d[v]=dec(v);for(int v=0;v<U;++v){int p=0;for(int m=0;m<243;++m){int t=m;auto z=d[v];for(int j=0;j<D;++j){int q=t%3-1;t/=3;z[j]=(z[j]+q+Q)%Q;}nb[v][p++]=enc(z);}std::sort(nb[v].begin(),nb[v].end());}for(int v=0;v<U;++v){xf[v].fill(0);for(int i=0;i<N;++i)if(confd(d[v],d[x[i]]))xf[v][i/64]|=1ull<<(i%64);}}};
bool conf(const W&w,int a,int b){return confd(w.d[a],w.d[b]);}
std::vector<int>load(const std::string&p){std::ifstream in(p);std::vector<int>r;int a,b,c,d,e;while(in>>a>>b>>c>>d>>e)r.push_back(enc(Dig{(uint8_t)a,(uint8_t)b,(uint8_t)c,(uint8_t)d,(uint8_t)e}));if(r.size()!=N||std::unordered_set<int>(r.begin(),r.end()).size()!=N)throw std::runtime_error("bad R");return r;}
std::vector<int>makex(const std::vector<int>&r,const std::array<Dig,U>&d){std::vector<int>x;for(int id:r){auto a=d[id];x.push_back(enc(Dig{(uint8_t)((2-a[1]+Q)%Q),a[3],a[0],(uint8_t)((2-a[2]+Q)%Q),a[4]}));}x[267]=enc(Dig{1,5,6,3,5});return x;}
struct Info{std::vector<Pair>priv;int centers;};
Info analyze(const W&w,const std::vector<int>&p){std::array<uint16_t,U>cnt{};std::array<char,U>in{};for(int z:p){in[z]=1;for(int q:w.nb[z])++cnt[q];}std::vector<Pair>v;std::unordered_set<int>cs;for(int q=0;q<U;++q)if(!in[q]&&cnt[q]==1){int c=-1;for(int z:w.nb[q])if(in[z]){c=z;break;}v.push_back({c,q});cs.insert(c);}return{std::move(v),(int)cs.size()};}
int overlap(const Foot&a,const Foot&b){int c=0;for(int i=0;i<XW;++i)c+=std::popcount(a[i]&b[i]);return c;}void OR(Foot&a,const Foot&b){for(int i=0;i<XW;++i)a[i]|=b[i];}
int best_overlap(const W&w,const Info&info,std::vector<Port>&best){if(info.centers<K)return 1e9;std::unordered_map<int,std::vector<int>>by;for(auto&p:info.priv)by[p.c].push_back(p.a);std::vector<int>cs;for(auto&[c,a]:by)cs.push_back(c);int bo=1e9;best.clear();std::vector<Port>ch;std::vector<int>hs,vs;std::unordered_set<int>used;Foot hu{},vu{};hu.fill(0);vu.fill(0);
 std::function<void(int)>dfs=[&](int pos){if(ch.size()==K){int o=overlap(hu,vu);if(o<bo){bo=o;best=ch;}return;}if(pos>=(int)cs.size())return;if(ch.size()+cs.size()-pos<K)return;for(int ci=pos;ci<(int)cs.size();++ci){std::swap(cs[pos],cs[ci]);int c=cs[pos];for(int a:by[c])for(int s=0;s<2;++s){int h=s?a:c,v=s?c:a;bool ok=true;for(int z:hs)if(conf(w,h,z)){ok=false;break;}if(ok)for(int z:vs)if(conf(w,v,z)){ok=false;break;}if(!ok)continue;auto oh=hu,ov=vu;OR(hu,w.xf[h]);OR(vu,w.xf[v]);int lower=overlap(hu,vu);if(lower<bo){hs.push_back(h);vs.push_back(v);ch.push_back({c,a,s});dfs(pos+1);ch.pop_back();vs.pop_back();hs.pop_back();}hu=oh;vu=ov;}std::swap(cs[pos],cs[ci]);}};dfs(0);return bo;}
std::string key(std::vector<int>p){std::sort(p.begin(),p.end());std::string s(2*p.size(),'\0');for(size_t i=0;i<p.size();++i){s[2*i]=p[i]&255;s[2*i+1]=(p[i]>>8)&255;}return s;}
}
int main(int argc,char**argv){try{if(argc!=3){std::cerr<<"usage: neutral2 R367 OUT\n";return 2;}std::array<Dig,U>d{};for(int i=0;i<U;++i)d[i]=dec(i);auto r=load(argv[1]);auto x=makex(r,d);W w(x);std::unordered_map<int,int>idx;for(int i=0;i<N;++i)idx[r[i]]=i;std::array<uint16_t,U>cnt{};std::array<int,U>o1{},o2{};o1.fill(-1);o2.fill(-1);std::array<char,U>in{};for(int i=0;i<N;++i){in[r[i]]=1;for(int q:w.nb[r[i]]){if(cnt[q]==0)o1[q]=i;else if(cnt[q]==1)o2[q]=i;++cnt[q];}}
 std::unordered_map<std::uint64_t,std::vector<int>>pool;auto pk=[](int a,int b){if(a>b)std::swap(a,b);return(std::uint64_t(a)<<32)|std::uint32_t(b);};
 // For every removed owner pair, admissible outside additions are all support-1 points of either owner plus support-2 points of the pair.
 std::vector<std::vector<int>>one(N);for(int q=0;q<U;++q)if(!in[q]&&cnt[q]==1)one[o1[q]].push_back(q);for(int q=0;q<U;++q)if(!in[q]&&cnt[q]==2)pool[pk(o1[q],o2[q])].push_back(q);
 std::unordered_set<std::string>seen;long long states=0;int maxpriv=0,maxcent=0,bestov=1e9;std::vector<int>beststate;std::vector<Port>bestports;std::array<int,2>bestrem{},bestadd{};
 std::set<std::uint64_t>ownerpairs;for(auto&[k,v]:pool)ownerpairs.insert(k);for(int i=0;i<N;++i)if(!one[i].empty())for(int j=i+1;j<N;++j)if(!one[j].empty())ownerpairs.insert(pk(i,j));
 for(auto k:ownerpairs){int a=k>>32,b=std::uint32_t(k);std::vector<int>cand=one[a];cand.insert(cand.end(),one[b].begin(),one[b].end());auto it=pool.find(k);if(it!=pool.end())cand.insert(cand.end(),it->second.begin(),it->second.end());std::sort(cand.begin(),cand.end());cand.erase(std::unique(cand.begin(),cand.end()),cand.end());for(int i=0;i<(int)cand.size();++i)for(int j=i+1;j<(int)cand.size();++j){if(conf(w,cand[i],cand[j]))continue;auto st=r;st[a]=cand[i];st[b]=cand[j];auto sk=key(st);if(!seen.insert(sk).second)continue;++states;auto inf=analyze(w,st);maxpriv=std::max(maxpriv,(int)inf.priv.size());maxcent=std::max(maxcent,inf.centers);if(inf.centers>=K){std::vector<Port>ports;int ov=best_overlap(w,inf,ports);if(ov<bestov){bestov=ov;beststate=st;bestports=ports;bestrem={a,b};bestadd={cand[i],cand[j]};std::cerr<<"neutral2 best state="<<states<<" private="<<inf.priv.size()<<" centers="<<inf.centers<<" overlap="<<ov<<"\n";}if(ov==0){std::cerr<<"neutral2 ZERO overlap state="<<states<<"\n";}}}}
 std::ofstream out(argv[2]);out<<"{\"kind\":\"none\",\"method\":\"exact-neutral-2-for-2-5d\",\"states\":"<<states<<",\"max_private\":"<<maxpriv<<",\"max_private_centers\":"<<maxcent<<",\"best_overlap\":"<<(bestov==1000000000?-1:bestov);if(!beststate.empty()){out<<",\"best_remove_indices\":["<<bestrem[0]<<','<<bestrem[1]<<"],\"best_add\":["<<bestadd[0]<<','<<bestadd[1]<<"],\"best_state\":[";for(size_t i=0;i<beststate.size();++i){if(i)out<<',';out<<beststate[i];}out<<"],\"best_ports\":[";for(size_t i=0;i<bestports.size();++i){if(i)out<<',';auto&p=bestports[i];out<<"{\"center\":"<<p.c<<",\"alt\":"<<p.a<<",\"side\":"<<p.s<<"}";}out<<']';}out<<"}\n";std::cerr<<"neutral2 DONE states="<<states<<" maxpriv="<<maxpriv<<" maxcent="<<maxcent<<" bestov="<<bestov<<"\n";return 0;}catch(const std::exception&e){std::cerr<<"error: "<<e.what()<<"\n";return 1;}}
