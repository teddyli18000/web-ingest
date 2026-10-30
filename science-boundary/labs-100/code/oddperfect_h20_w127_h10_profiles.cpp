// Exact order-5/order-10 projection generator for the odd-perfect (20,0),
// W=127 branch (E=558).  It enforces the periodic odd-perfect cross condition
// H=A B*+x B A*=0 in the order-5 and order-10 quotients and the exact
// order-10 convex even-energy lower bound W>=127 (E_even>=508).
//
// Output files (default prefix "h10"):
//   <prefix>_A_codes.txt
//   <prefix>_B_codes.txt
//   <prefix>_pair_codes.txt
//
// Build: g++ -O3 -march=native -fopenmp oddperfect_h20_w127_h10_profiles.cpp -o h10_profiles
// Run:   OMP_NUM_THREADS=5 ./h10_profiles [prefix]
#include <algorithm>
#include <array>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <mutex>
#include <string>
#include <unordered_set>
#include <vector>
#ifdef _OPENMP
#include <omp.h>
#else
static double omp_get_wtime(){return 0.0;}
#endif
using A5=std::array<int,5>;

static std::vector<int> opts(int a){
 static const int o[6]={-5,-3,-1,1,3,5}; std::vector<int>d;
 for(int x:o)for(int y:o)if(x+y==a)d.push_back(x-y);
 std::sort(d.begin(),d.end());d.erase(std::unique(d.begin(),d.end()),d.end());return d;
}
static long long min_even_sq(int n,int S){
 if(S&1)return 1LL<<60;int t=S/2,q=t/n,r=t%n;if(r<0){r+=n;--q;}
 return 4LL*((n-r)*1LL*q*q+r*1LL*(q+1)*(q+1));
}
static A5 cross5(const A5&a,const A5&b){A5 k{};for(int j=0;j<5;j++)for(int i=0;i<5;i++)k[j]+=a[i]*b[(i-j+5)%5];return k;}
static A5 auto5(const A5&a){A5 k{};for(int j=0;j<5;j++)for(int i=0;i<5;i++)k[j]+=a[i]*a[(i+j)%5];return k;}
static bool h5(const A5&a,const A5&b){auto k=cross5(a,b);return k[0]+k[1]==0&&k[2]+k[4]==0&&k[3]==0;}
static long long lb5(const A5&a,const A5&b){
 auto x=auto5(a),y=auto5(b);int r0=x[0]+y[0],r1=x[1]+y[1],r2=x[2]+y[2];
 return min_even_sq(9,(r0-100)/2)+min_even_sq(20,r1)+min_even_sq(20,r2);
}
// Arithmetic in Z[x]/(x^5+1).
static A5 nmul(const A5&a,const A5&b){A5 o{};for(int i=0;i<5;i++)for(int j=0;j<5;j++){int k=i+j;if(k>=5)o[k-5]-=a[i]*b[j];else o[k]+=a[i]*b[j];}return o;}
static A5 nstar(const A5&a){return {a[0],-a[4],-a[3],-a[2],-a[1]};}
static A5 nx(const A5&a){return {-a[4],a[0],a[1],a[2],a[3]};}
static A5 heq(const A5&d,const A5&e){auto p=nmul(d,nstar(e)),q=nx(nmul(e,nstar(d)));A5 z{};for(int i=0;i<5;i++)z[i]=p[i]+q[i];return z;}
static std::array<A5,2> hmat(const A5&d){std::array<A5,2>M{};for(int j=0;j<5;j++){A5 e{};e[j]=1;auto z=heq(d,e);M[0][j]=z[0];M[1][j]=z[2];}return M;}
static bool contains(const std::vector<int>&v,int x){return std::binary_search(v.begin(),v.end(),x);}
static long long lb10(const A5&a,const A5&d,const A5&b,const A5&e,int aa[10],int bb[10]){
 for(int r=0;r<5;r++){aa[r]=(a[r]+d[r])/2;aa[r+5]=(a[r]-d[r])/2;bb[r]=(b[r]+e[r])/2;bb[r+5]=(b[r]-e[r])/2;}
 int R[6]{};for(int q=0;q<=5;q++)for(int i=0;i<10;i++)R[q]+=aa[i]*aa[(i+q)%10]+bb[i]*bb[(i+q)%10];
 long long L=min_even_sq(4,(R[0]-100)/2);for(int q=1;q<=4;q++)L+=min_even_sq(10,R[q]);if(R[5]&1)return 1LL<<60;return L+min_even_sq(5,R[5]/2);
}
static uint64_t code10(const int s[10]){uint64_t z=0,m=1;for(int i=0;i<10;i++){int v=(s[i]+5)/2;z+=m*v;m*=6;}return z;}
static std::mutex mu;static std::unordered_set<uint64_t> SA,SB,SP;
static void note(const A5&a,const A5&d,const A5&b,const A5&e){
 int aa[10],bb[10];if(lb10(a,d,b,e,aa,bb)!=508)return;uint64_t ca=code10(aa),cb=code10(bb),cp=ca|(cb<<26);
 std::lock_guard<std::mutex>g(mu);SA.insert(ca);SB.insert(cb);SP.insert(cp);
}
static void lift(const A5&a,const A5&b){
 std::array<std::vector<int>,5>D,E;for(int i=0;i<5;i++){D[i]=opts(a[i]);E[i]=opts(b[i]);}
 for(int d0:D[0])for(int d1:D[1])for(int d2:D[2])for(int d3:D[3])for(int d4:D[4]){
  A5 d{d0,d1,d2,d3,d4};auto M=hmat(d);int p=-1,q=-1,det0=0;
  for(int i=0;i<5;i++)for(int j=i+1;j<5;j++){int dt=M[0][i]*M[1][j]-M[0][j]*M[1][i];if(std::abs(dt)>std::abs(det0)){det0=dt;p=i;q=j;}}
  if(!det0)continue;
  int f[3],kk=0;for(int j=0;j<5;j++)if(j!=p&&j!=q)f[kk++]=j;
  for(int x:E[f[0]])for(int y:E[f[1]])for(int z:E[f[2]]){
   A5 e{};e[f[0]]=x;e[f[1]]=y;e[f[2]]=z;long long r0=0,r1=0;for(int j:f){r0-=1LL*M[0][j]*e[j];r1-=1LL*M[1][j]*e[j];}
   long long np=r0*M[1][q]-1LL*M[0][q]*r1,nq=1LL*M[0][p]*r1-r0*M[1][p];if(np%det0||nq%det0)continue;
   int ep=np/det0,eq=nq/det0;if(!contains(E[p],ep)||!contains(E[q],eq))continue;e[p]=ep;e[q]=eq;
   int aa[10],bb[10];if(lb10(a,d,b,e,aa,bb)<=508)note(a,d,b,e);
  }
 }
}
static void gen(int pos,int rem,A5&p,std::vector<A5>&out){if(pos==5){if(!rem)out.push_back(p);return;}for(int x=-10;x<=10;x+=2){p[pos]=x;gen(pos+1,rem-x,p,out);}}
int main(int argc,char**argv){
 std::string pre=argc>1?argv[1]:"h10";std::vector<A5>A,B;A5 p{};gen(0,20,p,A);gen(0,0,p,B);double t=omp_get_wtime();
#pragma omp parallel for schedule(dynamic,1)
 for(size_t i=0;i<A.size();i++)for(const auto&b:B)if(h5(A[i],b)&&lb5(A[i],b)<=508)lift(A[i],b);
 std::cerr<<"unique_A="<<SA.size()<<" unique_B="<<SB.size()<<" pairs="<<SP.size()<<" seconds="<<omp_get_wtime()-t<<"\n";
 std::ofstream fa(pre+"_A_codes.txt"),fb(pre+"_B_codes.txt"),fp(pre+"_pair_codes.txt");
 for(auto x:SA)fa<<x<<"\n";for(auto x:SB)fb<<x<<"\n";for(auto x:SP)fp<<x<<"\n";
}
