// Test parent-relative LABS symmetry alignment as a jointly optimized
// recombination variable, with the SAME balanced donor+consensus candidate
// generator and fully costed steepest+64-step-tabu repair for each arm.
// No hidden third optimum ever used in selecting a parent alignment.
#define main consensus_innovation_legacy_main
#include "innovation.cpp"
#undef main
#include <climits>
#include <unordered_set>
#include <iomanip>
using namespace std;
struct Relative {
 L A,B;
 vector<int>D,Q;
 int h,r,distance;
 string Bbits;
 Relative(const Parent&a,const string&b):A(a.state),B(parse(b)),Bbits(b){
  if(A.n!=B.n||A.e!=energy_direct(A.s)||B.e!=energy_direct(B.s))throw runtime_error("bad alignment");
  for(int i=0;i<A.n;i++)(A.s[i]==B.s[i]?Q:D).push_back(i);
  distance=D.size();h=distance/2;r=A.n<=47?4:(A.n==50?8:6);
  if(h<2||h>distance-2||r>=(int)Q.size())throw runtime_error("nonmixable orientation");
 }
 L candidate(mt19937_64&rng)const{
  L s=A;
  auto x=choose(D.size(),h,rng);
  auto y=choose(Q.size(),r,rng);
  for(int i=0;i<(int)D.size();i++)if(x[i])s.flip(D[i]);
  for(int i=0;i<(int)Q.size();i++)if(y[i])s.flip(Q[i]);
  return s;
 }
};
struct Generated{
 L child;
 int proposals,quench;
 Generated(L x,int v,int q):child(move(x)),proposals(v),quench(q){}
};
Generated draw(const Relative&v,mt19937_64&rng){
 int bestE=INT_MAX;L best=v.A;
 for(int j=0;j<4;j++){
  L c=v.candidate(rng),z=c;
  z.descend(0);
  if(z.e<bestE){bestE=z.e;best=move(c);}
 }
 return Generated(move(best),4,4);
}
vector<Relative> orientations(const Parent&A,const Parent&B){
 vector<Relative>v;
 for(const auto&x:orb(B.seq)){
  Relative r(A,x);
  v.push_back(move(r));
 }
 if(v.empty())throw runtime_error("empty B orbit");
 return v;
}
int select_alignment(int arm,const vector<Relative>&v,mt19937_64&rng,int&modelCandidates,int&modelQuenches){
 int idx=0;
 if(arm==0||arm==6){
  for(int i=1;i<(int)v.size();i++)if(v[i].distance<v[idx].distance)idx=i;
 }else if(arm==4){
  for(int i=1;i<(int)v.size();i++)if(v[i].distance>v[idx].distance)idx=i;
 }else if(arm==1){
  idx=int(rng()%v.size());
 }else if(arm==2||arm==5){
  // Sum or min of true raw candidate energies; 16 each orientation,
  // charged to budget, not informed by a third known optimum.
  double best=1e100;
  for(int i=0;i<(int)v.size();i++){
   double sum=0,bestE=INT_MAX;
   for(int j=0;j<16;j++){
    L s=v[i].candidate(rng);modelCandidates++;
    sum+=s.e;bestE=min(bestE,s.e);
   }
   double score=(arm==2)?sum/16:bestE;
   if(score<best){best=score;idx=i;}
  }
 }else if(arm==3){
  // Costed quench-proxy orientation choice, still no target labels.
  double best=1e100;
  for(int i=0;i<(int)v.size();i++){
   int opt=INT_MAX;
   for(int j=0;j<2;j++){
    L s=v[i].candidate(rng);modelCandidates++;s.descend(0);modelQuenches++;
    opt=min(opt,s.e);
   }
   if(opt<best){best=opt;idx=i;}
  }
 }else throw runtime_error("unknown orientation arm");
 return idx;
}
void selftest_align(){
 check();
 mt19937_64 rng(2031104);
 for(int n:{46,47,50,59,60,92,99}){
  Parent a,b;a.n=b.n=n;
  for(int i=0;i<n;i++){a.seq+=(rng()&1?'1':'0');b.seq+=(rng()&1?'1':'0');}
  a.state=parse(a.seq);b.state=parse(b.seq);
  auto all=orientations(a,b);
  for(int arm=0;arm<7;arm++){
   int props=0,qs=0;
   int i=select_alignment(arm,all,rng,props,qs);
   L s=all[i].candidate(rng);
   int da=0,dq=0;
   for(int z:all[i].D)da+=(s.s[z]!=all[i].A.s[z]);
   for(int z:all[i].Q)dq+=(s.s[z]!=all[i].A.s[z]);
   if(da!=all[i].h||dq!=all[i].r||s.e!=energy_direct(s.s))
    throw runtime_error("alignment/masked inheritance invariant failure");
   Generated g=draw(all[i],rng);
   int steps=0;auto w=repair(move(g.child),rng,steps);
   if(steps!=64||w.e!=energy_direct(w.s))throw runtime_error("repair invariant failure");
  }
 }
 cout<<"PASS all eight parent-relative symmetry orientations and joint mask cardinalities\n";
}
int main(int argc,char**argv){
 if(argc==2&&string(argv[1])=="--selftest"){selftest_align();return 0;}
 if(argc<6){cerr<<"usage PARENTS.tsv SESSION.tsv NOVEL.tsv REPS BUDGET_MS\n";return 2;}
 auto all=load(argv[1]);map<int,vector<Parent*>>groups;
 for(auto&p:all)groups[p.n].push_back(&p);
 const int reps=stoi(argv[4]),budget=stoi(argv[5]);
 ofstream out(argv[2]),children(argv[3]);
 if(!out||!children)throw runtime_error("could not write");
 out<<"N\tpair\tA_id\tB_id\tAE\tBE\trep\tarm\tgenerations\t"
  "meanRepairedE\tbestE\tbestBits\tbestCanonical\tbestNearestParent\t"
  "new5\tnew10\tnew15\tnew20\tbestNovelE\t"
  "modelCandidates\tmodelQuenches\tprequenchCalls\trepairMoves\t"
  "chosenOrientIndex\tchosenOrientDistance\tmodelMs\tproposeMs\trepairMs\telapsedMs\n";
 children<<"N\tpair\trep\tarm\tE\tbits\tcanonical\tminParentDist\tchosenOrientIndex\tbeforeBits\tbeforeE\n";
 out<<fixed<<setprecision(6);
 for(const auto&[n,pool]:groups){
  if(pool.size()<2)continue;
  int ref=INT_MAX;unordered_set<string>registry;
  for(const auto*p:pool)ref=min(ref,p->best),registry.insert(p->canonical);
  int ipair=0;
  for(int i=0;i<(int)pool.size();i++)for(int j=i+1;j<(int)pool.size();j++){
   const Parent&A=*pool[i],&B=*pool[j],other=B;
   auto choices=orientations(A,B);
   const string pair=A.id+"-"+B.id;
   for(int rep=0;rep<reps;rep++)for(int arm=0;arm<7;arm++){
    mt19937_64 rng(hashseed(20812002+n*9973+ipair*25331+rep*37003+arm*2381));
    auto time0=clk::now();
    int mdl=0,mdlQuenches=0,preq=0,moves=0;
    auto modelT=clk::now();
    int picked=select_alignment(arm,choices,rng,mdl,mdlQuenches);
    double modelSeconds=ns(clk::now()-modelT).count();
    int gens=0,new5=0,new10=0,new15=0,new20=0;
    int bestE=INT_MAX,bestNovel=INT_MAX,bestDist=INT_MAX;
    double sumE=0,proposalSeconds=0,repairSeconds=0;
    string bestBits,bestCanonical;
    unordered_set<string>seen;
    while(gens==0||ns(clk::now()-time0).count()*1000<budget){
     int orient=arm==1?select_alignment(arm,choices,rng,mdl,mdlQuenches):picked;
     auto tick=clk::now();
     auto g=draw(choices[orient],rng);
     proposalSeconds+=ns(clk::now()-tick).count();preq+=g.quench;
     string before=bits(g.child);int beforeE=g.child.e;
     tick=clk::now();int steps=0;L x=repair(move(g.child),rng,steps);
     repairSeconds+=ns(clk::now()-tick).count();
     if(steps!=64||x.e!=energy_direct(x.s))throw runtime_error("bad score");
     moves+=steps;gens++;sumE+=x.e;
     auto bs=bits(x),ca=canon(bs);
     int d=min(distance_to_parent_orbit(bs,A.seq),distance_to_parent_orbit(bs,B.seq));
     if(x.e<bestE){bestE=x.e;bestBits=bs;bestCanonical=ca;bestDist=d;}
     if(!registry.count(ca) && x.e<=ref*1.2 && seen.insert(ca).second){
      bestNovel=min(bestNovel,x.e);
      new20++;new15+=(x.e<=ref*1.15);new10+=(x.e<=ref*1.1);new5+=(x.e<=ref*1.05);
      children<<n<<"\t"<<pair<<"\t"<<rep<<"\t"<<arm<<"\t"<<x.e<<"\t"<<bs
       <<"\t"<<ca<<"\t"<<d<<"\t"<<orient<<"\t"<<before<<"\t"<<beforeE<<"\n";
     }
     if(gens>5000)throw runtime_error("unbounded test");
    }
    out<<n<<"\t"<<pair<<"\t"<<A.id<<"\t"<<B.id<<"\t"<<A.E<<"\t"<<B.E
     <<"\t"<<rep<<"\t"<<arm<<"\t"<<gens<<"\t"<<sumE/gens
     <<"\t"<<bestE<<"\t"<<bestBits<<"\t"<<bestCanonical<<"\t"<<bestDist
     <<"\t"<<new5<<"\t"<<new10<<"\t"<<new15<<"\t"<<new20
     <<"\t"<<(bestNovel==INT_MAX?-1:bestNovel)
     <<"\t"<<mdl<<"\t"<<mdlQuenches<<"\t"<<preq<<"\t"<<moves
     <<"\t"<<picked<<"\t"<<choices[picked].distance<<"\t"
     <<1000*modelSeconds<<"\t"<<1000*proposalSeconds<<"\t"<<1000*repairSeconds
     <<"\t"<<1000*ns(clk::now()-time0).count()<<"\n";
   }
  }
  ipair++;
  cerr<<"N="<<n<<" pair "<<ipair<<"/"<<pool.size()*(pool.size()-1)/2<<" tested\n";
  }
 }
 cout<<"PASS full-cost source-alignment and common-repair experiment\n";
}
