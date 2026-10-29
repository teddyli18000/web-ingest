#include <algorithm>
#include <array>
#include <cstdint>
#include <fstream>
#include <functional>
#include <iostream>
#include <sstream>
#include <unordered_map>
#include <vector>
using namespace std;
constexpr int D=5,Q=7,U=16807,N=367;
array<int,D> dec5(int v){array<int,D>a{};for(int i=0;i<D;i++){a[i]=v%7;v/=7;}return a;}
int enc5(const array<int,D>&a){int v=0,m=1;for(int i=0;i<D;i++){v+=a[i]*m;m*=7;}return v;}
vector<int> parse(const string&s,const string&key){vector<int>a;auto p=s.find("\""+key+"\"");p=s.find('[',p);auto e=s.find(']',p);stringstream ss(s.substr(p+1,e-p-1));while(ss){int x;if(ss>>x)a.push_back(x);if(ss.peek()==',')ss.get();else{ss.clear();char c;ss>>c;}}return a;}
struct Key{array<uint16_t,6>a{};bool operator==(Key const&o)const{return a==o.a;}};
struct KH{size_t operator()(Key const&k)const noexcept{size_t h=0;for(auto x:k.a)h=h*1000003u+x;return h;}};
struct Cand{int v;Key k;int n;};
bool subset(const Cand&c,const Key&U){int i=0,j=0;while(i<c.n&&j<6){if(c.k.a[i]==U.a[j]){i++;j++;}else if(c.k.a[i]>U.a[j])j++;else return false;}return i==c.n;}
bool conf(int a,int b,const vector<array<int,D>>&dig){auto x=dig[a],y=dig[b];for(int k=0;k<D;k++){int z=(x[k]-y[k]+7)%7;if(z!=0&&z!=1&&z!=6)return false;}return true;}
bool find7(vector<int>&p,const vector<array<int,D>>&dig,vector<int>&out){sort(p.begin(),p.end());p.erase(unique(p.begin(),p.end()),p.end());vector<int>ch;function<bool(int)> dfs=[&](int s){if(ch.size()==7){out=ch;return true;}if((int)ch.size()+(int)p.size()-s<7)return false;for(int i=s;i<(int)p.size();i++){bool ok=true;for(int z:ch)if(conf(z,p[i],dig)){ok=false;break;}if(!ok)continue;ch.push_back(p[i]);if(dfs(i+1))return true;ch.pop_back();}return false;};return dfs(0);}
int main(int argc,char**argv){if(argc!=2){cerr<<"usage: c7p5_r6_c5 I0_JSON\n";return 2;}ifstream in(argv[1]);string s((istreambuf_iterator<char>(in)),{});auto A=parse(s,"I0");if(A.size()!=N){cerr<<"bad A\n";return 2;}vector<int>idx(U,-1);for(int i=0;i<N;i++)idx[A[i]]=i;vector<array<int,D>>dig(U);for(int v=0;v<U;v++)dig[v]=dec5(v);array<int,D>w{};vector<Cand>cs;vector<Key>anchors;unordered_map<Key,int,KH>seen6;array<long long,12>cnt{};
for(int v=0;v<U;v++){if(idx[v]>=0)continue;vector<int>bs;auto d=dig[v];for(int m=0;m<243;m++){int z=m;for(int k=0;k<D;k++){int r=z%3-1;z/=3;w[k]=(d[k]+r+7)%7;}int q=enc5(w);if(idx[q]>=0)bs.push_back(idx[q]);}sort(bs.begin(),bs.end());bs.erase(unique(bs.begin(),bs.end()),bs.end());cnt[bs.size()]++;if(bs.empty()||bs.size()>6)continue;Cand c{};c.v=v;c.n=bs.size();for(int i=0;i<c.n;i++)c.k.a[i]=bs[i]+1;cs.push_back(c);if(c.n==6&&seen6.emplace(c.k,1).second)anchors.push_back(c.k);}
cerr<<"cands="<<cs.size()<<" anchors6="<<anchors.size()<<" counts";for(int i=0;i<12;i++)if(cnt[i])cerr<<" "<<i<<":"<<cnt[i];cerr<<"\n";
size_t maxpool=0,tested=0,generated=0; vector<vector<int>> adjOwner(N);
for(auto const&c:cs) if(c.n>=2 && c.n<=5) for(int i=0;i<c.n;i++) for(int j=i+1;j<c.n;j++){int a=c.k.a[i]-1,b=c.k.a[j]-1;adjOwner[a].push_back(b);adjOwner[b].push_back(a);}
for(auto&g:adjOwner){sort(g.begin(),g.end());g.erase(unique(g.begin(),g.end()),g.end());}
vector<Key> a5; unordered_map<Key,int,KH> seen5; for(auto const&c:cs)if(c.n==5&&seen5.emplace(c.k,1).second)a5.push_back(c.k);
unordered_map<Key,int,KH> seenU;
for(auto const&A5:a5){vector<int>xs;for(int i=0;i<5;i++){int u=A5.a[i]-1;for(int x:adjOwner[u]){bool inside=false;for(int h=0;h<5;h++)if(A5.a[h]==x+1)inside=true;if(!inside)xs.push_back(x);}}sort(xs.begin(),xs.end());xs.erase(unique(xs.begin(),xs.end()),xs.end());for(int x:xs){array<uint16_t,6>z{A5.a[0],A5.a[1],A5.a[2],A5.a[3],A5.a[4],(uint16_t)(x+1)};sort(z.begin(),z.end());Key U6{};U6.a=z;if(!seenU.emplace(U6,1).second)continue;generated++;vector<int>pool;for(auto const&c:cs)if(subset(c,U6))pool.push_back(c.v);maxpool=max(maxpool,pool.size());if(pool.size()<7)continue;tested++;vector<int>ch;if(find7(pool,dig,ch)){cout<<"FOUND c5 pool="<<pool.size()<<" remove=";for(int i=0;i<6;i++)cout<<(i?",":"")<<A[U6.a[i]-1];cout<<" add=";for(int i=0;i<7;i++)cout<<(i?",":"")<<ch[i];cout<<"\n";return 0;}}}
cout<<"NONE c5 anchors="<<a5.size()<<" owner6="<<generated<<" tested="<<tested<<" maxpool="<<maxpool<<"\n";
}
