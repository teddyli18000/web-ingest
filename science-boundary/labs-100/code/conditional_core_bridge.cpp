// Conditional-core LABS repair, exact integer autocorrelations.
// Reproduces hidden-teacher recovery experiment, with matched full-tabued control.
// mode: 0=N60 E218, 1=N100 E606, 2=N100 E578.
// Invocation:
// g++ -O3 -std=c++20 -fopenmp code/conditional_core_bridge.cpp -o /tmp/core
// /tmp/core <mode> 40 30000 <40|50> 9 0 <seedtag>   # core
// /tmp/core <mode> 40 <20000|15000> <40|50> 9 1 <seedtag> # full control
#include <algorithm>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <random>
#include <vector>
#include <string>
#include <numeric>
#include <chrono>
#ifdef _OPENMP
#include <omp.h>
#endif
using namespace std;
const string T60="++--++-+--++--+++-+--++++--+-+++-+-+-++++-++-+-++++++-------";
const string T606="+++++--++----++--++++--++++++++++++--+----+++++----++-+----++--++-+++--+--+-+-++-++-+-+-+-+-+--+-+-+";
const string T578="++++++--+++++-----++-++--+--++++++++++---+-++--++++-+--++----+--+-+-+-+-++---++---++-+-++-+-++--+-+-";
struct State{vector<int8_t>s;vector<int> c;int e=0;
 State(vector<int8_t> seq):s(move(seq)),c(s.size()){
  int n=s.size();for(int k=1;k<n;k++){
   int v=0;for(int i=0;i+k<n;i++)v+=s[i]*s[i+k];c[k]=v;e+=v*v;
  }
 }
 int delta(int p)const{
  int n=s.size(),v=0,dc,d=0;for(int k=1;k<n;k++){
   v=(p>=k?s[p-k]:0)+(p+k<n?s[p+k]:0);dc=-2*s[p]*v;d+=2*c[k]*dc+dc*dc;
  }return d;
 }
 void flip(int p){int n=s.size();for(int k=1;k<n;k++){
   int v=(p>=k?s[p-k]:0)+(p+k<n?s[p+k]:0),dc=-2*s[p]*v;
   e+=2*c[k]*dc+dc*dc;c[k]+=dc;
  }s[p]*=-1;
 }
};
vector<int8_t> parse(string s){vector<int8_t> r;for(char c:s)r.push_back(c=='+'?1:-1);return r;}
string str(vector<int8_t> s){string out;for(auto c:s)out+=c>0?'+':'-';return out;}
struct Result{int E;vector<int8_t> s;long long evals;};
Result bridge(State source,const vector<int>& sites,mt19937_64& rng,int steps,int kick, int tenure){
 State current=source,best=source;
 vector<int> taboo(current.s.size(),0),order=sites;
 int stalled=0;long long evals=0;
 for(int step=1;step<=steps;step++){
  shuffle(order.begin(),order.end(),rng);
  int where=-1,small=INT32_MAX,fb=INT32_MAX,find=0;
  for(int p:order){int newe=current.e+current.delta(p);evals++;
   if(newe<fb){fb=newe;find=p;}
   if(step>=taboo[p]||newe<best.e){if(newe<small){small=newe;where=p;}}
  }
  if(where<0)where=find;
  current.flip(where);taboo[where]=step+tenure+(int)(rng()%7);
  if(current.e<best.e){best=current;stalled=0;}else stalled++;
  if(stalled>=kick){
   current=best;shuffle(order.begin(),order.end(),rng);
   int count=min(int(sites.size())-1,8+int(rng()%21));
   for(int i=0;i<count;i++)current.flip(order[i]);
   fill(taboo.begin(),taboo.end(),0);stalled=0;
  }
 }
 if(State(best.s).e!=best.e)abort();
 return {best.e,best.s,evals};
}
int main(int argc,char**argv){
 if(argc!=8)return 1;
 int mode=atoi(argv[1]),runs=atoi(argv[2]),steps=atoi(argv[3]),width=atoi(argv[4]),tenure=atoi(argv[5]),control=atoi(argv[6]),seedtag=atoi(argv[7]);
 auto source=parse(mode==0?T60:mode==1?T606:T578);int n=source.size();vector<Result> res(runs);
#ifdef _OPENMP
 omp_set_num_threads(4);
#endif
 auto start=chrono::steady_clock::now();
#pragma omp parallel for schedule(dynamic,1)
 for(int trial=0;trial<runs;trial++){
  mt19937_64 rng(520261108ULL+uint64_t(seedtag)*893773ULL+trial*0x9e3779b97f4a7c15ULL);
  vector<int> sites;sites.reserve(width);
  int lo=(trial%2==0)?(n-width)/2:(int)(rng()%n);
  for(int i=0;i<width;i++)sites.push_back((lo+i)%n);
  vector<int8_t> initial=source;
  if(mode<=2){
   vector<int> shuffled=sites;shuffle(shuffled.begin(),shuffled.end(),rng);
   for(int i=0;i<min(20,width-1);i++)initial[shuffled[i]]*=-1;
  }
  if(control){sites.resize(n);iota(sites.begin(),sites.end(),0);}
  res[trial]=bridge(State(initial),sites,rng,steps,300,tenure);
 }
 int best=INT32_MAX,success=0;string witness;long long evals=0;double mean=0;
 for(auto x:res){evals+=x.evals;mean+=x.E;if(x.E<best){best=x.E;witness=str(x.s);}
  success+=(x.E <= (mode==0?218:mode==1?606:578));}
 cout<<"SUMMARY mode="<<mode<<" n="<<n<<" trials="<<runs<<" steps="<<steps<<" width="<<width
 <<" control="<<control<<" seedtag="<<seedtag<<" full_evals="<<evals<<" bestE="<<best<<" meanE="<<mean/runs<<" success="<<success
 <<" wall="<<chrono::duration<double>(chrono::steady_clock::now()-start).count()<<" best="<<witness<<"\n";
 for(int i=0;i<runs;i++)cout<<"TRIAL "<<i<<" E="<<res[i].E<<" "<<str(res[i].s)<<"\n";
}
