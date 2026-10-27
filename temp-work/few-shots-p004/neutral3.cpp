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
using Dig=std::array<std::uint8_t,D>; using Foot=std::array<std::uint64_t,XW>;
struct Pair{int c,a;}; struct Port{int c,a,s;};
struct Rec{int ov,priv,centers;std::array<int,3> rem,add;std::vector<int> state;};
int enc(const Dig&d){int v=0;for(auto x:d)v=v*Q+x;return v;}
Dig dec(int v){Dig d{};for(int i=D-1;i>=0;--i){d[i]=v%Q;v/=Q;}return d;}
bool confd(const Dig&a,const Dig&b){for(int i=0;i<D;++i){int z=(int(a[i])-int(b[i])+Q)%Q;if(z!=0&&z!=1&&z!=Q-1)return false;}return true;}
struct W{
 std::array<Dig,U>d{};std::vector<std::array<int,243>>nb;std::array<Foot,U>xf{};
 explicit W(const std::vector<int>&x):nb(U){
  for(int v=0;v<U;++v)d[v]=dec(v);
  for(int v=0;v<U;++v){int p=0;for(int m=0;m<243;++m){int t=m;auto z=d[v];for(int j=0;j<D;++j){int q=t%3-1;t/=3;z[j]=(z[j]+q+Q)%Q;}nb[v][p++]=enc(z);}std::sort(nb[v].begin(),nb[v].end());}
  for(int v=0;v<U;++v){xf[v].fill(0);for(int i=0;i<N;++i)if(confd(d[v],d[x[i]]))xf[v][i/64]|=1ull<<(i%64);}
 }
};
bool conf(const W&w,int a,int b){return confd(w.d[a],w.d[b]);}
std::vector<int>load(const std::string&p){std::ifstream in(p);std::vector<int>r;int a,b,c,d,e;while(in>>a>>b>>c>>d>>e)r.push_back(enc(Dig{(uint8_t)a,(uint8_t)b,(uint8_t)c,(uint8_t)d,(uint8_t)e}));if(r.size()!=N||std::unordered_set<int>(r.begin(),r.end()).size()!=N)throw std::runtime_error("bad R");return r;}
std::vector<int>makex(const std::vector<int>&r,const std::array<Dig,U>&d){std::vector<int>x;for(int id:r){auto a=d[id];x.push_back(enc(Dig{(uint8_t)((2-a[1]+Q)%Q),a[3],a[0],(uint8_t)((2-a[2]+Q)%Q),a[4]}));}x[267]=enc(Dig{1,5,6,3,5});return x;}
struct Info{std::vector<Pair>priv;int centers;};
Info analyze(const W&w,const std::vector<int>&p){std::array<uint16_t,U>cnt{};std::array<char,U>in{};for(int z:p){in[z]=1;for(int q:w.nb[z])++cnt[q];}std::vector<Pair>v;std::unordered_set<int>cs;for(int q=0;q<U;++q)if(!in[q]&&cnt[q]==1){int c=-1;for(int z:w.nb[q])if(in[z]){c=z;break;}if(c<0)throw std::runtime_error("private without center");v.push_back({c,q});cs.insert(c);}return{std::move(v),(int)cs.size()};}
int overlap(const Foot&a,const Foot&b){int c=0;for(int i=0;i<XW;++i)c+=std::popcount(a[i]&b[i]);return c;}void OR(Foot&a,const Foot&b){for(int i=0;i<XW;++i)a[i]|=b[i];}
int best_overlap(const W&w,const Info&info){if(info.centers<K)return 1000000000;std::unordered_map<int,std::vector<int>>by;for(auto&p:info.priv)by[p.c].push_back(p.a);std::vector<int>cs;for(auto&[c,a]:by)cs.push_back(c);int bo=1000000000;std::vector<int>hs,vs;Foot hu{},vu{};hu.fill(0);vu.fill(0);int chosen=0;
 std::function<void(int)>dfs=[&](int pos){if(chosen==K){bo=std::min(bo,overlap(hu,vu));return;}if(pos>=(int)cs.size()||chosen+(int)cs.size()-pos<K)return;for(int ci=pos;ci<(int)cs.size();++ci){std::swap(cs[pos],cs[ci]);int c=cs[pos];for(int a:by[c])for(int s=0;s<2;++s){int h=s?a:c,v=s?c:a;bool ok=true;for(int z:hs)if(conf(w,h,z)){ok=false;break;}if(ok)for(int z:vs)if(conf(w,v,z)){ok=false;break;}if(!ok)continue;auto oh=hu,ov=vu;OR(hu,w.xf[h]);OR(vu,w.xf[v]);int lower=overlap(hu,vu);if(lower<bo){hs.push_back(h);vs.push_back(v);++chosen;dfs(pos+1);--chosen;vs.pop_back();hs.pop_back();}hu=oh;vu=ov;}std::swap(cs[pos],cs[ci]);}};dfs(0);return bo;}
std::uint64_t tkey(int a,int b,int c){if(a>b)std::swap(a,b);if(b>c)std::swap(b,c);if(a>b)std::swap(a,b);return(std::uint64_t(a)<<20)|(std::uint64_t(b)<<10)|std::uint64_t(c);}
bool better(const Rec&a,const Rec&b){if(a.ov!=b.ov)return a.ov<b.ov;if(a.centers!=b.centers)return a.centers>b.centers;return a.priv>b.priv;}
void keep(std::vector<Rec>&top,Rec&&r){top.push_back(std::move(r));std::sort(top.begin(),top.end(),better);if((int)top.size()>TOPN)top.resize(TOPN);}
}
int main(int argc,char**argv){try{
 if(argc!=3){std::cerr<<"usage: neutral3 R367 OUT\n";return 2;}
 std::array<Dig,U>d{};for(int i=0;i<U;++i)d[i]=dec(i);auto r=load(argv[1]);auto x=makex(r,d);W w(x);
 std::array<uint16_t,U>cnt{};std::array<int,U>o1{},o2{},o3{};o1.fill(-1);o2.fill(-1);o3.fill(-1);std::array<char,U>in{};
 for(int i=0;i<N;++i){in[r[i]]=1;for(int q:w.nb[r[i]]){if(cnt[q]==0)o1[q]=i;else if(cnt[q]==1)o2[q]=i;else if(cnt[q]==2)o3[q]=i;++cnt[q];}}
 std::vector<std::vector<int>>one(N),two(N*N);std::unordered_map<std::uint64_t,std::vector<int>>three;three.reserve(4096);
 for(int q=0;q<U;++q){if(in[q])continue;if(cnt[q]==1)one[o1[q]].push_back(q);else if(cnt[q]==2){int a=o1[q],b=o2[q];if(a>b)std::swap(a,b);two[a*N+b].push_back(q);}else if(cnt[q]==3){int a=o1[q],b=o2[q],c=o3[q];three[tkey(a,b,c)].push_back(q);}}
 long long owner_triples=0,states=0,evaluated=0;int maxpriv=0,maxcent=0,bestov=1000000000;std::vector<Rec>top;
 std::vector<int>cand;cand.reserve(64);
 for(int a=0;a<N-2;++a)for(int b=a+1;b<N-1;++b)for(int c=b+1;c<N;++c){
  auto &ab=two[a*N+b],&ac=two[a*N+c],&bc=two[b*N+c];auto it3=three.find(tkey(a,b,c));
  size_t sz=one[a].size()+one[b].size()+one[c].size()+ab.size()+ac.size()+bc.size()+(it3==three.end()?0:it3->second.size());if(sz<3)continue;++owner_triples;
  cand.clear();cand.insert(cand.end(),one[a].begin(),one[a].end());cand.insert(cand.end(),one[b].begin(),one[b].end());cand.insert(cand.end(),one[c].begin(),one[c].end());cand.insert(cand.end(),ab.begin(),ab.end());cand.insert(cand.end(),ac.begin(),ac.end());cand.insert(cand.end(),bc.begin(),bc.end());if(it3!=three.end())cand.insert(cand.end(),it3->second.begin(),it3->second.end());
  for(int i=0;i<(int)cand.size()-2;++i)for(int j=i+1;j<(int)cand.size()-1;++j){if(conf(w,cand[i],cand[j]))continue;for(int k=j+1;k<(int)cand.size();++k){if(conf(w,cand[i],cand[k])||conf(w,cand[j],cand[k]))continue;++states;auto st=r;st[a]=cand[i];st[b]=cand[j];st[c]=cand[k];auto inf=analyze(w,st);maxpriv=std::max(maxpriv,(int)inf.priv.size());maxcent=std::max(maxcent,inf.centers);if(inf.centers<K)continue;++evaluated;int ov=best_overlap(w,inf);if(ov<bestov){bestov=ov;std::cerr<<"neutral3 best states="<<states<<" eval="<<evaluated<<" private="<<inf.priv.size()<<" centers="<<inf.centers<<" overlap="<<ov<<" rem="<<a<<','<<b<<','<<c<<" add="<<cand[i]<<','<<cand[j]<<','<<cand[k]<<"\n";}keep(top,Rec{ov,(int)inf.priv.size(),inf.centers,{a,b,c},{cand[i],cand[j],cand[k]},std::move(st)});}}
 }
 std::ofstream out(argv[2]);if(!out)throw std::runtime_error("cannot write output");out<<"{\"kind\":\"neutral3-states\",\"method\":\"exact-neutral-3-for-3-5d\",\"owner_triples\":"<<owner_triples<<",\"states\":"<<states<<",\"evaluated\":"<<evaluated<<",\"max_private\":"<<maxpriv<<",\"max_private_centers\":"<<maxcent<<",\"best_overlap\":"<<(bestov==1000000000?-1:bestov)<<",\"top\":[";
 for(size_t z=0;z<top.size();++z){if(z)out<<',';auto&t=top[z];out<<"{\"overlap\":"<<t.ov<<",\"private\":"<<t.priv<<",\"centers\":"<<t.centers<<",\"remove_indices\":["<<t.rem[0]<<','<<t.rem[1]<<','<<t.rem[2]<<"],\"add\":["<<t.add[0]<<','<<t.add[1]<<','<<t.add[2]<<"],\"state\":[";for(size_t i=0;i<t.state.size();++i){if(i)out<<',';out<<t.state[i];}out<<"]}";}
 out<<"]}\n";std::cerr<<"neutral3 DONE owner_triples="<<owner_triples<<" states="<<states<<" evaluated="<<evaluated<<" maxpriv="<<maxpriv<<" maxcent="<<maxcent<<" bestov="<<(bestov==1000000000?-1:bestov)<<"\n";return 0;
 }catch(const std::exception&e){std::cerr<<"error: "<<e.what()<<"\n";return 1;}}
