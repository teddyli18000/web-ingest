// Exact W127 order-25 ka=10,kc=16 projection search.
#include <bits/stdc++.h>
#include <omp.h>
using namespace std; static const int N=25,R=13,HS=1024; static const uint32_t FULL=(1u<<25)-1;
struct Perm{array<uint8_t,N>p;}; struct Work{uint32_t p,w;};
vector<Perm> perms; vector<Work> works;
uint32_t tr(uint32_t m,const Perm&p){uint32_t o=0;while(m){int i=__builtin_ctz(m);m&=m-1;o|=1u<<p.p[i];}return o;}
int paf(const array<int8_t,N>&x,int r){int s=0;for(int i=0;i<N;i++)s+=x[i]*x[(i+r)%N];return s;}
vector<uint32_t> kernel9(uint32_t P){vector<uint32_t>rows;for(int r=1;r<=12;r++){uint32_t row=0;for(int j=0;j<N;j++)if(((P>>((j-r+N)%N))&1)^((P>>((j+r)%N))&1))row|=1u<<j;rows.push_back(row);}int rr=0;vector<int>piv;for(int c=0;c<N&&rr<12;c++){int k=rr;while(k<12&&!((rows[k]>>c)&1))k++;if(k==12)continue;swap(rows[k],rows[rr]);for(int i=0;i<12;i++)if(i!=rr&&((rows[i]>>c)&1))rows[i]^=rows[rr];piv.push_back(c);rr++;}vector<char>ip(N);for(int x:piv)ip[x]=1;vector<uint32_t>b;for(int f=0;f<N;f++)if(!ip[f]){uint32_t v=1u<<f;for(int i=0;i<rr;i++)if((rows[i]>>f)&1)v|=1u<<piv[i];b.push_back(v);}vector<uint32_t>a{0};for(auto x:b){size_t q=a.size();for(size_t i=0;i<q;i++)a.push_back(a[i]^x);}vector<uint32_t>out;for(auto v:a)if(__builtin_popcount(v)==9)out.push_back(v);return out;}
void build(){for(int a=1;a<N;a++)if(gcd(a,N)==1)for(int b=0;b<N;b++){Perm p;for(int i=0;i<N;i++)p.p[i]=(a*i+b)%N;perms.push_back(p);}vector<uint8_t>vis(1u<<25);long long raw=0,rawpairs=0;for(uint32_t P=0;P<(1u<<25);P++){if(__builtin_popcount(P)!=10)continue;raw++;if(vis[P])continue;for(auto&pm:perms)vis[tr(P,pm)]=1;vector<int>stab;for(int i=0;i<500;i++)if(tr(P,perms[i])==P)stab.push_back(i);auto zs=kernel9(P);rawpairs+=zs.size();unordered_set<uint32_t>seen;for(uint32_t z:zs){if(seen.count(z))continue;uint32_t W=FULL^z;works.push_back({P,W});for(int pi:stab)seen.insert(tr(z,perms[pi]));} }
 if(raw!=3268760||works.size()!=3909436){cerr<<"coverage mismatch raw="<<raw<<" work="<<works.size()<<" rawpairs="<<rawpairs<<"\n";abort();}cerr<<"p_support_orbits=6578 support_pair_orbits="<<works.size()<<"\n";}
static inline uint64_t mix64(uint64_t x){x^=x>>30;x*=0xbf58476d1ce4e5b9ULL;x^=x>>27;x*=0x94d049bb133111ebULL;x^=x>>31;return x;}
struct Entry{uint64_t key;uint16_t mask;uint8_t cnt;};
struct Tab{array<int,HS>head,stamp;array<Entry,256>e;array<int,256>next;int gen=1;Tab(){stamp.fill(0);}void reset(){if(++gen==INT_MAX){stamp.fill(0);gen=1;}}void add(int i,uint64_t k,uint16_t m,int cnt){int b=mix64(k)&(HS-1);if(stamp[b]!=gen){stamp[b]=gen;head[b]=-1;}e[i]={k,m,(uint8_t)cnt};next[i]=head[b];head[b]=i;}int first(uint64_t k){int b=mix64(k)&(HS-1);return stamp[b]==gen?head[b]:-1;}};
int main(){build();array<int64_t,R>pw{};pw[0]=1;for(int r=1;r<R;r++)pw[r]=pw[r-1]*17;int64_t sw=0;for(auto x:pw)sw+=x;const int64_t OFF=8*sw;atomic<long long>cross{0},target{0},done{0};double t0=omp_get_wtime();
#pragma omp parallel
 {Tab tab;
#pragma omp for schedule(dynamic,256)
 for(size_t wi=0;wi<works.size();wi++){uint32_t P=works[wi].p,W=works[wi].w;array<int8_t,N>p{};for(int i=0;i<N;i++)if(P>>i&1)p[i]=1;vector<int>idx;for(int i=0;i<N;i++)if(W>>i&1)idx.push_back(i);if(idx.size()!=16)abort();array<array<int8_t,R>,N>col{};array<int64_t,N>lc{};for(int j=0;j<N;j++){int64_t L=0;for(int r=0;r<R;r++){int v=p[(j-r+N)%N]+p[(j+r)%N];col[j][r]=v;L+=v*pw[r];}lc[j]=L;}array<int,R>rhs{};for(int r=0;r<R;r++){int v=0;for(int j:idx)v+=col[j][r];if(v&1)abort();rhs[r]=v/2;}int64_t rhsL=0;for(int r=0;r<R;r++)rhsL+=rhs[r]*pw[r];
   tab.reset();int ep=0;for(int m=0;m<256;m++){int cnt=__builtin_popcount((unsigned)m),L=0;int64_t key=0;for(int b=0;b<8;b++)if(m>>b&1)key+=lc[idx[b]];tab.add(ep++,key+OFF,(uint16_t)m,cnt);}long long cc=0,tt=0;
   for(int mr=0;mr<256;mr++){int cr=__builtin_popcount((unsigned)mr);if(cr>8)continue;int64_t kr=0;for(int b=0;b<8;b++)if(mr>>b&1)kr+=lc[idx[b+8]];int needcnt=8-cr;uint64_t need=(uint64_t)(rhsL-kr+OFF);for(int e=tab.first(need);e!=-1;e=tab.next[e]){if(tab.e[e].key!=need||tab.e[e].cnt!=needcnt)continue;uint32_t neg=0;for(int b=0;b<8;b++)if(tab.e[e].mask>>b&1)neg|=1u<<idx[b];for(int b=0;b<8;b++)if(mr>>b&1)neg|=1u<<idx[b+8];if(neg&1u<<idx[0])continue;cc++;bool ok=true;for(int r=1;r<=12;r++){uint32_t Wr=((W<<r)|(W>>(25-r)))&FULL,nr=((neg<<r)|(neg>>(25-r)))&FULL;int ec=__builtin_popcount(W&Wr);int xo=__builtin_popcount((W&Wr)&(neg^nr));int cp=ec-2*xo;int pp=__builtin_popcount(P&(((P<<r)|(P>>(25-r)))&FULL));int g=pp+cp;if(g<2||g>4){ok=false;break;}}if(ok){array<int8_t,N>c{};for(int i=0;i<N;i++)if(W>>i&1)c[i]=(neg>>i&1)?-1:1;for(int r=0;r<N;r++){int h=0;for(int i=0;i<N;i++)h+=p[i]*c[(i-r+N)%N]+c[i]*p[(i-r+N)%N];if(h){cerr<<"target cross recheck fail\n";abort();}}tt++;
#pragma omp critical
         cerr<<"FOUND projected survivor work="<<wi<<" P="<<P<<" W="<<W<<" neg="<<neg<<"\n";
       }
   }}cross+=cc;target+=tt;long long d=++done;if(d%250000==0){
#pragma omp critical
      cerr<<"done="<<d<<"/"<<works.size()<<" cross="<<cross.load()<<" target="<<target.load()<<" sec="<<(omp_get_wtime()-t0)<<"\n";
   }
 }
 }
 cout<<"SUMMARY support_pair_orbits="<<works.size()<<" cross="<<cross.load()<<" target="<<target.load()<<" seconds="<<(omp_get_wtime()-t0)<<"\n";return target.load()?1:0;}
