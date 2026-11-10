// Exact conditional outer-bit ranking with planted hidden-source evaluation.
// All ranking decisions use only the corrupted input, allowed core locations,
// and full LABS energy. The teacher is used only to generate and audit trials.
// Build in science-boundary/labs-100:
// g++ -O3 -std=c++20 code/conditional_exterior_rank.cpp -o /tmp/labs-rank
// /tmp/labs-rank 1 30 300 50 12    # N100 E578 source
// /tmp/labs-rank 2 30 300 50 12    # N100 E606 source
// Equal proposal counts for three arms: conditional bank, full tabu,
// and 10 fixed-X full-tabu restarts. Timing is not equalized.
#define main conditional_core_legacy_main
#include "conditional_core_bridge.cpp"
#undef main
#include <climits>
#include <tuple>

struct Benchmark {vector<int8_t> input;vector<int> core,outer;int missing=-1;};
Benchmark planted(int source,int w,int trial,int seed){
 string teacher=source==0?T60:source==1?T578:T606;
 int n=teacher.size();
 mt19937_64 rng(842117324ULL+uint64_t(seed*10000+trial)*0x9e3779b97f4a7c15ULL+source*347ULL);
 int first=(trial%2==0)?(n-w)/2:int(rng()%n);
 vector<int> core,outer,mark(n);
 for(int k=0;k<w;k++){int i=(first+k)%n;core.push_back(i);mark[i]=1;}
 for(int i=0;i<n;i++)if(!mark[i])outer.push_back(i);
 auto a=core,b=outer;
 shuffle(a.begin(),a.end(),rng);shuffle(b.begin(),b.end(),rng);
 vector<int8_t> s=parse(teacher);
 for(int k=0;k<20;k++)s[a[k]]*=-1;
 s[b[0]]*=-1;
 return {s,core,outer,b[0]};
}
struct Candidate {int score,raw,index;};
struct Stats {int count=0,top5=0,raw5=0,top1=0,better=0,hits=0,fullhits=0,multihits=0;long long rank=0,rawrank=0,work=0,fullwork=0,multiwork=0;};
int main(int argc,char**argv){
 if(argc!=6){cerr<<"Usage: rank source(0=N60,1=N100-E578,2=N100-E606) trials innersteps width seed\n";return 1;}
 int source=atoi(argv[1]),trials=atoi(argv[2]),steps=atoi(argv[3]),width=atoi(argv[4]),seed=atoi(argv[5]);
 int target=source==0?218:source==1?578:606;
 Stats stats;
 for(int trial=0;trial<trials;trial++){
  auto b=planted(source,width,trial,seed);
  vector<Candidate> all;
  for(int p:b.outer){
   auto t=b.input;t[p]*=-1;
   int raw=State(t).e;
   mt19937_64 rng(140102030ULL+source*10ULL+seed*1000000ULL+trial*733ULL+p);
   auto repaired=bridge(State(t),b.core,rng,steps,140,8);
   stats.work+=repaired.evals+1;
   all.push_back({repaired.E,raw,p});
  }
  auto by_e=all,by_raw=all;
  sort(by_e.begin(),by_e.end(),[](auto a,auto b){return tie(a.score,a.index)<tie(b.score,b.index);});
  sort(by_raw.begin(),by_raw.end(),[](auto a,auto b){return tie(a.raw,a.index)<tie(b.raw,b.index);});
  int r1=0,r0=0;
  for(int j=0;j<(int)all.size();j++){
   if(by_e[j].index==b.missing)r1=j+1;
   if(by_raw[j].index==b.missing)r0=j+1;
  }
  vector<int> fullsites=b.core;
  fullsites.insert(fullsites.end(),b.outer.begin(),b.outer.end());
  int fullsteps=steps*width*(int)b.outer.size()/(int)fullsites.size();
  mt19937_64 fullrng(90261211ULL+source*13ULL+seed*130001ULL+trial*733ULL);
  auto full=bridge(State(b.input),fullsites,fullrng,fullsteps,140,8);
  stats.fullwork+=full.evals;
  int multibest=State(b.input).e;
  for(int rep=0;rep<10;rep++){
    mt19937_64 r(1827367ULL+source*177ULL+seed*100009ULL+trial*991ULL+rep*3781ULL);
    auto short_run=bridge(State(b.input),fullsites,r,fullsteps/10,140,8);
    stats.multiwork+=short_run.evals;
    multibest=min(multibest,short_run.E);
  }
  stats.fullhits+=full.E<=target;
  stats.multihits+=multibest<=target;
  stats.count++;stats.rank+=r1;stats.rawrank+=r0;stats.top5+=r1<=5;stats.raw5+=r0<=5;stats.top1+=r1==1;stats.better+=r1<r0;stats.hits+=by_e[0].score<=target;
  cout<<"ROW source="<<source<<" seed="<<seed<<" trial="<<trial<<" missing="<<b.missing<<" conditionalRank="<<r1<<" rawRank="<<r0<<" best="<<by_e[0].score<<" correct="<<by_e[r1-1].score<<" full="<<full.E<<" multi="<<multibest<<"\n";
 }
 cout<<"SUMMARY source="<<source<<" trials="<<trials<<" seed="<<seed<<" width="<<width<<" steps="<<steps<<" meanRank="<<double(stats.rank)/stats.count<<" meanRawRank="<<double(stats.rawrank)/stats.count<<" top1="<<stats.top1<<" top5="<<stats.top5<<" raw5="<<stats.raw5<<" better="<<stats.better<<" hits="<<stats.hits<<" fullHits="<<stats.fullhits<<" multiHits="<<stats.multihits<<" evals="<<stats.work<<" fullEvals="<<stats.fullwork<<" multiEvals="<<stats.multiwork<<"\n";
}
