// Exact fibre-signature MITM oracle for a fixed order-25 compressed candidate.
//
// Input is two ternary length-25 sequences p,c (values -1,0,+1), where c is
// the standard half-shifted B compression c=x^13 q.  Every zero of p or q has
// one binary fibre sign.  For every lift we form
//
//   NAF_X(r) = C_X(r) - C_X(50-r), r=1..24.
//
// The full even correlations satisfy
//   C_(2r)-C_(100-2r) = NAF_A(r)+NAF_B(r).
//
// Hence sparse near-NGP branches are exact nearest-key queries: defect=0 asks
// for a zero sum; defect=1 for exactly one +/-4 coordinate; defect=2 for
// exactly two +/-4 coordinates.  Each NAF entry is even and in [-50,50], so
// NAF/2+25 fits in six bits; all 24 entries are packed injectively into 144
// bits (three uint64_t words).  The larger lift family is sorted once and the
// smaller family probes the exact sparse target neighbourhood.
//
// This removes the Cartesian-product factor from fixed-candidate fibre tests.
// It does not enumerate the compressed periodic candidates themselves.
//
// Build: g++ -O3 -march=native -fopenmp oddperfect_order25_fibre_mitm.cpp -o fibre
// Usage:
//   ./fibre --defect 0 < candidate.txt
// candidate.txt: 25 integers for p followed by 25 integers for c.
// --regress-w127 runs the historical W127 homometric survivor; expected hits=0.
#include <algorithm>
#include <array>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <string>
#include <vector>
#ifdef _OPENMP
#include <omp.h>
#else
static double omp_get_wtime(){return 0.0;}
#endif
using namespace std;
static constexpr int N=25,L=50;

struct Key{
 uint64_t a=0,b=0,c=0;
 bool operator<(const Key&o)const{return a!=o.a?a<o.a:b!=o.b?b<o.b:c<o.c;}
 bool operator==(const Key&o)const{return a==o.a&&b==o.b&&c==o.c;}
};

static int ac(const array<int8_t,L>&x,int r){int s=0;for(int i=0;i<L-r;i++)s+=x[i]*x[i+r];return s;}

static bool pack(const array<int8_t,24>&v,Key&k){
 k={};int bit=0;
 for(int i=0;i<24;i++){
  int x=(int)v[i];if((x&1)||x<-50||x>50)return false;uint64_t z=(uint64_t)(x/2+25);
  int w=bit>>6,s=bit&63;uint64_t *p=w==0?&k.a:w==1?&k.b:&k.c;*p|=z<<s;
  if(s>58){if(w==2)return false;uint64_t *q=w==0?&k.b:&k.c;*q|=z>>(64-s);}bit+=6;
 }
 return true;
}

static int zeros(const array<int,N>&p){int z=0;for(int x:p)z+=!x;return z;}

static array<int8_t,24> one_naf(const array<int,N>&p,uint64_t mask){
 array<int8_t,L>x{};int q=0;
 for(int i=0;i<N;i++){
  if(p[i])x[i]=x[i+N]=(int8_t)p[i];
  else{int t=((mask>>q)&1)?1:-1;x[i]=(int8_t)t;x[i+N]=(int8_t)-t;q++;}
 }
 array<int8_t,24> out{};for(int r=1;r<=24;r++)out[r-1]=(int8_t)(ac(x,r)-ac(x,50-r));return out;
}

static vector<Key> all_keys(const array<int,N>&p){
 const uint64_t M=1ULL<<zeros(p);vector<Key> out(M);
#pragma omp parallel for schedule(static)
 for(uint64_t m=0;m<M;m++){auto v=one_naf(p,m);Key k;if(!pack(v,k))abort();out[m]=k;}
 sort(out.begin(),out.end());out.erase(unique(out.begin(),out.end()),out.end());return out;
}

static vector<array<int8_t,24>> all_vectors(const array<int,N>&p){
 const uint64_t M=1ULL<<zeros(p);vector<array<int8_t,24>> out(M);
#pragma omp parallel for schedule(static)
 for(uint64_t m=0;m<M;m++)out[m]=one_naf(p,m);return out;
}

static bool has(const vector<Key>&keys,const array<int8_t,24>&v){Key k;if(!pack(v,k))return false;return binary_search(keys.begin(),keys.end(),k);}

static long long fibre_hits(const array<int,N>&p,const array<int,N>&c,int defect){
 array<int,N>q{};for(int j=0;j<N;j++)q[j]=c[(j+13)%N];
 int zp=zeros(p),zq=zeros(q);const array<int,N>*hp=&p,*pp=&q;
 if(zp<zq){hp=&q;pp=&p;swap(zp,zq);} // hash the larger family, probe the smaller.
 auto keys=all_keys(*hp);auto probes=all_vectors(*pp);long long hits=0;
#pragma omp parallel for reduction(+:hits) schedule(static)
 for(size_t m=0;m<probes.size();m++){
  array<int8_t,24> base{};for(int i=0;i<24;i++)base[i]=(int8_t)-probes[m][i];bool yes=false;
  if(defect==0)yes=has(keys,base);
  else if(defect==1){
   for(int i=0;i<24&&!yes;i++)for(int s:{-4,4}){auto v=base;v[i]=(int8_t)(v[i]+s);if(has(keys,v)){yes=true;break;}}
  }else if(defect==2){
   for(int i=0;i<24&&!yes;i++)for(int j=i+1;j<24&&!yes;j++)for(int s1:{-4,4})for(int s2:{-4,4}){
    auto v=base;v[i]=(int8_t)(v[i]+s1);v[j]=(int8_t)(v[j]+s2);if(has(keys,v)){yes=true;break;}
   }
  }else abort();
  if(yes)hits++;
 }
 cerr<<"FIBRE_TABLE hash_unique="<<keys.size()<<" probe_lifts="<<probes.size()<<" hash_zero_bits="<<zp<<" probe_zero_bits="<<zq<<"\n";
 return hits;
}

static bool validate(const array<int,N>&p,const array<int,N>&c){
 int sp=0,sc=0;for(int i=0;i<N;i++){if(abs(p[i])>1||abs(c[i])>1)return false;sp+=p[i];sc+=c[i];}
 if(sp!=10||sc!=0)return false;
 // Periodic odd-perfect cross condition; fibre oracle is only intended after this projection.
 for(int r=0;r<N;r++){int h=0;for(int i=0;i<N;i++)h+=p[i]*c[(i-r+N)%N]+c[i]*p[(i-r+N)%N];if(h)return false;}
 return true;
}

int main(int argc,char**argv){
 int defect=-1;bool regress=false;
 for(int i=1;i<argc;i++){string a=argv[i];if(a=="--defect"&&i+1<argc)defect=atoi(argv[++i]);else if(a=="--regress-w127")regress=true;else{cerr<<"unknown arg "<<a<<"\n";return 2;}}
 array<int,N>p{},c{};
 if(regress){
  const array<int,N>u={1,-1,0,0,1,0,0,0,0,1,2,2,1,1,0,0,0,0,0,0,2,0,-2,2,0};
  const array<int,N>v={1,1,2,2,1,0,0,0,0,1,0,0,-1,1,0,2,-2,0,2,0,0,0,0,0,0};
  for(int i=0;i<N;i++){p[i]=(u[i]+v[i])/2;c[i]=(u[i]-v[i])/2;}if(defect<0)defect=0;
 }else{
  for(int i=0;i<N;i++)if(!(cin>>p[i])){cerr<<"need 25 p entries\n";return 2;}
  for(int i=0;i<N;i++)if(!(cin>>c[i])){cerr<<"need 25 c entries\n";return 2;}
 }
 if(defect<0||defect>2){cerr<<"--defect must be 0,1,2\n";return 2;}if(!validate(p,c)){cerr<<"INVALID_COMPRESSED_CANDIDATE\n";return 3;}
 int kp=0,kc=0;for(int i=0;i<N;i++){kp+=p[i]*p[i];kc+=c[i]*c[i];}
 double t=omp_get_wtime();long long h=fibre_hits(p,c,defect);double sec=omp_get_wtime()-t;
 cout<<"FIBRE_MITM kp="<<kp<<" kc="<<kc<<" defect="<<defect<<" compatible_probe_lifts="<<h<<" seconds="<<sec<<"\n";
 if(regress&&defect==0){if(h){cerr<<"W127 regression failed\n";return 4;}cout<<"REGRESSION_OK W127_HOMOMETRIC_SURVIVOR_HAS_NO_ZERO_DEFECT_LIFT\n";}
 return 0;
}
