// Final exact length-100 audit for the only Q-feasible fibre support in the
// O=58, K=18, center-defect, kp=3 branch. The upstream exact grouped search
// leaves one canonical support pair with SG=50 and two negacyclic fibre sign
// pairs (SH=30), hence Q=(SG+SH)/2=40 exactly. Targeted compressed recovery
// leaves exactly the two signed (p,c) representatives frozen below.
//
// We map both compressed representatives to the canonical fibre support,
// restore both independent global fibre signs, pair with both QHITs, and
// exhaust all 500 induced full-length affine maps. The Q-stage swap
// (p,c,alpha,gamma)->(c,p,gamma,alpha) is audited separately, covering the
// symmetric kp=15 branch without assuming aperiodic energy invariance.
#include <bits/stdc++.h>
using namespace std; static const int N=25,L=50;
using A25=array<int,N>; using A50=array<int,L>;
static const uint32_t CAN_AS=4194303u, CAN_GS=1195794u;
vector<int> units(){vector<int>u;for(int a=1;a<N;a++)if(gcd(a,N)==1)u.push_back(a);return u;}
uint32_t zmask(const A25&x){uint32_t m=0;for(int i=0;i<N;i++)if(!x[i])m|=1u<<i;return m;}
uint32_t affmask(uint32_t x,int a,int b){uint32_t y=0;for(int i=0;i<N;i++)if(x>>i&1)y|=1u<<((a*i+b)%N);return y;}
A25 aff25(const A25&x,int a,int b){A25 y{};for(int i=0;i<N;i++)y[(a*i+b)%N]=x[i];return y;}
int paf25(const A25&x,int r){int s=0;for(int i=0;i<N;i++)s+=x[i]*x[(i+r)%N];return s;}
int sg(const A25&p,const A25&c){int s=0;for(int r=1;r<=12;r++){int g=paf25(p,r)+paf25(c,r);s+=g*g;}return s;}
bool periodic_center(const A25&p,const A25&c){for(int r=0;r<N;r++){int h=0;for(int i=0;i<N;i++)h+=p[i]*c[(i-r+N)%N]+c[i]*p[(i-r+N)%N];if(h!=(r==0?2:0))return false;}return true;}
A25 beta_from_gamma(const A25&g){A25 b{};for(int i=0;i<N;i++){int j=i-13;if(j>=0)b[j]=g[i];else b[j+N]=-g[i];}return b;}
A25 q_from_c(const A25&c){A25 q{};for(int j=0;j<N;j++)q[j]=c[(j+13)%N];return q;}
bool negacyclic_zero(const A25&a,const A25&g){array<int,N>f{};auto add=[&](int e,int v){if(e>=0)f[e]+=v;else f[e+N]-=v;};for(int i=0;i<N;i++)if(a[i])for(int j=0;j<N;j++)if(g[j]){add(i-j,a[i]*g[j]);add(j-i,-g[j]*a[i]);}for(int v:f)if(v)return false;return true;}
A50 multperm(const A50&x,int a){A50 y{};for(int i=0;i<L;i++)y[(a*i)%L]=x[i];return y;}
A50 rot(const A50&x,int b){A50 y{};b%=L;for(int i=0;i<L;i++)y[(i+b)%L]=x[i];return y;}
struct Score{long long E=0,odd=0,even=0;};
Score score(const A50&A,const A50&B){array<int,100>s{};for(int i=0;i<L;i++){s[2*i]=A[i];s[2*i+1]=B[i];}Score z;for(int k=1;k<100;k++){int c=0;for(int i=0;i<100-k;i++)c+=s[i]*s[i+k];long long q=1LL*c*c;z.E+=q;if(k&1)z.odd+=q;else z.even+=q;}return z;}
A50 buildA(const A25&p,const A25&a){A50 x{};for(int i=0;i<N;i++){x[i]=p[i]+a[i];x[i+N]=p[i]-a[i];if(abs(x[i])!=1||abs(x[i+N])!=1)abort();}return x;}
A50 buildB(const A25&c,const A25&g){auto q=q_from_c(c),b=beta_from_gamma(g);A50 x{};for(int i=0;i<N;i++){x[i]=q[i]+b[i];x[i+N]=q[i]-b[i];if(abs(x[i])!=1||abs(x[i+N])!=1)abort();}return x;}
struct Tot{long long base=0,trans=0,o58=0,ele=0;long long minE=LLONG_MAX,minOdd=LLONG_MAX;};
void exhaust(const vector<pair<A25,A25>>&pcs,const vector<pair<uint32_t,uint32_t>>&fib,bool sw,Tot&st){auto us=units();for(auto [p0,c0]:pcs)for(auto [am,gm]:fib)for(int sa:{1,-1})for(int sg0:{1,-1}){A25 a{},g{};for(int i=0;i<N;i++){if(CAN_AS>>i&1)a[i]=sa*((am>>i&1)?1:-1);if(CAN_GS>>i&1)g[i]=sg0*((gm>>i&1)?1:-1);}if(!negacyclic_zero(a,g))abort();A25 p=p0,c=c0;if(sw){swap(p,c);swap(a,g);}if(!periodic_center(p,c))abort();auto A=buildA(p,a),B=buildB(c,g);st.base++;for(int aa:us){int ah=(aa&1)?aa:aa+25,h=(ah-1)/2;auto TA=multperm(A,ah),TB=multperm(B,ah);for(int bb=0;bb<N;bb++){auto z=score(rot(TA,bb),rot(TB,bb+h));st.trans++;st.minE=min(st.minE,z.E);st.minOdd=min(st.minOdd,z.odd);if(z.odd==58)st.o58++;if(z.E<=574)st.ele++;}}}}
int main(){
 vector<pair<A25,A25>> raw={
  {A25{0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-1,0,1,0,1,0},A25{1,0,0,1,1,-1,1,-1,0,0,-1,1,1,-1,1,0,0,-1,0,-1,0,1,0,-1,0}},
  {A25{0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,1,0,-1,0},A25{-1,0,0,1,-1,1,1,-1,0,0,-1,1,-1,1,1,0,0,1,0,-1,0,1,0,-1,0}}
 };
 vector<pair<A25,A25>> pcs;set<string>seen;auto us=units();for(auto [p,c]:raw){if(!periodic_center(p,c)||sg(p,c)!=50)abort();int maps=0;for(int a:us)for(int b=0;b<N;b++)if(affmask(zmask(p),a,b)==CAN_AS&&affmask(zmask(c),a,b)==CAN_GS){maps++;auto pp=aff25(p,a,b),cc=aff25(c,a,b);string k;for(int x:pp)k+=char(x+1);for(int x:cc)k+=char(x+1);if(seen.insert(k).second)pcs.push_back({pp,cc});}cout<<"PC_MAPS "<<maps<<"\n";if(maps!=2)abort();}
 if(pcs.size()!=2)abort();for(auto&z:pcs)if(sg(z.first,z.second)!=50||zmask(z.first)!=CAN_AS||zmask(z.second)!=CAN_GS)abort();
 vector<pair<uint32_t,uint32_t>> fib={{3402252u,2834u},{792051u,2834u}};
 Tot lo,hi;exhaust(pcs,fib,false,lo);exhaust(pcs,fib,true,hi);
 cout<<"O58_K18_KP3_CENTER_FINAL side=low base="<<lo.base<<" transforms="<<lo.trans<<" O58="<<lo.o58<<" E_le_574="<<lo.ele<<" minE="<<lo.minE<<" minOdd="<<lo.minOdd<<"\n";
 cout<<"O58_K18_KP3_CENTER_FINAL side=swap base="<<hi.base<<" transforms="<<hi.trans<<" O58="<<hi.o58<<" E_le_574="<<hi.ele<<" minE="<<hi.minE<<" minOdd="<<hi.minOdd<<"\n";
 if(lo.base!=16||lo.trans!=8000||lo.o58||lo.ele||lo.minE!=1438||lo.minOdd!=282)return 2;
 if(hi.base!=16||hi.trans!=8000||hi.o58||hi.ele||hi.minE!=1438||hi.minOdd!=282)return 3;
}
