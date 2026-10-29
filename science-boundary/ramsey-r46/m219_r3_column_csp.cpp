// Exact finite-domain CSP for the m=219, r=3 Ramsey(4,6,36) branch.
// Each of the 24 B vertices chooses an 11-bit cross-neighborhood in fixed A26.
// Domains enforce the 5A+1B independent-set clauses; binary/ternary/quaternary
// constraints enforce every remaining mixed K4/I6 split. Residual Aut(A) canonical
// augmentation is exact and removes isomorphic cross matrices without fixing labels.
// A26/B116 records are the complete extreme strata authenticated in
// results/m219-extreme-catalogs.json.
#include <bits/stdc++.h>
using namespace std;
static const int MA=11, MB=24, NM=1<<MA, W=32;
struct Bits { uint64_t x[W]; };
static inline void clearBits(Bits &b){ memset(b.x,0,sizeof b.x); }
static inline void setbit(Bits &b,int i){ b.x[i>>6]|=1ULL<<(i&63); }
static inline bool emptyB(const Bits&b){ for(auto v:b.x) if(v) return false; return true; }
static inline int countB(const Bits&b){ int s=0;for(auto v:b.x)s+=__builtin_popcountll(v);return s; }
static inline void andeq(Bits&a,const Bits&b){for(int i=0;i<W;i++)a.x[i]&=b.x[i];}
static inline bool intersects(const Bits&a,const Bits&b){for(int i=0;i<W;i++)if(a.x[i]&b.x[i])return true;return false;}
static inline bool subseteq(const Bits&a,const Bits&b){for(int i=0;i<W;i++)if(a.x[i]&~b.x[i])return false;return true;}
static inline vector<int> elems(const Bits&b){vector<int> v;for(int q=0;q<W;q++){uint64_t z=b.x[q];while(z){int r=__builtin_ctzll(z);v.push_back(q*64+r);z&=z-1;}}return v;}

vector<uint32_t> decodeg6(const string&s){int n=(unsigned char)s[0]-63; vector<int> bits; for(size_t z=1;z<s.size();z++){int v=(unsigned char)s[z]-63;for(int k=5;k>=0;k--)bits.push_back((v>>k)&1);}vector<uint32_t>a(n);int p=0;for(int j=1;j<n;j++)for(int i=0;i<j;i++){if(bits[p]){a[i]|=1u<<j;a[j]|=1u<<i;}p++;}return a;}
vector<int> subsetMasks(const vector<uint32_t>&a,int k,bool clique){int n=a.size();vector<int>o;for(int m=0;m<(1<<n);m++)if(__builtin_popcount((unsigned)m)==k){bool ok=1;for(int i=0;i<n&&ok;i++)if(m>>i&1)for(int j=i+1;j<n;j++)if(m>>j&1){bool e=(a[i]>>j)&1;if(e!=clique){ok=0;break;}}if(ok)o.push_back(m);}return o;}
bool hitsAll(int m,const vector<int>&sets){for(int s:sets)if(!(m&s))return false;return true;}
bool indepMask(const vector<uint32_t>&A,int m){for(int i=0;i<MA;i++)if(m>>i&1)if(A[i]&m)return false;return true;}

struct Hyper {int typ; vector<int> v;};
struct SolverCSP{
 vector<uint32_t>A,B; int da[MA],db[MB];
 vector<int>I2,I3,I4,I5;
 Bits sizeMask[12], contains[MA], edgeCompat[NM], nonCompat[NM], avoidInter[NM], hit3Filt[NM],hit2Filt[NM];
 vector<Hyper> hypers; vector<int> hypBy[MB]; bool bedge[MB][MB]{};
 Bits initDom[MB], classMask[MB][4];
 int seq[4];
 long long nodes=0; double deadline; int bestDepth=0; bool timed=false;
 int asg[MB]; int row[MA]; int bcnt[4]; int cross=0;
 vector<int> solution; vector<array<int,MA>> autos;
 int tmask(int m,const array<int,MA>&p)const{int z=0;for(int i=0;i<MA;i++)if(m>>i&1)z|=1<<p[i];return z;}
 void genAutos(){array<int,MA> p; p.fill(-1); bool used[MA]={}; function<void(int)> dfs=[&](int pos){if(pos==MA){autos.push_back(p);return;} int v=-1;
   int best=99; for(int i=0;i<MA;i++)if(p[i]<0){int c=0;for(int j=0;j<MA;j++)if(!used[j]&&da[j]==da[i]){bool ok=1;for(int u=0;u<MA;u++)if(p[u]>=0){bool e1=(A[i]>>u)&1,e2=(A[j]>>p[u])&1;if(e1!=e2){ok=0;break;}}if(ok)c++;}if(c<best){best=c;v=i;}}
   for(int j=0;j<MA;j++)if(!used[j]&&da[j]==da[v]){bool ok=1;for(int u=0;u<MA;u++)if(p[u]>=0){if(((A[v]>>u)&1)!=((A[j]>>p[u])&1)){ok=0;break;}}if(!ok)continue;p[v]=j;used[j]=1;dfs(pos+1);used[j]=0;p[v]=-1;} }; dfs(0);}
 
 SolverCSP(string ag,string bg, array<int,4> sq){A=decodeg6(ag);B=decodeg6(bg);for(int i=0;i<MA;i++)da[i]=__builtin_popcount(A[i]);for(int i=0;i<MB;i++)db[i]=__builtin_popcount(B[i]);for(int i=0;i<4;i++)seq[i]=sq[i];genAutos();
  I2=subsetMasks(A,2,false);I3=subsetMasks(A,3,false);I4=subsetMasks(A,4,false);I5=subsetMasks(A,5,false);
  for(int k=0;k<12;k++)clearBits(sizeMask[k]);for(int a=0;a<MA;a++)clearBits(contains[a]);
  for(int m=0;m<NM;m++){setbit(sizeMask[__builtin_popcount((unsigned)m)],m);for(int a=0;a<MA;a++)if(m>>a&1)setbit(contains[a],m);}
  for(int m=0;m<NM;m++){clearBits(edgeCompat[m]);clearBits(nonCompat[m]);clearBits(avoidInter[m]);clearBits(hit3Filt[m]);clearBits(hit2Filt[m]);for(int n=0;n<NM;n++){if(indepMask(A,m&n))setbit(edgeCompat[m],n);if(hitsAll(m|n,I4))setbit(nonCompat[m],n);if((m&n)==0)setbit(avoidInter[m],n);if(hitsAll(m|n,I3))setbit(hit3Filt[m],n);if(hitsAll(m|n,I2))setbit(hit2Filt[m],n);}}
  for(int i=0;i<MB;i++)for(int j=i+1;j<MB;j++)bedge[i][j]=bedge[j][i]=((B[i]>>j)&1);
  auto addHyp=[&](int typ,int mask){Hyper h;h.typ=typ;for(int i=0;i<MB;i++)if(mask>>i&1)h.v.push_back(i);int id=hypers.size();hypers.push_back(h);for(int v:h.v)hypBy[v].push_back(id);};
  for(int m:subsetMasks(B,3,true)) addHyp(0,m);
  for(int m:subsetMasks(B,3,false)) addHyp(1,m);
  for(int m:subsetMasks(B,4,false)) addHyp(2,m);
  for(int b=0;b<MB;b++){clearBits(initDom[b]);for(int d=11;d<=14;d++){clearBits(classMask[b][d-11]);int k=d-db[b];if(k<0||k>11)continue;for(int m=0;m<NM;m++)if(__builtin_popcount((unsigned)m)==k && hitsAll(m,I5)){setbit(classMask[b][d-11],m);setbit(initDom[b],m);}}}
  fill(asg,asg+MB,-1);fill(row,row+MA,0);fill(bcnt,bcnt+4,0);
 }
 bool restrictHyper(Bits dom[MB], int changed, uint32_t unmask){
  for(int hid:hypBy[changed]){auto &h=hypers[hid];int rem=-1, nr=0;int inter=(1<<MA)-1, uni=0;for(int v:h.v){if(unmask>>v&1){rem=v;nr++;}else{int m=asg[v]; if(m<0)abort(); inter&=m;uni|=m;}}
   if(nr==0){bool ok = h.typ==0 ? inter==0 : (h.typ==1 ? hitsAll(uni,I3):hitsAll(uni,I2)); if(!ok)return false;}
   else if(nr==1){if(h.typ==0) andeq(dom[rem],avoidInter[inter]); else if(h.typ==1) andeq(dom[rem],hit3Filt[uni]); else andeq(dom[rem],hit2Filt[uni]); if(emptyB(dom[rem]))return false;}
  }
  return true;
 }
 int minSize(const Bits&d){for(int k=0;k<=11;k++)if(intersects(d,sizeMask[k]))return k;return 99;}
 int maxSize(const Bits&d){for(int k=11;k>=0;k--)if(intersects(d,sizeMask[k]))return k;return -1;}
 bool globalPrune(Bits dom[MB],uint32_t unmask){
  if(cross>66)return false;int mn=cross,mx=cross;for(int b=0;b<MB;b++)if(unmask>>b&1){mn+=minSize(dom[b]);mx+=maxSize(dom[b]);}if(mn>66||mx<66)return false;
  int aforce[4]={},aposs[4]={};
  for(int a=0;a<MA;a++){int minadd=0,maxadd=0;for(int b=0;b<MB;b++)if(unmask>>b&1){if(subseteq(dom[b],contains[a]))minadd++;if(intersects(dom[b],contains[a]))maxadd++;}int poss=0,last=-1;for(int d=11;d<=14;d++){if(seq[d-11]==0)continue;int t=d-1-da[a];if(t>=row[a]+minadd&&t<=row[a]+maxadd){aposs[d-11]++;poss++;last=d-11;}}if(!poss)return false;if(poss==1)aforce[last]++;}
  int bforce[4]={},bposs[4]={};
  for(int b=0;b<MB;b++)if(unmask>>b&1){int poss=0,last=-1;for(int d=0;d<4;d++)if(intersects(dom[b],classMask[b][d])){bposs[d]++;poss++;last=d;}if(!poss)return false;if(poss==1)bforce[last]++;}
  for(int d=0;d<4;d++){int need=seq[d]-(d==0?1:0)-bcnt[d];if(need<0)return false;if(aforce[d]+bforce[d]>need)return false;if(aposs[d]+bposs[d]<need)return false;}
  return true;
 }
 bool rec(Bits dom[MB],uint32_t unmask,const vector<int>&stab){
  nodes++; if((nodes&0x3fff)==0 && chrono::duration<double>(chrono::steady_clock::now().time_since_epoch()).count()>deadline){timed=true;return false;}
  int depth=MB-__builtin_popcount(unmask);bestDepth=max(bestDepth,depth);
  for(int b=0;b<MB;b++)if(unmask>>b&1){for(int d=0;d<4;d++){int lim=seq[d]-(d==0?1:0);if(bcnt[d]>=lim){Bits inv=classMask[b][d];for(int q=0;q<W;q++)dom[b].x[q]&=~inv.x[q];}}if(emptyB(dom[b]))return false;}
  if(!globalPrune(dom,unmask))return false;
  if(!unmask){if(cross!=66)return false;int ac[4]={};for(int a=0;a<MA;a++){int d=1+da[a]+row[a];if(d<11||d>14)return false;ac[d-11]++;}for(int d=0;d<4;d++)if(ac[d]+bcnt[d]+(d==0?1:0)!=seq[d])return false;solution.assign(asg,asg+MB);return true;}
  int b=-1,bc=1e9;for(int i=0;i<MB;i++)if(unmask>>i&1){int c=countB(dom[i]);if(c<bc){bc=c;b=i;}}
  auto vals=elems(dom[b]); vector<int> reps; reps.reserve(vals.size());
  for(int m:vals){int mn=m;for(int gi:stab)mn=min(mn,tmask(m,autos[gi]));if(m==mn)reps.push_back(m);}
  uint32_t newmask=unmask&~(1u<<b);
  for(int m:reps){int cls=db[b]+__builtin_popcount((unsigned)m)-11;if(cls<0||cls>=4)continue;int lim=seq[cls]-(cls==0?1:0);if(bcnt[cls]>=lim)continue;
    bool rowok=true;for(int a=0;a<MA;a++)if(m>>a&1){int maxT=-1;for(int d=11;d<=14;d++)if(seq[d-11])maxT=max(maxT,d-1-da[a]);if(row[a]+1>maxT){rowok=false;break;}}if(!rowok)continue;
    Bits nd[MB];memcpy(nd,dom,sizeof nd); bool ok=true;
    for(int c=0;c<MB;c++)if(newmask>>c&1){andeq(nd[c],bedge[b][c]?edgeCompat[m]:nonCompat[m]);if(emptyB(nd[c])){ok=false;break;}}
    if(!ok)continue;asg[b]=m;bcnt[cls]++;cross+=__builtin_popcount((unsigned)m);for(int a=0;a<MA;a++)if(m>>a&1)row[a]++;
    vector<int> nstab; nstab.reserve(stab.size());for(int gi:stab)if(tmask(m,autos[gi])==m)nstab.push_back(gi);
    if(restrictHyper(nd,b,newmask) && rec(nd,newmask,nstab))return true;
    for(int a=0;a<MA;a++)if(m>>a&1)row[a]--;cross-=__builtin_popcount((unsigned)m);bcnt[cls]--;asg[b]=-1;if(timed)return false;
  }
  return false;
 }
 string run(double sec){Bits d[MB];memcpy(d,initDom,sizeof d);deadline=chrono::duration<double>(chrono::steady_clock::now().time_since_epoch()).count()+sec;vector<int> stab(autos.size());iota(stab.begin(),stab.end(),0);bool sat=rec(d,(1u<<MB)-1,stab);if(sat)return"SAT";if(timed)return"TIMEOUT";return"UNSAT";}
};
static int ecount(const vector<uint32_t>&g){long long s=0;for(auto x:g)s+=__builtin_popcount(x);return int(s/2);}
static bool isIndependent(const vector<string>&r,const vector<int>&v){for(int i=0;i<(int)v.size();i++)for(int j=i+1;j<(int)v.size();j++)if(r[v[i]][v[j]]!='0')return false;return true;}
static vector<string> reconstruct(const SolverCSP&sp,const array<int,4>&sq){
 vector<string> r(36,string(36,'0'));
 for(int a=0;a<MA;a++)r[0][1+a]=r[1+a][0]='1';
 for(int i=0;i<MA;i++)for(int j=i+1;j<MA;j++)if((sp.A[i]>>j)&1)r[1+i][1+j]=r[1+j][1+i]='1';
 for(int i=0;i<MB;i++)for(int j=i+1;j<MB;j++)if((sp.B[i]>>j)&1)r[12+i][12+j]=r[12+j][12+i]='1';
 for(int b=0;b<MB;b++)for(int a=0;a<MA;a++)if((sp.solution[b]>>a)&1)r[1+a][12+b]=r[12+b][1+a]='1';
 array<int,4> got{};for(auto&s:r){int d=count(s.begin(),s.end(),'1');if(d<11||d>14)throw runtime_error("degree outside selected r3 classes");got[d-11]++;}if(got!=sq)throw runtime_error("degree sequence mismatch");
 for(int a=0;a<36;a++)for(int b=a+1;b<36;b++)for(int c=b+1;c<36;c++)for(int d=c+1;d<36;d++){int v[4]={a,b,c,d};bool bad=true;for(int i=0;i<4&&bad;i++)for(int j=i+1;j<4;j++)if(r[v[i]][v[j]]!='1'){bad=false;break;}if(bad)throw runtime_error("K4 in reconstructed candidate");}
 vector<int> v(6); for(v[0]=0;v[0]<31;v[0]++)for(v[1]=v[0]+1;v[1]<32;v[1]++)for(v[2]=v[1]+1;v[2]<33;v[2]++)for(v[3]=v[2]+1;v[3]<34;v[3]++)for(v[4]=v[3]+1;v[4]<35;v[4]++)for(v[5]=v[4]+1;v[5]<36;v[5]++)if(isIndependent(r,v))throw runtime_error("independent 6 in reconstructed candidate");
 return r;
}
int main(int argc,char**argv){
 vector<string> As={"JiQC@{}N`{?","JqPA@{}N`{?"};
 vector<string> Bs={"W?jIhu?OG_cD`ZIfAnQTiyJIp[UhiJdsQU_seQobWKbkYLE","WkGjGVA_SdqKItLBGiIoSFPNoRsxd@eoOEsZQXWoXQjkF~?","WoCJ?j?@XDBBmGr@shMaHUgKrRiMU`[cuh{PbnIBb{CIvg_","WoCJ?j?GgJBBmGsPx_dIbUgKrIh[UqMfIM{Wi^Obb{AIvc_","WoCOZBSmLKXOLQUPDWAM@oE]_fgLlGgysWetAeuhBqigLtT","Wt@IXqOg?W`SCYGTGQqHQjH]YZfDMmg|?jYwF\\SAfYaKnSA","Wt@IXqOg?W`SCYGTGQqHQjH]YZnDMeg|?jYqF\\SAfYaKnSA","Wt@IXqOg?W`SCYGTGQqHQjH]YZnDMeg|?jYqF\\SQfY_KnS@","Wv?IXZ?gGT?kAU@dE@a_FiZZIVUIfdLXgtZOTjg`teoJNcC"};
 vector<array<int,4>> S={{{7,17,11,1}},{{7,18,9,2}},{{8,15,12,1}},{{9,12,15,0}},{{9,13,13,1}},{{10,10,16,0}},{{11,8,17,0}},{{12,6,18,0}}};
 if(argc==2 && string(argv[1])=="--self-test"){
   for(auto&s:As){auto g=decodeg6(s);if((int)g.size()!=11||ecount(g)!=26||!subsetMasks(g,3,true).empty()||!subsetMasks(g,6,false).empty())return 2;}
   for(auto&s:Bs){auto g=decodeg6(s);if((int)g.size()!=24||ecount(g)!=116||!subsetMasks(g,4,true).empty()||!subsetMasks(g,5,false).empty())return 3;}
   SolverCSP x(As[0],Bs[4],S[0]),y(As[1],Bs[4],S[0]);if(x.autos.size()!=288||y.autos.size()!=1152)return 4;
   cerr<<"self-test ok: A26=2 B116=9 Aut(A)={288,1152}\n";return 0;
 }
 if(argc<5){cerr<<"usage: m219_r3_column_csp A_ORD B_ORD SEQ_ORD SECONDS [CANDIDATE_JSON]\n";return 64;}
 int ai=atoi(argv[1]),bi=atoi(argv[2]),si=atoi(argv[3]);double sec=atof(argv[4]);if(ai<0||ai>=2||bi<0||bi>=9||si<0||si>=8||sec<=0)return 64;
 auto t=chrono::steady_clock::now();SolverCSP sp(As[ai],Bs[bi],S[si]);string st=sp.run(sec);double elapsed=chrono::duration<double>(chrono::steady_clock::now()-t).count();
 cerr<<"{\"a\":"<<ai<<",\"b\":"<<bi<<",\"seq\":"<<si<<",\"status\":\""<<st<<"\",\"nodes\":"<<sp.nodes<<",\"depth\":"<<sp.bestDepth<<",\"autA\":"<<sp.autos.size()<<",\"seconds\":"<<elapsed<<"}\n";
 if(st=="SAT"){
   auto rows=reconstruct(sp,S[si]);if(argc>=6){ofstream f(argv[5]);f<<"{\"adjacency\":[";for(int i=0;i<36;i++){if(i)f<<',';f<<'\"'<<rows[i]<<'\"';}f<<"]}\n";}
   return 10;
 }
 return st=="UNSAT"?20:124;
}
