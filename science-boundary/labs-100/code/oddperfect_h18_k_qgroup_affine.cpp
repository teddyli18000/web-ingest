// Generic affine-canonical grouped fibre-Q solver for odd-perfect (18,0).
// Usage: qgroup K compressed_hits.txt
// For odd compression norm K, m=K-25 and E<=570 gives
//   Q+R <= B = floor((130-m^2)/2).
// For a compressed candidate, SG=sum G_j^2. For its negacyclic fibre pair,
// SH=sum H_j^2 and the exact identity is 2Q=SG+SH. Thus Q<=B iff
// SG+SH<=2B. Fibre support pairs are canonicalized under simultaneous
// AGL(1,Z25), and signs are enumerated on the smaller support side.
#include <bits/stdc++.h>
#include <omp.h>
using namespace std;
static const int N=25;
using A=array<int,N>; using Vec=array<int16_t,N>;

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

// Fix a signed vector on osupp and solve every +/-1 sign vector on ssupp
// satisfying comm(outer,second)=0. Both independent global signs are
// quotiented at this Q-only stage.
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
 vector<char>isp(nc);for(int c:piv)isp[c]=1;vector<int>fr;for(int c=0;c<nc;c++)if(!isp[c])fr.push_back(c);int d=fr.size();if(d>24)abort();
 vector<uint32_t>sol;uint64_t M=1ULL<<d;vector<int>x(nc);A oo{};for(int i=0;i<N;i++)if(osupp>>i&1)oo[i]=(oplus>>i&1)?1:-1;
 for(uint64_t m=0;m<M;m++){
  fill(x.begin(),x.end(),0);for(int k=0;k<d;k++)x[fr[k]]=(m>>k&1)?2:1;bool ok=true;
  for(int r=rr-1;r>=0;r--){int ss=0;for(int k=0;k<d;k++)ss=(ss+a[r][fr[k]]*x[fr[k]])%3;int z=(3-ss)%3;if(z!=1&&z!=2){ok=false;break;}x[piv[r]]=z;}
  if(!ok||x[0]!=1)continue;
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
 if(argc<3){cerr<<"usage: qgroup K hits.txt\n";return 2;}int K0=atoi(argv[1]),m0=K0-25,B=(130-m0*m0)/2,T=2*B;if(K0<19||K0>35||(K0%2)==0||B<0)return 2;
 ifstream f(argv[2]);if(!f){cerr<<"cannot open input\n";return 2;}string line;map<Key,Group>mp;long long hits=0;
 while(getline(f,line)){
  if(line.rfind("HIT ",0))continue;auto a=line.find("p="),b=line.find("|c=");if(a==string::npos||b==string::npos)return 3;a+=2;
  string ps=line.substr(a,b-a),cs=line.substr(b+3);replace(ps.begin(),ps.end(),',',' ');replace(cs.begin(),cs.end(),',',' ');stringstream sp(ps),sc(cs);A p{},c{};uint32_t as=0,gs=0;
  for(int i=0;i<N;i++){if(!(sp>>p[i]))return 3;if(!p[i])as|=1u<<i;}for(int i=0;i<N;i++){if(!(sc>>c[i]))return 3;if(!c[i])gs|=1u<<i;}
  Key k=canon_pair(as,gs);auto&g=mp[k];g.k=k;g.count++;g.minSG=min(g.minSG,sg_of(p,c));hits++;
 }
 vector<Group>groups;for(auto&kv:mp)groups.push_back(kv.second);
 cout<<"H18K_AFFINE_QGROUP_INPUT K="<<K0<<" budget="<<B<<" hits="<<hits<<" canonical_groups="<<groups.size()<<"\n";
 atomic<long long>outer_states{0},half{0},qpass{0};atomic<int>minMargin{INT_MAX},minSHglobal{INT_MAX};
#pragma omp parallel for schedule(dynamic,1)
 for(int gi=0;gi<(int)groups.size();gi++){
  auto G=groups[gi];int za=__builtin_popcount(G.k.as),zg=__builtin_popcount(G.k.gs);bool sw=(zg<za);uint32_t os=sw?G.k.gs:G.k.as,ss=sw?G.k.as:G.k.gs;
  vector<int>opos;for(int i=0;i<N;i++)if(os>>i&1)opos.push_back(i);int Z=opos.size();if(!Z)abort();uint64_t OM=1ULL<<(Z-1);long long lh=0,lq=0;int lmin=INT_MAX;
  for(uint64_t m=0;m<OM;m++){
   uint32_t op=1u<<opos[0];for(int t=1;t<Z;t++)if(m>>(t-1)&1)op|=1u<<opos[t];outer_states++;auto sols=solve_second(os,op,ss);lh+=sols.size();
   for(uint32_t spm:sols){uint32_t ap=sw?spm:op,gp=sw?op:spm;int sh=0;for(int r=1;r<=12;r++){int h=npaf(G.k.as,ap,r)+npaf(G.k.gs,gp,r);sh+=h*h;}lmin=min(lmin,sh);if(G.minSG+sh<=T){lq++;
#pragma omp critical
    cout<<"QHIT as="<<G.k.as<<" gs="<<G.k.gs<<" minSG="<<G.minSG<<" sh="<<sh<<" Q="<<(G.minSG+sh)/2<<" amask="<<ap<<" gmask="<<gp<<" swapped="<<sw<<"\n";
   }}
  }
  half+=lh;qpass+=lq;if(lmin<INT_MAX){int old=minSHglobal.load();while(lmin<old&&!minSHglobal.compare_exchange_weak(old,lmin)){}int mar=G.minSG+lmin-T;old=minMargin.load();while(mar<old&&!minMargin.compare_exchange_weak(old,mar)){}}
 }
 cout<<"H18K_AFFINE_QGROUP_SUMMARY K="<<K0<<" budget="<<B<<" canonical_groups="<<groups.size()<<" outer_states="<<outer_states<<" half_second_solutions="<<half<<" Q_feasible_halfpairs="<<qpass<<" minSH="<<minSHglobal<<" min_margin="<<minMargin<<"\n";
 return 0;
}
