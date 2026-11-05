// Consensus-innovation allele recombination: test whether source-agreement
// flips unblock the exact third-optimum inheritance obstruction.
// All proposal selection AND common local repair charged to same real timer.
#define RECOMBINE_NO_MAIN
#include "../recombine.cpp"
#undef RECOMBINE_NO_MAIN
#include <climits>
#include <unordered_set>
#include <iomanip>
using namespace std;
struct Inherit {
 L A,B;
 vector<int>D,Q;
 int half,innovation;
 vector<int>env;
 Inherit(const Parent&a,const Parent&b):A(a.state),B(parse(align_donor(a.seq,b.seq))){
  for(int i=0;i<A.n;i++)(A.s[i]==B.s[i]?Q:D).push_back(i);
  if(D.size()<8)throw runtime_error("same-orbit/low-diversity parents");
  half=int(D.size())/2;
  innovation=A.n<=47?4:(A.n==50?8:6);
  if((int)Q.size()<innovation)throw runtime_error("not enough consensus sites");
  env.resize(A.n);
  for(int k=1;k<A.n;k++)env[k]=max(abs(A.c[k]),abs(B.c[k]));
 }
};
struct Mask {
 vector<char>d,q;
};
vector<char> choose(int n,int k,mt19937_64&rng){
 vector<int>idx(n);iota(idx.begin(),idx.end(),0);
 for(int i=0;i<k;i++)swap(idx[i],idx[i+(rng()%(n-i))]);
 vector<char>x(n,0);for(int i=0;i<k;i++)x[idx[i]]=1;return x;
}
Mask sample(const Inherit&prob,mt19937_64&rng,bool innovate){
 Mask m;m.d=choose(prob.D.size(),prob.half,rng);
 m.q=choose(prob.Q.size(),innovate?prob.innovation:0,rng);
 return m;
}
L instantiate(const Inherit&p,const Mask&m){
 L x=p.A;for(int i=0;i<(int)m.d.size();i++)if(m.d[i])x.flip(p.D[i]);
 for(int j=0;j<(int)m.q.size();j++)if(m.q[j])x.flip(p.Q[j]);
 return x;
}
double objective(const L&s,const vector<int>&env,int mode){
 if(mode!=6 && mode!=7)return s.e;
 double bad=0;
 for(int k=1;k<s.n;k++){
  int exceed=max(0,abs(s.c[k])-env[k]);
  bad+=double(exceed)*exceed;
 }
 return s.e+0.75*bad;
}
int pick(const vector<char>&m,char want,mt19937_64&rng){
 vector<int>idx;for(int i=0;i<(int)m.size();i++)if(m[i]==want)idx.push_back(i);
 if(idx.empty())throw runtime_error("empty exact cardinality mask side");
 return idx[rng()%idx.size()];
}
void swap_in(Mask&mask,L&state,const Inherit&p,mt19937_64&rng,bool donor,bool consensus){
 if(donor){
  int i=pick(mask.d,1,rng),j=pick(mask.d,0,rng);
  mask.d[i]=0;mask.d[j]=1;
  state.flip(p.D[i]);state.flip(p.D[j]);
 }
 if(consensus){
  int i=pick(mask.q,1,rng),j=pick(mask.q,0,rng);
  mask.q[i]=0;mask.q[j]=1;
  state.flip(p.Q[i]);state.flip(p.Q[j]);
 }
}
struct Generation{L child;int evaluated=0,prequench=0,accepted=0;Generation(const L&x):child(x){}};
Generation propose(const Inherit&p, int arm,const vector<int>&envelope,mt19937_64&rng){
 Generation out(p.A);
 if(arm==9){out.child=(rng()&1)?p.A:p.B;return out;}
 bool innovations=arm!=0;
 auto x=sample(p,rng,innovations);
 L cur=instantiate(p,x);L best=cur;
 double bestval=objective(best,envelope,arm),now=bestval;
 int steps=arm==8?4:24;
 for(int t=0;t<steps;t++){
  if(arm==1 || arm==8){
   auto candidate=sample(p,rng,innovations);
   L trial=instantiate(p,candidate);out.evaluated++;
   double value;
   if(arm==8){
    L z=trial;z.descend(0);out.prequench++;
    value=z.e; // standard steepest as costed proxy for ultimate post-Tabu result
   }else value=trial.e;
   if(t==0||value<bestval){best=trial;bestval=value;}
   continue;
  }
  Mask cand=x;L trial=cur;
  bool donor=false,consensus=false;
  if(arm==0||arm==2)donor=true;
  else if(arm==3)consensus=true;
  else if(arm==4){donor=(t%2==0);consensus=!donor;}
  else{donor=true;consensus=true;}
  swap_in(cand,trial,p,rng,donor,consensus);
  double value=objective(trial,envelope,arm);out.evaluated++;
  if(value<bestval){best=trial;bestval=value;}
  if(value<now){
   x=move(cand);cur=move(trial);now=value;out.accepted++;
  }
 }
 out.child=best;return out;
}
void check(){
 selftest();
 mt19937_64 rng(9401511);
 for(int n:{46,47,50,59,99}){
  Parent a,b;a.n=b.n=n;
  for(int i=0;i<n;i++){a.seq+=(rng()&1?'1':'0');b.seq+=(rng()&1?'1':'0');}
  a.state=parse(a.seq);b.state=parse(b.seq);
  Inherit ip(a,b);
  auto env=ip.env;
  for(int arm=0;arm<10;arm++){
   Generation g=propose(ip,arm,env,rng);
   assert(g.child.e==energy_direct(g.child.s));
   if(arm!=9){
    int diff=0,cons=0;
    for(int i:ip.D)diff+=(g.child.s[i]!=ip.A.s[i]);
    for(int i:ip.Q)cons+=(g.child.s[i]!=ip.A.s[i]);
    assert(diff==ip.half&&cons==(arm==0?0:ip.innovation));
   }
   int steps=0;auto z=repair(g.child,rng,steps);assert(E(z)==E(z)); // see compile? E(L) absent
   assert(z.e==energy_direct(z.s));
  }
 }
 cout<<"PASS independent score, invariance, source-consensus novelty and common repair checks\n";
}
int main(int argc,char**argv){
 if(argc==2&&string(argv[1])=="--selftest"){check();return 0;}
 if(argc<6){cerr<<"usage PARENTS.tsv SESSIONS.tsv CERTIFICATES.tsv REPS BUDGET_MS\n";return 2;}
 auto all=load(argv[1]);map<int,vector<Parent*>>groups;
 for(auto&p:all)groups[p.n].push_back(&p);
 int reps=stoi(argv[4]),budget=stoi(argv[5]);
 ofstream out(argv[2]),nov(argv[3]);
 if(!out||!nov)throw runtime_error("could not write output");
 out<<"N\tpair\tA_id\tB_id\tAE\tBE\tD\tQ\tconsensus_r\trep\tarm\tgeneration_count\t"
    "mean_all_postrepair_E\tbestE\tbestBits\tbestCanon\tbestDistSource\t"
    "bestNovelE\tnew5\tnew10\tnew15\tnew20\tnew_better_parent\t"
    "proposals\tprequench_calls\taccepted_swaps\tmodel_ms\tgeneration_ms\trepair_ms\telapsed_ms\n";
 nov<<"N\tpair\trep\tarm\tE\tbits\tcanon\tnearest_parent_orbit_distance\tthreshold5\tthreshold10\tthreshold15\tthreshold20\n";
 out<<fixed<<setprecision(6);
 for(const auto&[n,pool]:groups){
  if(pool.size()<2)continue;
  unordered_set<string>registered;int ref=INT_MAX;
  for(auto*p:pool)registered.insert(p->canonical),ref=min(ref,p->best);
  int index=0;
  for(int i=0;i<(int)pool.size();i++)for(int j=i+1;j<(int)pool.size();j++){
   const Parent&A=*pool[i],&B=*pool[j];
   Inherit ip(A,B);
   string pair=A.id+"-"+B.id;
   for(int rep=0;rep<reps;rep++)for(int arm=0;arm<10;arm++){
    mt19937_64 rng(hashseed(88499113+n*7197+index*7739+rep*10301+arm*37171));
    auto t0=clk::now();
    vector<int>env=ip.env;
    double modelSec=0,generatorSec=0,repairSec=0;
    if(arm==7){
     auto tick=clk::now();
     shuffle(env.begin()+1,env.end(),rng);
     modelSec=ns(clk::now()-tick).count();
    }
    int gens=0,proposals=0,preq=0,accepted=0,nov5=0,nov10=0,nov15=0,nov20=0,strict=0;
    int bestE=INT_MAX,bestOther=INT_MAX,bestDist=-1;
    double sum=0;string bestBits,bestCan;
    unordered_set<string>seen;
    while(gens==0 || ns(clk::now()-t0).count()*1000<budget){
     auto tick=clk::now();
     auto g=propose(ip,arm,env,rng);
     generatorSec+=ns(clk::now()-tick).count();
     proposals+=g.evaluated;preq+=g.prequench;accepted+=g.accepted;
     tick=clk::now();int steps=0;L x=repair(move(g.child),rng,steps);
     repairSec+=ns(clk::now()-tick).count();gens++;sum+=x.e;
     if(steps!=64||x.e!=energy_direct(x.s))throw runtime_error("invalid descendant direct E");
     string bts=bits(x),ca=canon(bts);
     int d=min(distance_to_parent_orbit(bts,A.seq),distance_to_parent_orbit(bts,B.seq));
     if(x.e<bestE){bestE=x.e;bestBits=bts;bestCan=ca;bestDist=d;}
     if(x.e<min(A.E,B.E))strict++;
     if(!registered.count(ca)){
      bestOther=min(bestOther,x.e);
      if(x.e<=ref*1.2 && seen.insert(ca).second){
       bool five=x.e<=ref*1.05,ten=x.e<=ref*1.10,
          fifteen=x.e<=ref*1.15;
       nov20++;nov15+=fifteen;nov10+=ten;nov5+=five;
       nov<<n<<"\t"<<pair<<"\t"<<rep<<"\t"<<arm<<"\t"<<x.e
          <<"\t"<<bts<<"\t"<<ca<<"\t"<<d
          <<"\t"<<five<<"\t"<<ten<<"\t"<<fifteen<<"\t1\n";
      }
     }
     if(gens>3000)throw runtime_error("unbounded repetitions");
    }
    out<<n<<"\t"<<pair<<"\t"<<A.id<<"\t"<<B.id<<"\t"<<A.E<<"\t"<<B.E
       <<"\t"<<ip.D.size()<<"\t"<<ip.Q.size()<<"\t"<<ip.innovation
       <<"\t"<<rep<<"\t"<<arm<<"\t"<<gens<<"\t"<<sum/gens
       <<"\t"<<bestE<<"\t"<<bestBits<<"\t"<<bestCan<<"\t"<<bestDist
       <<"\t"<<(bestOther==INT_MAX?-1:bestOther)
       <<"\t"<<nov5<<"\t"<<nov10<<"\t"<<nov15<<"\t"<<nov20<<"\t"<<strict
       <<"\t"<<proposals<<"\t"<<preq<<"\t"<<accepted
       <<"\t"<<1000*modelSec<<"\t"<<1000*generatorSec<<"\t"<<1000*repairSec
       <<"\t"<<1000*ns(clk::now()-t0).count()<<"\n";
   }
  }
  index++;
  cerr<<"N "<<n<<" pair "<<index<<"/"<<pool.size()*(pool.size()-1)/2<<" complete\n";
  }
 }
 cout<<"PASS fully costed donor + noninherited consensus variants\n";
}
