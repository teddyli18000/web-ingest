// Exact low-order spectral projection enumerator for the odd-perfect (20,0)
// half-sum class.  It enumerates all order-5 residue profiles satisfying H=0,
// applies a rigorous even-energy lower bound, then exactly lifts every survivor
// to the order-10 negacyclic condition by eliminating two epsilon coordinates.
#include <array>
#include <vector>
#include <iostream>
#include <algorithm>
#include <atomic>
#include <chrono>
#include <cstdlib>
#ifdef _OPENMP
#include <omp.h>
#endif
using A5=std::array<int,5>;

static std::vector<int> opts(int a){
 static const int o[6]={-5,-3,-1,1,3,5};std::vector<int>d;
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
static std::array<A5,2> hmat(const A5&d){
 std::array<A5,2>M{};for(int j=0;j<5;j++){A5 e{};e[j]=1;auto z=heq(d,e);M[0][j]=z[0];M[1][j]=z[2];}return M;
}
static bool contains(const std::vector<int>&v,int x){return std::binary_search(v.begin(),v.end(),x);}

// Order-10 residue sums give six disjoint groups of the 49 even correlations:
// 4 lags congruent 0, 10 lags in each +/-1..+/-4 pair, and 5 lags ==5 mod10.
static long long lb10(const A5&a,const A5&d,const A5&b,const A5&e){
 int aa[10],bb[10];for(int r=0;r<5;r++){aa[r]=(a[r]+d[r])/2;aa[r+5]=(a[r]-d[r])/2;bb[r]=(b[r]+e[r])/2;bb[r+5]=(b[r]-e[r])/2;}
 int R[6]{};for(int q=0;q<=5;q++)for(int i=0;i<10;i++){int j=(i+q)%10;R[q]+=aa[i]*aa[j]+bb[i]*bb[j];}
 long long L=min_even_sq(4,(R[0]-100)/2);for(int q=1;q<=4;q++)L+=min_even_sq(10,R[q]);
 if(R[5]&1)return 1LL<<60;return L+min_even_sq(5,R[5]/2);
}

struct LiftStats{long long lifts=0,target=0,minlb=1LL<<60;};
static LiftStats lift_pair(const A5&a,const A5&b){
 std::array<std::vector<int>,5>D,E;for(int i=0;i<5;i++){D[i]=opts(a[i]);E[i]=opts(b[i]);}
 LiftStats st;
 for(int d0:D[0])for(int d1:D[1])for(int d2:D[2])for(int d3:D[3])for(int d4:D[4]){
  A5 d{d0,d1,d2,d3,d4};auto M=hmat(d);int p=-1,q=-1,bdet=0;
  for(int i=0;i<5;i++)for(int j=i+1;j<5;j++){int det=M[0][i]*M[1][j]-M[0][j]*M[1][i];if(std::abs(det)>std::abs(bdet)){bdet=det;p=i;q=j;}}
  if(bdet){
   int f[3],k=0;for(int j=0;j<5;j++)if(j!=p&&j!=q)f[k++]=j;
   for(int x:E[f[0]])for(int y:E[f[1]])for(int z:E[f[2]]){
    A5 e{};e[f[0]]=x;e[f[1]]=y;e[f[2]]=z;long long r0=0,r1=0;
    for(int j:f){r0-=1LL*M[0][j]*e[j];r1-=1LL*M[1][j]*e[j];}
    long long np=r0*M[1][q]-1LL*M[0][q]*r1,nq=1LL*M[0][p]*r1-r0*M[1][p];
    if(np%bdet||nq%bdet)continue;long long ep=np/bdet,eq=nq/bdet;
    if(ep<-100||ep>100||eq<-100||eq>100||!contains(E[p],(int)ep)||!contains(E[q],(int)eq))continue;
    e[p]=(int)ep;e[q]=(int)eq;st.lifts++;auto L=lb10(a,d,b,e);st.minlb=std::min(st.minlb,L);if(L<=524)st.target++;
   }
  }else{
   int row=-1,piv=-1;for(int r=0;r<2&&row<0;r++)for(int j=0;j<5;j++)if(M[r][j]){row=r;piv=j;break;}
   if(row<0){
    for(int e0:E[0])for(int e1:E[1])for(int e2:E[2])for(int e3:E[3])for(int e4:E[4]){A5 e{e0,e1,e2,e3,e4};st.lifts++;auto L=lb10(a,d,b,e);st.minlb=std::min(st.minlb,L);if(L<=524)st.target++;}
   }else{
    int f[4],k=0;for(int j=0;j<5;j++)if(j!=piv)f[k++]=j;
    for(int x:E[f[0]])for(int y:E[f[1]])for(int z:E[f[2]])for(int w:E[f[3]]){
     A5 e{};e[f[0]]=x;e[f[1]]=y;e[f[2]]=z;e[f[3]]=w;long long rhs=0;for(int j:f)rhs-=1LL*M[row][j]*e[j];int den=M[row][piv];
     if(rhs%den)continue;int ep=rhs/den;if(!contains(E[piv],ep))continue;e[piv]=ep;auto zz=heq(d,e);if(zz[0]||zz[2])continue;
     st.lifts++;auto L=lb10(a,d,b,e);st.minlb=std::min(st.minlb,L);if(L<=524)st.target++;
    }
   }
  }
 }
 return st;
}

static void gen(int pos,int rem,A5&p,std::vector<A5>&out){if(pos==5){if(!rem)out.push_back(p);return;}for(int x=-10;x<=10;x+=2){p[pos]=x;gen(pos+1,rem-x,p,out);}}
int main(){
 std::vector<A5>A,B;A5 p{};gen(0,20,p,A);gen(0,0,p,B);
 std::atomic<long long> nh5{0},ncoarse{0},nlifts{0},ntarget{0},globalmin{1LL<<60};auto t0=std::chrono::steady_clock::now();
#pragma omp parallel for schedule(dynamic,1)
 for(size_t ia=0;ia<A.size();ia++){
  long long lh=0,lc=0,ll=0,lt=0,lmin=1LL<<60;
  for(const auto&b:B){if(!h5(A[ia],b))continue;lh++;if(lb5(A[ia],b)>524)continue;lc++;auto z=lift_pair(A[ia],b);ll+=z.lifts;lt+=z.target;lmin=std::min(lmin,z.minlb);}
  nh5+=lh;ncoarse+=lc;nlifts+=ll;ntarget+=lt;
#pragma omp critical
  {if(lmin<globalmin.load())globalmin=lmin;}
 }
 double sec=std::chrono::duration<double>(std::chrono::steady_clock::now()-t0).count();
 std::cout<<"profiles_A="<<A.size()<<" profiles_B="<<B.size()<<" H5="<<nh5<<" coarse="<<ncoarse
          <<" H10_lifts="<<nlifts<<" target_H10_lifts="<<ntarget<<" minLB10="<<globalmin<<" seconds="<<sec<<"\n";
}
