// OFFLINE ONLY: enumerate one shared bank of five actual *nonzero* proposals
// after the identical direct repair(X); never load C or target-vault.
// Evaluates every candidate with exactly the usual 64-Tabu complete repair.
// This is an upper-bound diagnostic, not a costed deployable search strategy.
#define HIDDEN_REPAIR_NO_MAIN
#include "hidden_repair.cpp"
#undef HIDDEN_REPAIR_NO_MAIN
#include <fstream>
#include <iomanip>
using namespace std;

int main(int argc,char**argv){
 if(argc!=4)throw runtime_error("usage: probe_reachability INPUT FROZEN_MODELS OUTPUT");
 auto xs=load_inputs(argv[1]);auto models=load_models(argv[2]);
 ofstream out(argv[3]);if(!out)throw runtime_error("cannot open probe output");
 out<<"id\tn\tmode\tdamage\trep\tdonor_method\tj\tinitial_current_E"
    "\tbaseline_post_E\tbaseline_post_bits\tstarting_E\tstarting_bits\t"
    "raw_E\traw_bits\tpost_E\tpost_bits\tpost_canon\tpred_base\tpred_full\t"
    "candidate_repair_ms\n";
 out<<setprecision(14)<<fixed;
 long long counted=0;
 for(const Scenario&s:xs){
  uint64_t repSeed=hashseed(s.seed^0x44556677ULL);
  int st=0;L repaired=full_repair(s.X,repSeed,st);
  History hist(s.X.e);
  L current=s.X;
  if(repaired.e<s.X.e && canon(bits(repaired))!=s.ac){
    hist.prevGain=s.X.e-repaired.e;current=repaired;
    hist.best=min(hist.best,current.e);hist.stall=0;
  }else{hist.prevGain=0;hist.stall++;}
  hist.tried++;
  for(int method=0;method<3;method++){
    L B=parse(align_donor(s.astr,s.bstr));
    L donor=method==0?s.A:method==1?B:make_fake(s,s.seed);
    mt19937_64 rng(hashseed(s.seed^0xdff00ULL));
    for(int j=1;j<=5;j++){
      L raw=proposal(current,donor,rng,j);
      Feature f=describe(current,raw,s.A,B,hist);
      int steps=0;
      auto t0=clk::now();L post=full_repair(raw,repSeed,steps);
      double cost_ms=1000*dur(t0);
      if(steps!=64||post.e!=energy_direct(post.s))throw runtime_error("not exact repair");
      out<<s.id<<"\t"<<s.n<<"\t"<<s.mode<<"\t"<<s.damage<<"\t"<<s.rep
        <<"\t"<<method<<"\t"<<j<<"\t"<<s.X.e<<"\t"<<repaired.e<<"\t"
        <<bits(repaired)<<"\t"<<current.e<<"\t"<<bits(current)<<"\t"
        <<raw.e<<"\t"<<bits(raw)<<"\t"<<post.e<<"\t"<<bits(post)<<"\t"
        <<canon(bits(post))<<"\t"<<models.at("base").predict(f)<<"\t"
        <<models.at("full").predict(f)<<"\t"<<cost_ms<<"\n";
      counted++;
    }
  }
 }
 cerr<<"PASS probe complete repaired action bank "<<xs.size()<<" scenarios, "
   <<counted<<" exact candidate repairs with no C supplied\n";
 return 0;
}
