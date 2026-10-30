#include <algorithm>
#include <array>
#include <cstdint>
#include <iostream>
#include <numeric>
#include <set>
#include <string>
#include <vector>
using namespace std;
static constexpr int N=25;
using A=array<int,N>; using Mask=uint32_t;

static vector<int> units(){vector<int>u;for(int a=1;a<N;a++)if(gcd(a,N)==1)u.push_back(a);return u;}
static Mask tr(Mask m,int a,int b){Mask y=0;for(int i=0;i<N;i++)if(m>>i&1)y|=1u<<((a*i+b)%N);return y;}
static Mask canon(Mask m){Mask z=~0u;for(int a:units())for(int b=0;b<N;b++)z=min(z,tr(m,a,b));return z;}

static vector<array<int,12>> types(){
 vector<vector<int>> raw={
  {2,2,2,2,2,3,3,3,3,3,3,3},
  {2,2,2,2,2,2,3,3,3,3,3,4},
  {2,2,2,2,2,2,2,3,3,3,4,4},
  {2,2,2,2,2,2,2,2,3,4,4,4},
  {1,2,2,2,2,2,2,2,4,4,4,4},
  {1,2,2,2,2,2,2,3,3,4,4,4},
  {1,2,2,2,2,2,3,3,3,3,4,4},
  {1,2,2,2,2,3,3,3,3,3,3,4},
  {1,2,2,2,3,3,3,3,3,3,3,3},
  {2,2,2,2,2,2,2,2,2,4,4,5},
  {2,2,2,2,2,2,2,2,3,3,4,5},
  {2,2,2,2,2,2,2,3,3,3,3,5}
 };
 vector<array<int,12>> out;
 for(auto v:raw){sort(v.begin(),v.end());array<int,12>a{};copy(v.begin(),v.end(),a.begin());out.push_back(a);}
 sort(out.begin(),out.end());out.erase(unique(out.begin(),out.end()),out.end());return out;
}
static bool isbase(const array<int,12>&g){
 vector<vector<int>> r={{2,2,2,2,2,3,3,3,3,3,3,3},{2,2,2,2,2,2,3,3,3,3,3,4},{2,2,2,2,2,2,2,3,3,3,4,4},{2,2,2,2,2,2,2,2,3,4,4,4}};
 for(auto v:r){array<int,12>a{};copy(v.begin(),v.end(),a.begin());if(a==g)return true;}return false;
}
static array<int,12> paf(const A&p){array<int,12>g{};for(int r=1;r<=12;r++){int s=0;for(int i=0;i<N;i++)s+=p[i]*p[(i+r)%N];g[r-1]=s;}sort(g.begin(),g.end());return g;}

int main(){
 auto T=types(); if(T.size()!=12){cerr<<"unexpected target type count\n";return 3;} cerr<<"types="<<T.size()<<"\n";
 // kp=19,kc=0: p has six zeros and sum p=9, hence exactly five negative signs.
 set<Mask> reps;
 for(Mask m=0;m<(1u<<N);m++){if(__builtin_popcount(m)!=6)continue;Mask c=canon(m);if(c==m)reps.insert(m);}
 if(reps.size()!=366){cerr<<"unexpected support orbit count "<<reps.size()<<"\n";return 3;}
 cerr<<"support_orbits="<<reps.size()<<"\n";
 long long tests=0,hits=0,base=0;int sid=0;set<Mask> hit_supports;
 for(Mask z:reps){
  sid++;vector<int> nz;for(int i=0;i<N;i++)if(!(z>>i&1))nz.push_back(i);
  int M=nz.size();uint32_t comb=(1u<<5)-1,limit=1u<<M;
  while(comb<limit){
   A p{};for(int i:nz)p[i]=1;for(int j=0;j<M;j++)if(comb>>j&1)p[nz[j]]=-1;
   tests++;auto g=paf(p);
   if(binary_search(T.begin(),T.end(),g)){
    hits++;bool b=isbase(g);base+=b;hit_supports.insert(z);
    cout<<"HIT sid="<<sid<<" base="<<b<<" zeros=";
    for(int i=0;i<N;i++)if(z>>i&1)cout<<i<<',';
    cout<<" p=";for(int x:p)cout<<x<<',';
    cout<<" G=";for(int x:g)cout<<x<<',';cout<<"\n";
   }
   uint32_t c=comb&-comb,r=comb+c;if(!r)break;comb=(((r^comb)>>2)/c)|r;
  }
 }
 cerr<<"SUMMARY support_orbits="<<reps.size()<<" sign_tests="<<tests<<" spectral_hits="<<hits<<" base_hits="<<base<<" hit_support_orbits="<<hit_supports.size()<<"\n";
 if(tests!=4255848 || hits!=96 || base!=5 || hit_supports.size()!=73)return 4;
}
