// Exhaustive post-audit high-subgraph verifier for m=220, n11=6, seq4.
// This is a necessary-condition enumeration, not a search heuristic.
//
// The six low vertices have no high neighbors (certified low orbits
// Ep~o and EznW), and have an independent pair. Consequently the
// high graph on eleven degree-13 vertices and one degree-15 vertex z
// is K4-free and has independence number at most three.
// Write T=N_H(z), with y=|T| in {7,8}; U=H\(T union {z}).
// T is triangle-free and alpha(T)<=3, hence belongs to McKay's
// complete R(3,4,y) catalogue of respectively 9 or 3 graphs.
// For any degree-13 vertex v, its neighbor-degree sum is
// S(v)=156+d_{H[13]}(v)+3*[vz], bounded by 164.
// The exact class-edge parameters still open after the prior
// high-anchor verifier are (x,y)=(29,8),(30,8),(31,7), with
// (30,8) representing two distinct low-class matrices.
//
// A degree-13 vertex is EXTREME exactly when S(v)=164. The certified
// unique extreme A32 and complete three-graph B88 catalogue give:
// at every extreme v, the other extreme vertices not adjacent to v
// occupy an induced subset of the four eligible B88 sites. They induce
// 2K2; so any three such vertices must induce exactly one edge, while
// four induce 2K2, and five are impossible. This is a sound necessary
// condition and never uses the withdrawn row-domain tf() predicate.
//
// Build: g++ -O3 -std=c++17 m220_n11_6_seq4_high_exact.cpp -o /tmp/m220_seq4
// Run:   /tmp/m220_seq4
// Audit B88 sites independently with m220_n11_6_seq4_b88_embed_verify.py.
#include <algorithm>
#include <array>
#include <cassert>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <numeric>
#include <string>
#include <vector>
using namespace std;
struct Counts{long long rows=0,good=0,pair=0;};
using Adj=array<uint16_t,12>;
static vector<array<int,4>> quads;
int pop(int v){return __builtin_popcount((unsigned)v);}
vector<string> read_lines(string path){ifstream f(path);vector<string> a;string s;while(getline(f,s)){if(!s.empty())a.push_back(s);}return a;}
Adj decode(string s, int n){assert(s[0]==char(n+63));Adj a{};int bit=0;for(int j=1;j<n;j++)for(int i=0;i<j;i++){int b=(int(s[1+bit/6])-63)>>(5-bit%6)&1;if(b){a[i]|=(1u<<j);a[j]|=(1u<<i);}bit++;}return a;}
void init(){for(int i=0;i<12;i++)for(int j=i+1;j<12;j++)for(int k=j+1;k<12;k++)for(int l=k+1;l<12;l++)quads.push_back({i,j,k,l});}
void validate_T(Adj const &a,int n){
 for(int i=0;i<n;i++)assert(pop(a[i])<=3);
 for(int i=0;i<n;i++)for(int j=i+1;j<n;j++)for(int k=j+1;k<n;k++)
  assert(!((a[i]>>j&1)&&(a[i]>>k&1)&&(a[j]>>k&1)));
 for(int i=0;i<n;i++)for(int j=i+1;j<n;j++)for(int k=j+1;k<n;k++)for(int l=k+1;l<n;l++)
  assert((a[i]>>j&1)||(a[i]>>k&1)||(a[i]>>l&1)||(a[j]>>k&1)||(a[j]>>l&1)||(a[k]>>l&1));
}

bool valid_H(Adj const&a){
 for(auto Q:quads){auto [i,j,k,l]=Q;int e=((a[i]>>j)&1)+((a[i]>>k)&1)+((a[i]>>l)&1)+((a[j]>>k)&1)+((a[j]>>l)&1)+((a[k]>>l)&1);if(e==0||e==6)return false;}
 return true;
}
bool allowed_pair(Adj const&a,int nt){
 vector<int> ext;
 for(int v=0;v<11;v++){
  int d=pop(a[v]&((1<<11)-1));
  int slack=8-d-3*(v<nt);
  assert(slack>=0);
  if(slack==0)ext.push_back(v);
 }
 for(int v:ext){
  vector<int> f;
  for(int u:ext)if(u!=v && !(a[v]>>u&1))f.push_back(u);
  if(f.size()>4)return false;
  if(f.size()<3)continue;
  int e=0,maxd=0;
  for(int u:f){int d=0;for(int w:f)if(w!=u&&(a[u]>>w&1))d++;maxd=max(maxd,d);e+=d;}
  e/=2;
  if(f.size()==3 && e!=1)return false;
  if(f.size()==4 && (e!=2||maxd!=1))return false;
 }
 return true;
}
Counts run_one(Adj T,int nt,int x){
 int nu=11-nt,et=0;for(int i=0;i<nt;i++)et+=pop(T[i]);et/=2;
 Counts result;
 for(int mu=0;mu<(1<<(nu*(nu-1)/2));mu++){
  Adj base{};
  for(int i=0;i<nt;i++){base[i]=T[i]|(1u<<11);base[11]|=1u<<i;}
  int iu=0,eu=0;
  for(int i=0;i<nu;i++)for(int j=i+1;j<nu;j++){
   if(mu>>iu&1){base[nt+i]|=1u<<(nt+j);base[nt+j]|=1u<<(nt+i);eu++;}
   iu++;
  }
  int target=x-et-eu;
  if(target<0)continue;
  array<int,12> cap{};vector<vector<int>> masks(nt);
  int possible=0;
  for(int i=0;i<nt;i++){
   cap[i]=5-pop(T[i]);possible+=cap[i];
   for(int m=0;m<(1<<nu);m++)if(pop(m)<=cap[i])masks[i].push_back(m);
  }
  if(target>possible)continue;
  // Final H has fixed 13-13 edge count and 13-15 edge count.
  // Iteratively choose the complete T--U incidence matrix.
  Adj a=base;
  auto rec=[&](auto&&self,int row,int remaining)->void{
   if(remaining<0)return;
   if(row==nt){
    if(remaining)return;
    for(int i=0;i<nu;i++)if(pop(a[nt+i]&((1<<11)-1))>8)return;
    result.rows++;
    if(!valid_H(a))return;
    result.good++;
    if(allowed_pair(a,nt))result.pair++;
    return;
   }
   int upper=0;for(int j=row;j<nt;j++)upper+=cap[j];
   if(remaining>upper)return;
   for(int m:masks[row]){
    int pc=pop(m);
    if(pc>remaining)continue;
    bool ok=true;
    for(int k=0;k<nu;k++)if((m>>k&1) && pop(a[nt+k]&((1<<11)-1))>=8)ok=false;
    if(!ok)continue;
    a[row]=base[row]|(1u<<11);
    for(int k=0;k<nu;k++)if(m>>k&1){a[row]|=1u<<(nt+k);a[nt+k]|=1u<<row;}
    self(self,row+1,remaining-pc);
    for(int k=0;k<nu;k++)if(m>>k&1)a[nt+k]&=~(1u<<row);
   }
  };
  rec(rec,0,target);
 }
 return result;
}
// McKay's complete R(3,4,7) and R(3,4,8) graph6 catalogues.
// https://users.cecs.anu.edu.au/~bdm/data/ramsey.html
// The n=7 list also follows from the complete NetworkX 7-vertex atlas;
// the n=8 list can be independently reconstructed by adding one vertex
// with all 2^7 neighborhoods to each atlas graph on 7 vertices.
int main(){
 init();
 struct Case{int nt,x;vector<string>g6;long long nrows,ngood;};
 vector<Case> cases={
  {8,29,{"GPq?jG","GHhGm_","GlO[PK"},770466,13647},
  {8,30,{"GPq?jG","GHhGm_","GlO[PK"},125628,708},
  {7,31,{"Fhc?G","FPq?g","FhCKG","FHhGg","Fh_gg","FhEK_","FlO[O","FlgGg","FhUk_"},15577688,2256}
 };
 cout<<"{\n  \"campaign\": \"m220-n11-6-seq4-high-exact-post-audit\",\n";
 cout<<"  \"degree_sequence\": \"11^6 12^18 13^11 15\",\n";
 cout<<"  \"patterns\": [\n";
 for(int c=0;c<(int)cases.size();c++){
  auto C=cases[c];long long rows=0,good=0,pair=0;
  for(auto g:C.g6){
   auto T=decode(g,C.nt);validate_T(T,C.nt);
   auto r=run_one(T,C.nt,C.x);
   rows+=r.rows;good+=r.good;pair+=r.pair;
  }
  assert(rows==C.nrows && good==C.ngood && pair==0);
  cout<<"    {\"e13_13\": "<<C.x<<", \"e13_15\": "<<C.nt
      <<", \"T_isomorphism_types\": "<<C.g6.size()
      <<", \"degree_feasible_labelled\": "<<rows
      <<", \"K4_alpha3_feasible\": "<<good
      <<", \"B88_extreme_pair_compatible\": "<<pair<<"}"
      <<(c+1<(int)cases.size()?",":"")<<"\n";
 }
 cout<<"  ],\n  \"all_four_class_patterns_excluded\": true,\n"
     <<"  \"explanation\": \"Two e13_13=30,e13_15=8 class matrices share the same high-only case; all three cases are exact relaxations.\"\n}\n";
}
