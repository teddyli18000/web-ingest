// Exact lift/affine exhaustion for (a,b)=(18,0), K=19, kp=19,kc=0.
// Input is the 95 canonical p representatives emitted by
// oddperfect_h18_k19_kp19_compressed.cpp, one line as flags|25 comma values.
//
// For c=0, periodic cross is automatic.  Write A=(1+x^25)p+(1-x^25)alpha
// and B=(1-x^25)beta.  With gamma=x^13 beta in Z[x]/(x^25+1), the remaining
// cyclic odd-cross condition is exactly alpha gamma* - gamma alpha*=0.
// We enumerate all 2^6 alpha orientations.  For fixed alpha every gamma in
// {+-1}^25 satisfying the 25 exact integer equations is found by a 12/13
// MITM; gamma0=+1 quotients the harmless global sign B->-B.
//
// To cover the full compressed affine orbit without resolving fibres 500
// times, for each unit a mod25 choose its odd lift ahat mod50 and h=(ahat-1)/2.
// Then A'=x^b A(x^ahat), B'=x^(b+h) B(x^ahat) preserves the cyclic cross and
// induces the SAME affine map i->a i+b on p and c.  Thus every cyclic-cross
// lift of every compressed affine image is the transform of a lift enumerated
// here.  We score all 20*25 transforms.
//
// For K=19, W<=130 is classified exactly.  If flags has the base U45 type,
// sum V_r^2<=2 is necessary; for an alt-only U47 type, V=0 is necessary.
// V_r=[C_A(r)-C_A(50-r)+C_B(r)-C_B(50-r)]/4.  Expected exact result:
// 95 p orbits, 6080 alpha choices, 69314 half-B-sign cyclic lifts,
// 34,657,000 affine transforms, and ZERO transforms passing the necessary V
// budget.  Hence the complete kp19,kc0 K19 target is excluded before any
// odd-perfect magnitude or energy test is needed.
#include <bits/stdc++.h>
using namespace std;static const int N=25,L=50;using Vec=array<int16_t,N>;
struct VH{size_t operator()(Vec const&v)const noexcept{uint64_t h=1469598103934665603ULL;for(auto x:v){h^=(uint16_t)(x+64);h*=1099511628211ULL;}return h;}};
static Vec comm(const array<int,N>&a,const array<int,N>&g){Vec f{};auto add=[&](int e,int v){if(e>=0)f[e]+=v;else f[e+N]-=v;};for(int i=0;i<N;i++)if(a[i])for(int j=0;j<N;j++)if(g[j]){add(i-j,a[i]*g[j]);add(j-i,-g[j]*a[i]);}return f;}
static vector<uint32_t> solve_gamma(const array<int,N>&alpha){array<Vec,N>col{};for(int j=0;j<N;j++){array<int,N>e{};e[j]=1;col[j]=comm(alpha,e);}unordered_map<Vec,vector<uint16_t>,VH>mp;mp.reserve(5000);
 for(uint16_t m=0;m<(1u<<11);m++){Vec v=col[0];for(int j=1;j<12;j++){int s=(m>>(j-1)&1)?1:-1;for(int r=0;r<N;r++)v[r]+=s*col[j][r];}mp[v].push_back(m);}vector<uint32_t>sol;
 for(uint16_t m=0;m<(1u<<13);m++){Vec v{};for(int j=12;j<25;j++){int s=(m>>(j-12)&1)?1:-1;for(int r=0;r<N;r++)v[r]+=s*col[j][r];}for(auto &x:v)x=-x;auto it=mp.find(v);if(it==mp.end())continue;for(uint16_t lm:it->second){uint32_t z=1u;for(int j=1;j<12;j++)if(lm>>(j-1)&1)z|=1u<<j;for(int j=12;j<25;j++)if(m>>(j-12)&1)z|=1u<<j;sol.push_back(z);}}return sol;}
static array<int,N> invshift13(const array<int,N>&g){array<int,N>b{};for(int i=0;i<N;i++){int j=i-13;if(j>=0)b[j]=g[i];else b[j+N]=-g[i];}return b;}
static inline uint64_t masklo(int n){return n?((1ULL<<n)-1):0ULL;}
static inline int corr(uint64_t x,int r){int n=50-r;return n-2*__builtin_popcountll((x^(x>>r))&masklo(n));}
static inline int xcorr(uint64_t x,uint64_t y,int r){int n=50-r;return n-2*__builtin_popcountll((x^(y>>r))&masklo(n));}
static inline uint64_t rot50(uint64_t x,int k){const uint64_t M=(1ULL<<50)-1;k%=50;if(!k)return x&M;return((x<<k)|(x>>(50-k)))&M;}
static uint64_t multperm(uint64_t x,int ah){uint64_t y=0;for(int i=0;i<50;i++)if(x>>i&1)y|=1ULL<<((ah*i)%50);return y;}
static inline int oddcorr(uint64_t A,uint64_t B,int r){return xcorr(A,B,r)+(r<49?xcorr(B,A,r+1):0);}
static bool cyclic_odd_zero(uint64_t A,uint64_t B){for(int r=0;r<25;r++)if(oddcorr(A,B,r)+oddcorr(A,B,49-r)!=0)return false;return true;}
int main(int argc,char**argv){if(argc<2){cerr<<"usage: affine_lifts reps.txt\n";return 2;}ifstream in(argv[1]);string line;vector<int>units;for(int a=0;a<25;a++)if(gcd(a,25)==1)units.push_back(a);
 long long reps=0,alphas=0,lifts=0,trans=0,vpass=0;
 while(getline(in,line)){if(line.empty())continue;auto bar=line.find('|');int flags=stoi(line.substr(0,bar));string rest=line.substr(bar+1);array<int,N>p{};stringstream ss(rest);for(int i=0;i<N;i++){string z;getline(ss,z,',');p[i]=stoi(z);}vector<int>zeros;for(int i=0;i<N;i++)if(!p[i])zeros.push_back(i);if(zeros.size()!=6)return 3;
  for(int am=0;am<64;am++){alphas++;array<int,N>a{};for(int t=0;t<6;t++)a[zeros[t]]=(am>>t&1)?1:-1;auto gs=solve_gamma(a);lifts+=gs.size();
   for(uint32_t gm:gs){array<int,N>g{};for(int j=0;j<N;j++)g[j]=(gm>>j&1)?1:-1;auto beta=invshift13(g);uint64_t Ab=0,Bb=0;
    for(int i=0;i<N;i++){int A0=p[i]+a[i],A1=p[i]-a[i];if(abs(A0)!=1||abs(A1)!=1)return 4;if(A0==1)Ab|=1ULL<<i;if(A1==1)Ab|=1ULL<<(i+25);if(beta[i]==1)Bb|=1ULL<<i;if(beta[i]==-1)Bb|=1ULL<<(i+25);}
    if(!cyclic_odd_zero(Ab,Bb)){cerr<<"CYCLIC_CROSS_REGRESSION_FAIL rep="<<reps<<" am="<<am<<"\n";return 5;}
    for(int aa:units){int ah=(aa&1)?aa:aa+25,h=(ah-1)/2;uint64_t TA=multperm(Ab,ah),TB=multperm(Bb,ah);for(int b=0;b<25;b++){trans++;uint64_t A=rot50(TA,b),B=rot50(TB,b+h);int vsq=0,cap=(flags&1)?2:0;for(int r=1;r<=24;r++){int num=(corr(A,r)-corr(A,50-r))+(corr(B,r)-corr(B,50-r));if(num%4)return 6;int v=num/4;vsq+=v*v;if(vsq>cap)break;}if(vsq<=cap)vpass++;}}
   }
  }
  reps++;
 }
 cout<<"K19_KP19_SUMMARY reps="<<reps<<" alphas="<<alphas<<" cyclic_lifts_halfB="<<lifts<<" affine_transforms="<<trans<<" target_V_pass="<<vpass<<"\n";
 if(reps!=95||alphas!=6080||lifts!=69314||trans!=34657000||vpass!=0)return 7;
 cout<<"EXACT_EXCLUSION h18_K19_kp19_kc0_Wle130\n";
}
