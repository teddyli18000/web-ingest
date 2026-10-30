// Exact order-25 compressed search for low11 h20 overlap layers.
//
// For the remaining W129-A / W131-A2 / W131-B1 branches, let P,C be the
// support masks of ternary p,c.  Their weights are kp,kc in {12,14} with
// kp+kc=26.  If t=|P intersect C|, then D=P xor C has weight 26-2t.
//
// Modulo 2, the cyclic cross equation is
//
//   P C* + C P* = 0.
//
// Writing C=P+D and using characteristic two reduces this to the LINEAR
// equation in P
//
//   P D* + D P* = 0.                                      (1)
//
// When |D|>12 replace D by E=D+J, where J=1+x+...+x^24.  Since kp is even,
// P J* + J P*=0, so (1) is unchanged.  Thus overlap t=2,4,6,8,10,12 uses a
// difference representative of weight 3,7,11,10,6,2 respectively.
//
// This program enumerates affine orbits of the small difference support,
// solves (1) exactly over GF(2), quotients P by the stabilizer of the fixed
// difference, and then enumerates ALL compatible p signs (sum p=10).  For c,
// sum c=0 is solved by an exact meet-in-the-middle on all 13 independent
// integer cyclic cross coefficients H_r, r=0..12; c -> -c symmetry fixes the
// first c support sign positive.  Every H-compatible pair is finally checked
// against the exact low11 order-25 periodic condition
//
//   G_r=PAF_p(r)+PAF_c(r) in {2,3,4}, r=1..12, sum G_r=37.
//
// No SAT/CP solver or timeout is involved.  A zero compressed_hits count is an
// exact exclusion for the selected (t,kp) layer.
//
// Build: g++ -O3 -march=native -fopenmp oddperfect_low11_symdiff_exact.cpp -o symdiff
// Run:   OMP_NUM_THREADS=$(nproc) ./symdiff --overlap 12 --kp 12
#include <algorithm>
#include <array>
#include <atomic>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <mutex>
#include <numeric>
#include <unordered_map>
#include <unordered_set>
#include <utility>
#include <vector>
using namespace std;
using U=uint32_t;
static constexpr U ALL=(1u<<25)-1;

static U rot(U x,int k){k%=25;return ((x<<k)|(x>>(25-k)))&ALL;}
static U star(U x){U y=0;for(int i=0;i<25;i++)if(x>>i&1)y|=1u<<((25-i)%25);return y;}
static U mul(U a,U b){U y=0;for(int i=0;i<25;i++)if(a>>i&1)y^=rot(b,i);return y;}
static vector<int> units(){vector<int>u;for(int a=1;a<25;a++)if(gcd(a,25)==1)u.push_back(a);return u;}
static U aff(U x,int a,int b){U y=0;for(int i=0;i<25;i++)if(x>>i&1)y|=1u<<((a*i+b)%25);return y;}
static U canon(U x){static auto us=units();U best=ALL;for(int a:us)for(int b=0;b<25;b++)best=min(best,aff(x,a,b));return best;}

static vector<U> orbit_reps(int w){
 vector<U> reps;unordered_set<U>seen;const auto us=units();U x=(1u<<w)-1;
 while(x<(1u<<25)){
  if(!seen.count(x)){
   U c=canon(x);if(c==x)reps.push_back(x);
   for(int a:us)for(int b=0;b<25;b++)seen.insert(aff(x,a,b));
  }
  U c=x&-x,r=x+c;if(!r||r>=(1u<<25))break;x=(((r^x)>>2)/c)|r;
 }
 return reps;
}

struct Ker{vector<U>b;};
static Ker kernel(U D){
 U rows[25]{};U Ds=star(D);
 for(int j=0;j<25;j++){
  U col=mul(1u<<j,Ds)^mul(D,star(1u<<j));
  for(int r=0;r<25;r++)if(col>>r&1)rows[r]|=1u<<j;
 }
 int pr=0;vector<int>pc;
 for(int c=0;c<25&&pr<25;c++){
  int q=-1;for(int r=pr;r<25;r++)if(rows[r]>>c&1){q=r;break;}
  if(q<0)continue;swap(rows[pr],rows[q]);
  for(int r=0;r<25;r++)if(r!=pr&&(rows[r]>>c&1))rows[r]^=rows[pr];
  pc.push_back(c);pr++;
 }
 bool isp[25]{};for(int c:pc)isp[c]=1;Ker K;
 for(int f=0;f<25;f++)if(!isp[f]){
  U v=1u<<f;for(int r=0;r<pr;r++)if(rows[r]>>f&1)v|=1u<<pc[r];K.b.push_back(v);
 }
 return K;
}

static vector<pair<int,int>> stabilizer(U E){
 vector<pair<int,int>>s;const auto us=units();for(int a:us)for(int b=0;b<25;b++)if(aff(E,a,b)==E)s.push_back({a,b});return s;
}
static U canon_stab(U P,const vector<pair<int,int>>&st){U z=P;for(auto[a,b]:st)z=min(z,aff(P,a,b));return z;}

struct Key{array<int8_t,14>v{};bool operator==(const Key&o)const{return v==o.v;}};
struct KH{size_t operator()(const Key&k)const noexcept{uint64_t h=1469598103934665603ULL;for(auto x:k.v){h^=(uint8_t)(x+64);h*=1099511628211ULL;}return (size_t)h;}};

static bool low11G(const array<int8_t,25>&p,const array<int8_t,25>&c){
 int S=0;
 for(int r=1;r<=12;r++){
  int g=0;for(int i=0;i<25;i++)g+=p[i]*p[(i+r)%25]+c[i]*c[(i+r)%25];
  if(g<2||g>4)return false;S+=g;
 }
 return S==37;
}

struct SignStats{long long ptests=0,hmatch=0,ghit=0;};
static SignStats search_signs(U P,U C,int kp){
 vector<int>pi,ci;for(int i=0;i<25;i++){if(P>>i&1)pi.push_back(i);if(C>>i&1)ci.push_back(i);}
 const int np=(int)pi.size(),nc=(int)ci.size(),pneg=(kp-10)/2;
 SignStats ST;U pmask=pneg?((1u<<pneg)-1):0;bool firstp=true;
 while(true){
  if(!firstp&&pneg==0)break;firstp=false;ST.ptests++;
  array<int8_t,25>p{};for(int j=0;j<np;j++)p[pi[j]]=(pmask>>j&1)?-1:1;
  const int ml=nc/2,mr=nc-ml;
  unordered_map<Key,vector<uint16_t>,KH>right;right.reserve(1u<<mr);
  for(int mask=0;mask<(1<<mr);mask++){
   Key k{};int ss=0;
   for(int jj=0;jj<mr;jj++){
    int sgn=(mask>>jj&1)?-1:1,pos=ci[ml+jj];ss+=sgn;
    for(int r=0;r<=12;r++)k.v[r]+=(int8_t)(sgn*(p[(pos+r)%25]+p[(pos-r+25)%25]));
   }
   k.v[13]=(int8_t)ss;right[k].push_back((uint16_t)mask);
  }
  for(int mask=0;mask<(1<<ml);mask++){
   if(mask&1)continue; // c -> -c symmetry.
   Key need{};int ss=0;
   for(int jj=0;jj<ml;jj++){
    int sgn=(mask>>jj&1)?-1:1,pos=ci[jj];ss+=sgn;
    for(int r=0;r<=12;r++)need.v[r]-=(int8_t)(sgn*(p[(pos+r)%25]+p[(pos-r+25)%25]));
   }
   need.v[13]=(int8_t)-ss;auto it=right.find(need);if(it==right.end())continue;
   for(uint16_t rm:it->second){
    array<int8_t,25>c{};
    for(int jj=0;jj<ml;jj++)c[ci[jj]]=(mask>>jj&1)?-1:1;
    for(int jj=0;jj<mr;jj++)c[ci[ml+jj]]=(rm>>jj&1)?-1:1;
    ST.hmatch++;if(low11G(p,c))ST.ghit++;
   }
  }
  if(pneg==0)break;
  U c=pmask&-pmask,r=pmask+c;if(!r||r>=(1u<<np))break;pmask=(((r^pmask)>>2)/c)|r;
 }
 return ST;
}

int main(int argc,char**argv){
 int t=-1,kp=-1;
 for(int i=1;i<argc;i++){
  string a=argv[i];if(a=="--overlap"&&i+1<argc)t=atoi(argv[++i]);else if(a=="--kp"&&i+1<argc)kp=atoi(argv[++i]);else{cerr<<"unknown arg "<<a<<"\n";return 2;}
 }
 if(t<2||t>12||(t&1)||(kp!=12&&kp!=14)){cerr<<"need even --overlap 2..12 and --kp 12|14\n";return 2;}
 const int kc=26-kp,s=26-2*t,ew=min(s,25-s);const bool comp=s>12;
 auto Es=orbit_reps(ew);cerr<<"DIFF overlap="<<t<<" raw_weight="<<s<<" reduced_weight="<<ew<<" affine_reps="<<Es.size()<<"\n";
 atomic<long long>supp{0},ptests{0},hmatch{0},ghit{0};
#pragma omp parallel for schedule(dynamic,1)
 for(int ei=0;ei<(int)Es.size();ei++){
  U E=Es[ei],D=comp?(ALL^E):E;auto K=kernel(E);auto st=stabilizer(E);int dim=(int)K.b.size();
  long long ls=0,lp=0,lm=0,lg=0;const uint64_t M=1ull<<dim;
  for(uint64_t m=0;m<M;m++){
   U P=0;for(int j=0;j<dim;j++)if(m>>j&1)P^=K.b[j];
   if(__builtin_popcount(P)!=kp)continue;U C=P^D;if(__builtin_popcount(C)!=kc)continue;
   if(canon_stab(P,st)!=P)continue;ls++;auto z=search_signs(P,C,kp);lp+=z.ptests;lm+=z.hmatch;lg+=z.ghit;
  }
  supp+=ls;ptests+=lp;hmatch+=lm;ghit+=lg;
 }
 cout<<"SUMMARY overlap="<<t<<" kp="<<kp<<" kc="<<kc<<" difference_orbits="<<Es.size()
     <<" support_pair_orbits="<<supp<<" p_sign_tests="<<ptests<<" H_matches="<<hmatch
     <<" compressed_hits="<<ghit<<"\n";
 return 0;
}
