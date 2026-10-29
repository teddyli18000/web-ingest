// Exact row-dual exclusion for a degree-11 anchor with r=t-w=2 at m=220.
//
// For such an anchor v, S(v)=130 and the endpoint edge identity forces
// A=N(v) to be one of the two e(A)=26 R(3,6,11) graphs and
// B=V\(A union {v}) to be one of the nine e(B)=116 R(4,5,24) graphs.
// We deliberately relax all global degree labels on A: each A vertex may have
// any degree 11..17, so its cross-row size lies in
// [10-deg_A(a), 16-deg_A(a)], with the sole exact aggregate constraint
// sum_a |R_a| = S(v)-11-2e(A) = 67.
// Any solution of the real graph is therefore contained in this superfamily.
// Mixed K4/I6 constraints are checked exactly in the 11 row subsets R_a of B.
#include <bits/stdc++.h>
using namespace std;

static vector<uint32_t> parseg6(string s){
 vector<int>x;for(char c:s)x.push_back((unsigned char)c-63);
 int n=x[0],k=0;vector<int>bits;
 for(size_t q=1;q<x.size();q++)for(int i=5;i>=0;i--)bits.push_back((x[q]>>i)&1);
 vector<uint32_t>a(n);
 for(int j=1;j<n;j++)for(int i=0;i<j;i++)if(bits[k++])a[i]|=1u<<j,a[j]|=1u<<i;
 return a;
}
struct S{
 vector<uint32_t>A,B,BI2,BI3,BI4;array<vector<uint32_t>,11>D;
 array<uint32_t,11>asg{};array<char,11>done{};array<int,11>lo{},hi{};
 long long nodes=0;int maxd=0;bool timed=0;double tl;chrono::steady_clock::time_point t0;
 mt19937_64 rng;array<unsigned long long,12>dn{};
 S(string as,string bs,double t,uint64_t seed):A(parseg6(as)),B(parseg6(bs)),tl(t),rng(seed){
  for(int a=0;a<11;a++){int da=__builtin_popcount(A[a]);lo[a]=10-da;hi[a]=16-da;}
  buildSets();buildDom();
 }
 bool eA(int u,int v){return(A[u]>>v)&1u;} bool eB(int u,int v){return(B[u]>>v)&1u;}
 bool indep(uint32_t m){uint32_t q=m;while(q){int u=__builtin_ctz(q);q&=q-1;if(B[u]&q)return 0;}return 1;}
 bool tf(uint32_t m){uint32_t q=m;while(q){int u=__builtin_ctz(q);q&=q-1;uint32_t z=B[u]&q;while(z){int v=__builtin_ctz(z);z&=z-1;if(B[v]&q)return 0;}}return 1;}
 bool hit(uint32_t u,const vector<uint32_t>&V){for(auto z:V)if(!(u&z))return 0;return 1;}
 void buildSets(){
  for(int i=0;i<24;i++)for(int j=i+1;j<24;j++)if(!eB(i,j))BI2.push_back((1u<<i)|(1u<<j));
  for(int i=0;i<24;i++)for(int j=i+1;j<24;j++)for(int k=j+1;k<24;k++)if(!eB(i,j)&&!eB(i,k)&&!eB(j,k))BI3.push_back((1u<<i)|(1u<<j)|(1u<<k));
  for(int i=0;i<24;i++)for(int j=i+1;j<24;j++)for(int k=j+1;k<24;k++)for(int l=k+1;l<24;l++)
   if(!eB(i,j)&&!eB(i,k)&&!eB(i,l)&&!eB(j,k)&&!eB(j,l)&&!eB(k,l))BI4.push_back((1u<<i)|(1u<<j)|(1u<<k)|(1u<<l));
 }
 vector<uint32_t> comb(int k){
  vector<uint32_t>o;if(k<0||k>24)return o;uint32_t x=(1u<<k)-1,L=1u<<24;
  while(x<L){if(tf(x))o.push_back(x);uint32_t c=x&-x,r=x+c;if(r>=L||!r)break;x=(((r^x)>>2)/c)|r;}return o;
 }
 void buildDom(){
  map<int,vector<uint32_t>>cache;
  for(int a=0;a<11;a++)for(int k=lo[a];k<=hi[a];k++){
   if(!cache.count(k))cache[k]=comb(k);D[a].insert(D[a].end(),cache[k].begin(),cache[k].end());
  }
 }
 bool pairOK(int a,uint32_t x,int b,uint32_t y){return eA(a,b)?indep(x&y):hit(x|y,BI4);}
 bool highOK(int a,uint32_t x){
  vector<int>p;for(int b=0;b<11;b++)if(done[b])p.push_back(b);
  for(int i=0;i<(int)p.size();i++)for(int j=i+1;j<(int)p.size();j++){
   int b=p[i],c=p[j];if(eA(a,b)||eA(a,c)||eA(b,c))continue;if(!hit(x|asg[b]|asg[c],BI3))return 0;
  }
  for(int i=0;i<(int)p.size();i++)for(int j=i+1;j<(int)p.size();j++)for(int k=j+1;k<(int)p.size();k++){
   int b=p[i],c=p[j],d=p[k],v[4]={a,b,c,d};bool ok=1;
   for(int q=0;q<4;q++)for(int r=q+1;r<4;r++)if(eA(v[q],v[r]))ok=0;
   if(ok&&!hit(x|asg[b]|asg[c]|asg[d],BI2))return 0;
  }
  if(p.size()>=4){uint32_t ALL=(1u<<24)-1;
   for(int i=0;i<(int)p.size();i++)for(int j=i+1;j<(int)p.size();j++)for(int k=j+1;k<(int)p.size();k++)for(int l=k+1;l<(int)p.size();l++){
    int v[5]={a,p[i],p[j],p[k],p[l]};bool ok=1;
    for(int q=0;q<5;q++)for(int r=q+1;r<5;r++)if(eA(v[q],v[r]))ok=0;
    if(ok&&(x|asg[v[1]]|asg[v[2]]|asg[v[3]]|asg[v[4]])!=ALL)return 0;
   }
  }
  return 1;
 }
 vector<uint32_t> cand(int a,int used){
  vector<uint32_t>o;int minOther=0,maxOther=0;
  for(int b=0;b<11;b++)if(!done[b]&&b!=a){minOther+=lo[b];maxOther+=hi[b];}
  for(auto m:D[a]){int k=__builtin_popcount(m);if(used+k+minOther>67||used+k+maxOther<67)continue;
   bool ok=1;for(int b=0;b<11;b++)if(done[b]&&!pairOK(a,m,b,asg[b])){ok=0;break;}
   if(ok&&highOK(a,m))o.push_back(m);
  }return o;
 }
 bool timeout(){if((nodes&1023)==0&&chrono::duration<double>(chrono::steady_clock::now()-t0).count()>tl){timed=1;return 1;}return 0;}
 int dfs(int dep,int used){
  nodes++;dn[dep]++;maxd=max(maxd,dep);if(timeout())return 0;if(dep==11)return used==67?1:-1;
  int best=-1;vector<uint32_t>bc;
  for(int a=0;a<11;a++)if(!done[a]){auto c=cand(a,used);if(c.empty())return -1;if(best<0||c.size()<bc.size()){best=a;bc.swap(c);}}
  shuffle(bc.begin(),bc.end(),rng);
  for(auto m:bc){done[best]=1;asg[best]=m;int r=dfs(dep+1,used+__builtin_popcount(m));if(r==1)return 1;done[best]=0;if(timed)return 0;}
  return -1;
 }
 int run(){t0=chrono::steady_clock::now();return dfs(0,0);}
};
int main(int ac,char**av){
 if(ac<6){cerr<<"usage: solver A26.g6 B116.g6 A-index B-index seconds [seed]\n";return 2;}
 vector<string>A,B;string s;ifstream fa(av[1]);while(getline(fa,s))if(!s.empty())A.push_back(s);ifstream fb(av[2]);while(getline(fb,s))if(!s.empty())B.push_back(s);
 int ai=stoi(av[3]),bi=stoi(av[4]);double sec=stod(av[5]);uint64_t seed=ac>6?stoull(av[6]):1;
 S z(A.at(ai),B.at(bi),sec,seed);int r=z.run();
 cout<<"{\"a\":"<<ai<<",\"b\":"<<bi<<",\"status\":\""<<(r==1?"SAT":z.timed?"TIMEOUT":"UNSAT")<<"\",\"nodes\":"<<z.nodes<<",\"maxDepth\":"<<z.maxd<<",\"seconds\":"<<chrono::duration<double>(chrono::steady_clock::now()-z.t0).count()<<",\"rows\":[";
 if(r==1)for(int a=0;a<11;a++){if(a)cout<<",";cout<<z.asg[a];}cout<<"]}\n";
 return r==1?10:r==-1?20:0;
}
