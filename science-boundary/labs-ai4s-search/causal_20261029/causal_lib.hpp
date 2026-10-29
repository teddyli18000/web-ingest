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
