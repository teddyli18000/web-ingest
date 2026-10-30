// Exact order-10 negaperiodic defect projection filter for the low11 h20 cases.
//
// Input is the exact low11 profile table produced by
// oddperfect_h20_w129_w131_order10_profiles.cpp:
//   packed_profile R0 R1 R2 R3 R4 R5
//
// The packed profile fixes the ten ordinary residue sums of A and B.  For each
// residue sum we enumerate every compatible alternating five-block fold,
// gamma_r = sum_{j=0}^4 (-1)^j A_{r+10j}, and likewise eta for B.
// Thus gamma,eta are the images of A,B in Z[x]/(x^10+1).
//
// Let F_t=NAF_A(t)+NAF_B(t), t=1..24.  In the three remaining low11 cases,
// the full order-25 fibre target has exactly one or two nonzero coordinates,
// each equal to +/-4.  Mapping Z[x]/(x^50+1) -> Z[x]/(x^10+1) sends
//
//   F_q^(10) = sum_{m=0}^4 (-1)^m F_{q+10m}.
//
// Enumerating all one-defect targets gives exactly 11 distinct signatures
// (norm,n1,n2,n3,n4); two distinct defect coordinates give exactly 61.
// A profile can survive defect d only if some compatible gamma,eta have a
// combined negaperiodic signature in that exact target set.
//
// Outputs <prefix>_d1.txt and <prefix>_d2.txt in the SAME row format as input,
// so they can be fed directly into the compressed/full order-10 models.
#include <algorithm>
#include <array>
#include <cstdint>
#include <fstream>
#include <functional>
#include <iostream>
#include <set>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>
#ifdef _OPENMP
#include <omp.h>
#else
static double omp_get_wtime(){return 0.0;}
#endif
using namespace std;

struct Sig{
 int v[5]{};
 bool operator==(const Sig&o)const{return equal(begin(v),end(v),begin(o.v));}
 bool operator<(const Sig&o)const{return lexicographical_compare(begin(v),end(v),begin(o.v),end(o.v));}
};
struct SigHash{
 size_t operator()(const Sig&s)const noexcept{uint64_t h=1469598103934665603ULL;for(int x:s.v){h^=(uint32_t)(x+512);h*=1099511628211ULL;}return (size_t)h;}
};
struct Row{uint64_t cp=0;array<int,6>R{};int ai=-1,bi=-1;};

static vector<int> topts(int s){
 vector<int>v;for(int p:{-3,-1,1,3})for(int q:{-2,0,2})if(p+q==s)v.push_back(p-q);
 sort(v.begin(),v.end());v.erase(unique(v.begin(),v.end()),v.end());return v;
}
static array<int,10> decode(uint64_t c){array<int,10>s{};for(int i=0;i<10;i++){s[i]=-5+2*(c%6);c/=6;}return s;}
static Sig sig_of(const array<int,10>&g){
 Sig s{};for(int x:g)s.v[0]+=x*x;
 for(int k=1;k<=4;k++){int z=0;for(int i=0;i<10-k;i++)z+=g[i]*g[i+k];for(int i=10-k;i<10;i++)z-=g[i]*g[i+k-10];s.v[k]=z;}
 return s;
}
static vector<Sig> signatures(uint64_t code,int maxnorm){
 auto s=decode(code);array<vector<int>,10>o;for(int i=0;i<10;i++)o[i]=topts(s[i]);
 vector<Sig>out;array<int,10>g{};
 function<void(int,int)>dfs=[&](int p,int norm){
  if(norm>maxnorm)return;
  if(p==10){out.push_back(sig_of(g));return;}
  for(int x:o[p]){g[p]=x;dfs(p+1,norm+x*x);}
 };
 dfs(0,0);sort(out.begin(),out.end());out.erase(unique(out.begin(),out.end()),out.end());return out;
}

static Sig defect_sig(const vector<pair<int,int>>&def){
 // Full negaperiodic polynomial coefficients in Z[x]/(x^50+1).
 int F[50]{};F[0]=100;
 for(auto [t,d]:def){F[t]+=d;F[50-t]-=d;}
 int q[10]{};for(int j=0;j<50;j++)q[j%10]+=((j/10)&1)?-F[j]:F[j];
 Sig s{};for(int i=0;i<5;i++)s.v[i]=q[i];return s;
}
static vector<Sig> targets(int d){
 set<Sig>S;
 if(d==1){for(int t=1;t<=24;t++)for(int s:{-4,4})S.insert(defect_sig({{t,s}}));}
 else if(d==2){for(int a=1;a<=24;a++)for(int b=a+1;b<=24;b++)for(int s:{-4,4})for(int t:{-4,4})S.insert(defect_sig({{a,s},{b,t}}));}
 else abort();
 return vector<Sig>(S.begin(),S.end());
}
static Sig sub(const Sig&a,const Sig&b){Sig z;for(int i=0;i<5;i++)z.v[i]=a.v[i]-b.v[i];return z;}

int main(int argc,char**argv){
 if(argc<3){cerr<<"usage: nearngp10 input_low11.txt output_prefix\n";return 2;}
 string in=argv[1],pre=argv[2];ifstream f(in);if(!f){cerr<<"cannot open input\n";return 2;}
 const uint64_t MASK=(1ULL<<26)-1;
 vector<Row> rows; vector<uint64_t>Ac,Bc; uint64_t cp; Row r;
 while(f>>cp){r={};r.cp=cp;for(int q=0;q<6;q++)f>>r.R[q];rows.push_back(r);Ac.push_back(cp&MASK);Bc.push_back(cp>>26);}
 sort(Ac.begin(),Ac.end());Ac.erase(unique(Ac.begin(),Ac.end()),Ac.end());
 sort(Bc.begin(),Bc.end());Bc.erase(unique(Bc.begin(),Bc.end()),Bc.end());
 unordered_map<uint64_t,int> ai,bi;for(int i=0;i<(int)Ac.size();i++)ai[Ac[i]]=i;for(int i=0;i<(int)Bc.size();i++)bi[Bc[i]]=i;
 vector<vector<int>> byB(Bc.size());
 for(int j=0;j<(int)rows.size();j++){rows[j].ai=ai[rows[j].cp&MASK];rows[j].bi=bi[rows[j].cp>>26];byB[rows[j].bi].push_back(j);}
 auto T1=targets(1),T2=targets(2);if(T1.size()!=11||T2.size()!=61){cerr<<"target-size regression failed "<<T1.size()<<" "<<T2.size()<<"\n";return 3;}
 int maxnorm=0;for(auto&s:T2)maxnorm=max(maxnorm,s.v[0]);for(auto&s:T1)maxnorm=max(maxnorm,s.v[0]); // 116
 cerr<<"INPUT rows="<<rows.size()<<" unique_A="<<Ac.size()<<" unique_B="<<Bc.size()<<" target_d1="<<T1.size()<<" target_d2="<<T2.size()<<" maxnorm="<<maxnorm<<"\n";
 double t0=omp_get_wtime();
 vector<vector<Sig>> AS(Ac.size()),BS(Bc.size());
#pragma omp parallel for schedule(dynamic,1)
 for(int i=0;i<(int)Ac.size();i++)AS[i]=signatures(Ac[i],maxnorm);
#pragma omp parallel for schedule(dynamic,1)
 for(int i=0;i<(int)Bc.size();i++)BS[i]=signatures(Bc[i],maxnorm);
 long long nas=0,nbs=0;for(auto&v:AS)nas+=v.size();for(auto&v:BS)nbs+=v.size();
 cerr<<"SIGNATURES A="<<nas<<" B="<<nbs<<" seconds="<<omp_get_wtime()-t0<<"\n";

 unordered_map<Sig,vector<int>,SigHash> index;
 for(int a=0;a<(int)AS.size();a++)for(const auto&s:AS[a])index[s].push_back(a);
 vector<char> keep1(rows.size()),keep2(rows.size());
#pragma omp parallel for schedule(dynamic,1)
 for(int b=0;b<(int)Bc.size();b++){
  if(byB[b].empty())continue;
  unordered_set<int> h1,h2;
  for(const auto&sb:BS[b]){
   for(const auto&T:T1){Sig need=sub(T,sb);if(need.v[0]<0)continue;auto it=index.find(need);if(it!=index.end())for(int a:it->second)h1.insert(a);}
   for(const auto&T:T2){Sig need=sub(T,sb);if(need.v[0]<0)continue;auto it=index.find(need);if(it!=index.end())for(int a:it->second)h2.insert(a);}
  }
  for(int j:byB[b]){keep1[j]=h1.count(rows[j].ai);keep2[j]=h2.count(rows[j].ai);}
 }
 ofstream o1(pre+"_d1.txt"),o2(pre+"_d2.txt");long long n1=0,n2=0;
 for(int j=0;j<(int)rows.size();j++){
  auto emit=[&](ofstream&o){o<<rows[j].cp;for(int q=0;q<6;q++)o<<' '<<rows[j].R[q];o<<'\n';};
  if(keep1[j]){emit(o1);n1++;}if(keep2[j]){emit(o2);n2++;}
 }
 cout<<"SUMMARY input="<<rows.size()<<" d1_survivors="<<n1<<" d2_survivors="<<n2<<" seconds="<<omp_get_wtime()-t0<<"\n";
 return 0;
}
