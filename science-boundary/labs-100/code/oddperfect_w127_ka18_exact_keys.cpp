#include <bits/stdc++.h>
#include <omp.h>
using namespace std;
static const int N=25, MOD=101;
// Exact W127 order-25 exclusion for ka=18,kc=8.
// p has 14 plus, 4 minus, 7 zero; c has 4 plus, 4 minus, 17 zero.
// The search is exact and consists of:
//   (1) affine orbit reduction of the 7-zero support Z;
//   (2) an exact GF(2) phase key on Phi_5 and Phi_25 to retain only c-supports T
//       compatible with the cross equation modulo 2;
//   (3) all 12 independent projective character channels over F_101, where a
//       primitive 25th root exists.  Matching every channel is equivalent to the
//       full cross polynomial being zero modulo 101.  Its integer coefficients
//       have absolute value <=16, so this is already exact over Z;
//   (4) independent integer rechecking of every key match, followed by the
//       W127 combined-PAF test.
// Common affine maps of Z_25 preserve all projected equations.  c -> -c is also
// a symmetry, so only 35 of its 70 balanced signings are enumerated.
static vector<int> units25(){vector<int>u;for(int a=1;a<25;a++)if(gcd(a,25)==1)u.push_back(a);return u;}
static uint32_t transmask(uint32_t m,int a,int b){uint32_t o=0;while(m){int i=__builtin_ctz(m);m&=m-1;o|=1u<<((a*i+b)%25);}return o;}
static vector<uint32_t> z_orbit_reps(){auto U=units25();unordered_set<uint32_t>vis;vis.reserve(600000);vector<uint32_t> reps;
 for(int a=0;a<25;a++)for(int b=a+1;b<25;b++)for(int c=b+1;c<25;c++)for(int d=c+1;d<25;d++)for(int e=d+1;e<25;e++)for(int f=e+1;f<25;f++)for(int g=f+1;g<25;g++){
  uint32_t m=(1u<<a)|(1u<<b)|(1u<<c)|(1u<<d)|(1u<<e)|(1u<<f)|(1u<<g);if(vis.count(m))continue;reps.push_back(m);for(int q:U)for(int t=0;t<25;t++)vis.insert(transmask(m,q,t));
 }
 if(vis.size()!=480700)throw runtime_error("Z orbit coverage");cerr<<"Z_orbits="<<reps.size()<<"\n";return reps;}
// GF(2^20) = F2[x]/Phi_25 and GF(2^4) = F2[x]/Phi_5.
static uint32_t mul20(uint32_t a,uint32_t b){uint32_t r=0,mask=(1u<<20)-1,red=(1u<<15)|(1u<<10)|(1u<<5)|1u;while(b){if(b&1)r^=a;b>>=1;bool hi=a&(1u<<19);a=(a<<1)&mask;if(hi)a^=red;}return r;}
static uint32_t pow20(uint32_t a,uint32_t e){uint32_t r=1;while(e){if(e&1)r=mul20(r,a);a=mul20(a,a);e>>=1;}return r;}
static uint8_t mul4(uint8_t a,uint8_t b){uint8_t r=0;while(b){if(b&1)r^=a;b>>=1;bool hi=a&8;a=(a<<1)&15;if(hi)a^=15;}return r;}
static uint8_t pow4(uint8_t a,int e){uint8_t r=1;while(e){if(e&1)r=mul4(r,a);a=mul4(a,a);e>>=1;}return r;}
struct F2K{uint32_t k20;uint8_t k5;};
static uint32_t basis20[25];static uint8_t basis4[25];static uint8_t key5id[16];
static F2K f2key(uint32_t m){uint32_t v20=0;uint8_t v4=0;while(m){int i=__builtin_ctz(m);m&=m-1;v20^=basis20[i];v4^=basis4[i];}if(!v20)throw runtime_error("unexpected Phi25 zero");return {pow20(v20,1047552u),(uint8_t)(v4?key5id[pow4(v4,12)]:255)};}
struct Buck{array<vector<uint32_t>,6> v;};
static unordered_map<uint32_t,Buck> build_T_groups(){unordered_map<uint32_t,Buck> G;G.reserve(1200);
 for(int a=0;a<25;a++)for(int b=a+1;b<25;b++)for(int c=b+1;c<25;c++)for(int d=c+1;d<25;d++)for(int e=d+1;e<25;e++)for(int f=e+1;f<25;f++)for(int g=f+1;g<25;g++)for(int h=g+1;h<25;h++){
  uint32_t m=(1u<<a)|(1u<<b)|(1u<<c)|(1u<<d)|(1u<<e)|(1u<<f)|(1u<<g)|(1u<<h);auto k=f2key(m);G[k.k20].v[k.k5==255?5:k.k5].push_back(m);
 }cerr<<"T_k20_groups="<<G.size()<<"\n";return G;}
// Projective phase keys over F_101.  omega=16 has exact order 25.
static int inv101[101], pw[12][25], pwi[12][25];
static const int js[12]={1,2,3,4,6,7,8,9,11,12,5,10};
static int proj(int a,int b){a%=MOD;if(a<0)a+=MOD;b%=MOD;if(b<0)b+=MOD;if(a==0&&b==0)return 102;if(b==0)return 101;return a*inv101[b]%MOD;}
static int negproj(int r){if(r==102||r==101)return r;return r?MOD-r:0;}
struct K12{array<uint8_t,12>a{};bool operator==(K12 const&o)const{return a==o.a;}};
struct KH{size_t operator()(K12 const&k)const{size_t h=1469598103934665603ULL;for(auto x:k.a){h^=x;h*=1099511628211ULL;}return h;}};
struct PRec{K12 k;uint32_t neg;bool wild;};
struct PIndex{unordered_map<K12,vector<uint32_t>,KH> normal;vector<PRec>wild;vector<PRec>all;};
static bool match12(const K12&p,const K12&w){for(int j=0;j<12;j++)if(p.a[j]!=102&&w.a[j]!=102&&p.a[j]!=w.a[j])return false;return true;}
static PIndex build_pindex(uint32_t Z){vector<int>S;for(int i=0;i<25;i++)if(!(Z>>i&1))S.push_back(i);if(S.size()!=18)throw runtime_error("S size");int bz[12]={},bzi[12]={};for(int ch=0;ch<12;ch++)for(int i=0;i<25;i++)if(Z>>i&1){bz[ch]=(bz[ch]+pw[ch][i])%MOD;bzi[ch]=(bzi[ch]+pwi[ch][i])%MOD;}
 PIndex out;out.normal.reserve(5000);out.all.reserve(3060);
 for(int a=0;a<18;a++)for(int b=a+1;b<18;b++)for(int c=b+1;c<18;c++)for(int d=c+1;d<18;d++){
   int ids[4]={S[a],S[b],S[c],S[d]};K12 key;bool w=false;uint32_t nm=0;for(int x:ids)nm|=1u<<x;for(int ch=0;ch<12;ch++){int sn=0,sni=0;for(int q:ids){sn+=pw[ch][q];sni+=pwi[ch][q];}int va=(-bz[ch]-2*sn)%MOD,vb=(-bzi[ch]-2*sni)%MOD;int r=proj(va,vb);key.a[ch]=r;if(r==102)w=true;}PRec rec{key,nm,w};out.all.push_back(rec);if(w)out.wild.push_back(rec);else out.normal[key].push_back(nm);
 }
 return out;}
static int paf25(const array<int,25>&x,int r){int s=0;for(int i=0;i<25;i++)s+=x[i]*x[(i+r)%25];return s;}
// -1 means a key implementation error (modular match but nonzero integer cross),
// 0 means exact cross but wrong W127 PAF, 1 means a target survivor.
static int exact_target(uint32_t Z,uint32_t neg,uint32_t T,uint32_t plus){array<int,25>p{},c{};for(int i=0;i<25;i++){if(Z>>i&1)p[i]=0;else if(neg>>i&1)p[i]=-1;else p[i]=1;if(T>>i&1)c[i]=(plus>>i&1)?1:-1;}
 for(int r=0;r<25;r++){int h=0;for(int i=0;i<25;i++)h+=p[i]*c[(i-r+25)%25]+c[i]*p[(i-r+25)%25];if(h)return -1;}
 int sm=0;for(int r=1;r<=12;r++){int k=paf25(p,r)+paf25(c,r);if(k<2||k>4)return 0;sm+=k;}return sm==37?1:0;}
struct Res{long long csign=0,keymatch=0,badcross=0,target=0;};
static Res process_T(uint32_t Z,uint32_t T,const PIndex&pi){vector<int>v;for(int i=0;i<25;i++)if(T>>i&1)v.push_back(i);if(v.size()!=8)abort();int tot[12]={},toti[12]={};for(int ch=0;ch<12;ch++)for(int i:v){tot[ch]=(tot[ch]+pw[ch][i])%MOD;toti[ch]=(toti[ch]+pwi[ch][i])%MOD;}Res out;
 int fixed=v[0];for(int b=1;b<8;b++)for(int c=b+1;c<8;c++)for(int d=c+1;d<8;d++){
   int ids[4]={fixed,v[b],v[c],v[d]};uint32_t plus=0;for(int q:ids)plus|=1u<<q;K12 want;bool cw=false;for(int ch=0;ch<12;ch++){int sp=0,spi=0;for(int q:ids){sp+=pw[ch][q];spi+=pwi[ch][q];}int ca=(2*sp-tot[ch])%MOD,cb=(2*spi-toti[ch])%MOD;int r=proj(ca,cb);want.a[ch]=negproj(r);if(r==102)cw=true;}
   vector<uint32_t> matches;if(!cw){auto it=pi.normal.find(want);if(it!=pi.normal.end())matches.insert(matches.end(),it->second.begin(),it->second.end());for(auto &pr:pi.wild)if(match12(pr.k,want))matches.push_back(pr.neg);}else{for(auto &pr:pi.all)if(match12(pr.k,want))matches.push_back(pr.neg);}
   if(matches.empty())continue;out.csign++;for(uint32_t neg:matches){out.keymatch++;int verdict=exact_target(Z,neg,T,plus);if(verdict<0)out.badcross++;if(verdict>0){out.target++;cout<<"TARGET Z="<<Z<<" T="<<T<<" neg="<<neg<<" plus="<<plus<<"\n";}}
 }
 return out;}
int main(){basis20[0]=1;for(int i=1;i<25;i++)basis20[i]=mul20(basis20[i-1],2);basis4[0]=1;for(int i=1;i<25;i++)basis4[i]=mul4(basis4[i-1],2);
 for(int i=0;i<16;i++)key5id[i]=255;{int next=0;for(int v=1;v<16;v++){int raw=pow4(v,12);if(key5id[raw]==255)key5id[raw]=next++;}if(next!=5)throw runtime_error("Phi5 key count");}
 for(int a=1;a<101;a++)for(int b=1;b<101;b++)if(a*b%101==1){inv101[a]=b;break;}int omega=16;auto modpow=[](int a,int e){int r=1;while(e){if(e&1)r=r*a%101;a=a*a%101;e>>=1;}return r;};for(int ch=0;ch<12;ch++){int w=modpow(omega,js[ch]),wi=modpow(omega,(25-js[ch])%25);for(int i=0;i<25;i++){pw[ch][i]=modpow(w,i);pwi[ch][i]=modpow(wi,i);}}
 auto ZR=z_orbit_reps();auto TG=build_T_groups();atomic<long long>pairs{0},csign{0},keymatch{0},badcross{0},targets{0};atomic<int>done{0};
#pragma omp parallel for schedule(dynamic,1)
 for(size_t zi=0;zi<ZR.size();zi++){uint32_t Z=ZR[zi];auto zk=f2key(Z);auto it=TG.find(zk.k20);if(it==TG.end())continue;vector<uint32_t>cand;if(zk.k5==255){for(int s=0;s<6;s++)cand.insert(cand.end(),it->second.v[s].begin(),it->second.v[s].end());}else{auto&a=it->second.v[zk.k5];cand.insert(cand.end(),a.begin(),a.end());auto&w=it->second.v[5];cand.insert(cand.end(),w.begin(),w.end());}pairs+=cand.size();auto pi=build_pindex(Z);long long lc=0,lx=0,lb=0,lt=0;for(uint32_t T:cand){auto r=process_T(Z,T,pi);lc+=r.csign;lx+=r.keymatch;lb+=r.badcross;lt+=r.target;}csign+=lc;keymatch+=lx;badcross+=lb;targets+=lt;int d=++done;if(d%100==0){
#pragma omp critical
 cerr<<"done="<<d<<"/"<<ZR.size()<<" supportpairs="<<pairs.load()<<" csign="<<csign.load()<<" keymatch="<<keymatch.load()<<" badcross="<<badcross.load()<<" target="<<targets.load()<<"\n";}}
 cout<<"SUMMARY Zorbits="<<ZR.size()<<" supportpairs="<<pairs.load()<<" csign="<<csign.load()<<" keymatch="<<keymatch.load()<<" badcross="<<badcross.load()<<" target="<<targets.load()<<"\n";return targets.load()||badcross.load()?1:0;}
