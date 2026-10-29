#define main old_main
#include "../lns_mask.cpp"
#undef main
#include <unordered_set>
#include <sstream>
#include <array>
#include <climits>

using RNG=mt19937_64;
string s64="1101100100110110000000101010000010100101111000101000011001110011";
string s80="11111111111010000001111010001001101010001101000111000110011001011010100110100101";
string s100="++++++--+++++-----++-++--+--++++++++++---+-++--++++-+--++----+--+-+-+-+-++---++---++-+-++-+-++--+-+-";
vector<int> parse(int n) {
 string x=n==64?s64:(n==80?s80:s100);
 if((int)x.size()!=n) {cerr<<"bad length "<<n<<" "<<x.size()<<"\n";exit(2);}
 vector<int>v;for(char t:x)v.push_back(t=='1'||t=='+'?1:-1);
 return v;
}
struct Traj {L current,best;int calls=0,improvements=0,returns=0,accepted=0;double last_t=0;};
void choose_walk(Traj &z,RNG&r,int radius=4,bool uphill=false){
 L candidate=z.current;
 for(int i:random_mask(candidate.n,radius,r))candidate.flip(i);
 candidate.descend(0);z.calls++;
 bool improve=candidate.e<z.best.e;
 if(improve){z.best=candidate;z.improvements++;}
 if(candidate.e<=z.current.e){z.current=move(candidate);z.accepted++;}
 else if(uphill){
  uniform_real_distribution<double>unif(0,1);
  double T=12.0*z.current.n/100.;
  if(unif(r)<exp(-(candidate.e-z.current.e)/max(1.,T)))z.current=move(candidate),z.accepted++;
 }
 else z.returns++;
}
void choose_mask(Traj &z,RNG&r,int mode,int m){
 vector<int> ds(z.current.n);for(int i=0;i<z.current.n;i++)ds[i]=z.current.delta(i);
 vector<int> ids;
 if(mode==0)ids=random_mask(z.current.n,m,r);
 else if(mode==1){auto pair=interactions(z.current,ds);ids=structural_mask(ds,pair,z.current.n,m,2,r);}
 else ids=soft_mask(ds,m,r);
 auto x=enumerate(z.current,ids,max(3,m/3));
 L chosen=z.current;
 for(int rule=0;rule<2;rule++){
  L a=x.repair;a.descend(rule);if(a.e<chosen.e)chosen=move(a);
  L b=x.excursion;b.descend(rule);if(b.e<chosen.e)chosen=move(b);
 }
 z.calls++;
 if(chosen.e<z.current.e){z.current=chosen;z.accepted++;}
 else z.returns++;
 if(chosen.e<z.best.e){z.best=move(chosen);z.improvements++;}
}
void tabu_step(Traj &z,RNG&r,vector<int>&last,int iter){
 int n=z.current.n,p=-1,b=INT_MAX;
 for(int i=0;i<n;i++){
  int de=z.current.delta(i);
  bool tab=iter-last[i]<=7;
  if(tab && z.current.e+de>=z.best.e)continue;
  if(de<b){b=de;p=i;}
 }
 if(p<0)p=uniform_int_distribution<int>(0,n-1)(r);
 z.current.flip(p);last[p]=iter;z.calls++;
 if(z.current.e<z.best.e){z.best=z.current;z.improvements++;}
}
int choose_thompson(const array<int,3>&wins,const array<int,3>&fails,RNG &r){
 double best=-1;int arm=0;
 for(int i=0;i<3;i++){
  gamma_distribution<double>a(1.+wins[i],1.),b(1.+fails[i],1.);
  double x=a(r),y=b(r);
  double cost=i==0?1.: (i==1?10.:7.);
  double score=x/(x+y)/cost;
  if(score>best){best=score;arm=i;}
 }
 return arm;
}
void run_policy(Traj &z,int policy,RNG&r,double secs,int m){
 auto start=clk::now();int iter=0;vector<int>tabu(z.current.n,-10000);
 array<int,3>wins={0,0,0},fails={0,0,0};
 int stall=0,old_best=z.best.e;
 while(ns(clk::now()-start).count()<secs){
  if(policy==0) choose_walk(z,r);
  else if(policy==1)tabu_step(z,r,tabu,iter);
  else if(policy==2)choose_mask(z,r,0,m);
  else if(policy==3)choose_mask(z,r,1,m);
  else if(policy==4){
   int arm=choose_thompson(wins,fails,r);
   if(arm==0)choose_walk(z,r);else choose_mask(z,r,arm==1?0:1,m);
   if(z.best.e<old_best)wins[arm]++;else fails[arm]++;
  }else if(policy==5){
   // Fixed portfolio plus a stagnation kick; NOT a full published ALNS.
   if(stall>=15){choose_walk(z,r,8,true);stall=0;}
   else if((iter%7)==0)choose_mask(z,r,0,m);
   else choose_walk(z,r,4,true);
  }
  if(z.best.e<old_best){old_best=z.best.e;stall=0;}
  else stall++;
  iter++;
 }
 z.last_t=ns(clk::now()-start).count();
}
int main(int argc,char**argv){
 if(argc==2&&string(argv[1])=="--test"){
  test();for(int n:{64,80,100}){L b(parse(n));cout<<"reference n="<<n<<" E="<<b.e<<"\n";}
  return 0;
 }
 if(argc<7){cerr<<"usage OUT.csv N BASES SEED INTERVENTION_MS TAIL_MS [PERTURB_K=12] [MASK_M=10]\n";return 2;}
 string out=argv[1];int n=stoi(argv[2]),bases=stoi(argv[3]);uint64_t seed=stoull(argv[4]);
 double intervention=stod(argv[5])/1000.,tail=stod(argv[6])/1000.;
 int K=argc>7?stoi(argv[7]):12,m=argc>8?stoi(argv[8]):10, reps=argc>9?stoi(argv[9]):1;
 ofstream f(out);
 f<<"n,group,rep,policy,baseE,refE,base_hamming,meanDelta,sdDelta,negativePairs,probe_hit,probe_mean_gain,probe_unique,phaseE,finalE,phase_gain,final_gain,phase_calls,tail_calls,phase_seconds,tail_seconds,phase_accept,phase_return\n";
 f<<setprecision(9)<<fixed;
 L reference(parse(n));assert(energy_direct(reference.s)==reference.e);
 for(int g=0;g<bases;g++){
  RNG warm(seed+uint64_t(g)*911117+37);L base=reference;
  if(K>0){for(int i:random_mask(n,K,warm))base.flip(i);base.descend(0);}
  else if(K<0){vector<int> init(n);for(int &z:init)z=warm()%2?1:-1;base=L(init);base.descend(0);
   for(int t=0;t<(-K);t++){
    L trial=base;for(int i:random_mask(n,4,warm))trial.flip(i);
    trial.descend(0);if(trial.e<base.e)base=move(trial);
   }
  }
  int ham=0;for(int i=0;i<n;i++)ham+=(reference.s[i]!=base.s[i]);
  vector<int>ds(n);double mean=0,variance=0;for(int i=0;i<n;i++)ds[i]=base.delta(i),mean+=ds[i];
  mean/=n;for(int d:ds)variance+=(d-mean)*(d-mean);variance=sqrt(variance/n);
  int neg=0;for(int a=0;a<n;a++)for(int b=a+1;b<n;b++){
   L t=base;t.flip(a);if(t.delta(b)-ds[b]<0)neg++;
  }
  RNG diagnostics(seed+g*31237+8771);int phits=0;double pgain=0;set<vector<int>>visited;
  for(int i=0;i<12;i++){
   L p=base;for(int j:random_mask(n,4,diagnostics))p.flip(j);p.descend(0);
   phits+=(p.e<base.e);pgain+=max(0,base.e-p.e);visited.insert(p.s);
  }
  for(int rep=0;rep<reps;rep++)for(int policy=0;policy<=5;policy++){
   RNG r(seed+g*733111+policy*7703+rep*174301+177);
   Traj z;z.current=base;z.best=base;
   run_policy(z,policy,r,intervention,m);
   int phaseE=z.best.e,pcalls=z.calls,acc=z.accepted,ret=z.returns;double phase_t=z.last_t;
   z.current=z.best;
   RNG continu(seed+g*112123+rep*489271+999);
   run_policy(z,0,continu,tail,m);
   assert(energy_direct(z.best.s)==z.best.e);
   f<<n<<","<<g<<","<<rep<<","<<policy<<","<<base.e<<","<<reference.e<<","<<ham<<","<<mean<<","<<variance<<","<<neg<<","<<phits<<","<<pgain/12<<","<<visited.size()<<","<<phaseE<<","<<z.best.e<<","<<base.e-phaseE<<","<<base.e-z.best.e<<","<<pcalls<<","<<(z.calls-pcalls)<<","<<phase_t<<","<<z.last_t<<","<<acc<<","<<ret<<"\n";
  }
  if(g%30==0)cerr<<"n="<<n<<" group="<<g<<"/"<<bases<<" E="<<base.e<<"\n";
 }
}
