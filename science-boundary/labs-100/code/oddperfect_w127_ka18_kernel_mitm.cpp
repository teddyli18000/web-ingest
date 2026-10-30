// Exact W127 order-25 exclusion for ka=18,kc=8.
// c has four +1, four -1, seventeen 0. p has fourteen +1, four -1, seven 0.
// Write p=1-z-2n, |z|=7, |n|=4. For fixed c, M1=0 and cross=0 iff
// Mz+2Mn=0. Mod 2 first forces z into ker(M mod2), cutting C(25,7)
// masks to ~142 on average. Integer 13-vectors Mn in [-8,8]^13 are encoded
// injectively in base 17 in uint64_t, then matched exactly.
#include <bits/stdc++.h>
#include <omp.h>
using namespace std;
static const int N=25,R=13,HS=32768;
struct Perm{array<uint8_t,N> p;};
struct CRep{int sid; uint32_t plus;};
struct N4{uint8_t a,b,c,d; uint32_t mask;};
vector<Perm> perms; vector<vector<int>> stabilizers; vector<uint32_t> supports; vector<vector<uint32_t>> zlists; vector<CRep> creps; vector<N4> n4s;
static uint32_t trans(uint32_t m,const Perm&pm){uint32_t o=0;while(m){int i=__builtin_ctz(m);m&=m-1;o|=1u<<pm.p[i];}return o;}
static int paf(const array<int8_t,N>&x,int r){int s=0;for(int i=0;i<N;i++)s+=x[i]*x[(i+r)%N];return s;}
static vector<uint32_t> null_weight7(uint32_t S){
 vector<uint32_t> rows; rows.reserve(12);
 for(int r=1;r<=12;r++){uint32_t row=0;for(int j=0;j<N;j++){int a=(j-r+N)%N,b=(j+r)%N;if(((S>>a)&1)^((S>>b)&1))row|=1u<<j;}rows.push_back(row);}
 int rr=0;vector<int> piv;
 for(int c=0;c<N&&rr<(int)rows.size();c++){int k=rr;while(k<(int)rows.size()&&!((rows[k]>>c)&1))k++;if(k==(int)rows.size())continue;swap(rows[rr],rows[k]);for(int i=0;i<(int)rows.size();i++)if(i!=rr&&((rows[i]>>c)&1))rows[i]^=rows[rr];piv.push_back(c);rr++;}
 vector<char> isp(N);for(int c:piv)isp[c]=1;vector<uint32_t> bs;
 for(int f=0;f<N;f++)if(!isp[f]){uint32_t v=1u<<f;for(int i=0;i<rr;i++)if((rows[i]>>f)&1)v|=1u<<piv[i];bs.push_back(v);}
 vector<uint32_t> all{0};for(uint32_t b:bs){size_t q=all.size();for(size_t i=0;i<q;i++)all.push_back(all[i]^b);}vector<uint32_t> out;for(uint32_t v:all)if(__builtin_popcount(v)==7)out.push_back(v);return out;
}
static void build_orbits(){
 for(int a=1;a<N;a++)if(gcd(a,N)==1)for(int b=0;b<N;b++){Perm pm;for(int i=0;i<N;i++)pm.p[i]=(a*i+b)%N;perms.push_back(pm);} if(perms.size()!=500)abort();
 vector<uint8_t> vis(1u<<25); long long rawS=0;
 for(uint32_t S=0;S<(1u<<25);S++){if(__builtin_popcount(S)!=8)continue;rawS++;if(vis[S])continue;int sid=supports.size();supports.push_back(S);for(auto &pm:perms)vis[trans(S,pm)]=1;vector<int> stab;for(int pi=0;pi<(int)perms.size();pi++)if(trans(S,perms[pi])==S)stab.push_back(pi);stabilizers.push_back(stab);zlists.push_back(null_weight7(S));
   vector<int> idx;for(int i=0;i<N;i++)if(S>>i&1)idx.push_back(i);unordered_set<uint32_t> seen;seen.reserve(128);
   for(int a=0;a<8;a++)for(int b=a+1;b<8;b++)for(int c=b+1;c<8;c++)for(int d=c+1;d<8;d++){uint32_t P=(1u<<idx[a])|(1u<<idx[b])|(1u<<idx[c])|(1u<<idx[d]);if(seen.count(P))continue;creps.push_back({sid,P});uint32_t M=S^P;for(int pi:stab){uint32_t pp=trans(P,perms[pi]),mm=trans(M,perms[pi]);seen.insert(pp);seen.insert(mm);}}
   if(seen.size()!=70){cerr<<"sign orbit coverage fail sid="<<sid<<" got="<<seen.size()<<"\n";abort();}
 }
 if(rawS!=1081575 || supports.size()!=2191 || creps.size()!=75987){cerr<<"coverage mismatch rawS="<<rawS<<" supports="<<supports.size()<<" creps="<<creps.size()<<"\n";abort();}
 cerr<<"supports="<<supports.size()<<" c_reps="<<creps.size()<<"\n";
}
static void build_n4(){for(int a=0;a<N;a++)for(int b=a+1;b<N;b++)for(int c=b+1;c<N;c++)for(int d=c+1;d<N;d++)n4s.push_back({(uint8_t)a,(uint8_t)b,(uint8_t)c,(uint8_t)d,(1u<<a)|(1u<<b)|(1u<<c)|(1u<<d)});if(n4s.size()!=12650)abort();}
static inline uint64_t mix64(uint64_t x){x^=x>>30;x*=0xbf58476d1ce4e5b9ULL;x^=x>>27;x*=0x94d049bb133111ebULL;x^=x>>31;return x;}
struct Table{array<int,HS> head,stamp;array<uint64_t,12650> key;array<uint32_t,12650> mask;array<int,12650> next;int gen=1;Table(){stamp.fill(0);}void reset(){if(++gen==INT_MAX){stamp.fill(0);gen=1;}}void add(int i,uint64_t k,uint32_t m){int b=mix64(k)&(HS-1);if(stamp[b]!=gen){stamp[b]=gen;head[b]=-1;}key[i]=k;mask[i]=m;next[i]=head[b];head[b]=i;}int first(uint64_t k){int b=mix64(k)&(HS-1);return stamp[b]==gen?head[b]:-1;}};
int main(){build_n4();build_orbits();
 array<int64_t,R> pw{};pw[0]=1;for(int r=1;r<R;r++)pw[r]=pw[r-1]*17;int64_t sumw=0;for(auto x:pw)sumw+=x;const int64_t OFFSET=8*sumw;
 atomic<long long> cross{0},target{0},done{0}; double t0=omp_get_wtime();
#pragma omp parallel
 {Table tab;
#pragma omp for schedule(dynamic,4)
  for(size_t ci=0;ci<creps.size();ci++){
   int sid=creps[ci].sid;uint32_t S=supports[sid],P=creps[ci].plus,Msk=S^P;array<int8_t,N> c{};for(int i=0;i<N;i++){if(P>>i&1)c[i]=1;else if(Msk>>i&1)c[i]=-1;}
   array<array<int8_t,R>,N> col{};array<int64_t,N> lc{};
   for(int j=0;j<N;j++){int64_t L=0;for(int r=0;r<R;r++){int v=c[(j-r+N)%N]+c[(j+r)%N];col[j][r]=v;L+=v*pw[r];}lc[j]=L;}
   tab.reset();int ii=0;for(auto &q:n4s){int64_t L=lc[q.a]+lc[q.b]+lc[q.c]+lc[q.d];uint64_t k=(uint64_t)(L+OFFSET);tab.add(ii++,k,q.mask);}
   long long cc=0,tt=0;
   for(uint32_t z:zlists[sid]){int64_t Lz=0;uint32_t q=z;while(q){int j=__builtin_ctz(q);q&=q-1;Lz+=lc[j];}if(Lz&1){cerr<<"parity encoding inconsistency\n";abort();}uint64_t need=(uint64_t)(-Lz/2+OFFSET);int h=tab.first(need);for(int e=h;e!=-1;e=tab.next[e]){if(tab.key[e]!=need)continue;uint32_t n=tab.mask[e];if(n&z)continue;
      bool ok=true;for(int r=0;r<R;r++){int v=0;uint32_t a=z;while(a){int j=__builtin_ctz(a);a&=a-1;v+=col[j][r];}uint32_t b=n;while(b){int j=__builtin_ctz(b);b&=b-1;v+=2*col[j][r];}if(v){ok=false;break;}}if(!ok)continue;cc++;
      array<int8_t,N> p;p.fill(1);for(int i=0;i<N;i++){if(z>>i&1)p[i]=0;else if(n>>i&1)p[i]=-1;}
      for(int r=0;r<N;r++){int v=0;for(int i=0;i<N;i++)v+=p[i]*c[(i-r+N)%N]+c[i]*p[(i-r+N)%N];if(v){cerr<<"full cross recheck fail\n";abort();}}
      int sm=0;for(int r=1;r<=12;r++){int g=paf(p,r)+paf(c,r);if(g<2||g>4){ok=false;break;}sm+=g;}if(ok&&sm==37){tt++;
#pragma omp critical
        cerr<<"FOUND projected survivor ci="<<ci<<" z="<<z<<" n="<<n<<"\n";
      }
    }}
   cross+=cc;target+=tt;long long d=++done;if(d%5000==0){
#pragma omp critical
     cerr<<"done="<<d<<"/"<<creps.size()<<" cross="<<cross.load()<<" target="<<target.load()<<" sec="<<(omp_get_wtime()-t0)<<"\n";
   }
  }
 }
 cout<<"SUMMARY supports="<<supports.size()<<" c_reps="<<creps.size()<<" cross="<<cross.load()<<" target="<<target.load()<<" seconds="<<(omp_get_wtime()-t0)<<"\n";
 return target.load()?1:0;
}
