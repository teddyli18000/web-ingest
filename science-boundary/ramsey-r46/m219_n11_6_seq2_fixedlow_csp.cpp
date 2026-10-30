#include <bits/stdc++.h>
#include <omp.h>
using namespace std;
static const int MA=11, MB=24, NM=1<<MA, W=32;
struct Bits{uint64_t x[W];};
static inline void clr(Bits&b){memset(b.x,0,sizeof b.x);} static inline void setb(Bits&b,int i){b.x[i>>6]|=1ULL<<(i&63);} 
static inline bool emp(const Bits&b){for(auto z:b.x)if(z)return false;return true;} static inline int cnt(const Bits&b){int s=0;for(auto z:b.x)s+=__builtin_popcountll(z);return s;}
static inline void band(Bits&a,const Bits&b){for(int i=0;i<W;i++)a.x[i]&=b.x[i];} static inline bool ints(const Bits&a,const Bits&b){for(int i=0;i<W;i++)if(a.x[i]&b.x[i])return true;return false;}
static inline bool subeq(const Bits&a,const Bits&b){for(int i=0;i<W;i++)if(a.x[i]&~b.x[i])return false;return true;} static inline void bminus(Bits&a,const Bits&b){for(int i=0;i<W;i++)a.x[i]&=~b.x[i];}
static inline vector<int> elems(const Bits&b){vector<int>v;for(int q=0;q<W;q++){uint64_t z=b.x[q];while(z){int r=__builtin_ctzll(z);v.push_back(q*64+r);z&=z-1;}}return v;}
vector<uint32_t> g6(const string&s){int n=(unsigned char)s[0]-63;vector<int>bits;for(size_t z=1;z<s.size();z++){int v=(unsigned char)s[z]-63;for(int k=5;k>=0;k--)bits.push_back((v>>k)&1);}vector<uint32_t>a(n);int p=0;for(int j=1;j<n;j++)for(int i=0;i<j;i++){if(bits[p]){a[i]|=1u<<j;a[j]|=1u<<i;}p++;}return a;}
vector<int> subsets(const vector<uint32_t>&a,int k,bool clique){int n=a.size();vector<int>o;for(int m=0;m<(1<<n);m++)if(__builtin_popcount((unsigned)m)==k){bool ok=1;for(int i=0;i<n&&ok;i++)if(m>>i&1)for(int j=i+1;j<n;j++)if(m>>j&1){if(bool((a[i]>>j)&1)!=clique){ok=0;break;}}if(ok)o.push_back(m);}return o;}
bool hits(int m,const vector<int>&ss){for(int s:ss)if(!(m&s))return false;return true;} bool indep(const vector<uint32_t>&A,int m){for(int i=0;i<MA;i++)if(m>>i&1)if(A[i]&m)return false;return true;}
struct Hyper{int typ;array<int,4>v;int n;};
struct Base{
 vector<uint32_t>A,B; int da[MA],db[MB]; vector<int>I2,I3,I4,I5; Bits contains[MA], edgeC[NM], nonC[NM], avoidI[NM], hit3[NM],hit2[NM], classM[MB][4];
 bool bedge[MB][MB]{}; vector<Hyper> hy; vector<int> hyBy[MB]; vector<array<int,MA>> autos;
 Base(string as,string bs){A=g6(as);B=g6(bs);for(int i=0;i<MA;i++)da[i]=__builtin_popcount(A[i]);for(int i=0;i<MB;i++)db[i]=__builtin_popcount(B[i]);
  I2=subsets(A,2,false);I3=subsets(A,3,false);I4=subsets(A,4,false);I5=subsets(A,5,false);for(int a=0;a<MA;a++)clr(contains[a]);for(int m=0;m<NM;m++)for(int a=0;a<MA;a++)if(m>>a&1)setb(contains[a],m);
  for(int m=0;m<NM;m++){clr(edgeC[m]);clr(nonC[m]);clr(avoidI[m]);clr(hit3[m]);clr(hit2[m]);for(int n=0;n<NM;n++){if(indep(A,m&n))setb(edgeC[m],n);if(hits(m|n,I4))setb(nonC[m],n);if((m&n)==0)setb(avoidI[m],n);if(hits(m|n,I3))setb(hit3[m],n);if(hits(m|n,I2))setb(hit2[m],n);}}
  for(int i=0;i<MB;i++)for(int j=i+1;j<MB;j++)bedge[i][j]=bedge[j][i]=((B[i]>>j)&1);
  auto add=[&](int typ,int mask,int n){Hyper h{};h.typ=typ;h.n=0;for(int i=0;i<MB;i++)if(mask>>i&1)h.v[h.n++]=i;int id=hy.size();hy.push_back(h);for(int k=0;k<h.n;k++)hyBy[h.v[k]].push_back(id);};
  for(int m:subsets(B,3,true))add(0,m,3);for(int m:subsets(B,3,false))add(1,m,3);for(int m:subsets(B,4,false))add(2,m,4);
  for(int b=0;b<MB;b++)for(int c=0;c<4;c++){clr(classM[b][c]);int d=11+c,k=d-db[b];if(k<0||k>11)continue;for(int m=0;m<NM;m++)if(__builtin_popcount((unsigned)m)==k&&hits(m,I5))setb(classM[b][c],m);}
  genAutos();
 }
 void genAutos(){array<int,MA>p;p.fill(-1);bool used[MA]={};function<void(int)>dfs=[&](int pos){if(pos==MA){autos.push_back(p);return;}int v=-1,best=99;for(int i=0;i<MA;i++)if(p[i]<0){int c=0;for(int j=0;j<MA;j++)if(!used[j]&&da[j]==da[i]){bool ok=1;for(int u=0;u<MA;u++)if(p[u]>=0&&bool((A[i]>>u)&1)!=bool((A[j]>>p[u])&1)){ok=0;break;}if(ok)c++;}if(c<best){best=c;v=i;}}for(int j=0;j<MA;j++)if(!used[j]&&da[j]==da[v]){bool ok=1;for(int u=0;u<MA;u++)if(p[u]>=0&&bool((A[v]>>u)&1)!=bool((A[j]>>p[u])&1)){ok=0;break;}if(!ok)continue;p[v]=j;used[j]=1;dfs(pos+1);used[j]=0;p[v]=-1;}};dfs(0);}
 int tm(int m,const array<int,MA>&p)const{int z=0;for(int i=0;i<MA;i++)if(m>>i&1)z|=1<<p[i];return z;}
};
struct Branch{int typ,anchor,ai,bi;array<int,3>Tlow,Amap;array<int,2>Ulow,Bmap;};
struct Solver{
 const Base&Q; Branch br; vector<uint32_t> Lg; int seq[4],need[4],target[MA],asg[MB],row[MA],bc[4]; Bits init[MB]; vector<int> stab0; long long nodes=0;int depth=0;double deadline;bool timed=false;vector<int>sol;
 Solver(const Base&q,const Branch&b,const vector<uint32_t>&L):Q(q),br(b),Lg(L){int S[4]={6,20,8,2};for(int c=0;c<4;c++)seq[c]=S[c];need[0]=2;need[1]=12;need[2]=8;need[3]=2;
  bool lowA[MA]={};for(int i=0;i<3;i++)lowA[b.Amap[i]]=1;for(int a=0;a<MA;a++)target[a]=(lowA[a]?10:11)-Q.da[a];fill(asg,asg+MB,-1);fill(row,row+MA,0);fill(bc,bc+4,0);
  int lowb[MB];fill(lowb,lowb+MB,-1);for(int j=0;j<2;j++)lowb[b.Bmap[j]]=j;
  for(int x=0;x<MB;x++){clr(init[x]);if(lowb[x]>=0){init[x]=Q.classM[x][0];int uj=lowb[x];for(int ti=0;ti<3;ti++){int a=b.Amap[ti];bool e=(L[b.Tlow[ti]]>>b.Ulow[uj])&1;if(e)band(init[x],Q.contains[a]);else bminus(init[x],Q.contains[a]);}}
    else for(int c=1;c<4;c++)if(need[c])for(int w=0;w<W;w++)init[x].x[w]|=Q.classM[x][c].x[w];}
  for(int ti=0;ti<3;ti++){int a=b.Amap[ti],cap=__builtin_popcount(L[b.Tlow[ti]])-3;for(int x=0;x<MB;x++)for(int c=2;c<4;c++){int wt=c-1;if(wt>cap)for(int q=0;q<W;q++)init[x].x[q]&=~(Q.classM[x][c].x[q]&Q.contains[a].x[q]);}}
  for(int uj=0;uj<2;uj++){int u=b.Bmap[uj],cap=__builtin_popcount(L[b.Ulow[uj]])-3;for(int x=0;x<MB;x++)if((Q.B[u]>>x)&1)for(int c=2;c<4;c++)if(c-1>cap)bminus(init[x],Q.classM[x][c]);}
  for(int gi=0;gi<(int)Q.autos.size();gi++){bool ok=1;for(int i=0;i<3;i++)if(Q.autos[gi][b.Amap[i]]!=b.Amap[i]){ok=0;break;}if(ok)stab0.push_back(gi);} }
 bool hyp(Bits d[MB],int ch,uint32_t um){for(int id:Q.hyBy[ch]){auto &h=Q.hy[id];int rem=-1,nr=0,inter=(1<<MA)-1,uni=0;for(int k=0;k<h.n;k++){int v=h.v[k];if(um>>v&1){rem=v;nr++;}else{int m=asg[v];inter&=m;uni|=m;}}if(nr==0){bool ok=h.typ==0?inter==0:(h.typ==1?hits(uni,Q.I3):hits(uni,Q.I2));if(!ok)return false;}else if(nr==1){if(h.typ==0)band(d[rem],Q.avoidI[inter]);else if(h.typ==1)band(d[rem],Q.hit3[uni]);else band(d[rem],Q.hit2[uni]);if(emp(d[rem]))return false;}}return true;}
 int clsOf(int b,int m){return Q.db[b]+__builtin_popcount((unsigned)m)-11;}
 int weightClass(int c){return c<=1?0:c-1;}
 bool lowDynamic(Bits d[MB],uint32_t um,bool &changed){
  for(int ti=0;ti<3;ti++){int a=br.Amap[ti],cap=__builtin_popcount(Lg[br.Tlow[ti]])-3,cur=0;for(int x=0;x<MB;x++)if(!(um>>x&1)&&asg[x]>=0&&((asg[x]>>a)&1))cur+=weightClass(clsOf(x,asg[x]));if(cur>cap)return false;int rem=cap-cur;for(int x=0;x<MB;x++)if(um>>x&1)for(int c=2;c<4;c++)if(weightClass(c)>rem){int before=cnt(d[x]);for(int q=0;q<W;q++)d[x].x[q]&=~(Q.classM[x][c].x[q]&Q.contains[a].x[q]);if(emp(d[x]))return false;if(cnt(d[x])!=before)changed=true;}}
  for(int uj=0;uj<2;uj++){int u=br.Bmap[uj],cap=__builtin_popcount(Lg[br.Ulow[uj]])-3,cur=0;for(int x=0;x<MB;x++)if((Q.B[u]>>x)&1&&!(um>>x&1)&&asg[x]>=0)cur+=weightClass(clsOf(x,asg[x]));if(cur>cap)return false;int rem=cap-cur;for(int x=0;x<MB;x++)if((um>>x&1)&&((Q.B[u]>>x)&1))for(int c=2;c<4;c++)if(weightClass(c)>rem){int before=cnt(d[x]);bminus(d[x],Q.classM[x][c]);if(emp(d[x]))return false;if(cnt(d[x])!=before)changed=true;}}
  return true;}
 bool lowFinal(){int r3=1;for(int ti=0;ti<3;ti++){int a=br.Amap[ti],cap=__builtin_popcount(Lg[br.Tlow[ti]])-3,w=0;for(int x=0;x<MB;x++)if((asg[x]>>a)&1)w+=weightClass(clsOf(x,asg[x]));if(w>cap)return false;if(w==cap)r3++;}for(int uj=0;uj<2;uj++){int u=br.Bmap[uj],cap=__builtin_popcount(Lg[br.Ulow[uj]])-3,w=0;for(int x=0;x<MB;x++)if((Q.B[u]>>x)&1)w+=weightClass(clsOf(x,asg[x]));if(w>cap)return false;if(w==cap)r3++;}return r3>=4;}
 bool propagate(Bits d[MB],uint32_t um){bool changed=true;while(changed){changed=false;
   for(int c=0;c<4;c++){int forced=0,poss=0;vector<int>opt;for(int b=0;b<MB;b++)if(um>>b&1){bool has=ints(d[b],Q.classM[b][c]);if(!has)continue;poss++;Bits tmp=d[b];bminus(tmp,Q.classM[b][c]);if(emp(tmp))forced++;else opt.push_back(b);}int rem=need[c]-bc[c];if(rem<forced||rem>poss)return false;if(rem==forced){for(int b:opt){int before=cnt(d[b]);bminus(d[b],Q.classM[b][c]);if(emp(d[b]))return false;if(cnt(d[b])!=before)changed=true;}}else if(rem==poss){for(int b:opt){int before=cnt(d[b]);band(d[b],Q.classM[b][c]);if(emp(d[b]))return false;if(cnt(d[b])!=before)changed=true;}}}
   for(int a=0;a<MA;a++){int mn=0,mx=0;vector<int>opt;for(int b=0;b<MB;b++)if(um>>b&1){bool any=ints(d[b],Q.contains[a]);Bits tmp=d[b];bminus(tmp,Q.contains[a]);bool all=emp(tmp);if(all)mn++;if(any)mx++;if(any&&!all)opt.push_back(b);}int rem=target[a]-row[a];if(rem<mn||rem>mx)return false;if(rem==mn){for(int b:opt){int before=cnt(d[b]);bminus(d[b],Q.contains[a]);if(emp(d[b]))return false;if(cnt(d[b])!=before)changed=true;}}else if(rem==mx){for(int b:opt){int before=cnt(d[b]);band(d[b],Q.contains[a]);if(emp(d[b]))return false;if(cnt(d[b])!=before)changed=true;}}}
   if(!lowDynamic(d,um,changed))return false;
  }return true;}
 bool rec(Bits d[MB],uint32_t um,const vector<int>&stab){nodes++;if((nodes&0x3ff)==0&&omp_get_wtime()>deadline){timed=true;return false;}depth=max(depth,MB-__builtin_popcount(um));if(!propagate(d,um))return false;if(!um){for(int a=0;a<MA;a++)if(row[a]!=target[a])return false;for(int c=0;c<4;c++)if(bc[c]!=need[c])return false;if(!lowFinal())return false;sol.assign(asg,asg+MB);return true;}
  int b=-1,cc=INT_MAX;for(int i=0;i<MB;i++)if(um>>i&1){int z=cnt(d[i]);if(z<cc){cc=z;b=i;}}auto vs=elems(d[b]);vector<int>reps;for(int m:vs){int mn=m;for(int gi:stab)mn=min(mn,Q.tm(m,Q.autos[gi]));if(m==mn)reps.push_back(m);}uint32_t nm=um&~(1u<<b);
  for(int m:reps){int c=clsOf(b,m);if(c<0||c>=4||bc[c]>=need[c])continue;bool ok=1;for(int a=0;a<MA;a++)if((m>>a&1)&&row[a]>=target[a]){ok=0;break;}if(!ok)continue;Bits nd[MB];memcpy(nd,d,sizeof nd);for(int j=0;j<MB;j++)if(nm>>j&1){band(nd[j],Q.bedge[b][j]?Q.edgeC[m]:Q.nonC[m]);if(emp(nd[j])){ok=0;break;}}if(!ok)continue;asg[b]=m;bc[c]++;for(int a=0;a<MA;a++)if(m>>a&1)row[a]++;vector<int>ns;for(int gi:stab)if(Q.tm(m,Q.autos[gi])==m)ns.push_back(gi);if(hyp(nd,b,nm)&&rec(nd,nm,ns))return true;for(int a=0;a<MA;a++)if(m>>a&1)row[a]--;bc[c]--;asg[b]=-1;if(timed)return false;}
  return false;}
 string run(double sec){Bits d[MB];memcpy(d,init,sizeof d);for(int b=0;b<MB;b++)if(emp(d[b]))return"UNSAT";deadline=omp_get_wtime()+sec;bool s=rec(d,(1u<<MB)-1,stab0);if(s)return"SAT";return timed?"TIMEOUT":"UNSAT";}
};
vector<uint32_t> Lfrom(const vector<string>&r){vector<uint32_t>g(6);for(int i=0;i<6;i++)for(int j=0;j<6;j++)if(r[i][j]=='1')g[i]|=1u<<j;return g;}
bool samePat(const vector<uint32_t>&A,array<int,3>p,const vector<uint32_t>&L,array<int,3>t){for(int i=0;i<3;i++)for(int j=i+1;j<3;j++)if(bool((A[p[i]]>>p[j])&1)!=bool((L[t[i]]>>t[j])&1))return false;return true;}
int main(int argc,char**argv){double sec=argc>1?atof(argv[1]):0.2;int threads=argc>2?atoi(argv[2]):5;set<int>only;if(argc>3){ifstream f(argv[3]);int z;while(f>>z)only.insert(z);}
 vector<string>As={"JiQC@{}N`{?","JqPA@{}N`{?"};
 vector<string>Bs={"W?jIhu?OG_cD`ZIfAnQTiyJIp[UhiJdsQU_seQobWKbkYLE","WkGjGVA_SdqKItLBGiIoSFPNoRsxd@eoOEsZQXWoXQjkF~?","WoCJ?j?@XDBBmGr@shMaHUgKrRiMU`[cuh{PbnIBb{CIvg_","WoCJ?j?GgJBBmGsPx_dIbUgKrIh[UqMfIM{Wi^Obb{AIvc_","WoCOZBSmLKXOLQUPDWAM@oE]_fgLlGgysWetAeuhBqigLtT","Wt@IXqOg?W`SCYGTGQqHQjH]YZfDMmg|?jYwF\\SAfYaKnSA","Wt@IXqOg?W`SCYGTGQqHQjH]YZnDMeg|?jYqF\\SAfYaKnSA","Wt@IXqOg?W`SCYGTGQqHQjH]YZnDMeg|?jYqF\\SQfY_KnS@","Wv?IXZ?gGT?kAU@dE@a_FiZZIVUIfdLXgtZOTjg`teoJNcC"};
 vector<int>BI={0,1,5,6,7,8};map<int,vector<array<int,2>>>OP={
  {0,{{0,5},{5,0},{1,6},{6,1},{2,4},{4,2},{3,7},{7,3}}},{1,{{0,3},{3,0},{4,5},{5,4}}},
  {5,{{0,2},{2,0},{0,3},{3,0},{1,5},{5,1},{1,6},{6,1},{2,7},{7,2},{3,7},{7,3},{4,5},{5,4},{4,6},{6,4}}},
  {6,{{0,2},{2,0},{0,3},{3,0},{1,5},{5,1},{1,6},{6,1},{2,7},{7,2},{3,7},{7,3},{4,5},{5,4},{4,6},{6,4}}},
  {7,{{0,2},{2,0},{0,3},{3,0},{1,5},{5,1},{1,6},{6,1},{2,7},{7,2},{3,7},{7,3},{4,5},{5,4},{4,6},{6,4}}},
  {8,{{0,1},{1,0},{0,2},{2,0},{1,3},{3,1},{2,3},{3,2},{4,6},{6,4},{4,7},{7,4},{5,6},{6,5},{5,7},{7,5}}}};
 vector<vector<unique_ptr<Base>>>Q(2);for(int ai=0;ai<2;ai++)for(int bi:BI)Q[ai].push_back(make_unique<Base>(As[ai],Bs[bi]));auto qptr=[&](int ai,int bi)->Base*{auto it=find(BI.begin(),BI.end(),bi);return Q[ai][it-BI.begin()].get();};
 map<int,vector<string>>RR={{3,{"001110","001101","110011","110011","101101","011110"}},{4,{"011001","100101","100011","010011","001101","111110"}},{5,{"011010","100101","100011","010011","101101","011110"}},{6,{"011100","101100","110011","110011","001101","001110"}},{7,{"011100","101010","110001","100011","010101","001110"}}};map<int,vector<int>>AR={{3,{0}},{4,{0}},{5,{0,2}},{6,{0}},{7,{0}}};vector<Branch>brs;
 for(auto&kv:RR){int typ=kv.first;auto L=Lfrom(kv.second);for(int av:AR[typ]){array<int,3>T{};array<int,2>U{};int ti=0,ui=0;for(int x=0;x<6;x++)if(x!=av){if((L[av]>>x)&1)T[ti++]=x;else U[ui++]=x;}for(int ai=0;ai<2;ai++){auto&QA=*qptr(ai,0);for(int a=0;a<MA;a++)for(int b=0;b<MA;b++)if(b!=a)for(int c=0;c<MA;c++)if(c!=a&&c!=b){array<int,3>p{a,b,c};if(!samePat(QA.A,p,L,T))continue;bool canon=1;for(auto&au:QA.autos){array<int,3>z{au[a],au[b],au[c]};if(z<p){canon=0;break;}}if(!canon)continue;for(int bi:BI)for(auto bp:OP[bi]){Branch x{};x.typ=typ;x.anchor=av;x.ai=ai;x.bi=bi;x.Tlow=T;x.Ulow=U;x.Amap=p;x.Bmap=bp;brs.push_back(x);}}}}}
 cerr<<"branches="<<brs.size()<<" ordered_pairs=76 threads="<<threads<<" sec="<<sec<<"\n";vector<string>st(brs.size());vector<long long>nn(brs.size());vector<int>dd(brs.size()),ssz(brs.size());double t0=omp_get_wtime();omp_set_num_threads(threads);
 #pragma omp parallel for schedule(dynamic,1)
 for(int i=0;i<(int)brs.size();i++){if(!only.empty()&&!only.count(i)){st[i]="SKIP";continue;}auto&b=brs[i];auto L=Lfrom(RR[b.typ]);Solver z(*qptr(b.ai,b.bi),b,L);ssz[i]=z.stab0.size();st[i]=z.run(sec);nn[i]=z.nodes;dd[i]=z.depth;}
 map<string,int>C;long long nodes=0;for(auto&s:st)C[s]++;for(auto n:nn)nodes+=n;cerr<<"elapsed="<<(omp_get_wtime()-t0)<<" nodes="<<nodes;for(auto&x:C)cerr<<" "<<x.first<<"="<<x.second;cerr<<"\n";for(int i=0;i<(int)brs.size();i++)if(st[i]!="UNSAT"&&st[i]!="SKIP")cout<<i<<" typ="<<brs[i].typ<<" a="<<brs[i].ai<<" b="<<brs[i].bi<<" anchor="<<brs[i].anchor<<" T="<<brs[i].Amap[0]<<","<<brs[i].Amap[1]<<","<<brs[i].Amap[2]<<" Bpair="<<brs[i].Bmap[0]<<","<<brs[i].Bmap[1]<<" stab="<<ssz[i]<<" st="<<st[i]<<" nodes="<<nn[i]<<" depth="<<dd[i]<<"\n";return C["SAT"]?10:(C["TIMEOUT"]?124:20);
}
