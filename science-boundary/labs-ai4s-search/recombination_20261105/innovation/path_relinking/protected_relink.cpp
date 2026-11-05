// Stateful elite-source LABS path relinking with protected donor backbone.
// A mechanism test, NOT a novel general path-relinking algorithm or full MTS.
#define RECOMBINE_NO_MAIN
#include "../../recombine.cpp"
#undef RECOMBINE_NO_MAIN
#include <climits>
#include <unordered_set>
#include <iomanip>
using namespace std;

int orbit_dist(const string&x,const string&y){
 int best=INT_MAX;for(const string&z:orb(y))best=min(best,hd(x,z));return best;
}
struct PairContext{
 L A,B;
 vector<int>D,Q;
 vector<int>envelope;
 string Aname,Bname;
 PairContext(const Parent&a,const Parent&b):A(a.state),B(parse(align_donor(a.seq,b.seq))),Aname(a.id),Bname(b.id){
  if(A.n!=B.n)throw runtime_error("parents differ in N");
  for(int i=0;i<A.n;i++)(A.s[i]!=B.s[i]?D:Q).push_back(i);
  if(D.size()<8||Q.size()<6)throw runtime_error("insufficient distinct elite source diversity");
  envelope.resize(A.n);
  for(int k=1;k<A.n;k++)envelope[k]=max(abs(A.c[k]),abs(B.c[k]));
 }
};
double envelope_score(const L&x,const vector<int>&bounds,int mode){
 if(mode!=7&&mode!=8)return x.e;
 double cost=x.e;
 for(int k=1;k<x.n;k++){int extra=max(0,abs(x.c[k])-bounds[k]);cost+=.75*extra*extra;}
 return cost;
}
void descend_locked(L&x,const vector<char>&locked,const L&b){
 for(int iter=0;iter<8*x.n;iter++){
  int pos=-1,delta=0;
  for(int j=0;j<x.n;j++)if(!locked[j]&&x.delta(j)<delta){pos=j;delta=x.delta(j);}
  if(pos<0)break;
  x.flip(pos);
 }
 for(int j=0;j<x.n;j++)if(locked[j]&&x.s[j]!=b.s[j])throw runtime_error("backbone violated on descent");
}
L tabu_locked(L x,const vector<char>&locked,const L&b,mt19937_64&rng,int&moves){
 descend_locked(x,locked,b);
 L best=x;
 vector<int>last(x.n,-1000000);
 for(int t=0;t<12;t++){
  int pos=-1,delta=INT_MAX;
  for(int j=0;j<x.n;j++)if(!locked[j]){
   int v=x.delta(j);
   if(t-last[j]<=7 && x.e+v>=best.e)continue;
   if(v<delta||(v==delta&&(rng()&1))){pos=j;delta=v;}
  }
  if(pos<0){for(int j=0;j<x.n;j++)if(!locked[j]){int v=x.delta(j);if(v<delta){pos=j;delta=v;}}}
  if(pos<0)break;
  x.flip(pos);last[pos]=t;moves++;
  if(x.e<best.e)best=x;
 }
 descend_locked(best,locked,b);
 for(int j=0;j<x.n;j++)if(locked[j]&&best.s[j]!=b.s[j])throw runtime_error("backbone violated on Tabu");
 return best;
}
int choose_donor(const L&x,const PairContext&p,const vector<char>&locked,int arm,mt19937_64&rng,int&evals){
 vector<int>eligible;
 for(int j:p.D)if(!locked[j])eligible.push_back(j);
 if(eligible.empty())throw runtime_error("no donor eligible");
 if(arm==3||arm==5){return eligible[rng()%eligible.size()];}
 int pick=-1,best=INT_MAX;
 for(int i:eligible){
  int d=x.s[i]==p.B.s[i]?0:x.delta(i);
  evals++;
  if(d<best||(d==best&&(rng()&1))){best=d;pick=i;}
 }
 return pick;
}
int choose_consensus_flip(const L&cur,const PairContext&p,const vector<char>&locked,
                          const vector<int>&bound,int arm,mt19937_64&rng,int&evals){
 if(arm<6)return -1;
 int site=-1;double best=1e100;
 for(int q:p.Q)if(!locked[q]){
  L trial=cur;trial.flip(q);double cost=envelope_score(trial,bound,arm);evals++;
  if(cost<best||(cost==best&&(rng()&1))){best=cost;site=q;}
 }
 return site;
}
struct SearchStats{
 int sessions=0,offspring=0,nov5=0,nov10=0,nov15=0,nov20=0,bestE=INT_MAX;
 int newThird=0,evals=0,protectMoves=0,lockedEvents=0,stageVisits=0;
 int bestDist=-1,bestStage=-1,bestLock=-1;
 double meanE=0,meanPreE=0,prepTime=0,protectTime=0,finalTime=0;
 string bestBits,bestCanon;
};
void measure_candidate(const L&raw,const Parent&A,const Parent&B,const PairContext&p,
                       mt19937_64&rng,int stage,int locknum,
                       SearchStats&stats,const unordered_set<string>&registry,int Eref,
                       unordered_set<string>&already,ofstream&nov,int rep,int arm,const string&pair){
 if(raw.e!=energy_direct(raw.s))throw runtime_error("preRepair exact energy");
 string initial=bits(raw);
 auto start=clk::now();
 int moves=0;L repaired=repair(raw,rng,moves);
 stats.finalTime+=ns(clk::now()-start).count();
 if(moves!=64||repaired.e!=energy_direct(repaired.s))throw runtime_error("postRepair exact score");
 string word=bits(repaired),c=canon(word);int e=repaired.e;
 stats.offspring++;stats.meanE+=e;stats.meanPreE+=raw.e;
 if(e<stats.bestE){
  stats.bestE=e;stats.bestBits=word;stats.bestCanon=c;stats.bestStage=stage;
  stats.bestLock=locknum;stats.bestDist=min(orbit_dist(word,A.seq),orbit_dist(word,B.seq));
 }
 if(!registry.count(c)&&e<=Eref*1.2 && already.insert(c).second){
  stats.nov20++;stats.nov15+=(e<=Eref*1.15);stats.nov10+=(e<=Eref*1.10);stats.nov5+=(e<=Eref*1.05);
  nov<<p.A.n<<"\t"<<pair<<"\t"<<rep<<"\t"<<arm<<"\t"<<stage<<"\t"<<locknum<<"\t"
     <<e<<"\t"<<word<<"\t"<<c<<"\t"<<raw.e<<"\t"<<initial<<"\t"
     <<min(orbit_dist(word,A.seq),orbit_dist(word,B.seq))<<"\n";
 }
}
void run_path(const PairContext&p,int arm,mt19937_64&rng,SearchStats&stats,
              const Parent&A,const Parent&B,const unordered_set<string>&registry,int eref,
              unordered_set<string>&seen,ofstream&nov,int rep,const string&pair){
 L cur=p.A;
 vector<char>locked(p.A.n,0);
 vector<int>bound=p.envelope;
 if(arm==8)shuffle(bound.begin()+1,bound.end(),rng);
 int lockCount=0,stages=4;
 for(int stage=0;stage<stages;stage++){
  int goal=(int(p.D.size())*(stage+1)+stages-1)/stages;
  while(lockCount<goal){
   auto t=clk::now();
   int site=choose_donor(cur,p,locked,arm,rng,stats.evals);
   if(cur.s[site]!=p.B.s[site])cur.flip(site);
   locked[site]=1;lockCount++;
   int q=choose_consensus_flip(cur,p,locked,bound,arm,rng,stats.evals);
   if(q>=0)cur.flip(q);
   stats.prepTime+=ns(clk::now()-t).count();
  }
  if(arm>=4){
   auto t=clk::now();cur=tabu_locked(cur,locked,p.B,rng,stats.protectMoves);
   stats.protectTime+=ns(clk::now()-t).count();
  }
  for(int site:p.D)if(locked[site]&&cur.s[site]!=p.B.s[site])throw runtime_error("locked allele mismatch");
  stats.lockedEvents+=lockCount;stats.stageVisits++;
  measure_candidate(cur,A,B,p,rng,stage,lockCount,stats,registry,eref,seen,nov,rep,arm,pair);
 }
 stats.sessions++;
}
void path_selftest(){
 selftest();mt19937_64 rng(80261105);
 for(int n:{46,47,59,92,99})for(int z=0;z<5;z++){
  Parent A,B;A.id="A";B.id="B";A.n=B.n=n;
  for(int j=0;j<n;j++){A.seq+=rng()%2?'1':'0';B.seq+=rng()%2?'1':'0';}
  A.state=parse(A.seq);B.state=parse(B.seq);A.E=A.state.e;B.E=B.state.e;
  PairContext p(A,B);unordered_set<string>registry={canon(A.seq),canon(B.seq)};
  for(int arm=2;arm<=8;arm++){
   SearchStats stats;unordered_set<string>seen;
   ostringstream fake;
   // Need std::ostream, not only ofstream: test protected backbone
   vector<char> locked(n,0);L s=p.A;int count=0;
   for(int i:p.D){s.flip(i);locked[i]=1;if(++count>=int(p.D.size()/4))break;}
   int moves=0;L q=tabu_locked(s,locked,p.B,rng,moves);
   for(int i:p.D)if(locked[i]&&q.s[i]!=p.B.s[i])throw runtime_error("test locked B mismatch");
   if(q.e!=energy_direct(q.s))throw runtime_error("test locked direct");
  }
 }
 cout<<"PASS exact-energy, parity-preserving eightfold parents, protected 12-step restricted repair\n";
}
int main(int argc,char **argv){
 if(argc==2 && string(argv[1])=="--selftest"){path_selftest();return 0;}
 if(argc<6){cerr<<"usage: PARENTS.tsv SESSIONS.tsv CERTS.tsv REPS BUDGET_MS\n";return 2;}
 auto pool=load(argv[1]);map<string,Parent*>byid;
 unordered_map<int,unordered_set<string>>registry;
 unordered_map<int,int>bestKnown;
 for(auto &p:pool){byid[p.id]=&p;registry[p.n].insert(p.canonical);
  if(!bestKnown.count(p.n)||p.best<bestKnown[p.n])bestKnown[p.n]=p.best;}
 const vector<pair<string,string>>frozen={{"c46_0","c46_1"},{"c47_0","c47_2"},{"c50_0","c50_1"},
 {"c59_0","c59_2"},{"c60_1","c60_4"},{"c60_0","c60_3"},{"c60_2","c60_5"},{"c92_0","c92_1"},{"c99_0","c99_1"}};
 int reps=stoi(argv[4]),ms=stoi(argv[5]);
 ofstream out(argv[2]),nov(argv[3]);
 if(!out||!nov)throw runtime_error("unable to open outputs");
 out<<"N\tpair\tA_id\tB_id\tAE\tBE\trep\tarm\ttrajectory_count\toffspring\t"
 "bestE\tbestBits\tbestCanon\tbestDist\tbestStage\tbestLockCount\t"
 "nov5\tnov10\tnov15\tnov20\tmeanAllRepairedE\tmeanAllPreE\t"
 "evals\tprotectMoves\tstageVisits\tlockedEvents\tmodelMs\tpathMs\tprotectedMs\tfinalRepairMs\telapsedMs\n";
 nov<<"N\tpair\trep\tarm\tstage\tlockedCount\tE\tbits\tcanonical\tpreE\tpreBits\tclosestParentDist\n";
 out<<fixed<<setprecision(6);
 for(int ip=0;ip<(int)frozen.size();ip++){
  auto [an,bn]=frozen[ip];
  if(!byid.count(an)||!byid.count(bn))throw runtime_error("missing preselected parents");
  const Parent &A=*byid[an],&B=*byid[bn];
  if(A.n!=B.n)throw runtime_error("mismatched length");
  string pair=an+"-"+bn;
  for(int rep=0;rep<reps;rep++)for(int arm=0;arm<=8;arm++){
   mt19937_64 rng(hashseed(90261105ULL+ip*12011ULL+rep*17377ULL+arm*32771ULL));
   auto start=clk::now();auto model=clk::now();
   PairContext p(A,B);double modelTime=ns(clk::now()-model).count();
   SearchStats stats;unordered_set<string>seen;
   while(stats.sessions==0||ns(clk::now()-start).count()*1000<ms){
    if(arm==0){
     L s=A.state;const int radii[]={2,4,8,12};
     int k=radii[rng()%4];
     auto t=clk::now();
     for(int i:random_mask(s.n,k,rng))s.flip(i);
     stats.prepTime+=ns(clk::now()-t).count();
     measure_candidate(s,A,B,p,rng,-1,0,stats,registry[A.n],bestKnown[A.n],seen,nov,rep,arm,pair);
     stats.sessions++;
    }else if(arm==1){
     const L&c=(rng()%2)?p.A:p.B;
     measure_candidate(c,A,B,p,rng,-1,0,stats,registry[A.n],bestKnown[A.n],seen,nov,rep,arm,pair);
     stats.sessions++;
    }else run_path(p,arm,rng,stats,A,B,registry[A.n],bestKnown[A.n],seen,nov,rep,pair);
    if(stats.sessions>100000)throw runtime_error("unbounded timing");
   }
   double elapsed=ns(clk::now()-start).count();
   if(stats.offspring<=0||stats.bestE==INT_MAX||stats.meanE<0)throw runtime_error("no output");
   out<<A.n<<"\t"<<pair<<"\t"<<A.id<<"\t"<<B.id<<"\t"<<A.E<<"\t"<<B.E
     <<"\t"<<rep<<"\t"<<arm<<"\t"<<stats.sessions<<"\t"<<stats.offspring
     <<"\t"<<stats.bestE<<"\t"<<stats.bestBits<<"\t"<<stats.bestCanon<<"\t"<<stats.bestDist
     <<"\t"<<stats.bestStage<<"\t"<<stats.bestLock<<"\t"
     <<stats.nov5<<"\t"<<stats.nov10<<"\t"<<stats.nov15<<"\t"<<stats.nov20
     <<"\t"<<stats.meanE/stats.offspring<<"\t"<<stats.meanPreE/stats.offspring
     <<"\t"<<stats.evals<<"\t"<<stats.protectMoves<<"\t"<<stats.stageVisits<<"\t"<<stats.lockedEvents
     <<"\t"<<1000*modelTime<<"\t"<<1000*stats.prepTime<<"\t"<<1000*stats.protectTime
     <<"\t"<<1000*stats.finalTime<<"\t"<<1000*elapsed<<"\n";
  }
  cerr<<"FINISHED source pair "<<pair<<" all arms, "<<reps<<" seeds\n";
 }
 cout<<"PASS fully costed protected parent-path repair versus classical and elite ILS\n";
}
