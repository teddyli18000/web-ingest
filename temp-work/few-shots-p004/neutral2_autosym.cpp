#include <algorithm>
#include <array>
#include <bitset>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <unordered_set>
#include <vector>

namespace {
constexpr int Q=7,D=5,U=16807,N=367;
using Dig=std::array<std::uint8_t,D>;
struct Port{int c,a,s;};
int enc(const Dig&d){int v=0;for(auto x:d)v=v*Q+x;return v;}
Dig dec(int v){Dig d{};for(int i=D-1;i>=0;--i){d[i]=v%Q;v/=Q;}return d;}
bool confd(const Dig&a,const Dig&b){for(int i=0;i<D;++i){int z=(int(a[i])-int(b[i])+Q)%Q;if(z!=0&&z!=1&&z!=Q-1)return false;}return true;}
struct W{std::array<Dig,U>d{};std::vector<std::array<int,243>>nb;W():nb(U){for(int v=0;v<U;++v)d[v]=dec(v);for(int v=0;v<U;++v){int p=0;for(int m=0;m<243;++m){int t=m;auto z=d[v];for(int j=0;j<D;++j){int q=t%3-1;t/=3;z[j]=(z[j]+q+Q)%Q;}nb[v][p++]=enc(z);}std::sort(nb[v].begin(),nb[v].end());}}};
bool conf(const W&w,int a,int b){return confd(w.d[a],w.d[b]);}
std::vector<int>load(const std::string&p){std::ifstream in(p);std::vector<int>r;int a,b,c,d,e;while(in>>a>>b>>c>>d>>e)r.push_back(enc(Dig{(uint8_t)a,(uint8_t)b,(uint8_t)c,(uint8_t)d,(uint8_t)e}));if(r.size()!=N)throw std::runtime_error("bad R");return r;}
std::vector<int>makex(const std::vector<int>&r,const W&w){std::vector<int>x;for(int id:r){auto a=w.d[id];x.push_back(enc(Dig{(uint8_t)((2-a[1]+Q)%Q),a[3],a[0],(uint8_t)((2-a[2]+Q)%Q),a[4]}));}x[267]=enc(Dig{1,5,6,3,5});return x;}
int diff(const W&w,int f,int y){Dig t{};for(int i=0;i<D;++i)t[i]=(w.d[f][i]-w.d[y][i]+Q)%Q;return enc(t);}
int add(const W&w,int y,int t){Dig z{};for(int i=0;i<D;++i)z[i]=(w.d[y][i]+w.d[t][i])%Q;return enc(z);}
int linear(const W&w,int x,const std::array<int,D>&perm,int signs){Dig y{};for(int i=0;i<D;++i){int z=w.d[x][perm[i]];if((signs>>i)&1)z=(Q-z)%Q;y[i]=z;}return enc(y);}
void emit(const std::string&path,const std::vector<int>&state,const std::vector<int>&xp,const std::vector<Port>&ps,const std::array<int,D>&perm,int signs,int tr,int fs){std::ofstream o(path);o<<"{\"kind\":\"autosym-found\",\"score\":134770,\"scheme_index\":0,\"forbidden_size\":"<<fs<<",\"perm\":[";for(int i=0;i<D;++i){if(i)o<<',';o<<perm[i];}o<<"],\"signs\":"<<signs<<",\"translation\":"<<tr<<",\"independent_set\":[";for(size_t i=0;i<state.size();++i){if(i)o<<',';o<<state[i];}o<<"],\"companion_set\":[";for(size_t i=0;i<xp.size();++i){if(i)o<<',';o<<xp[i];}o<<"],\"ports\":[";for(size_t i=0;i<ps.size();++i){if(i)o<<',';auto&p=ps[i];o<<"{\"center\":"<<p.c<<",\"alt\":"<<p.a<<",\"side\":"<<p.s<<"}";}o<<"]}\n";}
}
int main(int argc,char**argv){try{if(argc!=3){std::cerr<<"usage: neutral2_autosym R367 OUT\n";return 2;}W w;auto r=load(argv[1]);auto x=makex(r,w);r[267]=15083;r[294]=16388;if(std::unordered_set<int>(r.begin(),r.end()).size()!=N)throw std::runtime_error("state duplicate");for(int i=0;i<N;++i)for(int j=i+1;j<N;++j)if(conf(w,r[i],r[j]))throw std::runtime_error("neutral2 state not independent");std::vector<Port>ps={{11283,13677,0},{15083,14733,1},{13108,13158,0},{15953,15910,1},{14328,12277,0},{16388,16046,0},{1321,15685,1},{8601,6494,0},{3660,6110,1}};std::unordered_set<int>ins(r.begin(),r.end()),cent;std::vector<int>ph,pv;for(auto&p:ps){if(!ins.count(p.c)||ins.count(p.a))throw std::runtime_error("bad port membership");int hits=0,last=-1;for(int z:r)if(conf(w,p.a,z)){++hits;last=z;}if(hits!=1||last!=p.c)throw std::runtime_error("port not private");cent.insert(p.c);ph.push_back(p.s?p.a:p.c);pv.push_back(p.s?p.c:p.a);}if(cent.size()!=9)throw std::runtime_error("duplicate centers");for(int i=0;i<9;++i)for(int j=i+1;j<9;++j)if(conf(w,ph[i],ph[j])||conf(w,pv[i],pv[j]))throw std::runtime_error("transversal conflict");std::bitset<U>H,V;for(int z:ph)for(int q:w.nb[z])H.set(q);for(int z:pv)for(int q:w.nb[z])V.set(q);auto F=H&V;std::vector<int>fv;for(int q=0;q<U;++q)if(F.test(q))fv.push_back(q);std::cerr<<"neutral2 autosym F="<<fv.size()<<"\n";std::array<int,D>perm{0,1,2,3,4};long long checked=0;do{for(int signs=0;signs<32;++signs){++checked;std::vector<int>y;y.reserve(N);for(int z:x)y.push_back(linear(w,z,perm,signs));std::array<char,U>blocked{};int n=0;for(int f:fv){for(int z:y){int t=diff(w,f,z);if(!blocked[t]){blocked[t]=1;if(++n==U)break;}}if(n==U)break;}if(n<U){int tr=0;while(blocked[tr])++tr;std::vector<int>xp;for(int z:y)xp.push_back(add(w,z,tr));std::cerr<<"neutral2 autosym FOUND checked="<<checked<<" signs="<<signs<<" tr="<<tr<<" blocked="<<n<<"\n";emit(argv[2],r,xp,ps,perm,signs,tr,fv.size());return 0;}}}while(std::next_permutation(perm.begin(),perm.end()));std::ofstream o(argv[2]);o<<"{\"kind\":\"none\",\"method\":\"neutral2-best-full-autosym\",\"linear_checked\":"<<checked<<",\"forbidden_size\":"<<fv.size()<<"}\n";std::cerr<<"neutral2 autosym NONE checked="<<checked<<"\n";return 0;}catch(const std::exception&e){std::cerr<<"error: "<<e.what()<<"\n";return 1;}}
