// Exact symmetric-difference enumerator with a safe mod-3 rank prefilter.
//
// This is the low11 order-25 search from oddperfect_low11_symdiff_exact.cpp,
// with one additional exact rejection before the c-sign meet-in-the-middle.
// For fixed signed p and fixed c support positions j, the equations
//
//   H_r = 0, r=0,...,12,  and  sum_j c_j = 0
//
// form a homogeneous 14 x kc integer linear system M c = 0.  The column for
// c_j has entries p_{j+r}+p_{j-r} in rows r=0..12 and 1 in the sum row.
// If M has full column rank modulo 3, its only F_3 null vector is zero, while
// every c_j in {-1,+1} is nonzero modulo 3.  Hence no signed c solution can
// exist.  Full rank mod 3 is therefore a rigorous rejection; rank-deficient
// cases continue to the unchanged exact integer MITM.
//
// --begin/--end select contiguous affine difference-support orbit ranges.
#include <bits/stdc++.h>
#ifdef _OPENMP
#include <omp.h>
#endif
using namespace std; using U=uint32_t; const U ALL=(1u<<25)-1;
U rot(U x,int k){k%=25;return ((x<<k)|(x>>(25-k)))&ALL;}
U star(U x){U y=0;for(int i=0;i<25;i++)if(x>>i&1)y|=1u<<((25-i)%25);return y;}
U mul(U a,U b){U y=0;for(int i=0;i<25;i++)if(a>>i&1)y^=rot(b,i);return y;}
vector<int> units(){vector<int>u;for(int a=1;a<25;a++)if(gcd(a,25)==1)u.push_back(a);return u;}
U aff(U x,int a,int b){U y=0;for(int i=0;i<25;i++)if(x>>i&1)y|=1u<<((a*i+b)%25);return y;}
U canon(U x){static auto us=units();U best=ALL;for(int a:us)for(int b=0;b<25;b++)best=min(best,aff(x,a,b));return best;}
vector<U> orbit_reps(int w){vector<U> reps;unordered_set<U>seen;auto us=units();U x=(1u<<w)-1;while(x<(1u<<25)){if(!seen.count(x)){U c=canon(x);if(c==x)reps.push_back(x);for(int a:us)for(int b=0;b<25;b++)seen.insert(aff(x,a,b));}U c=x&-x,r=x+c;if(!r||r>=(1u<<25))break;x=(((r^x)>>2)/c)|r;}return reps;}
struct Ker{vector<U>b;};
Ker kernel(U D){U rows[25]{};U Ds=star(D);for(int j=0;j<25;j++){U col=mul(1u<<j,Ds)^mul(D,star(1u<<j));for(int r=0;r<25;r++)if(col>>r&1)rows[r]|=1u<<j;}int pr=0;vector<int>pc;for(int c=0;c<25&&pr<25;c++){int q=-1;for(int r=pr;r<25;r++)if(rows[r]>>c&1){q=r;break;}if(q<0)continue;swap(rows[pr],rows[q]);for(int r=0;r<25;r++)if(r!=pr&&(rows[r]>>c&1))rows[r]^=rows[pr];pc.push_back(c);pr++;}bool isp[25]{};for(int c:pc)isp[c]=1;Ker K;for(int f=0;f<25;f++)if(!isp[f]){U v=1u<<f;for(int r=0;r<pr;r++)if(rows[r]>>f&1)v|=1u<<pc[r];K.b.push_back(v);}return K;}
vector<pair<int,int>> stabilizer(U E){vector<pair<int,int>>s;auto us=units();for(int a:us)for(int b=0;b<25;b++)if(aff(E,a,b)==E)s.push_back({a,b});return s;}
U canon_stab(U P,const vector<pair<int,int>>&st){U z=P;for(auto[a,b]:st)z=min(z,aff(P,a,b));return z;}
struct Key{array<int8_t,14>v{};bool operator==(Key const&o)const{return v==o.v;}};
struct KH{size_t operator()(Key const&k)const noexcept{uint64_t h=1469598103934665603ULL;for(auto x:k.v){h^=(uint8_t)(x+64);h*=1099511628211ULL;}return h;}};
static bool low11G(const array<int8_t,25>&p,const array<int8_t,25>&c){int S=0;for(int r=1;r<=12;r++){int g=0;for(int i=0;i<25;i++)g+=p[i]*p[(i+r)%25]+c[i]*c[(i+r)%25];if(g<2||g>4)return false;S+=g;}return S==37;}
static bool mod3_possible(const array<int8_t,25>&p,const vector<int>&ci){
 int nc=(int)ci.size();int a[14][14]{};
 for(int j=0;j<nc;j++){int pos=ci[j];for(int r=0;r<=12;r++){int z=p[(pos+r)%25]+p[(pos-r+25)%25];z%=3;if(z<0)z+=3;a[r][j]=z;}a[13][j]=1;}
 int rank=0;for(int col=0;col<nc;col++){int q=-1;for(int r=rank;r<14;r++)if(a[r][col]){q=r;break;}if(q<0)continue;for(int j=col;j<nc;j++)swap(a[rank][j],a[q][j]);if(a[rank][col]==2)for(int j=col;j<nc;j++)a[rank][j]=(2*a[rank][j])%3;for(int r=0;r<14;r++)if(r!=rank&&a[r][col]){int f=a[r][col];for(int j=col;j<nc;j++){a[r][j]=(a[r][j]-f*a[rank][j])%3;if(a[r][j]<0)a[r][j]+=3;}}rank++;}
 return rank<nc;
}
struct SignStats{long long ptests=0,rankpass=0,hmatch=0,ghit=0;};
static SignStats search_signs(U P,U C,int kp,vector<pair<array<int8_t,25>,array<int8_t,25>>>*outs=nullptr){
 vector<int>pi,ci;for(int i=0;i<25;i++){if(P>>i&1)pi.push_back(i);if(C>>i&1)ci.push_back(i);}int np=pi.size(),nc=ci.size(),pneg=(kp-10)/2;SignStats ST;U pmask=pneg?((1u<<pneg)-1):0;bool firstp=true;
 while(true){if(!firstp&&pneg==0)break;firstp=false;ST.ptests++;array<int8_t,25>p{};for(int j=0;j<np;j++)p[pi[j]]=(pmask>>j&1)?-1:1;
  if(!mod3_possible(p,ci)){if(pneg==0)break;U cc=pmask&-pmask,rr=pmask+cc;if(!rr||rr>=(1u<<np))break;pmask=(((rr^pmask)>>2)/cc)|rr;continue;}ST.rankpass++;
  int ml=nc/2,mr=nc-ml;static constexpr int HS=512;int head[HS];fill(begin(head),end(head),-1);Key rkey[128];uint16_t rmask[128];int nxt[128],rn=0;KH hasher;
  for(int mask=0;mask<(1<<mr);mask++){Key k{};int ss=0;for(int jj=0;jj<mr;jj++){int sgn=(mask>>jj&1)?-1:1,pos=ci[ml+jj];ss+=sgn;for(int r=0;r<=12;r++)k.v[r]+=(int8_t)(sgn*(p[(pos+r)%25]+p[(pos-r+25)%25]));}k.v[13]=(int8_t)ss;int h=(int)(hasher(k)&(HS-1));rkey[rn]=k;rmask[rn]=(uint16_t)mask;nxt[rn]=head[h];head[h]=rn;rn++;}
  for(int mask=0;mask<(1<<ml);mask++){if(mask&1)continue;Key need{};int ss=0;for(int jj=0;jj<ml;jj++){int sgn=(mask>>jj&1)?-1:1,pos=ci[jj];ss+=sgn;for(int r=0;r<=12;r++)need.v[r]-=(int8_t)(sgn*(p[(pos+r)%25]+p[(pos-r+25)%25]));}need.v[13]=(int8_t)-ss;int h=(int)(hasher(need)&(HS-1));for(int e=head[h];e>=0;e=nxt[e])if(rkey[e]==need){uint16_t rm=rmask[e];array<int8_t,25>c{};for(int jj=0;jj<ml;jj++)c[ci[jj]]=(mask>>jj&1)?-1:1;for(int jj=0;jj<mr;jj++)c[ci[ml+jj]]=(rm>>jj&1)?-1:1;ST.hmatch++;if(!low11G(p,c))continue;ST.ghit++;if(outs&&outs->size()<100)outs->push_back({p,c});}}
  if(pneg==0)break;U cc=pmask&-pmask,rr=pmask+cc;if(!rr||rr>=(1u<<np))break;pmask=(((rr^pmask)>>2)/cc)|rr;
 }return ST;
}
int main(int argc,char**argv){
 int t=-1,kp=-1,ibeg=0,iend=-1;for(int i=1;i<argc;i++){string a=argv[i];if(a=="--overlap"&&i+1<argc)t=atoi(argv[++i]);else if(a=="--kp"&&i+1<argc)kp=atoi(argv[++i]);else if(a=="--begin"&&i+1<argc)ibeg=atoi(argv[++i]);else if(a=="--end"&&i+1<argc)iend=atoi(argv[++i]);else{cerr<<"unknown arg "<<a<<"\n";return 2;}}
 if(t<2||t>12||(t&1)||(kp!=12&&kp!=14)){cerr<<"need even --overlap 2..12 and --kp 12|14\n";return 2;}int kc=26-kp,s=26-2*t,ew=min(s,25-s);bool comp=s>12;auto Es=orbit_reps(ew);if(iend<0)iend=(int)Es.size();if(ibeg<0||iend<ibeg||iend>(int)Es.size()){cerr<<"bad orbit range total="<<Es.size()<<"\n";return 2;}cerr<<"E_REPS "<<Es.size()<<" range=["<<ibeg<<","<<iend<<")\n";
 atomic<long long>supp{0},ptests{0},rankpass{0},hmatch{0},signedhits{0};vector<pair<array<int8_t,25>,array<int8_t,25>>>outs;mutex om;
#pragma omp parallel for schedule(dynamic,1)
 for(int ei=ibeg;ei<iend;ei++){U E=Es[ei],D=comp?(ALL^E):E;auto K=kernel(E);auto st=stabilizer(E);int dim=K.b.size();long long ls=0,lp=0,lr=0,lm=0,lh=0;vector<pair<array<int8_t,25>,array<int8_t,25>>>lo;uint64_t M=1ull<<dim;for(uint64_t m=0;m<M;m++){U P=0;for(int j=0;j<dim;j++)if(m>>j&1)P^=K.b[j];if(__builtin_popcount(P)!=kp)continue;U C=P^D;if(__builtin_popcount(C)!=kc)continue;if(canon_stab(P,st)!=P)continue;ls++;auto ss=search_signs(P,C,kp,&lo);lp+=ss.ptests;lr+=ss.rankpass;lm+=ss.hmatch;lh+=ss.ghit;}supp+=ls;ptests+=lp;rankpass+=lr;hmatch+=lm;signedhits+=lh;if(!lo.empty()){lock_guard<mutex>g(om);for(auto&x:lo)if(outs.size()<100)outs.push_back(x);}}
 cout<<"SUMMARY overlap="<<t<<" kp="<<kp<<" kc="<<kc<<" difference_orbits="<<Es.size()<<" support_pair_orbits="<<supp<<" p_sign_tests="<<ptests<<" mod3_rank_pass="<<rankpass<<" H_matches="<<hmatch<<" compressed_hits="<<signedhits<<" range_begin="<<ibeg<<" range_end="<<iend<<" processed="<<(iend-ibeg)<<"\n";
 for(auto&z:outs){cout<<"HIT p=";for(int i=0;i<25;i++)cout<<(int)z.first[i]<<(i==24?'|':' ');cout<<"c=";for(int i=0;i<25;i++)cout<<(int)z.second[i]<<(i==24?'\n':' ');}return 0;
}
