// Exact order-10 quotient profile generator for the five hard W129/W131 cases.
//
// For the (A,B) parity halves (length 50, sums 20 and 0), odd-perfectness
// implies H=A B* + x B A*=0 at every 10th root of unity.  We enumerate all
// order-5 residue profiles, lift them exactly to order 10, and retain only
// profiles whose order-10 periodic autocorrelation quotient matches one of
// three W129/W131 periodic types:
//   low11 : P25=4, eleven P_r=4 pairs and thirteen P_r=8 pairs;
//   a0    : P25=4, one P_r=0 pair, nine P_r=4, fourteen P_r=8;
//   low12 : P25=12, twelve P_r=4 pairs and twelve P_r=8 pairs.
//
// Output files <prefix>_{low11,a0,low12}.txt contain:
//   packed_profile R0 R1 R2 R3 R4 R5
// where packed_profile stores the ten A residue sums and ten B residue sums.
// Build: g++ -O3 -march=native -fopenmp ... -o profiles
#include <algorithm>
#include <array>
#include <atomic>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <mutex>
#include <string>
#include <unordered_map>
#include <vector>
#ifdef _OPENMP
#include <omp.h>
#endif
using A5=std::array<int,5>;
struct Row { std::array<int,6> R{}; };

static std::vector<int> opts(int a){
 static const int o[6]={-5,-3,-1,1,3,5}; std::vector<int>d;
 for(int x:o)for(int y:o)if(x+y==a)d.push_back(x-y);
 std::sort(d.begin(),d.end());d.erase(std::unique(d.begin(),d.end()),d.end());return d;
}
static A5 cross5(const A5&a,const A5&b){A5 k{};for(int q=0;q<5;q++)for(int i=0;i<5;i++)k[q]+=a[i]*b[(i-q+5)%5];return k;}
static bool h5(const A5&a,const A5&b){auto k=cross5(a,b);return k[0]+k[1]==0&&k[2]+k[4]==0&&k[3]==0;}
// Arithmetic in Z[x]/(x^5+1) for the odd 10th-root half of H=0.
static A5 nmul(const A5&a,const A5&b){A5 o{};for(int i=0;i<5;i++)for(int j=0;j<5;j++){int k=i+j;if(k>=5)o[k-5]-=a[i]*b[j];else o[k]+=a[i]*b[j];}return o;}
static A5 nstar(const A5&a){return {a[0],-a[4],-a[3],-a[2],-a[1]};}
static A5 nx(const A5&a){return {-a[4],a[0],a[1],a[2],a[3]};}
static A5 heq(const A5&d,const A5&e){auto p=nmul(d,nstar(e)),q=nx(nmul(e,nstar(d)));A5 z{};for(int i=0;i<5;i++)z[i]=p[i]+q[i];return z;}
static std::array<A5,2> hmat(const A5&d){std::array<A5,2>M{};for(int j=0;j<5;j++){A5 e{};e[j]=1;auto z=heq(d,e);M[0][j]=z[0];M[1][j]=z[2];}return M;}
static bool contains(const std::vector<int>&v,int x){return std::binary_search(v.begin(),v.end(),x);}
static uint64_t code10(const int s[10]){uint64_t z=0,m=1;for(int i=0;i<10;i++){z+=m*((s[i]+5)/2);m*=6;}return z;}

static bool target_type(const int R[6],int type){
 // Category capacities among r=1..24 for residues 0, +/-1, +/-2, +/-3, +/-4, 5 mod 10.
 static const int cap[6]={2,5,5,5,5,2};
 if(type==0 || type==2){
  const int target=(type==0?11:12), base5=(type==0?36:44);
  int n[6],x=132-R[0]; if(x%8)return false; n[0]=x/8;
  x=base5-R[5]; if(x%8)return false; n[5]=x/8;
  for(int q=1;q<=4;q++){x=40-R[q];if(x%4)return false;n[q]=x/4;}
  int s=0;for(int q=0;q<6;q++){if(n[q]<0||n[q]>cap[q])return false;s+=n[q];}
  return s==target;
 }
 // type 1: exactly one zero periodic pair and nine low (=4) periodic pairs.
 for(int z=0;z<6;z++){
  int n[6],x=132-R[0]-(z==0?16:0); if(x%8)continue; n[0]=x/8;
  x=36-R[5]-(z==5?16:0); if(x%8)continue; n[5]=x/8;
  bool ok=true;
  for(int q=1;q<=4;q++){x=40-R[q]-(z==q?8:0);if(x%4){ok=false;break;}n[q]=x/4;}
  if(!ok)continue;
  int s=0;for(int q=0;q<6;q++){int c=cap[q]-(z==q);if(n[q]<0||n[q]>c){ok=false;break;}s+=n[q];}
  if(ok&&s==9)return true;
 }
 return false;
}

static std::array<std::unordered_map<uint64_t,Row>,3> rows;
static std::array<std::mutex,3> mus;
static std::array<std::atomic<long long>,3> hits{};
static std::atomic<long long> lifts{0};

static void note(const A5&a,const A5&d,const A5&b,const A5&e){
 int aa[10],bb[10];
 for(int r=0;r<5;r++){
  aa[r]=(a[r]+d[r])/2; aa[r+5]=(a[r]-d[r])/2;
  bb[r]=(b[r]+e[r])/2; bb[r+5]=(b[r]-e[r])/2;
 }
 int R[6]{};
 for(int q=0;q<=5;q++)for(int i=0;i<10;i++)R[q]+=aa[i]*aa[(i+q)%10]+bb[i]*bb[(i+q)%10];
 const uint64_t cp=code10(aa)|(code10(bb)<<26); ++lifts;
 for(int t=0;t<3;t++)if(target_type(R,t)){
  ++hits[t]; Row row;for(int q=0;q<6;q++)row.R[q]=R[q];
  std::lock_guard<std::mutex>g(mus[t]); rows[t].emplace(cp,row);
 }
}

static void gen(int p,int rem,A5&x,std::vector<A5>&out){if(p==5){if(rem==0)out.push_back(x);return;}for(int v=-10;v<=10;v+=2){x[p]=v;gen(p+1,rem-v,x,out);}}

int main(int argc,char**argv){
 const std::string pre=argc>1?argv[1]:"w131_h10";
 std::vector<A5>A,B; A5 p{}; gen(0,20,p,A); gen(0,0,p,B);
#pragma omp parallel for schedule(dynamic,1)
 for(size_t ia=0;ia<A.size();ia++)for(const auto&b:B){
  if(!h5(A[ia],b))continue;
  std::array<std::vector<int>,5>D,E;for(int i=0;i<5;i++){D[i]=opts(A[ia][i]);E[i]=opts(b[i]);}
  for(int d0:D[0])for(int d1:D[1])for(int d2:D[2])for(int d3:D[3])for(int d4:D[4]){
   A5 d{d0,d1,d2,d3,d4};auto M=hmat(d);int pp=-1,qq=-1,det0=0;
   for(int i=0;i<5;i++)for(int j=i+1;j<5;j++){int dt=M[0][i]*M[1][j]-M[0][j]*M[1][i];if(std::abs(dt)>std::abs(det0)){det0=dt;pp=i;qq=j;}}
   if(det0){
    int f[3],k=0;for(int j=0;j<5;j++)if(j!=pp&&j!=qq)f[k++]=j;
    for(int x:E[f[0]])for(int y:E[f[1]])for(int z:E[f[2]]){
     A5 e{};e[f[0]]=x;e[f[1]]=y;e[f[2]]=z;long long r0=0,r1=0;
     for(int j:f){r0-=1LL*M[0][j]*e[j];r1-=1LL*M[1][j]*e[j];}
     long long np=r0*M[1][qq]-1LL*M[0][qq]*r1,nq=1LL*M[0][pp]*r1-r0*M[1][pp];
     if(np%det0||nq%det0)continue;int ep=np/det0,eq=nq/det0;
     if(!contains(E[pp],ep)||!contains(E[qq],eq))continue;e[pp]=ep;e[qq]=eq;note(A[ia],d,b,e);
    }
   }else{
    int row=-1,piv=-1;for(int rr=0;rr<2&&row<0;rr++)for(int j=0;j<5;j++)if(M[rr][j]){row=rr;piv=j;break;}
    if(row<0){for(int e0:E[0])for(int e1:E[1])for(int e2:E[2])for(int e3:E[3])for(int e4:E[4])note(A[ia],d,b,A5{e0,e1,e2,e3,e4});}
    else{
     int f[4],k=0;for(int j=0;j<5;j++)if(j!=piv)f[k++]=j;
     for(int x:E[f[0]])for(int y:E[f[1]])for(int z:E[f[2]])for(int w:E[f[3]]){
      A5 e{};e[f[0]]=x;e[f[1]]=y;e[f[2]]=z;e[f[3]]=w;long long rhs=0;for(int j:f)rhs-=1LL*M[row][j]*e[j];int den=M[row][piv];
      if(rhs%den)continue;int ep=rhs/den;if(!contains(E[piv],ep))continue;e[piv]=ep;auto zz=heq(d,e);if(zz[0]||zz[2])continue;note(A[ia],d,b,e);
     }
    }
   }
  }
 }
 const char* names[3]={"low11","a0","low12"};
 std::cerr<<"lifts="<<lifts;
 for(int t=0;t<3;t++){
  std::cerr<<" "<<names[t]<<"_hits="<<hits[t]<<" "<<names[t]<<"_unique="<<rows[t].size();
  std::ofstream f(pre+"_"+names[t]+".txt");
  for(const auto&kv:rows[t]){f<<kv.first;for(int q=0;q<6;q++)f<<' '<<kv.second.R[q];f<<'\n';}
 }
 std::cerr<<"\n";
}
