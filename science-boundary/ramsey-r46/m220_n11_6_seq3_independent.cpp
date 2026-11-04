// Independent C++ bitset verification of m=220 n11=6 seq3 exclusion.
// Standard graph6 column-major decoder, exhaustive six-vertex B88 scan,
// and independent exact class-matrix enumeration. No SAT or row CSP.
#include <algorithm>
#include <array>
#include <cassert>
#include <cstdint>
#include <iostream>
#include <string>
#include <vector>
using namespace std;
using Bits=uint32_t;
static int pc(Bits x){return __builtin_popcount(x);}
static vector<Bits> decode(const string& g){
 int n=int(g[0])-63; assert(n==22);
 vector<Bits> a(n,0); int p=0;
 for(int j=1;j<n;j++)for(int i=0;i<j;i++){
  int value=int(g[1+p/6])-63;
  if((value>>(5-p%6))&1){a[i]|=Bits(1)<<j;a[j]|=Bits(1)<<i;}
  p++;
 }
 assert(p==231);
 int edges=0;for(Bits b:a)edges+=pc(b);
 assert(edges==176);
 return a;
}
struct Scan{array<int,7> hist{};int q3tri=0;};
static Scan run(const vector<Bits>& adj,int R){
 Scan sc; constexpr Bits limit=Bits(1)<<22;
 for(Bits mask=(Bits(1)<<6)-1;mask<limit;){
  int d3=0,d4=0,other=0;
  for(int v=0;v<22;v++)if(mask&(Bits(1)<<v)){
   int d=pc(adj[v]&mask);
   if(d==3)d3++;else if(d==4)d4++;else other++;
  }
  bool matches=R==22?(d3==2&&d4==4&&other==0):(d4==6&&other==0);
  if(matches){
   int q=0;array<int,3> rest{};
   for(int v=0;v<22;v++)if(!(mask&(Bits(1)<<v))&&(adj[v]&mask)==0){
    if(q<3)rest[q]=v;
    q++;
   }
   assert(q<7);sc.hist[q]++;
   if(q==3){
    assert(((adj[rest[0]]>>rest[1])&1) && ((adj[rest[0]]>>rest[2])&1)
           && ((adj[rest[1]]>>rest[2])&1));
    sc.q3tri++;
   }
  }
  Bits c=mask&(-mask), r=mask+c;
  if(r==0)break;
  mask=(((r^mask)>>2)/c)|r;
 }
 return sc;
}
int main(){
 const vector<string> B={
   "U?`@?bGKdWSWRELSWk?fGtHUMVEuH@VP`}HA[Ui?",
   "U?`D@`gFCkIWwcbK\\CPVOdQWu[Cqsadm@ddCRPM?",
   "U?`@?bGpDcCY[PCyTahjgxobZG@tbAxIaMYGRY`?"
 };
 const array<array<int,7>,3> e22={{{0,8,8,12,0,0,0},{0,11,11,0,0,0,0},{0,22,22,0,0,0,0}}};
 for(int i=0;i<3;i++){
  auto a=decode(B[i]);auto s22=run(a,22),s24=run(a,24);
  assert(s22.hist==e22[i]);assert((s24.hist==array<int,7>{}));
  assert(s22.q3tri==(i==0?12:0));
 }
 int all=0,d10=0,survive=0;
 for(int R:{22,24})for(int x=0;x<=45;x++)for(int y=0;y<=20;y++)for(int z=0;z<=1;z++){
  int c=66-R,a=130-2*x-y,b=28-y-2*z;
  int p2=216-c-a-b;
  if(min({a,b,p2})<0||p2%2)continue;
  int p=p2/2,s12=11*c+24*p+13*a+14*b,
      s13=12*a+26*x+14*y,s14=12*b+13*y+28*z;
  if(s12<2376||s12>2646||s13<1430||s13>1640||s14<308||s14>356)continue;
  int D=1640-s13;
  assert(D==80-2*(x+y) && D%2==0);
  assert(y+4*z>=R+D-14);
  all++;
  if(D>=10){
   d10++;
   int high_cap = z==0?16:13;
   if(y<=high_cap)survive++;
  }
 }
 assert(all==170 && d10==10 && survive==0);
 cout<<"B88 qmax [3,2,2], q3 triangles [12,0,0], R24 no profile; "
       "class matrices 170 -> 10 -> 0. PASS\n";
}
