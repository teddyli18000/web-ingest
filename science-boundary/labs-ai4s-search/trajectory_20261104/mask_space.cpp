// Explore a *different* LABS action representation: exact fixed-Hamming-weight
// macro masks optimized by pairwise swaps inside mask space, rather than
// sequential low-energy bit flips in sequence space.
// Same wall-clock search time compared to i.i.d. random 12-bit subsets.
// This is candidate-generation-only. Post-descent is retrospective diagnostics.
#define main legacy_main_unused
#include "../lns_mask.cpp"
#undef main
#include <fstream>
#include <set>
#include <map>
#include <iomanip>
using namespace std;

struct Source{int n,e;string bits,provenance;};
vector<Source> load(const string&p){
 ifstream f(p);if(!f)throw runtime_error("missing corpus");string line;getline(f,line);
 map<int,set<int>> select={{64,{208}},{80,{352}},{92,{490}},{99,{553,577}},{100,{578}}};
 vector<Source> v;
 while(getline(f,line)){
  istringstream is(line);Source z;string parent,seed,near,orbit;
  if(!(is>>z.n>>z.e>>z.bits>>z.provenance>>parent>>seed>>near>>orbit))continue;
  if(select.count(z.n)&&select[z.n].count(z.e)){
    vector<int> s;for(char c:z.bits)s.push_back(c=='1'?1:-1);
    L a(s);if(a.e!=z.e||energy_direct(a.s)!=z.e)throw runtime_error("reference E invalid");
    v.push_back(z);
  }
 }
 if(v.size()!=6)throw runtime_error("expected six distinct anchor states, got "+to_string(v.size()));
 return v;
}
L mask_candidate(const L&base,const vector<int>&ids){
 L z=base;for(int i:ids)z.flip(i);return z;
}
void binenergy(const L&a,int&odd,int&even){
 odd=even=0;for(int k=1;k<a.n;k++)((k&1)?odd:even)+=a.c[k]*a.c[k];
 if(odd+even!=a.e)throw runtime_error("parity mismatch");
}
int ham(const L&a,const L&b){int r=0;for(int i=0;i<a.n;i++)r+=(a.s[i]!=b.s[i]);return r;}
uint64_t seedhash(uint64_t x){x+=0x9e3779b97f4a7c15ULL;x=(x^(x>>30))*0xbf58476d1ce4e5b9ULL;x=(x^(x>>27))*0x94d049bb133111ebULL;return x^(x>>31);}
int main(int argc,char**argv){
 if(argc<5){cerr<<"usage IN.tsv OUT.tsv REP BUDGET_MS [M=12]\n";return 2;}
 auto sources=load(argv[1]);ofstream out(argv[2]);int reps=stoi(argv[3]),m=argc>5?stoi(argv[5]):12;
 double target=stod(argv[4])/1000.;
 out<<"id\tn\tsourceE\tnear\tmethod\trep\tm\tbestE\tpostRelaxE\tdistFromSource\tpostDistance\tbestOdd\tbestEven\tproposals\tseconds\n";
 out<<fixed<<setprecision(8);
 for(int q=0;q<(int)sources.size();q++){
  const auto &z=sources[q];vector<int>sign;for(char c:z.bits)sign.push_back(c=='1'?1:-1);
  L base(sign);
  for(int rep=0;rep<reps;rep++)for(int method=0;method<2;method++){
   mt19937_64 rng(seedhash(98117711ULL+q*1000003ULL+rep*10009ULL+method*37ULL));
   L best=base;best.e=INT_MAX;vector<int>chosen;L cur=base;int proposals=0,stall=0;
   auto t0=clk::now();
   if(method==1){chosen=random_mask(base.n,m,rng);cur=mask_candidate(base,chosen);best=cur;proposals++;}
   while(ns(clk::now()-t0).count()<target){
    L trial=base;
    if(method==0){
     auto ids=random_mask(base.n,m,rng);
     trial=mask_candidate(base,ids);
    }else{
     int j=uniform_int_distribution<int>(0,m-1)(rng);
     int a=chosen[j],b;
     do{b=uniform_int_distribution<int>(0,base.n-1)(rng);}while(binary_search(chosen.begin(),chosen.end(),b));
     trial=cur;trial.flip(a);trial.flip(b);
     if(trial.e<cur.e){
      cur=trial;
      chosen.erase(chosen.begin()+j);
      chosen.insert(lower_bound(chosen.begin(),chosen.end(),b),b);
      stall=0;
     }else stall++;
     if(stall>300){
      chosen=random_mask(base.n,m,rng);
      cur=mask_candidate(base,chosen);
      stall=0;
     }
    }
    if(trial.e<best.e)best=trial;
    if(method==1 && cur.e<best.e)best=cur;
    proposals++;
   }
   double seconds=ns(clk::now()-t0).count();
   L post=best;post.descend(0); // retrospective diagnostic, NOT in search clock
   if(energy_direct(best.s)!=best.e||energy_direct(post.s)!=post.e||ham(best,base)!=m)
    throw runtime_error("candidate exactness or distance failed");
   int odd,even;binenergy(best,odd,even);
   int n=z.n;int near=(n%2==1)?0:0; // actual class source published in separate frozen corpus
   out<<q<<"\t"<<n<<"\t"<<z.e<<"\t"<<near<<"\t"<<method<<"\t"<<rep<<"\t"<<m<<"\t"
      <<best.e<<"\t"<<post.e<<"\t"<<ham(best,base)<<"\t"<<ham(post,base)<<"\t"
      <<odd<<"\t"<<even<<"\t"<<proposals<<"\t"<<seconds<<"\n";
  }
  cerr<<"completed "<<q<<" N="<<z.n<<" E="<<z.e<<"\n";
 }
}
