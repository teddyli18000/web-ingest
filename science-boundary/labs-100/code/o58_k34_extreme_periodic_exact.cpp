// Exhaust O=58, K=34, (kp,kc)=(25,9), center cyclic defect.
// Prove/expose the minimum periodic spectrum SG before any fibre lift.
#include <bits/stdc++.h>
#include <omp.h>
using namespace std;
using U=uint32_t;
using A=array<int8_t,25>;
U aff(U x,int a,int b){U y=0;for(int i=0;i<25;i++)if(x>>i&1)y|=1u<<((a*i+b)%25);return y;}
vector<U> support_orbits(){
 vector<int>us;for(int a=1;a<25;a++)if(gcd(a,25)==1)us.push_back(a);
 unordered_set<U>seen;seen.reserve(2500000);vector<U>reps;
 U x=(1u<<9)-1;
 while(x<(1u<<25)){
  if(!seen.count(x)){reps.push_back(x);for(int a:us)for(int b=0;b<25;b++)seen.insert(aff(x,a,b));}
  U c=x&-x,r=x+c;if(!r||r>=(1u<<25))break;
  x=(((r^x)>>2)/c)|r;
 }
 assert(seen.size()==2042975);
 return reps;
}
struct Lin{array<array<uint8_t,25>,14>m{};array<int,14>rhs{},piv{};vector<int>fr;int rank=0;bool valid=true;};
Lin solve(const A&c){
 Lin z;
 for(int r=0;r<=12;r++)for(int j=0;j<25;j++)z.m[r][j]=(c[(j+r)%25]+c[(j-r+25)%25]+6)%3;
 for(int j=0;j<25;j++)z.m[13][j]=1;
 z.rhs[0]=2;z.rhs[13]=1;
 for(int j=0;j<25;j++){
  int pivot=-1;for(int r=z.rank;r<14;r++)if(z.m[r][j]){pivot=r;break;}
  if(pivot<0)continue;
  swap(z.m[pivot],z.m[z.rank]);swap(z.rhs[pivot],z.rhs[z.rank]);
  if(z.m[z.rank][j]==2){for(int k=0;k<25;k++)z.m[z.rank][k]=(2*z.m[z.rank][k])%3;z.rhs[z.rank]=(2*z.rhs[z.rank])%3;}
  for(int r=0;r<14;r++)if(r!=z.rank&&z.m[r][j]){
   int fac=z.m[r][j];for(int k=0;k<25;k++)z.m[r][k]=(z.m[r][k]+6-fac*z.m[z.rank][k])%3;
   z.rhs[r]=(z.rhs[r]+6-fac*z.rhs[z.rank])%3;
  }
  z.piv[z.rank++]=j;
 }
 for(int r=z.rank;r<14;r++)if(z.rhs[r])z.valid=false;
 bool isp[25]{};for(int r=0;r<z.rank;r++)isp[z.piv[r]]=true;
 for(int j=0;j<25;j++)if(!isp[j])z.fr.push_back(j);
 return z;
}
int cross(const A&p,const A&c,int r){int h=0;for(int i=0;i<25;i++)h+=p[i]*c[(i-r+25)%25]+c[i]*p[(i-r+25)%25];return h;}
int spectrum(const A&p,const A&c){int sg=0;for(int r=1;r<=12;r++){int g=0;for(int i=0;i<25;i++)g+=p[i]*p[(i+r)%25]+c[i]*c[(i+r)%25];sg+=g*g;}return sg;}
string sequence(const A&a){string s;for(auto v:a)s+=(v>0?'+':v<0?'-':'0');return s;}
int main(int argc,char**argv){
 auto reps=support_orbits();
 int n=argc>1?min(atoi(argv[1]),int(reps.size())):int(reps.size());
 cerr<<"support_reps="<<reps.size()<<" tested_reps="<<n<<"\n";
 atomic<long long>sign_tests{0},systems{0},p_exact{0},sgpass{0};
 atomic<int>bestSG{INT_MAX};
 #pragma omp parallel for schedule(dynamic,1)
 for(int idx=0;idx<n;idx++){
  U support=reps[idx];vector<int>ci;for(int j=0;j<25;j++)if(support>>j&1)ci.push_back(j);
  for(int mask=0;mask<(1<<9);mask++)if(__builtin_popcount((unsigned)mask)==4){
   sign_tests++;
   A c{};for(int j=0;j<9;j++)c[ci[j]]=(mask>>j&1)?-1:1;
   auto z=solve(c);if(!z.valid)continue;
   systems++;
   U maxmask=1u<<z.fr.size();
   for(U m=0;m<maxmask;m++){
    int x[25]{};for(int k=0;k<(int)z.fr.size();k++)x[z.fr[k]]=(m>>k&1)?2:1;
    bool ok=true;
    for(int r=z.rank-1;r>=0;r--){
     int value=z.rhs[r];for(int f:z.fr)value-=z.m[r][f]*x[f];
     value%=3;if(value<0)value+=3;
     if(!value){ok=false;break;}x[z.piv[r]]=value;
    }
    if(!ok)continue;
    A p{};int sum=0;for(int j=0;j<25;j++){p[j]=(x[j]==1)?1:-1;sum+=p[j];}
    if(sum!=1)continue;
    for(int r=0;r<=12;r++)if(cross(p,c,r)!=(r==0?2:0)){ok=false;break;}
    if(!ok)continue;
    p_exact++;
    int SG=spectrum(p,c),old=bestSG.load();
    while(SG<old&&!bestSG.compare_exchange_weak(old,SG)){}
    if(SG<=48){sgpass++;
      #pragma omp critical
      cout<<"SPECTRAL_SURVIVOR SG="<<SG<<" p="<<sequence(p)<<" c="<<sequence(c)<<"\n";
    }
   }
  }
 }
 cout<<"K34_PERIODIC_EXACT reps_tested="<<n<<" reps_total="<<reps.size()
     <<" c_sign_tests="<<sign_tests<<" systems="<<systems
     <<" p_exact="<<p_exact<<" minSG="<<bestSG<<" SG_le_48="<<sgpass<<"\n";
}
