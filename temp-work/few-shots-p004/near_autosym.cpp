#include <algorithm>
#include <array>
#include <bit>
#include <bitset>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <numeric>
#include <set>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>

namespace {
constexpr int Q=7,D=5,U=16807,N=367,K=9;
using Dig=std::array<std::uint8_t,D>;
struct Pair{int c,a;};struct Port{int c,a,s;};
int enc(const Dig&d){int v=0;for(auto x:d)v=v*Q+x;return v;}
Dig dec(int v){Dig d{};for(int i=D-1;i>=0;--i){d[i]=v%Q;v/=Q;}return d;}
bool confd(const Dig&a,const Dig&b){for(int i=0;i<D;++i){int z=(int(a[i])-int(b[i])+Q)%Q;if(z!=0&&z!=1&&z!=Q-1)return false;}return true;}
struct World{std::array<Dig,U>d{};std::vector<std::array<int,243>>nb;World():nb(U){for(int v=0;v<U;++v)d[v]=dec(v);for(int v=0;v<U;++v){int p=0;for(int m=0;m<243;++m){int t=m;auto z=d[v];for(int j=0;j<D;++j){int q=t%3-1;t/=3;z[j]=(z[j]+q+Q)%Q;}nb[v][p++]=enc(z);}std::sort(nb[v].begin(),nb[v].end());}}};
bool conf(const World&w,int a,int b){return confd(w.d[a],w.d[b]);}
std::vector<int>load(const std::string&p){std::ifstream in(p);std::vector<int>r;int a,b,c,d,e;while(in>>a>>b>>c>>d>>e)r.push_back(enc(Dig{(uint8_t)a,(uint8_t)b,(uint8_t)c,(uint8_t)d,(uint8_t)e}));if(r.size()!=N)throw std::runtime_error("bad R");return r;}
std::vector<int>makex(const std::vector<int>&r,const World&w){std::vector<int>x;for(int id:r){auto a=w.d[id];x.push_back(enc(Dig{(uint8_t)((2-a[1]+Q)%Q),a[3],a[0],(uint8_t)((2-a[2]+Q)%Q),a[4]}));}x[267]=enc(Dig{1,5,6,3,5});return x;}
std::vector<Pair>analyze(const World&w,const std::vector<int>&p){std::array<uint16_t,U>cnt{};std::array<char,U>in{};for(int z:p){in[z]=1;for(int v:w.nb[z])++cnt[v];}std::vector<Pair>q;for(int a=0;a<U;++a)if(!in[a]&&cnt[a]==1){int c=-1;for(int z:w.nb[a])if(in[z]){c=z;break;}q.push_back({c,a});}return q;}
std::uint64_t foot(const World&w,int v,const std::vector<int>&x){std::uint64_t lo=0;for(int i=0;i<std::min(64,N);++i)if(conf(w,v,x[i]))lo|=1ull<<i;return lo;}
struct XFoot{std::array<std::uint64_t,6>b{};};
XFoot xfoot(const World&w,int v,const std::vector<int>&x){XFoot f{};for(int i=0;i<N;++i)if(conf(w,v,x[i]))f.b[i/64]|=1ull<<(i%64);return f;}
int overlap(const XFoot&a,const XFoot&b){int c=0;for(int i=0;i<6;++i)c+=std::popcount(a.b[i]&b.b[i]);return c;}
void orf(XFoot&a,const XFoot&b){for(int i=0;i<6;++i)a.b[i]|=b.b[i];}
struct Scheme{std::vector<int>state;std::vector<Port>ports;std::vector<int>forbidden;int overlap;};

std::vector<Scheme>near_schemes(const World&w,const std::vector<int>&r,const std::vector<int>&x){
 auto root=analyze(w,r);std::vector<Scheme>out;int sn=0;
 for(auto sw:root){auto st=r;*std::find(st.begin(),st.end(),sw.c)=sw.a;auto pp=analyze(w,st);std::unordered_map<int,std::vector<int>>by;for(auto&p:pp)by[p.c].push_back(p.a);if(by.size()<K)continue;++sn;std::vector<int>cent;for(auto&[c,a]:by)cent.push_back(c);
  for(auto csbeg=cent.begin();csbeg!=cent.end();++csbeg){} // keep deterministic map-derived order
  for(auto comb_it=std::array<int,1>{0};comb_it[0]<1;++comb_it[0]){ // one scope to avoid a helper template
   if(cent.size()!=K)continue; // one-swap near states currently have exactly nine centers
   std::vector<std::vector<int>>alts;for(int c:cent)alts.push_back(by[c]);std::vector<int>choice(K,0);
   while(true){std::vector<Pair>pairs;for(int j=0;j<K;++j)pairs.push_back({cent[j],alts[j][choice[j]]});std::unordered_map<int,XFoot>fp;for(auto&p:pairs){fp.emplace(p.c,xfoot(w,p.c,x));fp.emplace(p.a,xfoot(w,p.a,x));}
    for(int bits=0;bits<(1<<K);++bits){std::vector<int>hs,vs;std::vector<Port>ports;XFoot hu{},vu{};bool ok=true;for(int j=0;j<K;++j){auto p=pairs[j];int s=(bits>>j)&1,h=s?p.a:p.c,v=s?p.c:p.a;for(int z:hs)if(conf(w,h,z)){ok=false;break;}if(!ok)break;for(int z:vs)if(conf(w,v,z)){ok=false;break;}if(!ok)break;hs.push_back(h);vs.push_back(v);ports.push_back({p.c,p.a,s});orf(hu,fp[h]);orf(vu,fp[v]);}if(!ok)continue;int ov=overlap(hu,vu);if(ov>1)continue;std::bitset<U>H,V;for(int z:hs)for(int q:w.nb[z])H.set(q);for(int z:vs)for(int q:w.nb[z])V.set(q);auto F=H&V;std::vector<int>fv;fv.reserve(F.count());for(int q=0;q<U;++q)if(F.test(q))fv.push_back(q);out.push_back({st,ports,fv,ov});}
    int j=K-1;while(j>=0){if(++choice[j]<(int)alts[j].size())break;choice[j]=0;--j;}if(j<0)break;
   }
  }
 }
 std::sort(out.begin(),out.end(),[](const Scheme&a,const Scheme&b){return a.forbidden.size()<b.forbidden.size();});std::cerr<<"autosym near_states="<<sn<<" schemes="<<out.size();if(!out.empty())std::cerr<<" minF="<<out.front().forbidden.size();std::cerr<<"\n";return out;
}
int diff(const World&w,int f,int y){Dig t{};for(int i=0;i<D;++i)t[i]=(w.d[f][i]-w.d[y][i]+Q)%Q;return enc(t);}
int add(const World&w,int y,int t){Dig z{};for(int i=0;i<D;++i)z[i]=(w.d[y][i]+w.d[t][i])%Q;return enc(z);}
int linear(const World&w,int x,const std::array<int,D>&perm,int signs){Dig y{};for(int i=0;i<D;++i){int z=w.d[x][perm[i]];if((signs>>i)&1)z=(Q-z)%Q;y[i]=z;}return enc(y);}
void emit(const std::string&path,const World&w,const Scheme&s,const std::vector<int>&xp,const std::array<int,D>&perm,int signs,int tr,int idx){std::ofstream o(path);o<<"{\"kind\":\"autosym-found\",\"score\":134770,\"scheme_index\":"<<idx<<",\"forbidden_size\":"<<s.forbidden.size()<<",\"original_overlap\":"<<s.overlap<<",\"signs\":"<<signs<<",\"translation\":"<<tr<<",\"perm\":[";for(int i=0;i<D;++i){if(i)o<<',';o<<perm[i];}o<<"],\"independent_set\":[";for(size_t i=0;i<s.state.size();++i){if(i)o<<',';o<<s.state[i];}o<<"],\"companion_set\":[";for(size_t i=0;i<xp.size();++i){if(i)o<<',';o<<xp[i];}o<<"],\"ports\":[";for(size_t i=0;i<s.ports.size();++i){if(i)o<<',';auto&p=s.ports[i];o<<"{\"center\":"<<p.c<<",\"alt\":"<<p.a<<",\"side\":"<<p.s<<"}";}o<<"]}\n";}
}
int main(int argc,char**argv){try{if(argc!=3){std::cerr<<"usage: near_autosym R367 OUT\n";return 2;}World w;auto r=load(argv[1]);auto x=makex(r,w);auto schemes=near_schemes(w,r,x);std::array<int,D>perm{0,1,2,3,4};long long linear_checked=0;for(int si=0;si<(int)schemes.size();++si){auto&s=schemes[si];perm={0,1,2,3,4};do{for(int signs=0;signs<(1<<D);++signs){++linear_checked;std::vector<int>y;y.reserve(N);for(int z:x)y.push_back(linear(w,z,perm,signs));std::array<char,U>blocked{};int nb=0;for(int f:s.forbidden){for(int z:y){int t=diff(w,f,z);if(!blocked[t]){blocked[t]=1;if(++nb==U)break;}}if(nb==U)break;}if(nb<U){int tr=0;while(blocked[tr])++tr;std::vector<int>xp;xp.reserve(N);for(int z:y)xp.push_back(add(w,z,tr));std::cerr<<"autosym FOUND scheme="<<si<<" F="<<s.forbidden.size()<<" linear_checked="<<linear_checked<<" signs="<<signs<<" tr="<<tr<<"\n";emit(argv[2],w,s,xp,perm,signs,tr,si);return 0;}}}while(std::next_permutation(perm.begin(),perm.end()));if(si%10==0)std::cerr<<"autosym progress scheme="<<si<<"/"<<schemes.size()<<" linear="<<linear_checked<<"\n";}
 std::ofstream o(argv[2]);o<<"{\"kind\":\"none\",\"method\":\"one-swap-full-signed-permutation-translation\",\"schemes\":"<<schemes.size()<<",\"linear_checked\":"<<linear_checked<<",\"min_forbidden_size\":"<<(schemes.empty()?-1:(int)schemes.front().forbidden.size())<<"}\n";std::cerr<<"autosym NONE schemes="<<schemes.size()<<" linear="<<linear_checked<<"\n";return 0;}catch(const std::exception&e){std::cerr<<"error: "<<e.what()<<"\n";return 1;}}
