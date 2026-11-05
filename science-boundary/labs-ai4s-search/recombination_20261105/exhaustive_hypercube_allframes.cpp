// Exhaustively certify the two-source-parent inheritance hypercube at low N.
// This checks every feasible LABS symmetry orientation with D<=21; a bounded structural oracle study, NOT a prospective search algorithm.
#define main hypercube_legacy_main
#include "../lns_mask.cpp"
#undef main
#include <map>
#include <unordered_set>
#include <climits>
#include <sstream>
#include <iomanip>
using namespace std;
struct P {string id,s,canonical;int n,E,ref;L Ls;};
L frombits(string s){vector<int>v;for(char c:s)v.push_back(c=='1'?1:-1);return L(v);}
string tob(const L&q){string x;for(int z:q.s)x+=(z>0?'1':'0');return x;}
string neg(const string&s){string x=s;for(char&c:x)c=(c=='1'?'0':'1');return x;}
string alt(const string&s){string x=s;for(int i=1;i<(int)x.size();i++)if(i&1)x[i]=(x[i]=='1'?'0':'1');return x;}
vector<string> orbit(const string&s){
 set<string>v;for(int j=0;j<2;j++){string t=s;if(j)reverse(t.begin(),t.end());
  for(int k=0;k<2;k++){string z=k?alt(t):t;v.insert(z);v.insert(neg(z));}}
 return vector<string>(v.begin(),v.end());
}
string canon(const string&s){auto x=orbit(s);return x[0];}
int hd(string a,string b){int x=0;for(int i=0;i<(int)a.size();i++)x+=(a[i]!=b[i]);return x;}
string align(string a,string b){
 auto x=orbit(b);
 return *min_element(x.begin(),x.end(),[&](auto&l,auto&r){
  return pair<int,string>(hd(a,l),l)<pair<int,string>(hd(a,r),r);
 });
}
vector<P> load(string p){
 ifstream f(p);if(!f)throw runtime_error("missing source");
 string line;getline(f,line);vector<P>v;
 while(getline(f,line)){
  if(line.empty())continue;
  istringstream is(line);P q;string provenance,lineage,row,near;
  is>>q.id>>q.n>>q.E>>q.s>>q.canonical>>provenance>>lineage>>row>>near>>q.ref;
  q.Ls=frombits(q.s);
  if(q.Ls.e!=q.E||energy_direct(q.Ls.s)!=q.E||canon(q.s)!=q.canonical)throw runtime_error("parent certificate");
  v.push_back(q);
 }return v;
}
struct Peak{int E;uint32_t mask;};
void retain_top(vector<Peak>&top,int target,int E,uint32_t mask){
 if((int)top.size()<target){top.push_back({E,mask});return;}
 int worst=0;
 for(int i=1;i<(int)top.size();i++)if(top[i].E>top[worst].E)worst=i;
 if(E<top[worst].E)top[worst]={E,mask};
}
L instantiate(L base,const vector<int>&diff,uint32_t mask){
 for(int j=0;j<(int)diff.size();j++)if(mask>>j&1)base.flip(diff[j]);
 return base;
}
L repair(L x,mt19937_64&rng){
 x.descend(0);L cur=x,best=x;
 vector<int>last(x.n,-1000000);
 for(int t=0;t<64;t++){
  int p=-1,bd=INT_MAX;
  for(int i=0;i<x.n;i++){int d=cur.delta(i);
   if(t-last[i]<=7 && cur.e+d>=best.e)continue;
   if(d<bd||(d==bd&&(rng()&1)))bd=d,p=i;
  }
  if(p<0)p=rng()%x.n;
  cur.flip(p);last[p]=t;if(cur.e<best.e)best=cur;
 }
 best.descend(0);return best;
}
int main(int argc,char**argv){
 if(argc<4){cerr<<"usage PARENTS.tsv SUMMARY.tsv MAX_D (<=22)\n";return 2;}
 auto sources=load(argv[1]);ofstream out(argv[2]);int maxD=stoi(argv[3]);
 if(maxD>22||maxD<3)throw runtime_error("maxD must be 3..22");
 map<int,vector<P*>>byN;for(auto &p:sources)if(p.n<=50)byN[p.n].push_back(&p);
 out<<"N\tpair\tframe\tdonor_bits\tD\tstates\tmixed_states\tmaxD\trefE\tA_E\tB_E\t"
    "mixed_best_E\tbalanced_best_E\t"
    "mixed_le5_count\tmixed_le10_count\tmixed_le5_unique_orbits\tmixed_le10_unique_orbits\t"
    "balanced_top32_best_repaired_E\tbalanced_random32_best_repaired_E\t"
    "top32_nonparent_repaired_le10\t"
    "mean_all_E\tdirect_check_sampled\telapsed_seconds\n";
 out<<fixed<<setprecision(7);
 int pairs=0,skipped=0;long long all_states=0;
 for(auto &[n,pool]:byN){
  int ref=INT_MAX;set<string>allparent;for(auto*p:pool){ref=min(ref,p->ref);allparent.insert(p->canonical);}
  for(int i=0;i<(int)pool.size();i++)for(int j=i+1;j<(int)pool.size();j++){
   const P&A=*pool[i],&B=*pool[j];int frameIndex=0;
   for(const string& donor:orbit(B.s)){
    int frame=frameIndex++;
   vector<int>diff;for(int x=0;x<n;x++)if(A.s[x]!=donor[x])diff.push_back(x);
   int D=diff.size();if(D>maxD){skipped++;continue;}
   auto t0=clk::now();
   uint32_t count=1u<<D;
   L cur=A.Ls;int mixed_best=INT_MAX,balanced_best=INT_MAX,checkCount=0;
   uint64_t mixed=0,c5=0,c10=0,allEnergy=0;
   set<string>uniq5,uniq10;
   vector<Peak>top;vector<Peak>randomTop;
   mt19937_64 rng(20261105ULL+n*2017ULL+i*113ULL+j*311);
   const int half=D/2,band=max(1,D/6);
   // Uniform sample exact (among balanced donor fractions) while enumerating,
   // not a separate parent source or an allegedly independent elite.
   uint64_t chosen=0;vector<Peak>reservoir;
   for(uint32_t t=0;t<count;t++){
    uint32_t gray=t^(t>>1);
    if(t)cur.flip(diff[__builtin_ctz(t)]);
    int h=__builtin_popcount(gray);
    if(t%997==0){if(cur.e!=energy_direct(cur.s))throw runtime_error("enumeration incremental E mismatch");checkCount++;}
    if(cur.e<ref)throw runtime_error("contradicts exact known N<=66 optimum");
    allEnergy+=(uint64_t)cur.e;
    if(h==0||h==D)continue;
    mixed++;mixed_best=min(mixed_best,cur.e);
    if(abs(h-half)<=band){
     balanced_best=min(balanced_best,cur.e);
     retain_top(top,32,cur.e,gray);
     chosen++;
     // Source-fixed random uniform among balanced positions by reservoir sampling
     if(reservoir.size()<32)reservoir.push_back({cur.e,gray});
     else {uint64_t k=rng()%chosen;if(k<32)reservoir[k]={cur.e,gray};}
    }
    if(cur.e<=ref*1.10){
     auto can=canon(tob(cur));
     if(!allparent.count(can)){c10++;uniq10.insert(can);}
     if(cur.e<=ref*1.05 && !allparent.count(can)){c5++;uniq5.insert(can);}
    }
   }
   if(mixed==0||top.empty()||reservoir.size()!=32)throw runtime_error("no balanced mixes");
   auto evaluate=[&](const vector<Peak>&v,bool qualify)->pair<int,int>{
    int best=INT_MAX,good=0;
    for(const auto&p:v){
     L child=instantiate(A.Ls,diff,p.mask);
     if(child.e!=p.E||energy_direct(child.s)!=p.E)throw runtime_error("retained mask discrepancy");
     auto q=repair(child,rng);if(q.e!=energy_direct(q.s))throw runtime_error("repair scorer");
     auto ca=canon(tob(q));
     best=min(best,q.e);
     good+=(q.e<=ref*1.10&&!allparent.count(ca));
    }
    return {best,good};
   };
   auto topOutcome=evaluate(top,true),baseOutcome=evaluate(reservoir,false);
   double sec=ns(clk::now()-t0).count();
   out<<n<<"\t"<<A.id<<"-"<<B.id<<"\t"<<frame<<"\t"<<donor<<"\t"<<D<<"\t"<<count<<"\t"<<mixed
     <<"\t"<<maxD<<"\t"<<ref<<"\t"<<A.E<<"\t"<<B.E<<"\t"
     <<mixed_best<<"\t"<<balanced_best<<"\t"<<c5<<"\t"<<c10
     <<"\t"<<uniq5.size()<<"\t"<<uniq10.size()
     <<"\t"<<topOutcome.first<<"\t"<<baseOutcome.first<<"\t"<<topOutcome.second
     <<"\t"<<double(allEnergy)/count<<"\t"<<checkCount<<"\t"<<sec<<"\n";
   pairs++;all_states+=count;out.flush();
   cerr<<"N "<<n<<" pair "<<A.id<<"-"<<B.id<<" D="<<D<<" states="<<count
       <<" mixed_min="<<mixed_best<<" unique<=10%="<<uniq10.size()<<" top_repair="<<topOutcome.first<<"\n";
   }
  }
 }
 cerr<<"PASS "<<pairs<<" complete pair inheritance hypercubes, "<<all_states
     <<" exact Gray-code states, "<<skipped<<" declared D>"<<maxD<<" exclusions\n";
}
