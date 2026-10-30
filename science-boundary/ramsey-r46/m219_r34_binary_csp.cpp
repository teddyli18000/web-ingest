// Exact relaxed binary row-domain CSP for the final m=219 degree sequences.
// Usage: solver A25.g6 A26.g6 B116.g6 B117.g6 [threads]
//
// A genuine gluing is relaxed to pairwise row constraints only:
//  * row size is in [10-deg_A(a),12-deg_A(a)] (global degree 11..13);
//  * each row is triangle-free in B;
//  * for an A-edge, the two row intersection is independent in B;
//  * for an A-nonedge, the two row union hits every independent 4-set of B.
// B-column degrees, degree-class counts, total cross-edge count, and every
// >=3-row mixed condition are omitted. Therefore UNSAT here rigorously implies
// UNSAT for the original Ramsey gluing.
#include <bits/stdc++.h>
using namespace std;
static vector<string> lines(const string&p){ifstream f(p);if(!f)throw runtime_error("open "+p);vector<string>v;string s;while(getline(f,s))if(!s.empty())v.push_back(s);return v;}
static vector<uint32_t> g6(const string&s){vector<int>x;for(char c:s)x.push_back((unsigned char)c-63);int n=x.at(0),k=0;vector<int>b;for(size_t q=1;q<x.size();q++)for(int i=5;i>=0;i--)b.push_back((x[q]>>i)&1);vector<uint32_t>g(n);for(int j=1;j<n;j++)for(int i=0;i<j;i++){if(k>=(int)b.size())throw runtime_error("bad graph6");if(b[k++])g[i]|=1u<<j,g[j]|=1u<<i;}return g;}
static int edges(const vector<uint32_t>&g){long long s=0;for(auto x:g)s+=__builtin_popcount(x);return s/2;}
static bool K4(const vector<uint32_t>&g){int n=g.size();for(int a=0;a<n;a++)for(int b=a+1;b<n;b++)if((g[a]>>b)&1u)for(int c=b+1;c<n;c++)if(((g[a]>>c)&1u)&&((g[b]>>c)&1u))for(int d=c+1;d<n;d++)if(((g[a]>>d)&1u)&&((g[b]>>d)&1u)&&((g[c]>>d)&1u))return true;return false;}
static bool tri(const vector<uint32_t>&g){int n=g.size();for(int a=0;a<n;a++)for(int b=a+1;b<n;b++)if((g[a]>>b)&1u)for(int c=b+1;c<n;c++)if(((g[a]>>c)&1u)&&((g[b]>>c)&1u))return true;return false;}
static bool indK(const vector<uint32_t>&g,int k){int n=g.size();function<bool(int,int,uint32_t)>D=[&](int st,int left,uint32_t m){if(!left)return true;if(n-st<left)return false;for(int v=st;v<=n-left;v++)if(!(g[v]&m)&&D(v+1,left-1,m|(1u<<v)))return true;return false;};return D(0,k,0);}
struct Solver{
 vector<uint32_t>A,B,I4;array<vector<uint32_t>,11>dom;array<uint32_t,11>val{};array<char,11>set{};long long nodes=0;int depth=0;
 Solver(string as,string bs):A(g6(as)),B(g6(bs)){for(int i=0;i<24;i++)for(int j=i+1;j<24;j++)if(!((B[i]>>j)&1u))for(int k=j+1;k<24;k++)if(!((B[i]>>k)&1u)&&!((B[j]>>k)&1u))for(int l=k+1;l<24;l++)if(!((B[i]>>l)&1u)&&!((B[j]>>l)&1u)&&!((B[k]>>l)&1u))I4.push_back((1u<<i)|(1u<<j)|(1u<<k)|(1u<<l));build();}
 bool eA(int i,int j)const{return(A[i]>>j)&1u;}
 bool indep(uint32_t m)const{uint32_t q=m;while(q){int u=__builtin_ctz(q);q&=q-1;if(B[u]&q)return false;}return true;}
 bool tf(uint32_t m)const{uint32_t q=m;while(q){int u=__builtin_ctz(q);q&=q-1;uint32_t z=B[u]&q;while(z){int v=__builtin_ctz(z);z&=z-1;if(B[v]&q)return false;}}return true;}
 bool hit(uint32_t m)const{for(auto z:I4)if(!(m&z))return false;return true;}
 vector<uint32_t> masks(int k)const{vector<uint32_t>o;if(k<0||k>24)return o;if(!k){o.push_back(0);return o;}uint32_t x=(1u<<k)-1,L=1u<<24;while(x<L){if(tf(x))o.push_back(x);uint32_t c=x&-x,r=x+c;if(!r||r>=L)break;x=(((r^x)>>2)/c)|r;}return o;}
 void build(){map<int,vector<uint32_t>>cache;for(int a=0;a<11;a++){int d=__builtin_popcount(A[a]);for(int k=10-d;k<=12-d;k++){if(!cache.count(k))cache[k]=masks(k);dom[a].insert(dom[a].end(),cache[k].begin(),cache[k].end());}}}
 bool ok(int a,uint32_t x,int b,uint32_t y)const{return eA(a,b)?indep(x&y):hit(x|y);}
 vector<uint32_t> cand(int a)const{vector<uint32_t>o;for(auto x:dom[a]){bool z=true;for(int b=0;b<11;b++)if(set[b]&&!ok(a,x,b,val[b])){z=false;break;}if(z)o.push_back(x);}return o;}
 bool dfs(int dep){nodes++;depth=max(depth,dep);if(dep==11)return true;int best=-1;vector<uint32_t>C;for(int a=0;a<11;a++)if(!set[a]){auto c=cand(a);if(c.empty())return false;if(best<0||c.size()<C.size())best=a,C.swap(c);}for(auto x:C){set[best]=1;val[best]=x;if(dfs(dep+1))return true;set[best]=0;}return false;}
};
static void validate(const vector<string>&V,int n,int e,bool isA){for(auto&s:V){auto g=g6(s);if((int)g.size()!=n||edges(g)!=e)throw runtime_error("catalog mismatch");if(isA){if(tri(g)||indK(g,6))throw runtime_error("bad A");}else if(K4(g)||indK(g,5))throw runtime_error("bad B");}}
struct R{string f;int a,b;bool sat;long long nodes;int dep;};
static vector<R> family(string name,const vector<string>&A,const vector<string>&B,int nth){vector<pair<int,int>>J;for(int a=0;a<(int)A.size();a++)for(int b=0;b<(int)B.size();b++)J.push_back({a,b});vector<R>O(J.size());atomic<size_t>N{0};vector<thread>T;for(int t=0;t<nth;t++)T.emplace_back([&]{for(;;){auto i=N.fetch_add(1);if(i>=J.size())break;auto[a,b]=J[i];Solver s(A[a],B[b]);bool z=s.dfs(0);O[i]={name,a,b,z,s.nodes,s.depth};}});for(auto&t:T)t.join();return O;}
int main(int ac,char**av){if(ac<5){cerr<<"usage: solver A25 A26 B116 B117 [threads]\n";return 64;}auto A25=lines(av[1]),A26=lines(av[2]),B116=lines(av[3]),B117=lines(av[4]);int nth=ac>5?max(1,atoi(av[5])):max(1u,thread::hardware_concurrency());if(A25.size()!=6||A26.size()!=2||B116.size()!=9||B117.size()!=90)throw runtime_error("catalog count");validate(A25,11,25,1);validate(A26,11,26,1);validate(B116,24,116,0);validate(B117,24,117,0);vector<R>O;auto add=[&](auto x){O.insert(O.end(),x.begin(),x.end());};add(family("r3_A26_B116",A26,B116,nth));add(family("r4_A25_B116",A25,B116,nth));add(family("r4_A26_B117",A26,B117,nth));map<string,array<long long,4>>S;bool sat=false;for(auto&r:O){auto&x=S[r.f];x[0]++;x[1]+=r.nodes;x[2]=max(x[2],r.nodes);x[3]=max<long long>(x[3],r.dep);sat|=r.sat;}cout<<"{\"all_unsat\":"<<(sat?"false":"true")<<",\"total_pairs\":"<<O.size()<<",\"families\":{";bool first=true;for(auto&[k,x]:S){if(!first)cout<<',';first=false;cout<<'\"'<<k<<"\":{\"pairs\":"<<x[0]<<",\"total_nodes\":"<<x[1]<<",\"max_nodes\":"<<x[2]<<",\"max_depth\":"<<x[3]<<"}";}cout<<"}}\n";return sat?1:0;}
