// Exact lift check for one nontrivial W127 order-25 homometric survivor.
//
// For ternary order-25 p,c, put u=p+c and v=p-c. The symmetric cross
// condition p c* + c p* = 0 is equivalent to PAF_u = PAF_v. The fixed
// survivor below has (ka,kc)=(14,12) and satisfies every W127 order-25
// projection equation. We reconstruct q from c=x^13 q and exhaust all
// 2^(11+13)=2^24 binary A/B lifts. Every lift is checked with the original
// aperiodic even correlations C_A(r)+C_B(r); W127 requires each to be 2 or 4.
// The exhaustive result is zero even-compatible lifts.
#include <array>
#include <atomic>
#include <cstdlib>
#include <iostream>
#include <numeric>
#include <vector>
#include <omp.h>
using namespace std;
static constexpr int N=25,L=50;
static int ac(const array<signed char,L>&x,int r){int s=0;for(int i=0;i<L-r;i++)s+=x[i]*x[i+r];return s;}
static int paf25(const array<int,N>&x,int r){int s=0;for(int i=0;i<N;i++)s+=x[i]*x[(i+r)%N];return s;}
int main(){
 const array<int,N> u={1,-1,0,0,1,0,0,0,0,1,2,2,1,1,0,0,0,0,0,0,2,0,-2,2,0};
 const array<int,N> v={1,1,2,2,1,0,0,0,0,1,0,0,-1,1,0,2,-2,0,2,0,0,0,0,0,0};
 array<int,N> p{},c{},q{};int ka=0,kc=0;
 for(int i=0;i<N;i++){if(((u[i]+v[i])&1)||((u[i]-v[i])&1))return 2;p[i]=(u[i]+v[i])/2;c[i]=(u[i]-v[i])/2;if(abs(p[i])>1||abs(c[i])>1)return 3;ka+=p[i]*p[i];kc+=c[i]*c[i];}
 if(accumulate(p.begin(),p.end(),0)!=10||accumulate(c.begin(),c.end(),0)!=0||ka!=14||kc!=12)return 4;
 for(int r=0;r<N;r++){int h=0;for(int i=0;i<N;i++)h+=p[i]*c[(i-r+N)%N]+c[i]*p[(i-r+N)%N];if(h)return 5;}
 array<int,12>K{};int sm=0;for(int r=1;r<=12;r++){K[r-1]=paf25(p,r)+paf25(c,r);if(K[r-1]<2||K[r-1]>4)return 6;sm+=K[r-1];}if(sm!=37)return 7;
 // c=x^13 q in Z[x]/(x^25-1): c_i=q_{i-13}, hence q_j=c_{j+13}.
 for(int j=0;j<N;j++)q[j]=c[(j+13)%N];
 vector<int>zp,zq;array<int,N>ip{},iq{};ip.fill(-1);iq.fill(-1);
 for(int i=0;i<N;i++){if(!p[i]){ip[i]=zp.size();zp.push_back(i);}if(!q[i]){iq[i]=zq.size();zq.push_back(i);}}
 if(zp.size()!=11||zq.size()!=13)return 8;
 const int NA=1<<zp.size(),NB=1<<zq.size();
 vector<array<signed char,L>> A(NA),B(NB);vector<array<signed char,49>> CA(NA),CB(NB);
 for(int m=0;m<NA;m++)for(int i=0;i<N;i++){if(p[i])A[m][i]=A[m][i+N]=p[i];else{int t=(m>>ip[i]&1)?1:-1;A[m][i]=t;A[m][i+N]=-t;}}
 for(int m=0;m<NB;m++)for(int i=0;i<N;i++){if(q[i])B[m][i]=B[m][i+N]=q[i];else{int t=(m>>iq[i]&1)?1:-1;B[m][i]=t;B[m][i+N]=-t;}}
 for(int m=0;m<NA;m++)for(int r=1;r<L;r++)CA[m][r-1]=ac(A[m],r);
 for(int m=0;m<NB;m++)for(int r=1;r<L;r++)CB[m][r-1]=ac(B[m],r);
 atomic<long long> pairs{0},evenpass{0};
#pragma omp parallel for schedule(static)
 for(int ma=0;ma<NA;ma++)for(int mb=0;mb<NB;mb++){
   pairs++;bool ok=true;for(int r=0;r<49;r++){int x=(int)CA[ma][r]+(int)CB[mb][r];if(x!=2&&x!=4){ok=false;break;}}if(ok)evenpass++;
 }
 cout<<"W127_HOMOMETRIC_SURVIVOR ka="<<ka<<" kc="<<kc<<" K=";for(int x:K)cout<<x<<',';cout<<"\n";
 cout<<"EXACT_LIFT_SUMMARY A_lifts="<<NA<<" B_lifts="<<NB<<" pairs="<<pairs.load()<<" even_compatible="<<evenpass.load()<<" threads="<<omp_get_max_threads()<<"\n";
 if(pairs.load()!=16777216LL||evenpass.load()!=0)return 9;
 cout<<"EXACT_RESULT SURVIVOR_HAS_NO_W127_BINARY_LIFT\n";
 return 0;
}
