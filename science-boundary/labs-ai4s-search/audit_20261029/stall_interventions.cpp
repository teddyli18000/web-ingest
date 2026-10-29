// Audit-driven frozen-Tabu-state intervention experiment.
// Full tabu history and incumbent preserved across fork; reset-history ablation.
// Compile: g++ -O3 -std=c++17 -Wall -Wextra stall_interventions.cpp -o stall_interventions
// Run: ./stall_interventions --test
//      ./stall_interventions IN.tsv OUT.tsv 80 2 9 10 400 12000 [limit=0]
#define main lns_unused_main
#include "../lns_mask.cpp"
#undef main
#include <chrono>
#include <fstream>
#include <iomanip>
#include <sstream>
#include <set>
#include <climits>
using Clock=std::chrono::steady_clock;
double elapsed(Clock::time_point start){return std::chrono::duration<double>(Clock::now()-start).count();}
uint64_t scramble(uint64_t x){x+=0x9e3779b97f4a7c15ULL;x=(x^(x>>30))*0xbf58476d1ce4e5b9ULL;x=(x^(x>>27))*0x94d049bb133111ebULL;return x^(x>>31);}
L frombits(std::string b){std::vector<int>s;for(char c:b){if(c!='0'&&c!='1')throw std::runtime_error("bad input");s.push_back(c=='1'?1:-1);}return L(s);}
bool is_skew(const std::vector<int>&s,int begin,int len){
 if(len%2!=1)return false;int m=len/2;
 for(int j=1;j<=m;j++)if(s[begin+m+j]!=(j%2?-1:1)*s[begin+m-j])return false;
 return true;
}
bool near_skew(const L&x){return x.n%2?is_skew(x.s,0,x.n):is_skew(x.s,0,x.n-1)||is_skew(x.s,1,x.n-1);}
int odd_defect(const L&x){int d=0;for(int k=1;k<x.n;k+=2)d+=x.c[k]*x.c[k]-((x.n-k)&1);return d;}
struct Tabu {
 L cur,best;
 std::vector<int> last;
 int iteration=0,stall=0,calls=0,improvements=0,forced_moves=0;
 Tabu(L x):cur(x),best(x),last(x.n,-10000000){}
};
void update_best(Tabu&st){if(st.cur.e<st.best.e){st.best=st.cur;st.improvements++;st.stall=0;}else st.stall++;}
void step(Tabu&st, int tenure, std::mt19937_64&rng){
 int p=-1,db=INT_MAX;
 for(int i=0;i<st.cur.n;i++){
  int d=st.cur.delta(i);
  if(st.iteration-st.last[i]<=tenure && st.cur.e+d>=st.best.e)continue;
  if(d<db || (d==db && (rng()&1))){db=d;p=i;}
 }
 if(p<0){p=int(rng()%st.cur.n);st.forced_moves++;}
 st.cur.flip(p);st.last[p]=st.iteration++;st.calls++;update_best(st);
}
bool inject(Tabu&st,int type, bool reset, int m, std::mt19937_64 &rng){
 L original=st.cur,next=original;
 if(type==3){
  for(int idx:random_mask(original.n,8,rng))next.flip(idx);
  next.descend(0);
 } else {
  std::vector<int> mask;
  if(type==1)mask=random_mask(original.n,m,rng);
  if(type==2){
   std::vector<int> ds(original.n);
   for(int i=0;i<original.n;i++)ds[i]=original.delta(i);
   auto I=interactions(original,ds);
   mask=structural_mask(ds,I,original.n,m,2,rng);
  }
  auto options=enumerate(original,mask,std::max(3,m/3));
  bool found=false;
  // Best post-relax endpoint that actually differs from the frozen current state.
  // A different state can be uphill; this is a *nonmonotone* intervention.
  for(int descent=0;descent<2;descent++)for(const L&base:{options.repair,options.excursion}){
   L trial=base;trial.descend(descent);
   if(trial.s==original.s)continue;
   if(!found||trial.e<next.e){next=std::move(trial);found=true;}
  }
  if(!found)return false;
 }
 if(reset)std::fill(st.last.begin(),st.last.end(),-10000000);
 for(int i=0;i<original.n;i++)if(original.s[i]!=next.s[i])st.last[i]=st.iteration;
 st.cur=next;
 // Injection is charged to the same time cap but does not advance Tabu's iteration.
 // Treat it as a single strategic intervention, and preserve best-ever state.
 if(st.cur.e<st.best.e){st.best=st.cur;st.improvements++;st.stall=0;}
 st.calls++;return original.s!=st.cur.s;
}
struct Sample {int n,E;std::string bits,source,id;int near;};
std::vector<Sample> read_states(const std::string&p){
 std::ifstream f(p);if(!f)throw std::runtime_error("missing "+p);
 std::vector<Sample>v;std::string s;std::getline(f,s);
 while(std::getline(f,s)){
  if(s.empty())continue;
  std::istringstream ss(s);Sample t;int seed;std::string orbit;
  ss>>t.n>>t.E>>t.bits>>t.source>>t.id>>seed>>t.near>>orbit;
  L q=frombits(t.bits);
  if(q.n!=t.n||q.e!=t.E||energy_direct(q.s)!=t.E||int(near_skew(q))!=t.near)
   throw std::runtime_error("input certificate failed, "+std::to_string(t.n));
  v.push_back(t);
 }
 return v;
}
void test(){
 std::mt19937_64 rng(98310);
 for(int n:{12,64,80,92,99,100}){
  for(int rep=0;rep<15;rep++){
   std::string bits;for(int i=0;i<n;i++)bits+=(rng()&1?'1':'0');
   L q=frombits(bits);int d=odd_defect(q);
   int brute=0;for(int k=1;k<n;k+=2){
    int c=0;for(int i=0;i<n-k;i++)c+=q.s[i]*q.s[i+k];
    brute+=c*c-((n-k)&1);
   }
   if(d<0||d!=brute||q.e!=energy_direct(q.s))throw std::runtime_error("test discrepancy");
   Tabu st(q);for(int i=0;i<40;i++)step(st,9,rng);
   for(int a=1;a<=3;a++){
    Tabu t=st;inject(t,a,false,10,rng);
    if(t.cur.e!=energy_direct(t.cur.s)||t.best.e!=energy_direct(t.best.s))throw std::runtime_error("injection corrupt");
    for(int z=0;z<30;z++)step(t,9,rng);
    if(t.best.e!=energy_direct(t.best.s))throw std::runtime_error("tabu corrupt");
   }
  }
 }
 std::cout<<"PASS 90 random exact states; 270 injection/continuation paths; odd-defect parity\n";
}
int main(int argc,char**argv){
 if(argc==2 && std::string(argv[1])=="--test"){test();return 0;}
 if(argc<9){std::cerr<<"usage IN OUT BUDGET_MS REPS TENURE M STALL WARM_MAX [LIMIT]\n";return 2;}
 auto data=read_states(argv[1]);
 std::ofstream f(argv[2]);
 double budget=std::stod(argv[3])/1000.;
 int reps=std::stoi(argv[4]),tenure=std::stoi(argv[5]),m=std::stoi(argv[6]);
 int stallMin=std::stoi(argv[7]),maxWarm=std::stoi(argv[8]);
 int limit=argc>9?std::stoi(argv[9]):0;
 if(limit>0&&limit<(int)data.size())data.resize(limit);
 f<<"source_id\tN\tclass\tprovenance\trep\tarm\treset_history\t"
   "sourceE\tfrozenBestE\tfrozenCurE\tfrozenStall\twarmSteps\t"
   "frozenOddDefect\tbestE\tgain\tcurrentE\tfinalOddDefect\t"
   "tabu_calls\tinjected\tinjection_seconds\telapsed_seconds\tovershoot_ms\t"
   "first_gain_seconds\tfirst_gain_calls\timprovements\tforce_fallbacks\n";
 f<<std::fixed<<std::setprecision(7);
 int id=0;
 for(const auto &a:data){
  L x=frombits(a.bits);
  for(int rep=0;rep<reps;rep++){
   std::mt19937_64 warmrng(scramble(736391+id*99173+rep*811));
   Tabu frozen(x);
   while(frozen.iteration<maxWarm && (frozen.iteration<2000 || frozen.stall<stallMin))
      step(frozen,tenure,warmrng);
   const int fs=frozen.stall,fe=frozen.best.e,fc=frozen.cur.e,od=odd_defect(frozen.cur),warmSteps=frozen.iteration;
   for(int arm=0;arm<7;arm++){
    // 0=continue; 1/2=random LNS preserve/reset; 3/4=pair LNS preserve/reset;
    // 5/6=random 8-flip kick preserve/reset.
    Tabu st=frozen;
    int kind=arm==0?0:(arm<=2?1:(arm<=4?2:3));
    bool reset=arm>0&&(arm%2==0);
    std::mt19937_64 rng(scramble(93781+id*733133+rep*121711+arm*307));
    auto t0=Clock::now();
    bool injected=false;
    double injectSec=0;
    if(kind){
      injected=inject(st,kind,reset,m,rng);
      injectSec=elapsed(t0);
    }
    double gainTime=-1;int gainCalls=-1;
    if(st.best.e<fe){gainTime=elapsed(t0);gainCalls=st.calls-frozen.calls;}
    while(elapsed(t0)<budget){
      step(st,tenure,rng);
      if(gainTime<0 && st.best.e<fe){gainTime=elapsed(t0);gainCalls=st.calls-frozen.calls;}
    }
    double spent=elapsed(t0);
    if(st.best.e!=energy_direct(st.best.s)||st.cur.e!=energy_direct(st.cur.s))
       throw std::runtime_error("final independent energy check failed");
    f<<id<<"\t"<<a.n<<"\t"<<a.near<<"\t"<<a.source<<"\t"<<rep<<"\t"<<arm<<"\t"<<int(reset)<<"\t"
     <<a.E<<"\t"<<fe<<"\t"<<fc<<"\t"<<fs<<"\t"<<warmSteps<<"\t"<<od<<"\t"
     <<st.best.e<<"\t"<<fe-st.best.e<<"\t"<<st.cur.e<<"\t"<<odd_defect(st.cur)<<"\t"
     <<st.calls-frozen.calls<<"\t"<<int(injected)<<"\t"<<injectSec<<"\t"<<spent<<"\t"
     <<std::max(0.,(spent-budget)*1000)<<"\t"<<gainTime<<"\t"<<gainCalls<<"\t"
     <<st.improvements-frozen.improvements<<"\t"<<st.forced_moves-frozen.forced_moves<<"\n";
   }
  }
  id++;f.flush();
  std::cerr<<"N "<<a.n<<" state "<<id<<"/"<<data.size()<<"\n";
 }
}
