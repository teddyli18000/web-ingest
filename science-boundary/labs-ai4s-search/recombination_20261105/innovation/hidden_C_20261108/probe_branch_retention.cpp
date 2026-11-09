// Offline C-free two-branch reachability: after full repair(X), compare keeping
// just the accepted improved repaired state vs retaining original damaged X.
#define HIDDEN_REPAIR_NO_MAIN
#include "hidden_repair.cpp"
#undef HIDDEN_REPAIR_NO_MAIN
#include <fstream>
#include <iomanip>
using namespace std;
int main(int argc,char**argv){
 if(argc!=4)throw runtime_error("usage: probe_branch_retention INPUT FROZEN_MODEL BANK.TSV");
 auto xs=load_inputs(argv[1]);auto models=load_models(argv[2]);
 ofstream out(argv[3]);if(!out)throw runtime_error("output failed");
 out<<"id\tn\tmode\tdamage\trep\tbranch\tdonor_method\tj\tinitial_current_E"
    "\tbaseline_post_E\tbaseline_post_bits\tstarting_E\tstarting_bits\t"
    "raw_E\traw_bits\tpost_E\tpost_bits\tpost_canon\tpred_base\tpred_full\tcandidate_repair_ms\n";
 out<<setprecision(14)<<fixed;
 long long count=0;
 for(const Scenario&s:xs){
   uint64_t repSeed=hashseed(s.seed^0x44556677ULL);
   int steps=0;L base=full_repair(s.X,repSeed,steps);
   for(int branch=0;branch<2;branch++){
     // branch 0: exact original deployed behavior after initial direct repair
     // branch 1: never discard the original X anchor while exploring alternatives
     History hist(s.X.e);
     L current=s.X;
     if(base.e<s.X.e && canon(bits(base))!=s.ac && branch==0){
        current=base;
        hist.prevGain=s.X.e-base.e;
        hist.best=min(hist.best,base.e);hist.stall=0;
     }else{
        hist.prevGain=max(0,s.X.e-base.e);
        hist.best=min(hist.best,base.e);
        hist.stall++;
     }
     hist.tried=1;
     for(int method=0;method<3;method++){
        L B=parse(align_donor(s.astr,s.bstr));
        L donor=(method==0?s.A:method==1?B:make_fake(s,s.seed));
        mt19937_64 rng(hashseed(s.seed^0xdff00ULL));
        for(int j=1;j<=5;j++){
            L raw=proposal(current,donor,rng,j);
            Feature f=describe(current,raw,s.A,B,hist);
            int stepcount=0;auto t=clk::now();
            L after=full_repair(raw,repSeed,stepcount);
            double elapsed=1000*dur(t);
            if(stepcount!=64||after.e!=energy_direct(after.s))throw runtime_error("wrong repair");
            out<<s.id<<"\t"<<s.n<<"\t"<<s.mode<<"\t"<<s.damage<<"\t"<<s.rep<<"\t"
              <<branch<<"\t"<<method<<"\t"<<j<<"\t"<<s.X.e<<"\t"<<base.e
              <<"\t"<<bits(base)<<"\t"<<current.e<<"\t"<<bits(current)
              <<"\t"<<raw.e<<"\t"<<bits(raw)<<"\t"<<after.e<<"\t"
              <<bits(after)<<"\t"<<canon(bits(after))<<"\t"
              <<models.at("base").predict(f)<<"\t"<<models.at("full").predict(f)
              <<"\t"<<elapsed<<"\n";
            count++;
        }
     }
   }
 }
 cout<<"PASS two C-blind branches "<<xs.size()<<" source states, "<<count
     <<" exact full-repair proposed outcomes\n";
}
