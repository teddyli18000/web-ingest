#include <algorithm>
#include <array>
#include <cstdint>
#include <fstream>
#include <functional>
#include <iostream>
#include <sstream>
#include <unordered_map>
#include <unordered_set>
#include <vector>
using namespace std; constexpr int D=5,U=16807,N=367;
array<int,D> dec5(int v){array<int,D>a{};for(int i=0;i<D;i++){a[i]=v%7;v/=7;}return a;} int enc5(const array<int,D>&a){int v=0,m=1;for(int i=0;i<D;i++){v+=a[i]*m;m*=7;}return v;}
vector<int> parse(const string&s,const string&key){vector<int>a;auto p=s.find("\""+key+"\"");p=s.find('[',p);auto e=s.find(']',p);stringstream ss(s.substr(p+1,e-p-1));while(ss){int x;if(ss>>x)a.push_back(x);if(ss.peek()==',')ss.get();else{ss.clear();char c;ss>>c;}}return a;}
struct Key{array<uint16_t,6>a{};bool operator==(Key const&o)const{return a==o.a;}};struct KH{size_t operator()(Key const&k)const noexcept{size_t h=0;for(auto x:k.a)h=h*1000003u+x;return h;}};int ksize(Key const&k){int n=0;while(n<6&&k.a[n])n++;return n;}
Key sub6(Key const&u,unsigned mask){Key k{};int j=0;for(int i=0;i<6;i++)if(mask>>i&1)k.a[j++]=u.a[i];return k;}
bool conf(int a,int b,const vector<array<int,D>>&dig){auto x=dig[a],y=dig[b];for(int k=0;k<D;k++){int z=(x[k]-y[k]+7)%7;if(z!=0&&z!=1&&z!=6)return false;}return true;}
bool find7(vector<int>p,const vector<array<int,D>>&dig,vector<int>&out){sort(p.begin(),p.end());p.erase(unique(p.begin(),p.end()),p.end());vector<int>ch;function<bool(int)>dfs=[&](int s){if(ch.size()==7){out=ch;return true;}if((int)ch.size()+(int)p.size()-s<7)return false;for(int i=s;i<(int)p.size();i++){bool ok=true;for(int z:ch)if(conf(z,p[i],dig)){ok=false;break;}if(!ok)continue;ch.push_back(p[i]);if(dfs(i+1))return true;ch.pop_back();}return false;};return dfs(0);}
int main(int argc,char**argv){if(argc!=3){cerr<<"usage: c7p5_r6_connected I0_JSON K(2|3)\n";return 2;}int K=stoi(argv[2]);if(K<2||K>3)return 2;ifstream in(argv[1]);string s((istreambuf_iterator<char>(in)),{});auto A=parse(s,"I0");vector<int>idx(U,-1);for(int i=0;i<N;i++)idx[A[i]]=i;vector<array<int,D>>dig(U);for(int v=0;v<U;v++)dig[v]=dec5(v);array<int,D>w{};unordered_map<Key,vector<int>,KH> groups;
for(int v=0;v<U;v++){if(idx[v]>=0)continue;vector<int>bs;auto d=dig[v];for(int m=0;m<243;m++){int z=m;for(int k=0;k<D;k++){int r=z%3-1;z/=3;w[k]=(d[k]+r+7)%7;}int q=enc5(w);if(idx[q]>=0)bs.push_back(idx[q]);}sort(bs.begin(),bs.end());bs.erase(unique(bs.begin(),bs.end()),bs.end());if(bs.empty()||bs.size()>6)continue;Key k{};for(int i=0;i<(int)bs.size();i++)k.a[i]=bs[i]+1;groups[k].push_back(v);}
vector<Key> anchors;vector<vector<uint16_t>> hedges;vector<vector<int>> incident(N);for(auto const&kv:groups){int n=ksize(kv.first);if(n==K)anchors.push_back(kv.first);if(n>=2&&n<=K){vector<uint16_t>e(n);for(int i=0;i<n;i++)e[i]=kv.first.a[i];int id=hedges.size();hedges.push_back(e);for(auto x:e)incident[x-1].push_back(id);}}
auto poolFor=[&](Key const&u){vector<int>p;for(unsigned mask=1;mask<64;mask++){auto it=groups.find(sub6(u,mask));if(it!=groups.end())p.insert(p.end(),it->second.begin(),it->second.end());}sort(p.begin(),p.end());p.erase(unique(p.begin(),p.end()),p.end());return p;};
unordered_set<Key,KH> visited,finals;size_t expansions=0,tested=0,maxpool=0;vector<int>wadd;Key wU{};bool found=false;
function<void(Key)> dfs=[&](Key cur){if(found)return;if(!visited.insert(cur).second)return;int n=ksize(cur);if(n==6){if(!finals.insert(cur).second)return;auto p=poolFor(cur);maxpool=max(maxpool,p.size());if(p.size()<7)return;tested++;vector<int>ch;if(find7(p,dig,ch)){found=true;wU=cur;wadd=ch;}return;}vector<int>eids;for(int i=0;i<n;i++)eids.insert(eids.end(),incident[cur.a[i]-1].begin(),incident[cur.a[i]-1].end());sort(eids.begin(),eids.end());eids.erase(unique(eids.begin(),eids.end()),eids.end());for(int ei:eids){vector<uint16_t>u;for(int i=0;i<n;i++)u.push_back(cur.a[i]);bool crosses=false;for(auto x:hedges[ei]){if(!binary_search(u.begin(),u.end(),x)){u.push_back(x);crosses=true;}}if(!crosses||u.size()>6)continue;sort(u.begin(),u.end());u.erase(unique(u.begin(),u.end()),u.end());if(u.size()>6)continue;Key nx{};for(int i=0;i<(int)u.size();i++)nx.a[i]=u[i];expansions++;dfs(nx);if(found)return;}};
for(auto a:anchors){dfs(a);if(found)break;}if(found){cout<<"FOUND K="<<K<<" remove=";for(int i=0;i<6;i++)cout<<(i?",":"")<<A[wU.a[i]-1];cout<<" add=";for(int i=0;i<7;i++)cout<<(i?",":"")<<wadd[i];cout<<"\n";return 0;}cout<<"NONE K="<<K<<" anchors="<<anchors.size()<<" hyperedges="<<hedges.size()<<" visited="<<visited.size()<<" finals="<<finals.size()<<" expansions="<<expansions<<" tested="<<tested<<" maxpool="<<maxpool<<"\n";}
