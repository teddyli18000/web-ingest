// Exact orbit + meet-in-the-middle exclusion for W127 order-25 ka=20,kc=6.
//
// p has support 20 and sum 10, hence 15 entries +1, 5 entries -1 and 5
// zeros. Write p=1-z-2n with |z|=|n|=5.  For fixed c the order-25 cross
// condition is linear in p, and since sum(c)=0 the all-ones vector is in its
// kernel. Thus the exact condition is M z + 2 M n = 0.
//
// c has support 6 and sum 0, hence three +1 and three -1 entries. Common affine
// maps of Z_25 and an independent global sign of c preserve the cross equation,
// support data, and the combined PAF target. The code constructs all orbits
// explicitly, verifies that all 3,542,000 raw c states are covered, and then
// performs the exact subset-sum search in every orbit representative.
#include <bits/stdc++.h>
#include <omp.h>
using namespace std;
static const int N=25,R=13;
struct Key{array<signed char,R>a{};bool operator==(Key const&o)const{return a==o.a;}};
struct Hash{size_t operator()(Key const&k)const{size_t h=1469598103934665603ULL;for(auto x:k.a){h^=(unsigned char)(x+32);h*=1099511628211ULL;}return h;}};
static vector<int> units;
static uint32_t transmask(uint32_t m,int a,int b){uint32_t o=0;for(int i=0;i<N;i++)if(m>>i&1)o|=1u<<((a*i+b)%N);return o;}
static uint64_t enc(uint32_t p,uint32_t n){return ((uint64_t)p<<25)|n;}
static pair<uint32_t,uint32_t> dec(uint64_t x){return {(uint32_t)(x>>25),(uint32_t)(x&((1u<<25)-1))};}
static vector<uint64_t> gen_classes(){
 for(int a=1;a<N;a++)if(gcd(a,N)==1)units.push_back(a);
 unordered_set<uint64_t> visited; visited.reserve(4500000); vector<uint64_t> reps;
 vector<uint32_t> triples;for(int a=0;a<N;a++)for(int b=a+1;b<N;b++)for(int c=b+1;c<N;c++)triples.push_back((1u<<a)|(1u<<b)|(1u<<c));
 for(uint32_t p:triples) for(uint32_t n:triples) if(!(p&n)){
   uint64_t x=enc(p,n); if(visited.find(x)!=visited.end())continue; reps.push_back(x);
   for(int a:units)for(int b=0;b<N;b++){
      uint32_t pp=transmask(p,a,b),nn=transmask(n,a,b);
      visited.insert(enc(pp,nn)); visited.insert(enc(nn,pp));
   }
 }
 const long long raw=2300LL*1540; // C(25,3)*C(22,3)
 cerr<<"raw="<<raw<<" visited="<<visited.size()<<" classes="<<reps.size()<<"\n";
 if((long long)visited.size()!=raw || reps.size()!=3586) throw runtime_error("orbit coverage mismatch");
 return reps;
}
static vector<uint32_t> subsets5(){vector<uint32_t>v;for(int a=0;a<N;a++)for(int b=a+1;b<N;b++)for(int c=b+1;c<N;c++)for(int d=c+1;d<N;d++)for(int e=d+1;e<N;e++)v.push_back((1u<<a)|(1u<<b)|(1u<<c)|(1u<<d)|(1u<<e));return v;}
static int paf(const array<int,N>&x,int r){int s=0;for(int i=0;i<N;i++)s+=x[i]*x[(i+r)%N];return s;}
int main(){
 auto reps=gen_classes();auto subs=subsets5();cerr<<"sub5="<<subs.size()<<" threads="<<omp_get_max_threads()<<"\n";
 atomic<long long> TC{0},TT{0}; atomic<int> done{0};
#pragma omp parallel for schedule(dynamic,1)
 for(size_t idx=0;idx<reps.size();idx++){
   auto [pm,nm]=dec(reps[idx]);array<int,N>c{};for(int i=0;i<N;i++){if(pm>>i&1)c[i]=1;else if(nm>>i&1)c[i]=-1;}
   array<array<int,R>,N> col{};for(int j=0;j<N;j++)for(int r=0;r<R;r++)col[j][r]=c[(j-r+N)%N]+c[(j+r)%N];
   unordered_map<Key,vector<uint32_t>,Hash> sums;sums.reserve(90000);
   // Hash all five negative positions of p.
   for(uint32_t m:subs){Key k;for(int r=0;r<R;r++){int s=0;uint32_t q=m;while(q){int j=__builtin_ctz(q);q&=q-1;s+=col[j][r];}k.a[r]=(signed char)s;}sums[k].push_back(m);}
   long long cc=0,tt=0;
   // Enumerate the five zero positions and solve Mz+2Mn=0.
   for(uint32_t zm:subs){Key t;bool ok=true;for(int r=0;r<R;r++){int s=0;uint32_t q=zm;while(q){int j=__builtin_ctz(q);q&=q-1;s+=col[j][r];}if(s&1){ok=false;break;}t.a[r]=(signed char)(-s/2);}if(!ok)continue;auto it=sums.find(t);if(it==sums.end())continue;
     for(uint32_t neg:it->second){if(neg&zm)continue;cc++;array<int,N>p;p.fill(1);for(int i=0;i<N;i++){if(zm>>i&1)p[i]=0;else if(neg>>i&1)p[i]=-1;}
       // Recheck all 25 cross coefficients from the original integer equation.
       bool good=true;for(int r=0;r<N;r++){int h=0;for(int i=0;i<N;i++)h+=p[i]*c[(i-r+N)%N]+c[i]*p[(i-r+N)%N];if(h){good=false;break;}}if(!good) abort();
       int sm=0;for(int r=1;r<=12;r++){int z=paf(p,r)+paf(c,r);if(z<2||z>4){good=false;break;}sm+=z;}
       if(good&&sm==37)tt++;
     }
   }
   TC+=cc;TT+=tt;int d=++done;
   if(d%100==0){
#pragma omp critical
     cerr<<"done="<<d<<"/"<<reps.size()<<" cross="<<TC.load()<<" target="<<TT.load()<<"\n";
   }
 }
 cout<<"SUMMARY classes="<<reps.size()<<" cross="<<TC.load()<<" target="<<TT.load()<<"\n";
 if(TT.load()!=0)return 1;
}
