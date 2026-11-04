// Exact enumeration of every O=58 one-B-flip-near-skew state in given A-case list.
// Each free antipodal B pair is toggled in Gray order, updating even C_k exactly.
#include <bits/stdc++.h>
#include <omp.h>
using namespace std;
using X=array<int8_t,50>;using Corr=array<int,50>;
struct Case{int j,h;X A;};
struct Result{uint64_t configs=0;int minE=INT_MAX;string sequence;int minH=999;int f=0;int j=-1,h=-1;};
int energy100(const X&A,const X&B,int &O,int &V){int s[100];for(int i=0;i<50;i++){s[2*i]=A[i];s[2*i+1]=B[i];}
 O=V=0;for(int k=1;k<100;k++){int c=0;for(int i=0;i+k<100;i++)c+=s[i]*s[i+k];if(k&1)O+=c*c;else V+=c*c;}return O+V;
}
string str100(const X&A,const X&B){string s;for(int i=0;i<50;i++){s+=A[i]>0?'+':'-';s+=B[i]>0?'+':'-';}return s;}
Corr acf(const X&s){Corr c{};for(int k=1;k<50;k++)for(int j=0;j+k<50;j++)c[k]+=s[j]*s[j+k];return c;}
Result scan(const Case&z,int minf,int maxf){
 X A=z.A,B{};int j=z.j,h=z.h;int w[50]{};for(int r=0;r<50;r++){
  if(j>=r)w[r]+=A[j-r];if(j+r+1<50)w[r]+=A[j+r+1];
 }
 vector<int>free;int fixedCounts=0;
 for(int r=0;r<25;r++){
  int target=(r==h?10:2);
  int required=j==r?-1:j==49-r?1:0;
  vector<int>opts;
  for(int b:{-1,1}){
   if(required&&b!=required)continue;
   int D1=A[0]*b+2*w[r],D2=-A[0]*b+2*w[49-r];
   if(D1*D1+D2*D2==target)opts.push_back(b);
  }
  assert(!opts.empty());
  B[r]=opts[0];B[49-r]=-opts[0];
  if(opts.size()==2)free.push_back(r);else fixedCounts++;
 }
 Result out{};out.f=free.size();out.j=j;out.h=h;
 if(out.f>maxf||out.f<minf)return out;
 assert(B[j]==-1);B[j]=1;
 Corr ca=acf(A),cb=acf(B);int V=0;for(int k=1;k<50;k++){int v=ca[k]+cb[k];V+=v*v;}
 int OD,VD;assert(energy100(A,B,OD,VD)==58+V&&OD==58&&VD==V);
 out.minE=58+V;out.sequence=str100(A,B);uint64_t max=1ull<<free.size();
 for(uint64_t step=1;step<max;step++){
  int r=free[__builtin_ctzll(step)],u=r,v=49-r;
  for(int k=1;k<50;k++){
   int delta=0;
   int u1=u+k,u0=u-k;
   if(u1<50&&u1!=v)delta-=2*B[u]*B[u1];
   if(u0>=0&&u0!=v)delta-=2*B[u]*B[u0];
   int v1=v+k,v0=v-k;
   if(v1<50&&v1!=u)delta-=2*B[v]*B[v1];
   if(v0>=0&&v0!=u)delta-=2*B[v]*B[v0];
   int before=ca[k]+cb[k],after=before+delta;
   V+=after*after-before*before;cb[k]+=delta;
  }
  B[u]=-B[u];B[v]=-B[v];
  int E=58+V;
  if(E<out.minE){
   int Ocheck,Vcheck;assert(energy100(A,B,Ocheck,Vcheck)==E&&Ocheck==58&&Vcheck==V);
   out.minE=E;out.sequence=str100(A,B);
  }
 }
 out.configs=max;
 return out;
}
int main(int argc,char**argv){
 int maxf=argc>1?atoi(argv[1]):24;
 int restrictJ=argc>2?atoi(argv[2]):-1;
 int minf=argc>3?atoi(argv[3]):0;
 vector<Case>input;string str;int j,h;
 while(cin>>j>>h>>str){Case z{};z.j=j;z.h=h;assert(str.size()==50);for(int i=0;i<50;i++)z.A[i]=str[i]=='+'?1:-1;input.push_back(z);}
 uint64_t cases=0, configs=0;int bestE=INT_MAX;string bestSeq;
 map<int,int>casehist;array<uint64_t,25>completedPerF{};
#pragma omp parallel for schedule(dynamic,1) reduction(+:cases,configs)
 for(int i=0;i<(int)input.size();i++){
  if(restrictJ>=0&&input[i].j!=restrictJ)continue;
  auto out=scan(input[i],minf,maxf);
  if(out.configs==0)continue;
  cases++;configs+=out.configs;
#pragma omp critical
  {
   casehist[out.f]++;
   completedPerF[out.f]+=out.configs;
   if(out.minE<bestE){bestE=out.minE;bestSeq=out.sequence;
    cerr<<"NEW_BEST E="<<bestE<<" j="<<out.j<<" h="<<out.h<<" free="<<out.f<<"\n";
   }
  }
 }
 cout<<"ONEFLIP_EXACT inputCases="<<input.size()<<" scannedCases="<<cases<<" maxFree="<<maxf
     <<" restrictJ="<<restrictJ<<" minFree="<<minf<<" configurations="<<configs<<" minE="<<bestE<<"\n";
 cout<<"BEST_SEQUENCE "<<bestSeq<<"\n";
 for(auto [f,n]:casehist)cout<<"FAMILY f="<<f<<" cases="<<n<<" configurations="<<completedPerF[f]<<"\n";
}
