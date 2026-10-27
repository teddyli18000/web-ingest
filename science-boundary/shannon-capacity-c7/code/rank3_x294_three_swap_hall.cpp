#include <algorithm>
#include <array>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <queue>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>

namespace {
constexpr int Q=7,D=5,U=16807,N=367,ZERO_X=250;
using Dig=std::array<unsigned char,D>;
int enc(const Dig& d){int v=0;for(auto x:d)v=v*Q+x;return v;}
Dig dec(int v){Dig d{};for(int i=D-1;i>=0;--i){d[i]=v%Q;v/=Q;}return d;}
bool conf(const Dig&a,const Dig&b){for(int i=0;i<D;++i){int z=(int(a[i])-int(b[i])+Q)%Q;if(z!=0&&z!=1&&z!=6)return false;}return true;}
std::vector<int> load(const std::string&p){std::ifstream in(p);std::vector<int>r;int a,b,c,d,e;while(in>>a>>b>>c>>d>>e)r.push_back(enc(Dig{(unsigned char)a,(unsigned char)b,(unsigned char)c,(unsigned char)d,(unsigned char)e}));if(r.size()!=N)throw std::runtime_error("bad R");return r;}
std::vector<int> makex(const std::vector<int>&r,const std::array<Dig,U>&d){std::vector<int>x;for(int id:r){auto a=d[id];x.push_back(enc(Dig{(unsigned char)((2-a[1]+Q)%Q),a[3],a[0],(unsigned char)((2-a[2]+Q)%Q),a[4]}));}x[267]=enc(Dig{1,5,6,3,5});return x;}
std::uint64_t pk(int a,int b){if(a>b)std::swap(a,b);return (std::uint64_t(a)<<10)|b;}
std::uint64_t tk(int a,int b,int c){std::array<int,3>v{a,b,c};std::sort(v.begin(),v.end());return(std::uint64_t(v[0])<<20)|(std::uint64_t(v[1])<<10)|v[2];}
int hk(const std::vector<std::vector<int>>&adj){int L=adj.size(),R=N-1;std::vector<int>pu(L,-1),pv(R,-1),dist(L);int m=0;for(;;){std::queue<int>q;bool found=false;for(int u=0;u<L;++u){if(pu[u]<0){dist[u]=0;q.push(u);}else dist[u]=-1;}while(!q.empty()){int u=q.front();q.pop();for(int v:adj[u]){int w=pv[v];if(w<0)found=true;else if(dist[w]<0){dist[w]=dist[u]+1;q.push(w);}}}if(!found)break;std::function<bool(int)>dfs=[&](int u){for(int v:adj[u]){int w=pv[v];if(w<0||(dist[w]==dist[u]+1&&dfs(w))){pu[u]=v;pv[v]=u;return true;}}dist[u]=-1;return false;};for(int u=0;u<L;++u)if(pu[u]<0&&dfs(u))++m;}return m;}
}
int main(int argc,char**argv){try{
 if(argc!=4){std::cerr<<"usage: three_swap_hall R367 FAMILY OUT\n";return 2;}std::string fam=argv[2];
 std::array<Dig,U>d{};for(int v=0;v<U;++v)d[v]=dec(v);auto r0=load(argv[1]);auto x=makex(r0,d);std::vector<int>f;
 if(fam=="r0")f=r0;else if(fam=="rank3"){f=r0;f[267]=15083;f[294]=16388;}else if(fam=="x")f=x;else throw std::runtime_error("bad family");
 if(std::unordered_set<int>(f.begin(),f.end()).size()!=N)throw std::runtime_error("family dup");for(int i=0;i<N;++i)for(int j=i+1;j<N;++j)if(conf(d[f[i]],d[f[j]]))throw std::runtime_error("family not independent");
 // Fixed Hall target: the 366 positive-weight X nodes from the rank-3 tie; X_250 has weight zero.
 std::array<int,N> ridx{};ridx.fill(-1);int rr=0;for(int j=0;j<N;++j)if(j!=ZERO_X)ridx[j]=rr++;
 std::array<std::vector<int>,U> hadj;for(int v=0;v<U;++v)for(int j=0;j<N;++j)if(j!=ZERO_X&&conf(d[v],d[x[j]]))hadj[v].push_back(ridx[j]);
 std::array<int,U> cnt{},o1{},o2{},o3{};o1.fill(-1);o2.fill(-1);o3.fill(-1);std::array<char,U>in{};
 for(int i=0;i<N;++i){in[f[i]]=1;for(int v=0;v<U;++v)if(conf(d[v],d[f[i]])){if(cnt[v]==0)o1[v]=i;else if(cnt[v]==1)o2[v]=i;else if(cnt[v]==2)o3[v]=i;++cnt[v];}}
 std::vector<std::vector<int>>one(N);std::unordered_map<std::uint64_t,std::vector<int>>two,three;two.reserve(4096);three.reserve(4096);
 for(int v=0;v<U;++v){if(in[v])continue;if(cnt[v]==1)one[o1[v]].push_back(v);else if(cnt[v]==2)two[pk(o1[v],o2[v])].push_back(v);else if(cnt[v]==3)three[tk(o1[v],o2[v],o3[v])].push_back(v);}
 long long owner_triples=0,states=0;int best=366;std::array<int,3>bestrem{-1,-1,-1},bestadd{-1,-1,-1};std::unordered_set<std::string>seen;std::vector<int>cand;cand.reserve(64);
 for(int a=0;a<N-2;++a)for(int b=a+1;b<N-1;++b)for(int c=b+1;c<N;++c){cand.clear();cand.insert(cand.end(),one[a].begin(),one[a].end());cand.insert(cand.end(),one[b].begin(),one[b].end());cand.insert(cand.end(),one[c].begin(),one[c].end());for(auto key:{pk(a,b),pk(a,c),pk(b,c)}){auto it=two.find(key);if(it!=two.end())cand.insert(cand.end(),it->second.begin(),it->second.end());}auto it3=three.find(tk(a,b,c));if(it3!=three.end())cand.insert(cand.end(),it3->second.begin(),it3->second.end());std::sort(cand.begin(),cand.end());cand.erase(std::unique(cand.begin(),cand.end()),cand.end());if(cand.size()<3)continue;++owner_triples;
  for(int i=0;i<(int)cand.size()-2;++i)for(int j=i+1;j<(int)cand.size()-1;++j){if(conf(d[cand[i]],d[cand[j]]))continue;for(int k=j+1;k<(int)cand.size();++k){if(conf(d[cand[i]],d[cand[k]])||conf(d[cand[j]],d[cand[k]]))continue;std::vector<int>g=f;g[a]=cand[i];g[b]=cand[j];g[c]=cand[k];auto sorted=g;std::sort(sorted.begin(),sorted.end());std::string key(reinterpret_cast<const char*>(sorted.data()),sorted.size()*sizeof(int));if(!seen.insert(key).second)continue;++states;std::vector<std::vector<int>>adj;adj.reserve(N);for(int z:g)adj.push_back(hadj[z]);int m=hk(adj);if(m<best){best=m;bestrem={a,b,c};bestadd={cand[i],cand[j],cand[k]};std::cerr<<"BEST family="<<fam<<" states="<<states<<" matching="<<m<<" rem="<<a<<','<<b<<','<<c<<" add="<<cand[i]<<','<<cand[j]<<','<<cand[k]<<"\n";}if(m<=365)goto done;}}}
 }
 done: std::ofstream out(argv[3]);out<<"{\"family\":\""<<fam<<"\",\"method\":\"exact-neutral3-hall\",\"owner_triples\":"<<owner_triples<<",\"states\":"<<states<<",\"min_matching\":"<<best<<",\"max_closure_objective\":"<<(N-best)<<",\"candidate\":"<<(best<=365?"true":"false")<<",\"best_remove\":["<<bestrem[0]<<','<<bestrem[1]<<','<<bestrem[2]<<"],\"best_add\":["<<bestadd[0]<<','<<bestadd[1]<<','<<bestadd[2]<<"]}\n";std::cerr<<"DONE family="<<fam<<" owner_triples="<<owner_triples<<" states="<<states<<" best="<<best<<"\n";return 0;
 }catch(const std::exception&e){std::cerr<<"error: "<<e.what()<<"\n";return 1;}}
