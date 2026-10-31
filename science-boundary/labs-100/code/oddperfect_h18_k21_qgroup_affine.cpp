// Exact affine-canonical grouped fibre-Q solver for odd-perfect (18,0), K=21.
//
// Input: HIT lines emitted by oddperfect_h18_k21_compressed.cpp.
// For a compressed candidate (p,c), let
//   as = supp(alpha) = zeros(p),  gs = supp(gamma) = zeros(c),
// where alpha,gamma are the two negacyclic fibre sign vectors.
// The full even-pair norm obeys
//   2 Q = SG + SH,
//   SG = sum_{r=1}^{12} (PAF_p(r)+PAF_c(r))^2,
//   SH = sum_{r=1}^{12} (NPAF_alpha(r)+NPAF_gamma(r))^2.
// K=21 and E<=570 require Q<=57, hence SG+SH<=114.
//
// Two exact reductions are used before fibre enumeration.
//
// (1) Canonicalize the support pair (as,gs) under the simultaneous
//     AGL(1,Z25) action i -> a*i+b.  The induced length-50 odd-unit/translation
//     automorphism sends p,c,alpha,gamma through this same support action
//     (fibre signs may acquire negacyclic sign twists).  SG is invariant, and
//     because all fibre signs are enumerated, the attainable SH set is also
//     invariant.  Thus only one canonical support pair is needed per orbit.
//
// (2) Enumerate signs on the smaller of as and gs and solve the other side.
//     The negacyclic cross equation alpha gamma* - gamma alpha*=0 is symmetric
//     up to sign under swapping alpha,gamma, so zero-solutions are unchanged.
//     This matters for low kp: kp=9 has |as|=16 but |gs|=13.
//
// For each fixed outer sign vector, solve the other signs exactly by a GF(3)
// nullspace enumeration followed by all original integer negacyclic equations.
// Independent global signs of alpha and gamma are quotiented because cross=0
// and SH are invariant under either sign flip.
#include <bits/stdc++.h>
#include <omp.h>
using namespace std;
static const int N=25;
using A=array<int,N>;
using Vec=array<int16_t,N>;

static vector<int> units(){vector<int>u;for(int a=1;a<N;a++)if(gcd(a,N)==1)u.push_back(a);return u;}
static uint32_t affmask(uint32_t x,int a,int b){uint32_t y=0;for(int i=0;i<N;i++)if(x>>i&1)y|=1u<<((a*i+b)%N);return y;}
struct Key{uint32_t as=0,gs=0;bool operator<(Key const&o)const{return as!=o.as?as<o.as:gs<o.gs;}};
static Key canon_pair(uint32_t as,uint32_t gs){static const auto us=units();Key best{UINT32_MAX,UINT32_MAX};for(int a:us)for(int b=0;b<N;b++){Key z{affmask(as,a,b),affmask(gs,a,b)};if(z<best)best=z;}return best;}

static Vec comm_mask(uint32_t osupp,uint32_t oplus,int j){
 Vec f{};auto add=[&](int e,int v){if(e>=0)f[e]+=v;else f[e+N]-=v;};
 for(int i=0;i<N;i++)if(osupp>>i&1){int oi=(oplus>>i&1)?1:-1;add(i-j,oi);add(j-i,-oi);}return f;
}
static Vec comm(const A&a,const A&g){
 Vec f{};auto add=[&](int e,int v){if(e>=0)f[e]+=v;else f[e+N]-=v;};
 for(int i=0;i<N;i++)if(a[i])for(int j=0;j<N;j++)if(g[j]){add(i-j,a[i]*g[j]);add(j-i,-g[j]*a[i]);}return f;
}

// Given a fixed signed outer vector, enumerate every signed vector on ssupp
// satisfying comm(outer,second)=0.  This equation is zero-equivalent to the
// desired comm(alpha,gamma)=0 even when outer/second are swapped.
static vector<uint32_t> solve_second(uint32_t osupp,uint32_t oplus,uint32_t ssupp){
 vector<int>sp;for(int i=0;i<N;i++)if(ssupp>>i&1)sp.push_back(i);int nc=sp.size();if(!nc)return{0};
 vector<vector<uint8_t>>a(12,vector<uint8_t>(nc));
 for(int j=0;j<nc;j++){auto v=comm_mask(osupp,oplus,sp[j]);for(int r=1;r<=12;r++){int z=v[r]%3;if(z<0)z+=3;a[r-1][j]=z;}}
 int rr=0;vector<int>piv;
 for(int c=0;c<nc&&rr<12;c++){
  int q=-1;for(int r=rr;r<12;r++)if(a[r][c]){q=r;break;}if(q<0)continue;swap(a[rr],a[q]);
  if(a[rr][c]==2)for(int j=0;j<nc;j++)a[rr][j]=(2*a[rr][j])%3;
  for(int r=0;r<12;r++)if(r!=rr&&a[r][c]){int f=a[r][c];for(int j=0;j<nc;j++)a[r][j]=(a[r][j]+6-f*a[rr][j])%3;}
  piv.push_back(c);rr++;
 }
 vector<char>isp(nc);for(int c:piv)isp[c]=1;vector<int>fr;for(int c=0;c<nc;c++)if(!isp[c])fr.push_back(c);int d=fr.size();
 if(d>24)abort();vector<uint32_t>sol;uint64_t M=1ULL<<d;vector<int>x(nc);A oo{};for(int i=0;i<N;i++)if(osupp>>i&1)oo[i]=(oplus>>i&1)?1:-1;
 for(uint64_t m=0;m<M;m++){
  fill(x.begin(),x.end(),0);for(int k=0;k<d;k++)x[fr[k]]=(m>>k&1)?2:1;bool ok=true;
  for(int r=rr-1;r>=0;r--){int ss=0;for(int k=0;k<d;k++)ss=(ss+a[r][fr[k]]*x[fr[k]])%3;int z=(3-ss)%3;if(z!=1&&z!=2){ok=false;break;}x[piv[r]]=z;}
  if(!ok||x[0]!=1)continue; // quotient second-vector global sign.
  A sec{};uint32_t plus=0;for(int j=0;j<nc;j++){int sg=x[j]==1?1:-1;sec[sp[j]]=sg;if(sg==1)plus|=1u<<sp[j];}
  auto z=comm(oo,sec);bool ex=true;for(int r=0;r<N;r++)if(z[r]){ex=false;break;}if(ex)sol.push_back(plus);
 }
 return sol;
}

static inline int npaf(uint32_t supp,uint32_t plus,int r){
 uint32_t pair=supp&(supp>>r),sx=plus^(plus>>r);int non=__builtin_popcount(pair)-2*__builtin_popcount(pair&sx);
 uint32_t mr=(1u<<r)-1,hi=supp>>(N-r),lo=supp&mr,pw=hi&lo,sh=plus>>(N-r),sl=plus&mr;
 int wrap=__builtin_popcount(pw)-2*__builtin_popcount(pw&(sh^sl));return non-wrap;
}
static int sg_of(const A&p,const A&c){int s=0;for(int r=1;r<=12;r++){int g=0;for(int i=0;i<N;i++)g+=p[i]*p[(i+r)%N]+c[i]*c[(i+r)%N];s+=g*g;}return s;}
struct Group{Key k{};int minSG=INT_MAX,count=0;};

int main(int argc,char**argv){
 if(argc<2){cerr<<"usage: qgroup_affine hits.txt\n";return 2;}ifstream f(argv[1]);if(!f){cerr<<"cannot open input\n";return 2;}
 string line;map<Key,Group>mp;long long hits=0;
 while(getline(f,line)){
  if(line.rfind("HIT ",0))continue;auto a=line.find("p=")+2,b=line.find("|c=");if(a==string::npos||b==string::npos)return 3;
  string ps=line.substr(a,b-a),cs=line.substr(b+3);replace(ps.begin(),ps.end(),',',' ');replace(cs.begin(),cs.end(),',',' ');stringstream sp(ps),sc(cs);A p{},c{};uint32_t as=0,gs=0;
  for(int i=0;i<N;i++){if(!(sp>>p[i]))return 3;if(!p[i])as|=1u<<i;}for(int i=0;i<N;i++){if(!(sc>>c[i]))return 3;if(!c[i])gs|=1u<<i;}
  Key k=canon_pair(as,gs);auto&g=mp[k];g.k=k;g.count++;g.minSG=min(g.minSG,sg_of(p,c));hits++;
 }
 vector<Group>groups;for(auto&kv:mp)groups.push_back(kv.second);
 cout<<"AFFINE_QGROUP_INPUT hits="<<hits<<" canonical_groups="<<groups.size()<<"\n";
 atomic<long long>outer_states{0},half{0},qpass{0};atomic<int>minMargin{INT_MAX},minSHglobal{INT_MAX};
#pragma omp parallel for schedule(dynamic,1)
 for(int gi=0;gi<(int)groups.size();gi++){
  auto G=groups[gi];int za=__builtin_popcount(G.k.as),zg=__builtin_popcount(G.k.gs);bool swap=(zg<za);
  uint32_t os=swap?G.k.gs:G.k.as, ss=swap?G.k.as:G.k.gs;vector<int>opos;for(int i=0;i<N;i++)if(os>>i&1)opos.push_back(i);int Z=opos.size();if(!Z)abort();
  uint64_t OM=1ULL<<(Z-1);long long lh=0,lq=0;int lmin=INT_MAX;
  for(uint64_t m=0;m<OM;m++){
   uint32_t op=1u<<opos[0];for(int t=1;t<Z;t++)if(m>>(t-1)&1)op|=1u<<opos[t];outer_states++;
   auto sols=solve_second(os,op,ss);lh+=sols.size();
   for(uint32_t spm:sols){uint32_t ap=swap?spm:op,gp=swap?op:spm;int sh=0;for(int r=1;r<=12;r++){int h=npaf(G.k.as,ap,r)+npaf(G.k.gs,gp,r);sh+=h*h;}lmin=min(lmin,sh);if(G.minSG+sh<=114){lq++;
#pragma omp critical
    cout<<"QHIT as="<<G.k.as<<" gs="<<G.k.gs<<" minSG="<<G.minSG<<" sh="<<sh<<" Q="<<(G.minSG+sh)/2<<" amask="<<ap<<" gmask="<<gp<<" swapped="<<swap<<"\n";
   }}
  }
  half+=lh;qpass+=lq;if(lmin<INT_MAX){int old=minSHglobal.load();while(lmin<old&&!minSHglobal.compare_exchange_weak(old,lmin)){}int mar=G.minSG+lmin-114;old=minMargin.load();while(mar<old&&!minMargin.compare_exchange_weak(old,mar)){}}
 }
 cout<<"K21_AFFINE_QGROUP_SUMMARY canonical_groups="<<groups.size()<<" outer_states="<<outer_states<<" half_second_solutions="<<half<<" Q_feasible_halfpairs="<<qpass<<" minSH="<<minSHglobal<<" min_margin="<<minMargin<<"\n";
 return 0;
}
