#include <algorithm>
#include <array>
#include <atomic>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <numeric>
#include <sstream>
#include <string>
#include <unordered_set>
#include <vector>
#include <omp.h>
using namespace std;
static constexpr int N=25,L=50;

struct K{uint64_t a=0,b=0;bool operator<(K const&o)const{return a!=o.a?a<o.a:b<o.b;}bool operator==(K const&o)const{return a==o.a&&b==o.b;}};
struct KH{size_t operator()(K const&k)const noexcept{uint64_t x=k.a^(k.b+0x9e3779b97f4a7c15ULL+(k.a<<6)+(k.a>>2));x^=x>>33;x*=0xff51afd7ed558ccdULL;x^=x>>33;return (size_t)x;}};
using A=array<int,N>; using V=array<int8_t,24>;

static int ac50(const array<int8_t,L>&x,int r){int s=0;for(int i=0;i<L-r;i++)s+=x[i]*x[i+r];return s;}

// Reconstruct the A half from compressed p and the antisymmetric fibre mask,
// then return NAF_A(r)=C_A(r)-C_A(50-r), r=1..24.
static V one_naf(const A&p,uint32_t mask){
 array<int8_t,L>x{};int q=0;
 for(int i=0;i<N;i++){
  if(p[i])x[i]=x[i+N]=(int8_t)p[i];
  else{int t=((mask>>q)&1)?1:-1;x[i]=t;x[i+N]=-t;q++;}
 }
 V v{};for(int r=1;r<=24;r++)v[r-1]=(int8_t)(ac50(x,r)-ac50(x,50-r));return v;
}

// Pack the 24 ACF coordinates of a binary length-25 sequence into 120 bits.
// For lag r the ACF is -(25-r),-(25-r)+2,...,+ (25-r), so five bits suffice.
static bool pack_acf_from_naf(const V&naf,K&k){
 k={};int bit=0;
 for(int r=1;r<=24;r++){
  int v=naf[r-1];if(v&1)return false;int x=v/2,n=25-r;
  if(abs(x)>n||((x-n)&1))return false;
  uint64_t z=(uint64_t)((x+n)/2);int w=bit>>6,s=bit&63;uint64_t* p=w?&k.b:&k.a;*p|=z<<s;
  if(s>59){if(w)return false;k.b|=z>>(64-s);}bit+=5;
 }
 return true;
}
static K pack_beta_acf(const array<int8_t,N>&b){
 V naf{};for(int r=1;r<=24;r++){int c=0;for(int i=0;i<N-r;i++)c+=b[i]*b[i+r];naf[r-1]=(int8_t)(2*c);}K k;if(!pack_acf_from_naf(naf,k))abort();return k;
}

// q=0 implies B=[beta,-beta].  Global beta sign is immaterial, so fix beta_0=+1
// and exhaust all 2^24 remaining fibres.  NAF_B(r)=2*ACF_beta(r).
static vector<K> build_table(){
 const uint32_t M=1u<<24;vector<K> out(M);array<int8_t,N>b{};b[0]=1;for(int i=1;i<N;i++)b[i]=-1;
 array<int,24> c{};for(int r=1;r<=24;r++){int s=0;for(int i=0;i<N-r;i++)s+=b[i]*b[i+r];c[r-1]=s;}
 auto packc=[&](){V naf{};for(int r=1;r<=24;r++)naf[r-1]=(int8_t)(2*c[r-1]);K k;if(!pack_acf_from_naf(naf,k))abort();return k;};
 out[0]=packc();
 // Gray-code traversal: transition step-1 -> step flips bit ctz(step).
 for(uint32_t step=1;step<M;step++){
  int j=1+__builtin_ctz(step),old=b[j];
  for(int r=1;r<=24;r++){
   int delta=0;if(j-r>=0)delta+=-2*old*b[j-r];if(j+r<N)delta+=-2*old*b[j+r];c[r-1]+=delta;
  }
  b[j]=-old;out[step]=packc();
 }
 cerr<<"TABLE_GENERATED raw="<<out.size()<<"\n";sort(out.begin(),out.end());out.erase(unique(out.begin(),out.end()),out.end());cerr<<"TABLE_UNIQUE "<<out.size()<<"\n";return out;
}
static bool has(const vector<K>&T,const K&k){return binary_search(T.begin(),T.end(),k);}

static bool acf_target_from_naf(const V&a,array<int,24>&x){
 for(int i=0;i<24;i++){
  int v=-int(a[i]);if(v&1)return false;x[i]=v/2;int n=24-i;
  // Parity must already be valid; range may be repaired by sparse defects below.
  if(((x[i]-n)&1))return false;
 }
 return true;
}
static bool pack_acf_vals(const array<int,24>&x,K&k){
 k={};int bit=0;
 for(int i=0;i<24;i++){
  int n=24-i;if(abs(x[i])>n||((x[i]-n)&1))return false;uint64_t z=(uint64_t)((x[i]+n)/2);
  int w=bit>>6,sh=bit&63;uint64_t* p=w?&k.b:&k.a;*p|=z<<sh;
  if(sh>59){if(w)return false;k.b|=z>>(64-sh);}bit+=5;
 }
 return true;
}
static bool query0(const vector<K>&T,const V&a,K*ret=nullptr){
 array<int,24>x{};if(!acf_target_from_naf(a,x))return false;K k;if(!pack_acf_vals(x,k))return false;bool h=has(T,k);if(h&&ret)*ret=k;return h;
}

// Search zero/one/two +/-4 NAF defects, equivalent to zero/one/two +/-2 ACF changes.
// Important: do not reject an out-of-range unmodified coordinate before allowing a defect
// to repair it.  The self-test below includes such one- and two-defect boundary cases.
static bool query12(const vector<K>&T,const V&a,int maxd,int &which,K*ret=nullptr){
 array<int,24>x{};if(!acf_target_from_naf(a,x))return false;
 vector<int> bad;for(int i=0;i<24;i++)if(abs(x[i])>24-i)bad.push_back(i);if((int)bad.size()>maxd)return false;
 K base;bool baseok=pack_acf_vals(x,base);if(baseok&&has(T,base)){which=0;if(ret)*ret=base;return true;}
 if(maxd>=1 && bad.size()<=1){
  for(int i=0;i<24;i++){
   if(!bad.empty()&&i!=bad[0])continue;
   for(int dx:{-2,2}){auto y=x;y[i]+=dx;K k;if(pack_acf_vals(y,k)&&has(T,k)){which=1;if(ret)*ret=k;return true;}}
  }
 }
 if(maxd>=2){
  for(int i=0;i<24;i++)for(int j=i+1;j<24;j++){
   bool cover=true;for(int b:bad)if(b!=i&&b!=j){cover=false;break;}if(!cover)continue;
   for(int di:{-2,2})for(int dj:{-2,2}){auto y=x;y[i]+=di;y[j]+=dj;K k;if(pack_acf_vals(y,k)&&has(T,k)){which=2;if(ret)*ret=k;return true;}}
  }
 }
 return false;
}

struct R{A p;bool base;int rid;};
static vector<int> units(){vector<int>u;for(int a=1;a<25;a++)if(gcd(a,25)==1)u.push_back(a);return u;}
static A aff(const A&p,int a,int b){A y{};for(int i=0;i<N;i++)y[(a*i+b)%N]=p[i];return y;}

int main(int argc,char**argv){
 if(argc>1 && string(argv[1])=="--selftest"){
  A qzero{};
  for(uint32_t m:{1u,3u,0x1555555u,0x1ffffffu}){
   auto nv=one_naf(qzero,m);array<int8_t,N>b{};for(int i=0;i<N;i++)b[i]=((m>>i)&1)?1:-1;
   K k1,k2;if(!pack_acf_from_naf(nv,k1))abort();k2=pack_beta_acf(b);if(!(k1==k2))abort();
  }
  array<int8_t,N> all{};all.fill(1);K ka=pack_beta_acf(all);vector<K>T{ka};
  V nb{};for(int r=1;r<=24;r++)nb[r-1]=(int8_t)(2*(25-r));V a0=nb;for(auto&x:a0)x=-x;int d=-1;K kk;
  if(!query12(T,a0,2,d,&kk)||d!=0)abort();
  V a1=a0;a1[23]=(int8_t)(a1[23]-4);d=-1;if(!query12(T,a1,1,d,&kk)||d!=1)abort();
  V a2=a1;a2[22]=(int8_t)(a2[22]-4);d=-1;if(!query12(T,a2,2,d,&kk)||d!=2)abort();
  cout<<"UNIVERSAL_FIBRE_SELFTEST_OK\n";return 0;
 }
 if(argc<2){cerr<<"usage: "<<argv[0]<<" --selftest | <compressed-hits.txt>\n";return 2;}
 string path=argv[1];ifstream f(path);if(!f){cerr<<"cannot open "<<path<<"\n";return 2;}
 string line;vector<R> reps;int rid=0;
 while(getline(f,line)){
  if(line.find("HIT ")!=0)continue;rid++;bool base=line.find("base=1")!=string::npos;
  auto s=line.find(" p=")+3,e=line.find(" G=",s);string q=line.substr(s,e-s);replace(q.begin(),q.end(),',',' ');stringstream ss(q);A p{};for(int&i:p)ss>>i;reps.push_back({p,base,rid});
 }
 cerr<<"REPS "<<reps.size()<<"\n";if(reps.size()!=96){cerr<<"expected 96 spectral reps\n";return 3;}
 auto T=build_table();if(T.size()!=8390620){cerr<<"unexpected q-key count "<<T.size()<<"\n";return 3;}
 struct Task{A p;bool base;int rid,a,b;};vector<Task> tasks;unordered_set<string> seen;
 for(auto&r:reps)for(int a:units())for(int b=0;b<25;b++){
  A p=aff(r.p,a,b);string key;key.resize(25);for(int i=0;i<25;i++)key[i]=char(p[i]+1);
  if(seen.insert(key).second)tasks.push_back({p,r.base,r.rid,a,b});
 }
 cerr<<"AFFINE_SIGNED_IMAGES "<<tasks.size()<<"\n";if(tasks.size()!=47500){cerr<<"unexpected affine image count\n";return 3;}
 atomic<long long> done{0},hit0{0},hit1{0},hit2{0};double t0=omp_get_wtime();
#pragma omp parallel for schedule(dynamic,1)
 for(long long ti=0;ti<(long long)tasks.size();ti++){
  auto &x=tasks[ti];int z=0;for(int v:x.p)z+=v==0;if(z!=6)abort();uint32_t M=1u<<z;
  for(uint32_t m=0;m<M;m++){
   auto na=one_naf(x.p,m);int d=-1;K k;bool h=x.base?query12(T,na,2,d,&k):query0(T,na,&k);
   if(h){
    if(!x.base)d=0;if(d==0)hit0++;else if(d==1)hit1++;else hit2++;
#pragma omp critical
    {cout<<"FIBRE_HIT rid="<<x.rid<<" base="<<x.base<<" a="<<x.a<<" b="<<x.b<<" alpha_mask="<<m<<" defect="<<d<<" key="<<k.a<<":"<<k.b<<" p=";for(int v:x.p)cout<<v<<',';cout<<"\n"<<flush;}
    break;
   }
  }
  auto d=++done;if(d%1000==0){
#pragma omp critical
   cerr<<"PROGRESS "<<d<<"/"<<tasks.size()<<" sec="<<omp_get_wtime()-t0<<" hits="<<(hit0+hit1+hit2)<<"\n";
  }
 }
 cout<<"KP19_UNIVERSAL_FIBRE_SUMMARY reps="<<reps.size()<<" images="<<tasks.size()<<" hit0="<<hit0.load()<<" hit1="<<hit1.load()<<" hit2="<<hit2.load()<<" seconds="<<omp_get_wtime()-t0<<" qkeys="<<T.size()<<"\n";
 return (hit0||hit1||hit2)?5:0;
}
