// Exact final witness/exclusion verifier for affine-canonical K21 Q survivors.
//
// Inputs:
//   argv[1] = complete compressed HIT lines for one kp split
//   argv[2] = affine-qgroup transcript containing QHIT lines
//
// The qgroup solver canonicalizes the fibre support pair
//   (supp(alpha), supp(gamma)) = (zeros(p), zeros(c))
// under simultaneous AGL(1,Z25). For every QHIT this verifier:
//   1. finds every original compressed HIT whose support pair is in that orbit
//      and whose exact SG plus this survivor's SH is <=114;
//   2. enumerates every AGL map taking that support pair to the exact QHIT
//      canonical pair, transforms p,c, and deduplicates the resulting signed
//      compressed candidates;
//   3. restores both independent global signs of alpha and gamma (4 choices),
//      reconstructs binary A,B and independently checks the exact Q identity;
//   4. exhausts all 20*25 full-length affine images induced by odd units mod50
//      and translations, then directly recomputes V^2, every odd correlation,
//      and the original LABS energy.
//
// No qgroup lower bound is used as a final exclusion: every remaining fibre is
// scored in the original length-100 objective. Any E<=570 candidate is printed.
#include <bits/stdc++.h>
using namespace std;
static const int N=25,L=50;
using A25=array<int,25>; using A50=array<int,50>;

static vector<int> units25(){vector<int>u;for(int a=1;a<N;a++)if(gcd(a,N)==1)u.push_back(a);return u;}
static uint32_t affmask(uint32_t x,int a,int b){uint32_t y=0;for(int i=0;i<N;i++)if(x>>i&1)y|=1u<<((a*i+b)%N);return y;}
static A25 aff25(const A25&x,int a,int b){A25 y{};for(int i=0;i<N;i++)y[(a*i+b)%N]=x[i];return y;}
struct SKey{uint32_t as=0,gs=0;bool operator<(SKey const&o)const{return as!=o.as?as<o.as:gs<o.gs;}};
static SKey canon_pair(uint32_t as,uint32_t gs){static auto us=units25();SKey best{UINT32_MAX,UINT32_MAX};for(int a:us)for(int b=0;b<N;b++){SKey z{affmask(as,a,b),affmask(gs,a,b)};if(z<best)best=z;}return best;}

static int sg_of(const A25&p,const A25&c){int s=0;for(int r=1;r<=12;r++){int g=0;for(int i=0;i<N;i++)g+=p[i]*p[(i+r)%N]+c[i]*c[(i+r)%N];s+=g*g;}return s;}
static int npaf25(uint32_t supp,uint32_t plus,int r){
 uint32_t pair=supp&(supp>>r),sx=plus^(plus>>r);int non=__builtin_popcount(pair)-2*__builtin_popcount(pair&sx);
 uint32_t mr=(1u<<r)-1,hi=supp>>(N-r),lo=supp&mr,pw=hi&lo,sh=plus>>(N-r),sl=plus&mr;
 int wrap=__builtin_popcount(pw)-2*__builtin_popcount(pw&(sh^sl));return non-wrap;
}
static bool periodic_cross(const A25&p,const A25&c){for(int r=0;r<N;r++){int h=0;for(int i=0;i<N;i++)h+=p[i]*c[(i-r+N)%N]+c[i]*p[(i-r+N)%N];if(h)return false;}return true;}
static bool negacyclic_cross(const A25&a,const A25&g){
 array<int,25> f{};auto add=[&](int e,int v){if(e>=0)f[e]+=v;else f[e+N]-=v;};
 for(int i=0;i<N;i++)if(a[i])for(int j=0;j<N;j++)if(g[j]){add(i-j,a[i]*g[j]);add(j-i,-g[j]*a[i]);}
 for(int z:f)if(z)return false;return true;
}
static A25 beta_from_gamma(const A25&g){A25 b{};for(int i=0;i<N;i++){int j=i-13;if(j>=0)b[j]=g[i];else b[j+N]=-g[i];}return b;}
static A25 q_from_c(const A25&c){A25 q{};for(int j=0;j<N;j++)q[j]=c[(j+13)%N];return q;}
static int ac(const A50&x,int r){int s=0;for(int i=0;i<L-r;i++)s+=x[i]*x[i+r];return s;}
static int paf(const A50&x,int r){int s=0;for(int i=0;i<L;i++)s+=x[i]*x[(i+r)%L];return s;}
static int oddcorr(const A50&A,const A50&B,int r){int s=0;for(int i=0;i<L-r;i++)s+=A[i]*B[i+r];if(r<49)for(int i=0;i<49-r;i++)s+=B[i]*A[i+r+1];return s;}
static long long energy(const A50&A,const A50&B,long long&odd){long long e=0;odd=0;for(int r=1;r<L;r++){int c=ac(A,r)+ac(B,r);e+=1LL*c*c;}for(int r=0;r<L;r++){int c=oddcorr(A,B,r);odd+=1LL*c*c;e+=1LL*c*c;}return e;}
static A50 multperm(const A50&x,int a){A50 y{};for(int i=0;i<L;i++)y[(a*i)%L]=x[i];return y;}
static A50 rot(const A50&x,int b){A50 y{};b%=L;if(b<0)b+=L;for(int i=0;i<L;i++)y[(i+b)%L]=x[i];return y;}
static string pc_key(const A25&p,const A25&c){string s;s.reserve(50);for(int x:p)s.push_back(char(x+1));for(int x:c)s.push_back(char(x+1));return s;}
static string seq100(const A50&A,const A50&B){string s;s.reserve(100);for(int i=0;i<50;i++){s.push_back(A[i]>0?'+':'-');s.push_back(B[i]>0?'+':'-');}return s;}

struct PC{A25 p{},c{};uint32_t as=0,gs=0;int SG=0;};
struct QH{uint32_t as=0,gs=0,am=0,gm=0;int minSG=0,sh=0,Q=0;};

int main(int argc,char**argv){
 if(argc<3){cerr<<"usage: affine_witness compressed.hits qgroup.log\n";return 2;}
 ifstream fh(argv[1]),fq(argv[2]);if(!fh||!fq){cerr<<"cannot open input\n";return 2;}
 string line;vector<PC>pcs;
 while(getline(fh,line)){
  if(line.rfind("HIT ",0))continue;auto a=line.find("p="),b=line.find("|c=");if(a==string::npos||b==string::npos)return 3;a+=2;
  string ps=line.substr(a,b-a),cs=line.substr(b+3);replace(ps.begin(),ps.end(),',',' ');replace(cs.begin(),cs.end(),',',' ');stringstream sp(ps),sc(cs);PC x;
  for(int i=0;i<N;i++){if(!(sp>>x.p[i]))return 3;if(!x.p[i])x.as|=1u<<i;}for(int i=0;i<N;i++){if(!(sc>>x.c[i]))return 3;if(!x.c[i])x.gs|=1u<<i;}
  x.SG=sg_of(x.p,x.c);if(!periodic_cross(x.p,x.c)){cerr<<"PERIODIC_CROSS_FAIL\n";return 4;}pcs.push_back(x);
 }
 vector<QH>qs;
 while(getline(fq,line)){
  if(line.rfind("QHIT ",0))continue;QH h;unsigned as,gs,am,gm;int n=sscanf(line.c_str(),"QHIT as=%u gs=%u minSG=%d sh=%d Q=%d amask=%u gmask=%u",&as,&gs,&h.minSG,&h.sh,&h.Q,&am,&gm);if(n!=7)return 5;
  h.as=as;h.gs=gs;h.am=am;h.gm=gm;qs.push_back(h);
 }
 auto units=units25();long long mappedCandidates=0,orient=0,trans=0,vpass=0,opass=0,ele=0;int minV=INT_MAX,minOdd=INT_MAX;long long minE=LLONG_MAX;set<string> emitted;
 int qindex=0;
 for(auto&h:qs){
  qindex++;auto hc=canon_pair(h.as,h.gs);if(hc.as!=h.as||hc.gs!=h.gs){cerr<<"QHIT_NOT_CANONICAL\n";return 6;}
  A25 abase{},gbase{};for(int i=0;i<N;i++){if(h.as>>i&1)abase[i]=(h.am>>i&1)?1:-1;if(h.gs>>i&1)gbase[i]=(h.gm>>i&1)?1:-1;}
  if(!negacyclic_cross(abase,gbase)){cerr<<"NEGACYCLIC_CROSS_FAIL q="<<qindex<<"\n";return 7;}
  int sh=0;for(int r=1;r<=12;r++){int z=npaf25(h.as,h.am,r)+npaf25(h.gs,h.gm,r);sh+=z*z;}if(sh!=h.sh){cerr<<"SH_FAIL q="<<qindex<<" got="<<sh<<" want="<<h.sh<<"\n";return 8;}
  map<string,pair<A25,A25>> mapped;
  for(auto&x:pcs){auto ck=canon_pair(x.as,x.gs);if(ck.as!=h.as||ck.gs!=h.gs||x.SG+h.sh>114)continue;
   for(int aa:units)for(int bb=0;bb<N;bb++)if(affmask(x.as,aa,bb)==h.as&&affmask(x.gs,aa,bb)==h.gs){A25 p=aff25(x.p,aa,bb),c=aff25(x.c,aa,bb);mapped.emplace(pc_key(p,c),make_pair(p,c));}
  }
  cout<<"QMAP q="<<qindex<<" mapped_compressed="<<mapped.size()<<" minSG="<<h.minSG<<" sh="<<h.sh<<" QHIT_Q="<<h.Q<<"\n";
  mappedCandidates+=mapped.size();
  for(auto &kv:mapped){auto p=kv.second.first,c=kv.second.second;int SG=sg_of(p,c),Qarith=(SG+h.sh)/2;if((SG+h.sh)&1||Qarith>57){cerr<<"MAPPED_BUDGET_FAIL\n";return 9;}
   for(int sa:{1,-1})for(int sg:{1,-1}){
    orient++;A25 alpha{},gamma{};for(int i=0;i<N;i++){if(h.as>>i&1)alpha[i]=sa*abase[i];if(h.gs>>i&1)gamma[i]=sg*gbase[i];}
    if(!negacyclic_cross(alpha,gamma))return 10;auto q=q_from_c(c),beta=beta_from_gamma(gamma);A50 A{},B{};
    for(int i=0;i<N;i++){A[i]=p[i]+alpha[i];A[i+N]=p[i]-alpha[i];B[i]=q[i]+beta[i];B[i+N]=q[i]-beta[i];if(abs(A[i])!=1||abs(A[i+N])!=1||abs(B[i])!=1||abs(B[i+N])!=1){cerr<<"NONBINARY_LIFT\n";return 11;}}
    int Q=0;for(int r=1;r<=24;r++){int num=paf(A,r)+paf(B,r);if(num%4){cerr<<"Q_DIV_FAIL\n";return 12;}int u=num/4;Q+=u*u;}if(Q!=Qarith){cerr<<"Q_IDENTITY_FAIL got="<<Q<<" arith="<<Qarith<<"\n";return 13;}
    for(int aa:units){int ah=(aa&1)?aa:aa+25,hshift=(ah-1)/2;auto TA=multperm(A,ah),TB=multperm(B,ah);for(int bb=0;bb<N;bb++){
      trans++;auto X=rot(TA,bb),Y=rot(TB,bb+hshift);int vs=0;for(int r=1;r<=24;r++){int num=(ac(X,r)-ac(X,50-r))+(ac(Y,r)-ac(Y,50-r));if(num%4)return 14;int v=num/4;vs+=v*v;}minV=min(minV,vs);if(vs<=57-Q)vpass++;
      bool op=true;long long odd=0;for(int r=0;r<50;r++){int z=oddcorr(X,Y,r);odd+=1LL*z*z;if(abs(z)!=1)op=false;}minOdd=min<long long>(minOdd,odd);if(op)opass++;
      long long odd2,E=energy(X,Y,odd2);if(odd2!=odd)return 15;minE=min(minE,E);if(E<=570){ele++;string s=seq100(X,Y);if(emitted.insert(s).second)cout<<"CANDIDATE energy="<<E<<" odd="<<odd<<" Q="<<Q<<" V2="<<vs<<" sequence="<<s<<"\n";}
    }}
   }
  }
 }
 cout<<"K21_AFFINE_WITNESS_SUMMARY qhits="<<qs.size()<<" mapped_compressed_candidates="<<mappedCandidates<<" fibre_orientations="<<orient<<" affine_transforms="<<trans<<" Vbudget_pass="<<vpass<<" oddperfect_pass="<<opass<<" E_le_570="<<ele<<" minV="<<minV<<" minOddEnergy="<<minOdd<<" minEnergy="<<minE<<"\n";
 return ele?20:0;
}
