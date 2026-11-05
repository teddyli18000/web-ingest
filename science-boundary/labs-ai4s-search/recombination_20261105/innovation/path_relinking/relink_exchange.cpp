// Reversible donor-backbone quotas: exact E, envelope and virtual-B controls.
// Includes frozen first-round protected path and fully charged common LABS repair.
#define main protected_main_disabled
#include "protected_relink.cpp"
#undef main
#include <climits>
#include <unordered_set>
using namespace std;

struct Movable {
 PairContext source;
 PairContext active;
 Movable(const Parent&A,const Parent&B,mt19937_64&rng,bool fake)
     :source(A,B),active(A,B){
  if(fake){
   int d=source.D.size();
   auto idx=random_mask(A.n,d,rng);
   vector<int>s=source.A.s;
   vector<char>which(A.n,0);
   for(int i:idx){s[i]=-s[i];which[i]=1;}
   active.B=L(s);
   active.D=idx;active.Q.clear();
   for(int j=0;j<A.n;j++)if(!which[j])active.Q.push_back(j);
   if(active.D.size()!=source.D.size()||active.Q.size()!=source.Q.size())
    throw runtime_error("virtual B mismatch cardinality");
  }
 }
};
int greedy_adopt(L&x,const PairContext&p,vector<char>&locked,int goal,mt19937_64&rng,int&evals){
 int count=0;
 while(count<goal){
  int site=choose_donor(x,p,locked,2,rng,evals);
  if(x.s[site]!=p.B.s[site])x.flip(site);
  locked[site]=1;count++;
 }
 return count;
}
struct SwapChoice{
 int release=-1,adopt=-1;
 double score=1e200;
 L child;
 SwapChoice(const L&x):child(x){}
};
SwapChoice select_exchange(const L&cur,const PairContext&p,const vector<char>&locked,
                           const vector<int>&bound,int arm,mt19937_64&rng,int&evals){
 vector<int>on,off;
 for(int i:p.D)(locked[i]?on:off).push_back(i);
 if(on.empty()||off.empty())throw runtime_error("empty donor swap side");
 SwapChoice best(cur);
 int num=arm==4?1:6;
 for(int t=0;t<num;t++){
  int a=on[rng()%on.size()],b=off[rng()%off.size()];
  L trial=cur;
  // Undo released B allele, then impose newly adopted B allele.
  if(trial.s[a]!=p.A.s[a])trial.flip(a);
  if(trial.s[b]!=p.B.s[b])trial.flip(b);
  double obj=trial.e;
  if(arm==5||arm==6){
   double bad=0;
   for(int k=1;k<trial.n;k++){int excess=max(0,abs(trial.c[k])-bound[k]);bad+=excess*excess;}
   obj+=.75*bad;
  }
  evals++;
  if(obj<best.score){best.release=a;best.adopt=b;best.score=obj;best.child=move(trial);}
 }
 if(best.release<0||best.adopt<0)throw runtime_error("selection failed");
 return best;
}
void moving_trajectory(const Parent&A,const Parent&B,int arm,mt19937_64&rng,
                       SearchStats&stats,const unordered_set<string>&registry,int Eref,
                       unordered_set<string>&seen,ofstream&nov,int rep,const string&pair){
 auto t=clk::now();Movable m(A,B,rng,arm==7);
 PairContext&p=m.active;
 stats.prepTime+=ns(clk::now()-t).count();
 L current=p.A;
 vector<char>locked(p.A.n,0);
 int d=p.D.size(),quota=max(2,d/2);
 t=clk::now();int lockCount=greedy_adopt(current,p,locked,quota,rng,stats.evals);
 vector<int>bounds=p.envelope;
 if(arm==6)shuffle(bounds.begin()+1,bounds.end(),rng);
 stats.prepTime+=ns(clk::now()-t).count();
 for(int stage=0;stage<4;stage++){
  if(stage>0 && arm>=3){
   auto st=clk::now();
   for(int sub=0;sub<2;sub++){
    SwapChoice sw=select_exchange(current,p,locked,bounds,arm,rng,stats.evals);
    current=move(sw.child);
    locked[sw.release]=0;locked[sw.adopt]=1;
   }
   stats.prepTime+=ns(clk::now()-st).count();
  }
  t=clk::now();current=tabu_locked(current,locked,p.B,rng,stats.protectMoves);
  stats.protectTime+=ns(clk::now()-t).count();
  for(int i:p.D)if(locked[i]&&current.s[i]!=p.B.s[i])
    throw runtime_error("released lock has wrong B allele");
  stats.lockedEvents+=lockCount;stats.stageVisits++;
  measure_candidate(current,A,B,m.source,rng,stage,lockCount,stats,
                    registry,Eref,seen,nov,rep,arm,pair);
 }
 stats.sessions++;
}
void selftest_exchange(){
 path_selftest();
 mt19937_64 rng(560113);
 for(int n:{46,47,59,60,92,99}){
  Parent A,B;A.n=B.n=n;A.id="A";B.id="B";
  for(int j=0;j<n;j++){A.seq+=rng()%2?'1':'0';B.seq+=rng()%2?'1':'0';}
  A.state=parse(A.seq);B.state=parse(B.seq);
  for(int arm:{2,3,4,5,6,7}){
   auto mt=Movable(A,B,rng,arm==7);
   const auto&p=mt.active;vector<char>locked(n,0);
   L x=p.A;int ev=0;
   int goal=greedy_adopt(x,p,locked,max(2,int(p.D.size())/2),rng,ev);
   for(int q=0;q<8;q++){
    SwapChoice t=select_exchange(x,p,locked,p.envelope,arm,rng,ev);
    x=move(t.child);
    locked[t.release]=0;locked[t.adopt]=1;
    int lockedCount=0;
    for(int i:p.D)if(locked[i]){
      lockedCount++;
      if(x.s[i]!=p.B.s[i])throw runtime_error("exchange broken constraint");
    }
    if(lockedCount!=goal||x.e!=energy_direct(x.s))throw runtime_error("exchange integrity failed");
    int steps=0;x=tabu_locked(x,locked,p.B,rng,steps);
    if(x.e!=energy_direct(x.s))throw runtime_error("restricted tabu energy invalid");
   }
  }
 }
 cout<<"PASS moving-protection donor source geometry, matched virtual B and eightfold LABS score\n";
}
int main(int argc,char**argv){
 if(argc==2 && string(argv[1])=="--selftest"){selftest_exchange();return 0;}
 if(argc<6){cerr<<"usage: PARENTS.tsv OUT_SESSIONS.tsv OUT_NOVEL.tsv REPS BUDGET_MS\n";return 2;}
 auto pool=load(argv[1]);map<string,Parent*>byid;
 unordered_map<int,unordered_set<string>>registry;
 unordered_map<int,int>opt;
 for(auto&p:pool){byid[p.id]=&p;registry[p.n].insert(p.canonical);
  opt[p.n]=opt.count(p.n)?min(opt[p.n],p.best):p.best;}
 const vector<pair<string,string>>selected={{"c46_0","c46_1"},{"c47_0","c47_2"},
 {"c50_0","c50_1"},{"c59_0","c59_2"},{"c60_1","c60_4"},
 {"c60_0","c60_3"},{"c60_2","c60_5"},{"c92_0","c92_1"},{"c99_0","c99_1"}};
 int reps=stoi(argv[4]),ms=stoi(argv[5]);
 ofstream out(argv[2]),nov(argv[3]);if(!out||!nov)throw runtime_error("output open error");
 out<<"N\tpair\tA_id\tB_id\trep\tarm\ttrajectory_count\toffspring\t"
 "bestE\tbestBits\tbestCanon\tbestDist\tbestStage\tbestLockCount\t"
 "nov5\tnov10\tnov15\tnov20\tmeanAllRepairedE\tmeanAllPreE\t"
 "evals\tprotectMoves\tstageVisits\tlockedEvents\tmodelMs\tpathMs\tprotectedMs\tfinalRepairMs\telapsedMs\n";
 nov<<"N\tpair\trep\tarm\tstage\tlockedCount\tE\tbits\tcanonical\tpreE\tpreBits\tclosestParentDist\n";
 out<<fixed<<setprecision(6);
 for(int pairIndex=0;pairIndex<(int)selected.size();pairIndex++){
  auto [an,bn]=selected[pairIndex];
  if(!byid.count(an)||!byid.count(bn))throw runtime_error("missing source");
  Parent&A=*byid[an],&B=*byid[bn];
  const string pair=an+"-"+bn;
  for(int rep=0;rep<reps;rep++)for(int arm=0;arm<8;arm++){
   mt19937_64 rng(hashseed(11761105ULL+pairIndex*17377ULL+rep*30931ULL+arm*22377ULL));
   auto start=clk::now();auto t=clk::now();PairContext p(A,B);
   double modelTime=ns(clk::now()-t).count();
   SearchStats stats;unordered_set<string>seen;
   while(stats.sessions==0 || ns(clk::now()-start).count()*1000<ms){
    if(arm==0){
     L s=A.state;const int radii[]={2,4,8,12};int k=radii[rng()%4];
     t=clk::now();
     for(int i:random_mask(A.n,k,rng))s.flip(i);
     stats.prepTime+=ns(clk::now()-t).count();
     measure_candidate(s,A,B,p,rng,-1,0,stats,registry[A.n],opt[A.n],seen,nov,rep,arm,pair);
     stats.sessions++;
    }else if(arm==1)run_path(p,4,rng,stats,A,B,registry[A.n],opt[A.n],seen,nov,rep,pair);
    else moving_trajectory(A,B,arm,rng,stats,registry[A.n],opt[A.n],seen,nov,rep,pair);
   }
   out<<A.n<<"\t"<<pair<<"\t"<<A.id<<"\t"<<B.id<<"\t"<<rep<<"\t"<<arm
      <<"\t"<<stats.sessions<<"\t"<<stats.offspring
      <<"\t"<<stats.bestE<<"\t"<<stats.bestBits<<"\t"<<stats.bestCanon<<"\t"<<stats.bestDist
      <<"\t"<<stats.bestStage<<"\t"<<stats.bestLock
      <<"\t"<<stats.nov5<<"\t"<<stats.nov10<<"\t"<<stats.nov15<<"\t"<<stats.nov20
      <<"\t"<<stats.meanE/stats.offspring<<"\t"<<stats.meanPreE/stats.offspring
      <<"\t"<<stats.evals<<"\t"<<stats.protectMoves<<"\t"<<stats.stageVisits
      <<"\t"<<stats.lockedEvents<<"\t"<<1000*modelTime
      <<"\t"<<1000*stats.prepTime<<"\t"<<1000*stats.protectTime
      <<"\t"<<1000*stats.finalTime<<"\t"<<1000*ns(clk::now()-start).count()<<"\n";
  }
  cerr<<"FINISHED moving-backbone pair "<<pair<<"\n";
 }
 cout<<"PASS fully costed donor lock exchange with source and virtual placebos\n";
}
