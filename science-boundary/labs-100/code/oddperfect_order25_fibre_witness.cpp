// Exact witness extractor for a fixed order-25 compressed low11 candidate.
//
// This is the constructive counterpart of oddperfect_order25_fibre_mitm.cpp.
// Given p,c and a requested sparse negaperiodic defect size 0,1,2, it finds an
// explicit pair of binary length-50 lifts A,B whenever one exists, interleaves
// them into the original length-100 LABS sequence, and independently recomputes
// all aperiodic autocorrelations and the total energy.
//
// Input: 25 integers p followed by 25 integers c, each in {-1,0,+1}.
// Usage: ./fibre_witness --defect 1 < candidate.txt
#include <algorithm>
#include <array>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <string>
#include <vector>
using namespace std;
static constexpr int N=25,L=50;

struct Key{
  uint64_t a=0,b=0,c=0;
  bool operator<(const Key&o)const{return a!=o.a?a<o.a:b!=o.b?b<o.b:c<o.c;}
  bool operator==(const Key&o)const{return a==o.a&&b==o.b&&c==o.c;}
};
struct KM{Key k;uint64_t mask=0;bool operator<(const KM&o)const{return k<o.k;}};

static int ac50(const array<int8_t,L>&x,int r){int s=0;for(int i=0;i<L-r;i++)s+=x[i]*x[i+r];return s;}
static bool pack(const array<int8_t,24>&v,Key&k){
  k={};int bit=0;
  for(int i=0;i<24;i++){
    int x=(int)v[i];if((x&1)||x<-50||x>50)return false;
    uint64_t z=(uint64_t)(x/2+25);int w=bit>>6,s=bit&63;
    uint64_t *p=w==0?&k.a:w==1?&k.b:&k.c;*p|=z<<s;
    if(s>58){if(w==2)return false;uint64_t *q=w==0?&k.b:&k.c;*q|=z>>(64-s);}bit+=6;
  }
  return true;
}
static int zeros(const array<int,N>&p){int z=0;for(int x:p)z+=!x;return z;}
static array<int8_t,L> lift(const array<int,N>&p,uint64_t mask){
  array<int8_t,L>x{};int q=0;
  for(int i=0;i<N;i++){
    if(p[i])x[i]=x[i+N]=(int8_t)p[i];
    else{int t=((mask>>q)&1)?1:-1;x[i]=(int8_t)t;x[i+N]=(int8_t)-t;q++;}
  }
  return x;
}
static array<int8_t,24> naf(const array<int,N>&p,uint64_t mask){
  auto x=lift(p,mask);array<int8_t,24> out{};
  for(int r=1;r<=24;r++)out[r-1]=(int8_t)(ac50(x,r)-ac50(x,50-r));
  return out;
}
static vector<KM> all_key_masks(const array<int,N>&p){
  const uint64_t M=1ULL<<zeros(p);vector<KM> out;out.reserve(M);
  for(uint64_t m=0;m<M;m++){Key k;if(!pack(naf(p,m),k))abort();out.push_back({k,m});}
  sort(out.begin(),out.end());
  // Keep one explicit mask for each signature; one is enough to construct a witness.
  out.erase(unique(out.begin(),out.end(),[](const KM&x,const KM&y){return x.k==y.k;}),out.end());
  return out;
}
static bool lookup(const vector<KM>&v,const array<int8_t,24>&sig,uint64_t&mask){
  Key k;if(!pack(sig,k))return false;KM probe{k,0};auto it=lower_bound(v.begin(),v.end(),probe);
  if(it==v.end()||!(it->k==k))return false;mask=it->mask;return true;
}
static bool validate_compressed(const array<int,N>&p,const array<int,N>&c){
  int sp=0,sc=0;for(int i=0;i<N;i++){if(abs(p[i])>1||abs(c[i])>1)return false;sp+=p[i];sc+=c[i];}
  if(sp!=10||sc!=0)return false;
  for(int r=0;r<N;r++){int h=0;for(int i=0;i<N;i++)h+=p[i]*c[(i-r+N)%N]+c[i]*p[(i-r+N)%N];if(h)return false;}
  return true;
}
static long long score100(const array<int8_t,100>&s,array<int,100>&C){
  long long E=0;C.fill(0);
  for(int k=1;k<100;k++){int v=0;for(int i=0;i<100-k;i++)v+=s[i]*s[i+k];C[k]=v;E+=1LL*v*v;}
  return E;
}
static string signs(const array<int8_t,100>&s){string z;z.reserve(100);for(auto x:s)z.push_back(x>0?'+':'-');return z;}

int main(int argc,char**argv){
  int defect=-1;
  for(int i=1;i<argc;i++){string a=argv[i];if(a=="--defect"&&i+1<argc)defect=atoi(argv[++i]);else{cerr<<"unknown arg "<<a<<"\n";return 2;}}
  if(defect<0||defect>2){cerr<<"--defect must be 0,1,2\n";return 2;}
  array<int,N>p{},c{};for(int i=0;i<N;i++)if(!(cin>>p[i])){cerr<<"need 25 p entries\n";return 2;}for(int i=0;i<N;i++)if(!(cin>>c[i])){cerr<<"need 25 c entries\n";return 2;}
  if(!validate_compressed(p,c)){cerr<<"INVALID_COMPRESSED_CANDIDATE\n";return 3;}
  array<int,N>q{};for(int j=0;j<N;j++)q[j]=c[(j+13)%N];
  int zp=zeros(p),zq=zeros(q);const array<int,N>*hp=&p,*pp=&q;bool hash_is_A=true;
  if(zp<zq){hp=&q;pp=&p;swap(zp,zq);hash_is_A=false;}
  auto table=all_key_masks(*hp);const uint64_t PM=1ULL<<zeros(*pp);
  for(uint64_t pm=0;pm<PM;pm++){
    auto pv=naf(*pp,pm);array<int8_t,24> base{};for(int i=0;i<24;i++)base[i]=(int8_t)-pv[i];
    uint64_t hm=0;bool found=false;
    if(defect==0) found=lookup(table,base,hm);
    else if(defect==1){
      for(int i=0;i<24&&!found;i++)for(int s:{-4,4}){auto v=base;v[i]=(int8_t)(v[i]+s);if(lookup(table,v,hm)){found=true;break;}}
    }else{
      for(int i=0;i<24&&!found;i++)for(int j=i+1;j<24&&!found;j++)for(int s1:{-4,4})for(int s2:{-4,4}){auto v=base;v[i]=(int8_t)(v[i]+s1);v[j]=(int8_t)(v[j]+s2);if(lookup(table,v,hm)){found=true;break;}}
    }
    if(!found)continue;
    array<int8_t,L>A{},B{};if(hash_is_A){A=lift(p,hm);B=lift(q,pm);}else{B=lift(q,hm);A=lift(p,pm);}
    array<int8_t,100>s{};for(int i=0;i<50;i++){s[2*i]=A[i];s[2*i+1]=B[i];}
    array<int,100>C{};long long E=score100(s,C);long long oddE=0,evenE=0;int oddBad=0;
    for(int k=1;k<100;k++){if(k&1){oddE+=1LL*C[k]*C[k];oddBad+=abs(C[k])!=1;}else evenE+=1LL*C[k]*C[k];}
    cout<<"WITNESS defect="<<defect<<" hash_mask="<<hm<<" probe_mask="<<pm
        <<" energy="<<E<<" odd_energy="<<oddE<<" even_energy="<<evenE
        <<" odd_bad="<<oddBad<<" sequence="<<signs(s)<<"\n";
    cout<<"CORRELATIONS";for(int k=1;k<100;k++)cout<<' '<<C[k];cout<<"\n";
    return 0;
  }
  cout<<"NO_WITNESS defect="<<defect<<"\n";
  return 1;
}
