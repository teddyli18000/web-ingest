#include <algorithm>
#include <array>
#include <bit>
#include <bitset>
#include <cstdint>
#include <fstream>
#include <functional>
#include <iostream>
#include <numeric>
#include <string>
#include <unordered_set>
#include <vector>

namespace {
constexpr int Q=7,D=5,U=16807,N=367,K=9;
using Dig=std::array<std::uint8_t,D>;
struct Pair{int c,a;}; struct Port{int c,a,s;};
int enc(const Dig&d){int v=0;for(auto x:d)v=v*Q+x;return v;}
Dig dec(int v){Dig d{};for(int i=D-1;i>=0;--i){d[i]=v%Q;v/=Q;}return d;}
bool confd(const Dig&a,const Dig&b){for(int i=0;i<D;++i){int z=(int(a[i])-int(b[i])+Q)%Q;if(z!=0&&z!=1&&z!=Q-1)return false;}return true;}
struct W{
 std::array<Dig,U>d{};std::vector<std::array<int,243>>nb;
 W():nb(U){for(int v=0;v<U;++v)d[v]=dec(v);for(int v=0;v<U;++v){int p=0;for(int m=0;m<243;++m){int t=m;auto z=d[v];for(int j=0;j<D;++j){int q=t%3-1;t/=3;z[j]=(z[j]+q+Q)%Q;}nb[v][p++]=enc(z);}std::sort(nb[v].begin(),nb[v].end());}}
};
bool conf(const W&w,int a,int b){return confd(w.d[a],w.d[b]);}
std::vector<int> load(const std::string&p){std::ifstream in(p);std::vector<int>r;int a,b,c,d,e;while(in>>a>>b>>c>>d>>e)r.push_back(enc(Dig{(uint8_t)a,(uint8_t)b,(uint8_t)c,(uint8_t)d,(uint8_t)e}));if(r.size()!=N)throw std::runtime_error("bad R");return r;}
std::vector<int> makex(const std::vector<int>&r,const W&w){std::vector<int>x;for(int id:r){auto a=w.d[id];x.push_back(enc(Dig{(uint8_t)((2-a[1]+Q)%Q),a[3],a[0],(uint8_t)((2-a[2]+Q)%Q),a[4]}));}x[267]=enc(Dig{1,5,6,3,5});return x;}
struct S{std::vector<int>p;std::vector<Pair>q;};
S analyze(const W&w,const std::vector<int>&p){std::array<uint16_t,U>cnt{};std::array<char,U>in{};for(int z:p){in[z]=1;for(int v:w.nb[z])++cnt[v];}std::vector<Pair>q;for(int a=0;a<U;++a)if(!in[a]&&cnt[a]==1){int c=-1;for(int z:w.nb[a])if(in[z]){c=z;break;}q.push_back({c,a});}return{p,q};}
std::string key(std::vector<int>p){std::sort(p.begin(),p.end());std::string s(2*p.size(),'\0');for(size_t i=0;i<p.size();++i){s[2*i]=p[i]&255;s[2*i+1]=(p[i]>>8)&255;}return s;}
int sub_id(const W&w,int f,int x){Dig t{};for(int i=0;i<D;++i)t[i]=(w.d[f][i]-w.d[x][i]+Q)%Q;return enc(t);}
int add_id(const W&w,int x,int t){Dig z{};for(int i=0;i<D;++i)z[i]=(w.d[x][i]+w.d[t][i])%Q;return enc(z);}

bool translation_avoids(const W&w,const std::vector<int>&x,const std::vector<Port>&ps,int&trans,int&fsize){
 std::bitset<U> h,v;for(auto&p:ps){int a=p.s?p.a:p.c,b=p.s?p.c:p.a;for(int z:w.nb[a])h.set(z);for(int z:w.nb[b])v.set(z);}auto f=h&v;fsize=f.count();
 std::array<char,U>blocked{};int nblock=0;
 for(int z=0;z<U;++z)if(f.test(z)){for(int q:x){int t=sub_id(w,z,q);if(!blocked[t]){blocked[t]=1;++nblock;if(nblock==U)return false;}}}
 for(int t=0;t<U;++t)if(!blocked[t]){trans=t;return true;}return false;
}

struct Best{int f=1e9,depth=-1,priv=0;long long leaves=0;};
bool search_ports(const W&w,const std::vector<int>&x,const S&st,int depth,Best&best,std::vector<Port>&ans,int&trans){
 if(st.q.size()<K)return false;std::unordered_set<int>cs;for(auto&p:st.q)cs.insert(p.c);if(cs.size()<K)return false;
 std::vector<int>ord(st.q.size());std::iota(ord.begin(),ord.end(),0);std::unordered_set<int>used;std::vector<int>hs,vs;std::vector<Port>sel;
 std::function<bool(int)>dfs=[&](int pos){
  if(sel.size()==K){++best.leaves;int t,fs;if(translation_avoids(w,x,sel,t,fs)){ans=sel;trans=t;std::cerr<<"translate FOUND depth="<<depth<<" priv="<<st.q.size()<<" F="<<fs<<" leaves="<<best.leaves<<" trans="<<t<<"\n";return true;}if(fs<best.f){best.f=fs;best.depth=depth;best.priv=st.q.size();std::cerr<<"translate best F="<<fs<<" depth="<<depth<<" priv="<<st.q.size()<<" leaves="<<best.leaves<<"\n";}return false;}
  if(pos>=(int)ord.size())return false;std::unordered_set<int>rem;for(int k=pos;k<(int)ord.size();++k)if(!used.count(st.q[ord[k]].c))rem.insert(st.q[ord[k]].c);if(sel.size()+rem.size()<K)return false;
  for(int kk=pos;kk<(int)ord.size();++kk){std::swap(ord[pos],ord[kk]);auto p=st.q[ord[pos]];if(!used.count(p.c)){for(int s=0;s<2;++s){int h=s?p.a:p.c,v=s?p.c:p.a;bool ok=true;for(int z:hs)if(conf(w,h,z)){ok=false;break;}if(ok)for(int z:vs)if(conf(w,v,z)){ok=false;break;}if(!ok)continue;used.insert(p.c);hs.push_back(h);vs.push_back(v);sel.push_back({p.c,p.a,s});if(dfs(pos+1))return true;sel.pop_back();vs.pop_back();hs.pop_back();used.erase(p.c);}}std::swap(ord[pos],ord[kk]);}
  return false;};return dfs(0);
}
void emit(const std::string&path,const S&st,const std::vector<int>&x,const W&w,const std::vector<Port>&ps,int tr,int depth,const Best&best){std::ofstream o(path);o<<"{\"kind\":\"translate-found\",\"score\":134770,\"depth\":"<<depth<<",\"translation\":"<<tr<<",\"best_forbidden_size\":"<<best.f<<",\"independent_set\":[";for(size_t i=0;i<st.p.size();++i){if(i)o<<',';o<<st.p[i];}o<<"],\"companion_set\":[";for(size_t i=0;i<x.size();++i){if(i)o<<',';o<<add_id(w,x[i],tr);}o<<"],\"ports\":[";for(size_t i=0;i<ps.size();++i){if(i)o<<',';auto&p=ps[i];o<<"{\"center\":"<<p.c<<",\"alt\":"<<p.a<<",\"side\":"<<p.s<<"}";}o<<"]}\n";}
}
int main(int argc,char**argv){try{if(argc!=4){std::cerr<<"usage: translate_ports R367 OUT DEPTH\n";return 2;}int md=std::stoi(argv[3]);W w;auto r=load(argv[1]);auto x=makex(r,w);std::vector<std::vector<int>>front{r};std::unordered_set<std::string>seen{key(r)};Best best;long long states=0;for(int dep=0;dep<=md;++dep){std::cerr<<"translate depth="<<dep<<" frontier="<<front.size()<<"\n";std::vector<std::vector<int>>next;for(auto&pts:front){auto st=analyze(w,pts);++states;if(st.q.size()>=K){std::vector<Port>ps;int tr;if(search_ports(w,x,st,dep,best,ps,tr)){emit(argv[2],st,x,w,ps,tr,dep,best);return 0;}}if(dep<md)for(auto p:st.q){auto q=pts;auto it=std::find(q.begin(),q.end(),p.c);*it=p.a;auto k=key(q);if(seen.insert(k).second)next.push_back(std::move(q));}}front=std::move(next);}std::ofstream o(argv[2]);o<<"{\"kind\":\"none\",\"method\":\"exact-companion-translations\",\"states\":"<<states<<",\"seen\":"<<seen.size()<<",\"leaves\":"<<best.leaves<<",\"best_forbidden_size\":"<<(best.f==1000000000?-1:best.f)<<",\"best_depth\":"<<best.depth<<",\"best_private\":"<<best.priv<<"}\n";std::cerr<<"translate NONE states="<<states<<" leaves="<<best.leaves<<" bestF="<<best.f<<"\n";return 0;}catch(const std::exception&e){std::cerr<<"error: "<<e.what()<<"\n";return 1;}}
