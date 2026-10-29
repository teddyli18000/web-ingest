// Reproducible independent LABS 4-flip decomposition experiment; C++17 exact integers.
// g++ -O3 -std=c++17 fresh_interactions.cpp -o fresh_interactions
// ./fresh_interactions output.csv 100 3500 962167 40
// Arguments: path, length, independent starts, seed, greedy-hopping stages.
#include <bits/stdc++.h>
using namespace std;
struct L {
 int n,e; vector<int8_t> s; vector<int> c;
 L(vector<int8_t> v):n((int)v.size()),e(0),s(move(v)),c(n){
  for(int k=1;k<n;k++){for(int i=0;i<n-k;i++)c[k]+=s[i]*s[i+k];e+=c[k]*c[k];}}
 int delta(int p)const{
  int d=0;for(int k=1;k<n;k++){
   int t=(p>=k?s[p-k]:0)+(p+k<n?s[p+k]:0),h=-2*s[p]*t;
   d+=2*c[k]*h+h*h;
  }return d;}
 void flip(int p){
  int d=delta(p);
  for(int k=1;k<n;k++){int t=(p>=k?s[p-k]:0)+(p+k<n?s[p+k]:0);c[k]+=-2*s[p]*t;}
  s[p]=-s[p];e+=d;}
 int descent(int rule){
  int steps=0;while(true){
   int pos=-1,bd=0;for(int i=0;i<n;i++){int d=delta(i);if(d<bd){bd=d;pos=i;if(rule==1)break;}}
   if(pos<0)break;flip(pos);steps++;if(steps>10*n)throw runtime_error("descending loop");
  }return steps;}
};
int directE(const vector<int8_t>&s){
 int n=s.size(),e=0;for(int k=1;k<n;k++){int c=0;for(int i=0;i<n-k;i++)c+=s[i]*s[i+k];e+=c*c;}return e;}
void selftest(){
 mt19937_64 rng(483819);
 for(int n:{12,24,64,100})for(int it=0;it<70;it++){
  vector<int8_t> s(n);for(auto &v:s)v=(rng()%2)?1:-1;L a(s);assert(a.e==directE(s));
  for(int j=0;j<n;j++){auto u=s;u[j]=-u[j];assert(a.delta(j)==directE(u)-a.e);
   L b=a;b.flip(j);assert(b.e==directE(u)&&b.s==u);}
  a.descent(0);assert(a.e==directE(a.s));for(int j=0;j<n;j++)assert(a.delta(j)>=0);}
 string rec="++++++--+++++-----++-++--+--++++++++++---+-++--++++-+--++----+--+-+-+-+-++---++---++-+-++-+-++--+-+-";
 vector<int8_t> s;for(char x:rec)s.push_back(x=='+'?1:-1);
 assert(s.size()==100&&directE(s)==578);cerr<<"selftest PASS official E100=578 random delta/descent\n";
}
int main(int argc,char**argv){
 selftest();if(argc!=6){cerr<<"usage output N groups seed stage\n";return 2;}
 ofstream f(argv[1]);int n=stoi(argv[2]),groups=stoi(argv[3]),stage=stoi(argv[5]);
 uint64_t seed=stoull(argv[4]);mt19937_64 rng(seed),crng(seed+1000000007ULL);
 uniform_int_distribution<int> bit(0,n-1);int K=4,P=6;
 f<<"n,group,stage,candidate,baseE,singles,pairs,higher,exactDelta,steepE,firstE,steepSteps,firstSteps\n";
 for(int g=0;g<groups;g++){
  vector<int8_t> s(n);for(auto &v:s)v=(rng()&1)?1:-1;L base(s);base.descent(0);
  for(int h=0;h<stage;h++){
   auto t=base;vector<int> ids;while(ids.size()<4){int x=bit(rng);if(find(ids.begin(),ids.end(),x)==ids.end())ids.push_back(x);}
   for(int i:ids)t.flip(i);t.descent(0);if(t.e<base.e)base=move(t);}
  vector<int> d(n);for(int i=0;i<n;i++)d[i]=base.delta(i);
  for(int j=0;j<P;j++){
   vector<int> ids;while((int)ids.size()<K){int x=bit(crng);if(find(ids.begin(),ids.end(),x)==ids.end())ids.push_back(x);}
   sort(ids.begin(),ids.end());int singles=0,pairs=0;for(int i:ids)singles+=d[i];
   for(int a=0;a<K;a++)for(int b=a+1;b<K;b++){
    auto t=base;t.flip(ids[a]);int ij=t.delta(ids[b])-d[ids[b]];pairs+=ij;
    if(g==0&&j==0){auto w=base;w.flip(ids[a]);w.flip(ids[b]);assert(w.e-base.e-d[ids[a]]-d[ids[b]]==ij);}}
   auto t=base;for(int i:ids)t.flip(i);int full=t.e-base.e;
   auto u=t;int ss=u.descent(0);auto v=t;int fs=v.descent(1);
   if(g==0&&j==0){assert(directE(t.s)==t.e);assert(directE(u.s)==u.e);assert(directE(v.s)==v.e);}
   f<<n<<","<<g<<","<<stage<<","<<j<<","<<base.e<<","<<singles<<","<<pairs<<","
    <<(full-singles-pairs)<<","<<full<<","<<u.e<<","<<v.e<<","<<ss<<","<<fs<<"\n";
  }
  if(g%500==0)cerr<<"done "<<g<<" / "<<groups<<"\n";
 }
 cerr<<"done all groups "<<groups<<"\n";
}
