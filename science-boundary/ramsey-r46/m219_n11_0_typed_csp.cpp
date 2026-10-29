// Exact finite-domain gluing for the two m=219,n11=0 Ramsey(4,6,36) cases.
//
// A fixed degree-12 anchor splits the other vertices into A=N(v), |A|=12,
// and B, |B|=23.  A and B are fixed catalogue graphs.  Each B vertex is one
// finite-domain variable whose value is its 12-bit cross-neighbourhood in A.
//
// Input label representatives encode which A/B vertices have global degree
// 13 or 14.  The solver enforces exact degrees, all mixed K4/I6 constraints,
// the complete no-lucky-d12 excess-capacity condition, and local triangle
// lower bounds implied by e(4,5,23)=101, e(4,5,22)=88, e(4,5,21)=77.
// Residual Aut(A) is used by canonical augmentation after the typed labels are
// fixed.  UNSAT with no timeout is therefore an exact exclusion of the label
// orbit, not a heuristic result.
#include <bits/stdc++.h>
using namespace std;
static const int NA=12, NB=23, NM=1<<NA, W=NM/64;
struct Bits{ array<uint64_t,W> x{}; };
static inline void clearB(Bits&b){b.x.fill(0);} static inline void setbit(Bits&b,int i){b.x[i>>6]|=1ULL<<(i&63);}
static inline bool emptyB(const Bits&b){for(auto z:b.x)if(z)return false;return true;} static inline int countB(const Bits&b){int s=0;for(auto z:b.x)s+=__builtin_popcountll(z);return s;}
static inline void andeq(Bits&a,const Bits&b){for(int i=0;i<W;i++)a.x[i]&=b.x[i];}
static inline bool intersects(const Bits&a,const Bits&b){for(int i=0;i<W;i++)if(a.x[i]&b.x[i])return true;return false;}
static inline bool subseteq(const Bits&a,const Bits&b){for(int i=0;i<W;i++)if(a.x[i]&~b.x[i])return false;return true;}
static vector<int> elems(const Bits&b){vector<int>v;for(int q=0;q<W;q++){uint64_t z=b.x[q];while(z){int r=__builtin_ctzll(z);v.push_back(q*64+r);z&=z-1;}}return v;}

vector<uint32_t> decodeg6(const string&s){int n=(unsigned char)s[0]-63;vector<int>bits;for(size_t p=1;p<s.size();p++){int z=(unsigned char)s[p]-63;for(int k=5;k>=0;k--)bits.push_back((z>>k)&1);}vector<uint32_t>a(n);int p=0;for(int j=1;j<n;j++)for(int i=0;i<j;i++){if(bits[p]){a[i]|=1u<<j;a[j]|=1u<<i;}p++;}return a;}
vector<int> subsetMasks(const vector<uint32_t>&a,int k,bool edge){int n=a.size();vector<int>o;for(int m=0;m<(1<<n);m++)if(__builtin_popcount((unsigned)m)==k){bool ok=1;for(int i=0;i<n&&ok;i++)if(m>>i&1)for(int j=i+1;j<n;j++)if(m>>j&1){bool e=(a[i]>>j)&1;if(e!=edge){ok=0;break;}}if(ok)o.push_back(m);}return o;}
bool hitsAll(int m,const vector<int>&sets){for(int s:sets)if(!(m&s))return false;return true;}
bool indepMaskA(const vector<uint32_t>&A,int m){for(int i=0;i<NA;i++)if((m>>i)&1)if(A[i]&m)return false;return true;}

struct Hyper{int typ; vector<int>v;}; //0 B-triangle; 1 B-I3; 2 B-I4
struct Solver{
 vector<uint32_t>A,B; int da[NA],db[NB]; bool bedge[NB][NB]{};
 vector<int>I2,I3,I4,I5; Bits contains[NA], sizeMask[NA+1];
 vector<Bits> edgeCompat,nonCompat,avoidInter,hit3Filt,hit2Filt;
 vector<Hyper> hypers; vector<vector<int>> hypBy;
 uint16_t A13=0,A14=0; uint32_t B13=0,B14=0; int exA[NA],exB[NB],globA[NA],globB[NB]; int rowTarget[NA], row[NA], highCapA[NA], highRow[NA]; int asg[NB];
 long long nodes=0, placements=0, domain_empty=0, pruned_global=0; bool timed=false; double deadline=0; vector<int>sol;
 int triB[NB], eAin[NM]; vector<array<int,NA>> autos;
 int tmask(int m,const array<int,NA>&p)const{int z=0;for(int i=0;i<NA;i++)if(m>>i&1)z|=1<<p[i];return z;}
 void genAutos(){array<int,NA> p;p.fill(-1);bool used[NA]={};function<void(int)> dfs=[&](int pos){if(pos==NA){autos.push_back(p);return;}int v=-1,best=99;for(int i=0;i<NA;i++)if(p[i]<0){int c=0;for(int j=0;j<NA;j++)if(!used[j]&&da[j]==da[i]){bool ok=1;for(int u=0;u<NA;u++)if(p[u]>=0&&(((A[i]>>u)&1)!=((A[j]>>p[u])&1))){ok=0;break;}if(ok)c++;}if(c<best){best=c;v=i;}}for(int j=0;j<NA;j++)if(!used[j]&&da[j]==da[v]){bool ok=1;for(int u=0;u<NA;u++)if(p[u]>=0&&(((A[v]>>u)&1)!=((A[j]>>p[u])&1))){ok=0;break;}if(!ok)continue;p[v]=j;used[j]=1;dfs(pos+1);used[j]=0;p[v]=-1;}};dfs(0);}
 Solver(const vector<uint32_t>&aa,const vector<uint32_t>&bb):A(aa),B(bb),edgeCompat(NM),nonCompat(NM),avoidInter(NM),hit3Filt(NM),hit2Filt(NM),hypBy(NB){
  for(int i=0;i<NA;i++)da[i]=__builtin_popcount(A[i]);for(int i=0;i<NB;i++)db[i]=__builtin_popcount(B[i]);genAutos();
  for(int b=0;b<NB;b++){int t=0;for(int c=0;c<NB;c++)if(c!=b&&((B[b]>>c)&1))for(int d=c+1;d<NB;d++)if(d!=b&&((B[b]>>d)&1)&&((B[c]>>d)&1))t++;triB[b]=t;}
  for(int m=0;m<NM;m++){int e=0;for(int a=0;a<NA;a++)if((m>>a)&1)e+=__builtin_popcount(A[a]&m);eAin[m]=e/2;}
  I2=subsetMasks(A,2,false);I3=subsetMasks(A,3,false);I4=subsetMasks(A,4,false);I5=subsetMasks(A,5,false);
  for(int k=0;k<=NA;k++)clearB(sizeMask[k]);for(int a=0;a<NA;a++)clearB(contains[a]);
  for(int m=0;m<NM;m++){setbit(sizeMask[__builtin_popcount((unsigned)m)],m);for(int a=0;a<NA;a++)if(m>>a&1)setbit(contains[a],m);}
  for(int m=0;m<NM;m++){clearB(edgeCompat[m]);clearB(nonCompat[m]);clearB(avoidInter[m]);clearB(hit3Filt[m]);clearB(hit2Filt[m]);
    for(int n=0;n<NM;n++){
      if(indepMaskA(A,m&n))setbit(edgeCompat[m],n);
      if(hitsAll(m|n,I4))setbit(nonCompat[m],n);
      if((m&n)==0)setbit(avoidInter[m],n);
      if(hitsAll(m|n,I3))setbit(hit3Filt[m],n);
      if(hitsAll(m|n,I2))setbit(hit2Filt[m],n);
    }
  }
  for(int i=0;i<NB;i++)for(int j=i+1;j<NB;j++)bedge[i][j]=bedge[j][i]=((B[i]>>j)&1);
  auto addHyp=[&](int typ,int mask){Hyper h;h.typ=typ;for(int i=0;i<NB;i++)if(mask>>i&1)h.v.push_back(i);int id=hypers.size();hypers.push_back(h);for(int v:h.v)hypBy[v].push_back(id);};
  for(int m:subsetMasks(B,3,true))addHyp(0,m);for(int m:subsetMasks(B,3,false))addHyp(1,m);for(int m:subsetMasks(B,4,false))addHyp(2,m);
 }
 bool restrictHyp(Bits dom[NB],int changed,uint32_t unmask){
  for(int hid:hypBy[changed]){auto &h=hypers[hid];int rem=-1,nr=0,inter=(1<<NA)-1,uni=0;for(int v:h.v){if(unmask>>v&1){rem=v;nr++;}else{int m=asg[v];if(m<0)abort();inter&=m;uni|=m;}}
   if(nr==0){bool ok=h.typ==0?inter==0:(h.typ==1?hitsAll(uni,I3):hitsAll(uni,I2));if(!ok)return false;}
   else if(nr==1){if(h.typ==0)andeq(dom[rem],avoidInter[inter]);else if(h.typ==1)andeq(dom[rem],hit3Filt[uni]);else andeq(dom[rem],hit2Filt[uni]);if(emptyB(dom[rem]))return false;}
  }return true;
 }
 int maxInter(const Bits&d,int m)const{int best=0;for(int q=0;q<W;q++){uint64_t z=d.x[q];while(z){int r=__builtin_ctzll(z),n=q*64+r;best=max(best,__builtin_popcount((unsigned)(m&n)));if(best==__builtin_popcount((unsigned)m))return best;z&=z-1;}}return best;}
 bool triangleUpperOK(const Bits dom[NB],uint32_t unmask){
  auto baseNeed=[](int d){return d==13?25:26;};
  for(int b=0;b<NB;b++)if(!(unmask>>b&1)){
    int m=asg[b],wfix=0;for(int h=0;h<NB;h++)if(h!=b&&bedge[b][h])wfix+=exB[h];for(int a=0;a<NA;a++)if(m>>a&1)wfix+=exA[a];
    int need=baseNeed(globB[b])+wfix,up=triB[b]+eAin[m];for(int c=0;c<NB;c++)if(bedge[b][c]){if(unmask>>c&1)up+=maxInter(dom[c],m);else up+=__builtin_popcount((unsigned)(m&asg[c]));}if(up<need)return false;
  }
  for(int a=0;a<NA;a++){
    int wcur=0;for(int h=0;h<NA;h++)if(h!=a&&((A[a]>>h)&1))wcur+=exA[h];wcur+=highRow[a];int need=baseNeed(globA[a])+wcur,up=da[a];
    for(int b=0;b<NB;b++){if(unmask>>b&1){if(intersects(dom[b],contains[a]))up+=da[a];}else{int m=asg[b];if((m>>a)&1)up+=__builtin_popcount((unsigned)(A[a]&m));}}
    for(int b=0;b<NB;b++)for(int c=b+1;c<NB;c++)if(bedge[b][c]){bool pb=(unmask>>b&1)?intersects(dom[b],contains[a]):((asg[b]>>a)&1);bool pc=(unmask>>c&1)?intersects(dom[c],contains[a]):((asg[c]>>a)&1);if(pb&&pc)up++;}
    if(up<need)return false;
  }
  return true;
 }
 bool globalPrune(Bits dom[NB],uint32_t unmask){
  for(int a=0;a<NA;a++){
    int mn=row[a],mx=row[a],wforce=highRow[a];
    for(int b=0;b<NB;b++)if(unmask>>b&1){if(subseteq(dom[b],contains[a])){mn++;wforce+=exB[b];}if(intersects(dom[b],contains[a]))mx++;}
    if(mn>rowTarget[a]||mx<rowTarget[a]){pruned_global++;return false;}if(globA[a]==12&&wforce>highCapA[a]){pruned_global++;return false;}
  }
  if(!triangleUpperOK(dom,unmask)){pruned_global++;return false;}return true;
 }
 bool rec(Bits dom[NB],uint32_t unmask,const vector<int>&stab){
  nodes++;if((nodes&0x3fff)==0&&chrono::duration<double>(chrono::steady_clock::now().time_since_epoch()).count()>deadline){timed=true;return false;}
  if(!globalPrune(dom,unmask))return false;
  if(!unmask){for(int a=0;a<NA;a++)if(row[a]!=rowTarget[a])return false;sol.assign(asg,asg+NB);return true;}
  int b=-1,bc=1e9;for(int i=0;i<NB;i++)if(unmask>>i&1){int c=countB(dom[i]);if(c<bc){bc=c;b=i;}}
  auto allvals=elems(dom[b]);vector<int>vals;vals.reserve(allvals.size());for(int m:allvals){int mn=m;for(int gi:stab)mn=min(mn,tmask(m,autos[gi]));if(m==mn)vals.push_back(m);}uint32_t newmask=unmask&~(1u<<b);
  sort(vals.begin(),vals.end(),[&](int m,int n){int sm=0,sn=0;for(int a=0;a<NA;a++){int need=rowTarget[a]-row[a];if(m>>a&1)sm+=need;if(n>>a&1)sn+=need;}return sm>sn;});
  for(int m:vals){
    bool ok=true;for(int a=0;a<NA;a++)if((m>>a)&1){if(row[a]>=rowTarget[a]){ok=false;break;}if(globA[a]==12&&highRow[a]+exB[b]>highCapA[a]){ok=false;break;}}if(!ok)continue;
    Bits nd[NB];memcpy(nd,dom,sizeof nd);for(int c=0;c<NB;c++)if(newmask>>c&1){andeq(nd[c],bedge[b][c]?edgeCompat[m]:nonCompat[m]);if(emptyB(nd[c])){ok=false;break;}}if(!ok)continue;
    asg[b]=m;for(int a=0;a<NA;a++)if(m>>a&1){row[a]++;highRow[a]+=exB[b];}
    vector<int>nstab;nstab.reserve(stab.size());for(int gi:stab)if(tmask(m,autos[gi])==m)nstab.push_back(gi);
    if(restrictHyp(nd,b,newmask)&&rec(nd,newmask,nstab))return true;
    for(int a=0;a<NA;a++)if(m>>a&1){row[a]--;highRow[a]-=exB[b];}asg[b]=-1;if(timed)return false;
  }
  return false;
 }
 string solvePlacement(uint16_t a13,uint16_t a14,uint32_t b13,uint32_t b14,double sec){
  A13=a13;A14=a14;B13=b13;B14=b14;placements++;fill(row,row+NA,0);fill(highRow,highRow+NA,0);fill(asg,asg+NB,-1);
  for(int a=0;a<NA;a++){exA[a]=((A13>>a)&1)+2*((A14>>a)&1);globA[a]=12+exA[a];}
  for(int b=0;b<NB;b++){exB[b]=((B13>>b)&1)+2*((B14>>b)&1);globB[b]=12+exB[b];}
  for(int a=0;a<NA;a++){rowTarget[a]=globA[a]-1-da[a];int fixedW=0;for(int h=0;h<NA;h++)if(h!=a&&((A[a]>>h)&1))fixedW+=exA[h];highCapA[a]=2-fixedW;if(globA[a]==12&&highCapA[a]<0)return"UNSAT";if(rowTarget[a]<0||rowTarget[a]>NB)return"UNSAT";}
  Bits dom[NB];for(int b=0;b<NB;b++){
    clearB(dom[b]);int k=globB[b]-db[b],fixedW=0;for(int h=0;h<NB;h++)if(h!=b&&bedge[b][h])fixedW+=exB[h];int cap=2-fixedW;if(globB[b]==12&&cap<0)return"UNSAT";if(k<0||k>NA)return"UNSAT";
    for(int m=0;m<NM;m++)if(__builtin_popcount((unsigned)m)==k&&hitsAll(m,I5)){if(globB[b]==12){int w=0;for(int a=0;a<NA;a++)if(m>>a&1)w+=exA[a];if(w>cap)continue;}setbit(dom[b],m);}if(emptyB(dom[b])){domain_empty++;return"UNSAT";}
  }
  deadline=chrono::duration<double>(chrono::steady_clock::now().time_since_epoch()).count()+sec;timed=false;vector<int>stab;for(int gi=0;gi<(int)autos.size();gi++){bool ok=1;for(int a=0;a<NA;a++)if(exA[autos[gi][a]]!=exA[a]){ok=0;break;}if(ok)stab.push_back(gi);}bool sat=rec(dom,(1u<<NB)-1,stab);if(sat)return"SAT";if(timed)return"TIMEOUT";return"UNSAT";
 }
};

int main(int argc,char**argv){
 if(argc<6){cerr<<"usage A.g6 B.g6 aordinal seconds reps.txt [percap]\n";return 2;}
 string ap=argv[1],bp=argv[2];int ao=stoi(argv[3]);double totalSec=stod(argv[4]);string repsPath=argv[5];double perCap=argc>6?stod(argv[6]):5.0;
 ifstream fa(ap),fb(bp);string z;vector<string>as,bs;while(getline(fa,z))if(!z.empty())as.push_back(z);while(getline(fb,z))if(!z.empty())bs.push_back(z);if(ao<0||ao>=as.size()||bs.size()!=1)return 2;
 Solver sp(decodeg6(as[ao]),decodeg6(bs[0]));
 struct P{uint16_t a13,a14;uint32_t b13,b14;};vector<P>ps;ifstream rf(repsPath);unsigned a13,a14,b13,b14;while(rf>>a13>>a14>>b13>>b14)ps.push_back({(uint16_t)a13,(uint16_t)a14,(uint32_t)b13,(uint32_t)b14});
 long long u=0,t=0;vector<array<unsigned,4>>hard;double start=chrono::duration<double>(chrono::steady_clock::now().time_since_epoch()).count();int pi=0;
 for(auto p:ps){double now=chrono::duration<double>(chrono::steady_clock::now().time_since_epoch()).count(),remain=totalSec-(now-start);if(remain<=0){cout<<"{\"a\":"<<ao<<",\"status\":\"TIMEOUT\",\"placements_done\":"<<pi<<",\"placements_total\":"<<ps.size()<<",\"nodes\":"<<sp.nodes<<"}\n";return 124;}string st=sp.solvePlacement(p.a13,p.a14,p.b13,p.b14,min(perCap,remain));pi++;if(st=="SAT"){cout<<"{\"a\":"<<ao<<",\"status\":\"SAT\",\"placement\":["<<p.a13<<','<<p.a14<<','<<p.b13<<','<<p.b14<<"],\"placements_done\":"<<pi<<",\"nodes\":"<<sp.nodes<<",\"solution\":[";for(int i=0;i<NB;i++){if(i)cout<<',';cout<<sp.sol[i];}cout<<"]}\n";return 0;}if(st=="TIMEOUT"){t++;hard.push_back({p.a13,p.a14,p.b13,p.b14});}else u++;if(pi%100==0)cerr<<"done="<<pi<<" U="<<u<<" T="<<t<<" nodes="<<sp.nodes<<"\n";}
 cout<<"{\"a\":"<<ao<<",\"status\":\"UNSAT\",\"placements_done\":"<<pi<<",\"placements_total\":"<<pi<<",\"placement_unsat\":"<<u<<",\"placement_timeouts\":"<<t<<",\"nodes\":"<<sp.nodes<<",\"hard\":[";for(size_t i=0;i<hard.size();i++){if(i)cout<<',';cout<<'['<<hard[i][0]<<','<<hard[i][1]<<','<<hard[i][2]<<','<<hard[i][3]<<']';}cout<<"]}\n";return t?124:20;
}
