// Test information value of a *real* elite second parent against a
// uniform virtual-donor null with the SAME total Hamming distance from A.
// The original 2026-11-05 innovation source is imported, so full 64-step
// Tabu + steepest pre/post-repair is IDENTICAL across all treatment arms.
#define INNOVATION_NO_MAIN
#include "innovation.cpp"
#undef INNOVATION_NO_MAIN
#include <fstream>
#include <sstream>
#include <iomanip>
using namespace std;

Inherit fake_inherit(const Parent&A,int d,mt19937_64&rng){
 Parent fake;
 fake.n=A.n;fake.seq=A.seq;
 auto ids=choose(A.n,d,rng);
 for(int i=0;i<A.n;i++)if(ids[i])fake.seq[i]=fake.seq[i]=='1'?'0':'1';
 fake.state=parse(fake.seq);
 Inherit p(A,fake,false);
 if((int)p.D.size()!=d||p.A.e!=A.E||p.Q.size()!=size_t(A.n-d))
  throw runtime_error("bad virtual donor matched source size");
 return p;
}
struct Candidate{L state;int operations=0,prequench=0,accepted=0;Candidate(const L&x):state(x){}};
Candidate construct(int arm,const Parent&A,const Inherit&trueB,int d,mt19937_64&rng){
 Candidate ret(A.state);
 if(arm==0)return ret;
 if(arm==9){
  // Single-parent exact Hamming-weight m mask-space hillclimb.
  int m=d/2+trueB.innovation;
  vector<char>mask=choose(A.n,m,rng);
  L cur=A.state;for(int i=0;i<A.n;i++)if(mask[i])cur.flip(i);
  L best=cur;
  for(int i=0;i<24;i++){
   int from=pick(mask,1,rng),to=pick(mask,0,rng);
   L nxt=cur;nxt.flip(from);nxt.flip(to);ret.operations++;
   if(nxt.e<best.e)best=nxt;
   if(nxt.e<cur.e){cur=move(nxt);mask[from]=0;mask[to]=1;ret.accepted++;}
  }
  ret.state=best;
  return ret;
 }
 bool real=(arm%2)==1;
 Inherit fake=real?trueB:fake_inherit(A,d,rng);
 const Inherit&p=real?trueB:fake;
 int origin=arm<=2?1:(arm<=4?8:(arm<=6?5:6));
 Generation proposal=propose(p,origin,p.env,rng);
 ret.state=move(proposal.child);
 ret.operations=proposal.evaluated;
 ret.prequench=proposal.prequench;
 ret.accepted=proposal.accepted;
 // Exact generation invariant: m flips from A, regardless of real or fake B.
 int m=d/2+trueB.innovation;
 int dist=hd(bits(ret.state),A.seq);
 if(dist!=m)throw runtime_error("not matched exact Hamming radius");
 if(ret.state.e!=energy_direct(ret.state.s))throw runtime_error("virtual donor pre-score");
 return ret;
}
void test_virtual(){
 selftest();
 mt19937_64 rng(991113);
 for(int n:{46,47,50,59,60,99}){
  Parent A,B;A.n=B.n=n;A.E=0;
  for(int i=0;i<n;i++){A.seq+=(rng()&1?'1':'0');B.seq+=(rng()&1?'1':'0');}
  A.state=parse(A.seq);A.E=A.state.e;B.state=parse(B.seq);B.E=B.state.e;
  Inherit original(A,B);
  for(int arm=0;arm<10;arm++){
   auto t=construct(arm,A,original,original.D.size(),rng);
   assert(t.state.e==energy_direct(t.state.s));
   if(arm!=0)assert(hd(bits(t.state),A.seq)==(int)original.D.size()/2+original.innovation);
   int moves=0;auto quench=repair(t.state,rng,moves);
   assert(moves==64&&quench.e==energy_direct(quench.s));
  }
 }
 cout<<"PASS virtual-donor matched-cardinality, direct E and all identical repair arms\n";
}
#ifndef VIRTUAL_DONOR_NO_MAIN
int main(int argc,char**argv){
 if(argc==2&&string(argv[1])=="--selftest"){test_virtual();return 0;}
 if(argc<7){
  cerr<<"usage PARENTS.tsv SESSIONS.tsv NOVEL.tsv REPS BUDGET_MS PAIR_ID [SEED_OFFSET]\n";
  return 2;
 }
 const auto parents=load(argv[1]);
 string target=argv[6];int reps=stoi(argv[4]),budget=stoi(argv[5]),offset=argc>7?stoi(argv[7]):10000;
 map<string,const Parent*> byid;for(const auto&z:parents)byid[z.id]=&z;
 auto hyphen=target.find('-');
 if(hyphen==string::npos)throw runtime_error("pair must be idA-idB");
 string ida=target.substr(0,hyphen),idb=target.substr(hyphen+1);
 if(!byid.count(ida)||!byid.count(idb))throw runtime_error("no target pair in parent library");
 const Parent&A=*byid[ida],&B=*byid[idb];
 if(A.n!=B.n)throw runtime_error("different source length");
 Inherit trueP(A,B);
 int n=A.n,d=trueP.D.size(),m=d/2+trueP.innovation;
 map<int,unordered_set<string>>known;
 map<int,int> optimum;
 for(const auto&z:parents){
  known[z.n].insert(z.canonical);
  if(!optimum.count(z.n))optimum[z.n]=z.best;
  optimum[z.n]=min(optimum[z.n],z.best);
 }
 ofstream out(argv[2]),nov(argv[3]);
 if(!out||!nov)throw runtime_error("unwritable output path");
 out<<"N\tpair\tA_id\tB_id\tAE\tBE\tD\tm\trep\tarm\tgeneration_count\t"
       "mean_all_postrepair_E\tbestE\tbestBits\tbestCanon\tbestDistSource\tbestNovelE\t"
       "new5\tnew10\tnew15\tnew20\tnew_better_parent\t"
       "proposals\tprequench_calls\taccepted_swaps\tgeneration_ms\trepair_ms\telapsed_ms\n";
 nov<<"N\tpair\trep\tarm\tE\tbits\tcanon\tnearest_parent_orbit_distance\tthreshold5\tthreshold10\tthreshold15\tthreshold20\n";
 out<<fixed<<setprecision(6);
 for(int rep=offset;rep<offset+reps;rep++){
  for(int arm=0;arm<10;arm++){
   mt19937_64 rng(hashseed(42473331ULL+n*7777ULL+d*17411ULL+rep*100991ULL+arm*71717ULL));
   auto start=clk::now();int gens=0,n5=0,n10=0,n15=0,n20=0,strict=0;
   int operations=0,preq=0,accepted=0,be=INT_MAX,bnov=INT_MAX,bd=-1;
   double sum=0,genSeconds=0,repairSeconds=0;
   string bestBits,bestCan;
   unordered_set<string>found;
   while(gens==0||ns(clk::now()-start).count()<budget/1000.){
    auto t=clk::now();Candidate c=construct(arm,A,trueP,d,rng);
    genSeconds+=ns(clk::now()-t).count();
    operations+=c.operations;preq+=c.prequench;accepted+=c.accepted;
    t=clk::now();int moves=0;L post=repair(c.state,rng,moves);
    repairSeconds+=ns(clk::now()-t).count();
    if(moves!=64||post.e!=energy_direct(post.s))throw runtime_error("invalid repaired true E");
    string bs=bits(post),canonBS=canon(bs);
    int dist=min(distance_to_parent_orbit(bs,A.seq),distance_to_parent_orbit(bs,B.seq));
    gens++;sum+=post.e;
    if(post.e<be){be=post.e;bestBits=bs;bestCan=canonBS;bd=dist;}
    if(post.e<min(A.E,B.E))strict++;
    if(!known[n].count(canonBS)){
     bnov=min(bnov,post.e);
     if(post.e<=1.2*optimum[n]+1e-8&&found.insert(canonBS).second){
      bool a=post.e<=1.05*optimum[n]+1e-8,
       b=post.e<=1.10*optimum[n]+1e-8,
       c=post.e<=1.15*optimum[n]+1e-8;
      n5+=a;n10+=b;n15+=c;n20++;
      nov<<n<<"\t"<<target<<"\t"<<rep<<"\t"<<arm<<"\t"<<post.e<<"\t"<<bs
         <<"\t"<<canonBS<<"\t"<<dist<<"\t"<<a<<"\t"<<b<<"\t"<<c<<"\t1\n";
     }
    }
    if(gens>3000)throw runtime_error("unexpected runaway time loop");
   }
   out<<n<<"\t"<<target<<"\t"<<A.id<<"\t"<<B.id<<"\t"<<A.E<<"\t"<<B.E<<"\t"
      <<d<<"\t"<<m<<"\t"<<rep<<"\t"<<arm<<"\t"<<gens<<"\t"
      <<sum/gens<<"\t"<<be<<"\t"<<bestBits<<"\t"<<bestCan<<"\t"<<bd<<"\t"
      <<(bnov==INT_MAX?-1:bnov)<<"\t"<<n5<<"\t"<<n10<<"\t"<<n15<<"\t"<<n20
      <<"\t"<<strict<<"\t"<<operations<<"\t"<<preq<<"\t"<<accepted<<"\t"
      <<1000*genSeconds<<"\t"<<1000*repairSeconds<<"\t"<<1000*ns(clk::now()-start).count()<<"\n";
  }
 }
 cout<<"PASS prospective matched-radius parent-information ablation for "<<target
     <<" new seeds "<<offset<<".."<<offset+reps-1<<"\n";
}

#endif // VIRTUAL_DONOR_NO_MAIN
