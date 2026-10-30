// Exact W127 order-25 ka=16,kc=10 search using GF2 kernel + integer MITM.
// Writes every projected survivor to ka16_survivors.txt for independent lifting.
#include <bits/stdc++.h>
#include <omp.h>
using namespace std;static const int N=25,R=13,HS=8192;static const uint32_t FULL=(1u<<25)-1;
struct Perm{array<uint8_t,N>p;};struct CRep{int sid;uint32_t plus;};struct N3{uint8_t a,b,c;uint32_t mask;};
vector<Perm>perms;vector<uint32_t>supports;vector<vector<int>>stabs;vector<vector<uint32_t>>zlists;vector<CRep>creps;vector<N3>n3s;
struct Surv{array<int8_t,N> p,c; uint32_t z,n; size_t ci;}; vector<Surv> survivors; mutex surv_mu;
uint32_t tr(uint32_t m,const Perm&p){uint32_t o=0;while(m){int i=__builtin_ctz(m);m&=m-1;o|=1u<<p.p[i];}return o;}
vector<uint32_t> nullw(uint32_t S){vector<uint32_t>rows;for(int r=1;r<=12;r++){uint32_t row=0;for(int j=0;j<N;j++)if(((S>>((j-r+N)%N))&1)^((S>>((j+r)%N))&1))row|=1u<<j;rows.push_back(row);}int rr=0;vector<int>piv;for(int c=0;c<N&&rr<12;c++){int k=rr;while(k<12&&!((rows[k]>>c)&1))k++;if(k==12)continue;swap(rows[k],rows[rr]);for(int i=0;i<12;i++)if(i!=rr&&((rows[i]>>c)&1))rows[i]^=rows[rr];piv.push_back(c);rr++;}vector<char>ip(N);for(int x:piv)ip[x]=1;vector<uint32_t>b;for(int f=0;f<N;f++)if(!ip[f]){uint32_t v=1u<<f;for(int i=0;i<rr;i++)if((rows[i]>>f)&1)v|=1u<<piv[i];b.push_back(v);}vector<uint32_t>a{0};for(auto x:b){size_t q=a.size();for(size_t i=0;i<q;i++)a.push_back(a[i]^x);}vector<uint32_t>out;for(auto v:a)if(__builtin_popcount(v)==9)out.push_back(v);return out;}
void build(){for(int a=1;a<N;a++)if(gcd(a,N)==1)for(int b=0;b<N;b++){Perm p;for(int i=0;i<N;i++)p.p[i]=(a*i+b)%N;perms.push_back(p);}vector<uint8_t>vis(1u<<25);long long raw=0;for(uint32_t S=0;S<(1u<<25);S++){if(__builtin_popcount(S)!=10)continue;raw++;if(vis[S])continue;int sid=supports.size();supports.push_back(S);for(auto&pm:perms)vis[tr(S,pm)]=1;vector<int>stab;for(int i=0;i<500;i++)if(tr(S,perms[i])==S)stab.push_back(i);stabs.push_back(stab);zlists.push_back(nullw(S));vector<int>idx;for(int i=0;i<N;i++)if(S>>i&1)idx.push_back(i);unordered_set<uint32_t>seen;for(int a=0;a<10;a++)for(int b=a+1;b<10;b++)for(int c=b+1;c<10;c++)for(int d=c+1;d<10;d++)for(int e=d+1;e<10;e++){uint32_t P=(1u<<idx[a])|(1u<<idx[b])|(1u<<idx[c])|(1u<<idx[d])|(1u<<idx[e]);if(seen.count(P))continue;creps.push_back({sid,P});uint32_t M=S^P;for(int pi:stab){auto pp=tr(P,perms[pi]),mm=tr(M,perms[pi]);seen.insert(pp);seen.insert(mm);}}if(seen.size()!=252){cerr<<"sign coverage fail\n";abort();}}
 if(raw!=3268760||supports.size()!=6578||creps.size()!=824362){cerr<<"coverage mismatch raw="<<raw<<" supports="<<supports.size()<<" creps="<<creps.size()<<"\n";abort();}for(int a=0;a<N;a++)for(int b=a+1;b<N;b++)for(int c=b+1;c<N;c++)n3s.push_back({(uint8_t)a,(uint8_t)b,(uint8_t)c,(1u<<a)|(1u<<b)|(1u<<c)});if(n3s.size()!=2300)abort();cerr<<"supports="<<supports.size()<<" c_reps="<<creps.size()<<"\n";}
static inline uint64_t mix64(uint64_t x){x^=x>>30;x*=0xbf58476d1ce4e5b9ULL;x^=x>>27;x*=0x94d049bb133111ebULL;x^=x>>31;return x;}
struct Tab{array<int,HS>head,stamp;array<uint64_t,2300>key;array<uint32_t,2300>mask;array<int,2300>next;int gen=1;Tab(){stamp.fill(0);}void reset(){if(++gen==INT_MAX){stamp.fill(0);gen=1;}}void add(int i,uint64_t k,uint32_t m){int b=mix64(k)&(HS-1);if(stamp[b]!=gen){stamp[b]=gen;head[b]=-1;}key[i]=k;mask[i]=m;next[i]=head[b];head[b]=i;}int first(uint64_t k){int b=mix64(k)&(HS-1);return stamp[b]==gen?head[b]:-1;}};
static int spaf(uint32_t S,uint32_t neg,int r){uint32_t Sr=((S<<r)|(S>>(25-r)))&FULL,nr=((neg<<r)|(neg>>(25-r)))&FULL;int e=__builtin_popcount(S&Sr),xo=__builtin_popcount((S&Sr)&(neg^nr));return e-2*xo;}
int main(){build();array<int64_t,R>pw{};pw[0]=1;for(int r=1;r<R;r++)pw[r]=pw[r-1]*19;int64_t sw=0;for(auto x:pw)sw+=x;const int64_t OFF=9*sw;atomic<long long>cross{0},target{0},done{0};double t0=omp_get_wtime();
#pragma omp parallel
 {Tab tab;
#pragma omp for schedule(dynamic,32)
 for(size_t ci=0;ci<creps.size();ci++){int sid=creps[ci].sid;uint32_t S=supports[sid],plus=creps[ci].plus,cneg=S^plus;array<int8_t,N>c{};for(int i=0;i<N;i++)if(S>>i&1)c[i]=(cneg>>i&1)?-1:1;array<array<int8_t,R>,N>col{};array<int64_t,N>lc{};for(int j=0;j<N;j++){int64_t L=0;for(int r=0;r<R;r++){int v=c[(j-r+N)%N]+c[(j+r)%N];col[j][r]=v;L+=v*pw[r];}lc[j]=L;}int cpaf[13]{};for(int r=1;r<=12;r++)cpaf[r]=spaf(S,cneg,r);
   tab.reset();int ii=0;for(auto&q:n3s){int64_t L=lc[q.a]+lc[q.b]+lc[q.c];tab.add(ii++,(uint64_t)(L+OFF),q.mask);}long long cc=0,tt=0;
   for(uint32_t z:zlists[sid]){int64_t Lz=0;uint32_t q=z;while(q){int j=__builtin_ctz(q);q&=q-1;Lz+=lc[j];}if(Lz&1){cerr<<"parity fail\n";abort();}int64_t want=-Lz/2+OFF;if(want<0)continue;uint64_t need=(uint64_t)want;for(int e=tab.first(need);e!=-1;e=tab.next[e]){if(tab.key[e]!=need)continue;uint32_t n=tab.mask[e];if(n&z)continue;cc++;uint32_t PS=FULL^z;bool ok=true;for(int r=1;r<=12;r++){int g=spaf(PS,n,r)+cpaf[r];if(g<2||g>4){ok=false;break;}}if(ok){array<int8_t,N>p{};for(int i=0;i<N;i++)if(PS>>i&1)p[i]=(n>>i&1)?-1:1;for(int r=0;r<N;r++){int h=0;for(int i=0;i<N;i++)h+=p[i]*c[(i-r+N)%N]+c[i]*p[(i-r+N)%N];if(h){cerr<<"target cross recheck fail\n";abort();}}tt++;{lock_guard<mutex>lk(surv_mu);survivors.push_back({p,c,z,n,ci});}
   }}}
   cross+=cc;target+=tt;long long d=++done;if(d%50000==0){
#pragma omp critical
    cerr<<"done="<<d<<"/"<<creps.size()<<" cross="<<cross.load()<<" target="<<target.load()<<" sec="<<(omp_get_wtime()-t0)<<"\n";
   }
 }
 }
 sort(survivors.begin(),survivors.end(),[](const Surv&a,const Surv&b){if(a.ci!=b.ci)return a.ci<b.ci;if(a.z!=b.z)return a.z<b.z;return a.n<b.n;});ofstream fo("ka16_survivors.txt");for(auto&s:survivors){fo<<"ci="<<s.ci<<" z="<<s.z<<" n="<<s.n<<" p=";for(int i=0;i<N;i++){if(i)fo<<",";fo<<(int)s.p[i];}fo<<" c=";for(int i=0;i<N;i++){if(i)fo<<",";fo<<(int)s.c[i];}fo<<"\n";}
 cout<<"SUMMARY supports="<<supports.size()<<" c_reps="<<creps.size()<<" cross="<<cross.load()<<" target="<<target.load()<<" seconds="<<(omp_get_wtime()-t0)<<"\n";return 0;}
