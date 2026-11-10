// Controlled LABS third-optimum study: this process MUST NOT see C or the vault.
// All state/parent features are signed correlation and history summaries; no
// target positions, target orbit, oracle paths, or C bits are passed here.
#define RECOMBINE_NO_MAIN
#include "../../recombine.cpp"
#undef RECOMBINE_NO_MAIN
#include <array>
#include <fstream>
#include <map>
#include <cmath>
#include <numeric>
#include <iomanip>
using namespace std;
constexpr int F=16;
constexpr int K=6;
struct Scenario {
 string id,aid,bid,mode,astr,bstr,xstr,ac,bc;
 int n,damage,rep,ex,da,db;
 uint64_t seed;
 L A,B,X;
 Scenario():n(0),damage(0),rep(0),ex(0),da(0),db(0){}
};
vector<Scenario> load_inputs(const string&path){
 ifstream f(path);if(!f)throw runtime_error("missing input");
 string line;getline(f,line);
 if(line.find("C_orbit")!=string::npos || line.find("C_id")!=string::npos)
  throw runtime_error("oracle target field in solver input!");
 vector<Scenario>out;
 while(getline(f,line)){
  if(line.empty())continue;istringstream z(line);Scenario s;
  z>>s.id>>s.n>>s.astr>>s.bstr>>s.xstr>>s.ac>>s.bc>>
   s.aid>>s.bid>>s.mode>>s.damage>>s.rep>>s.seed>>s.ex>>s.da>>s.db;
  s.A=parse(s.astr);s.B=parse(s.bstr);s.X=parse(s.xstr);
  if(s.n!=s.A.n||s.n!=s.B.n||s.n!=s.X.n ||
    s.X.e!=s.ex ||s.X.e!=energy_direct(s.X.s)||
    s.A.e!=energy_direct(s.A.s)||s.B.e!=energy_direct(s.B.s)||
    canon(s.astr)!=s.ac||canon(s.bstr)!=s.bc||s.ac==s.bc)
     throw runtime_error("invalid parent or initial certificate: "+s.id);
  if(s.mode!="AB_blind" && s.mode!="C_shell")throw runtime_error("bad tier");
  out.push_back(move(s));
 }
 if(out.empty())throw runtime_error("no scenarios");
 return out;
}
uint64_t stable_hash(const string&s,uint64_t seed){
 uint64_t h=1469598103934665603ULL ^ hashseed(seed);
 for(unsigned char ch:s){h^=ch;h*=1099511628211ULL;}
 return hashseed(h);
}
int hamming(const L&a,const L&b){
 int d=0;for(int i=0;i<a.n;i++)d+=(a.s[i]!=b.s[i]);return d;
}
L make_fake(const Scenario&s,uint64_t seed){
 mt19937_64 rng(hashseed(seed^0x9fac11ULL));
 L aligned=parse(align_donor(s.astr,s.bstr));
 int d=hamming(s.A,aligned);
 L fake=s.A;vector<int>pos(s.n);iota(pos.begin(),pos.end(),0);
 shuffle(pos.begin(),pos.end(),rng);
 for(int i=0;i<d;i++)fake.flip(pos[i]);
 if(hamming(fake,s.A)!=d)throw runtime_error("fake support distance mismatch");
 return fake;
}
struct History{
 int tried=0,stall=0,best,prevGain=0;int recoveries=0;
 explicit History(int e):best(e){}
};
struct Feature{
 array<double,F>f;
};
double signed_cos(const L&x,const L&y){
 double num=0,nx=0,ny=0;
 for(int k=1;k<x.n;k++){num+=double(x.c[k])*y.c[k];
 nx+=double(x.c[k])*x.c[k];ny+=double(y.c[k])*y.c[k];}
 return num/sqrt(max(1.0,nx*ny));
}
Feature describe(const L&current,const L&cand,const L&A,const L&B,const History&h){
 const int n=current.n;
 double odd=0,even=0;
 for(int k=1;k<n;k++)((k&1)?odd:even)+=double(cand.c[k])*cand.c[k];
 vector<int>changed;changed.reserve(n);
 for(int i=0;i<n;i++)if(current.s[i]!=cand.s[i])changed.push_back(i);
 long long linear=0;for(int i:changed)linear+=current.delta(i);
 double synergy=double(cand.e-current.e)-linear;
 double signed_joint=0;
 for(int k=1;k<n;k++)
   signed_joint+=double(cand.c[k]-current.c[k])*(A.c[k]-B.c[k])/(n-k);
 double support=0;
 for(int i:changed)support+=(A.s[i]!=B.s[i]);
 double den=n;
 Feature r;
 r.f={double(cand.e)/n,
      double(cand.e)/(double(n)*n),
      double(cand.e-current.e)/n,
      double(hamming(cand,A))/n,
      double(hamming(cand,B))/n,
      double(changed.size())/n,
      synergy/n,
      odd/max(1.0,odd+even),
      signed_cos(cand,A),
      signed_cos(cand,B),
      signed_joint/n,
      support/max(1.,double(changed.size())),
      double(h.best)/n,
      double(h.prevGain)/n,
      double(h.stall)/max(1.,double(h.tried+1)),
      double(current.e)/n};
 for(double v:r.f)if(!isfinite(v))throw runtime_error("nonfinite feature");
 return r;
}
L proposal(const L&current,const L&donor,mt19937_64&rng,int j){
 if(j==0)return current; // common unperturbed origin as a control
 int k=2*j;if(k>current.n)k=current.n;
 vector<int>diff,same,positions;
 for(int i=0;i<current.n;i++)(current.s[i]!=donor.s[i]?diff:same).push_back(i);
 shuffle(diff.begin(),diff.end(),rng);
 shuffle(same.begin(),same.end(),rng);
 int nd=min(int(diff.size()),k/2);
 int nq=min(int(same.size()),k-nd);
 while(nd+nq<k && nd<int(diff.size()))nd++;
 while(nd+nq<k && nq<int(same.size()))nq++;
 for(int i=0;i<nd;i++)positions.push_back(diff[i]);
 for(int i=0;i<nq;i++)positions.push_back(same[i]);
 L v=current;
 for(int pos:positions)v.flip(pos);
 if(hamming(v,current)!=k||v.e!=energy_direct(v.s))
  throw runtime_error("corrupted proposal");
 return v;
}
L full_repair(const L&raw,uint64_t baseSeed,int&steps){
 mt19937_64 rng(stable_hash(bits(raw),baseSeed));
 auto child=repair(raw,rng,steps);
 if(steps!=64 || child.e!=energy_direct(child.s))throw runtime_error("bad full repair");
 return child;
}
struct Model{
 double intercept=0;array<double,F>coef{};bool loaded=false;
 double predict(const Feature&f)const{
  double v=intercept;for(int i=0;i<F;i++)v+=coef[i]*f.f[i];return v;
 }
};
map<string,Model> load_models(const string&path){
 ifstream f(path);if(!f)throw runtime_error("missing frozen models");
 string line;getline(f,line);
 map<string,Model>out;
 while(getline(f,line)){
  if(line.empty())continue;
  istringstream z(line);string name;z>>name;
  Model m;z>>m.intercept;
  for(double&v:m.coef)if(!(z>>v))throw runtime_error("bad frozen coefficient file");
  m.loaded=true;out[name]=m;
 }
 if(!out.count("base")||!out.count("full"))throw runtime_error("missing learned baselines");
 return out;
}
void header_features(ofstream&out){
 for(int i=0;i<F;i++)out<<"\tf"<<i;
}
void print_features(ofstream&out,const Feature&f){
 for(double a:f.f)out<<"\t"<<setprecision(12)<<a;
}
void harvest(const vector<Scenario>&data,const string&file,int rounds){
 ofstream out(file);if(!out)throw runtime_error("harvest output open");
 out<<"id\tn\tmode\tA_id\tB_id\trep\tseed\tround\tproposal_index\tcurrentE\trawE\t"
    "repairE\trepairBits\trepairCanon\trepairSteps";
 header_features(out);out<<"\n";
 out<<fixed;
 for(const Scenario&s:data){
  mt19937_64 rng(hashseed(s.seed^0x112233445566ULL));
  const L B=parse(align_donor(s.astr,s.bstr));
  L current=s.X;History hist(current.e);
  uint64_t repairSeed=hashseed(s.seed^0xaa990011ULL);
  for(int round=0;round<rounds;round++){
   int selected=0;int selectedE=INT_MAX;L selectedRepair=current;
   for(int j=0;j<K;j++){
    L raw=proposal(current,B,rng,j);
    Feature feat=describe(current,raw,s.A,B,hist);
    int steps=0;L t=full_repair(raw,repairSeed,steps);
    out<<s.id<<"\t"<<s.n<<"\t"<<s.mode<<"\t"<<s.aid<<"\t"<<s.bid<<"\t"
       <<s.rep<<"\t"<<s.seed<<"\t"<<round<<"\t"<<j<<"\t"<<current.e<<"\t"
       <<raw.e<<"\t"<<t.e<<"\t"<<bits(t)<<"\t"<<canon(bits(t))<<"\t"<<steps;
    print_features(out,feat);out<<"\n";
    if(raw.e<selectedE){selectedE=raw.e;selected=j;selectedRepair=t;}
   }
   hist.tried++; // only the one chosen repair is observed by the simulated policy
   if(selectedRepair.e<current.e && canon(bits(selectedRepair))!=s.ac){
     hist.prevGain=current.e-selectedRepair.e;
     current=selectedRepair;hist.best=min(hist.best,current.e);hist.stall=0;
   }else{hist.prevGain=0;hist.stall++;}
  }
 }
 cout<<"PASS C-inaccessible harvest "<<data.size()<<" scenarios "<<K*rounds<<" repairs each\n";
}
void deploy(const vector<Scenario>&data,const map<string,Model>&models,
            const string&events,const string&summary,int budget){
 ofstream ev(events),out(summary);if(!ev||!out)throw runtime_error("deploy outputs open");
 ev<<"id\tn\tmode\tdamage\trep\tarm\titeration\tt_ms\tpostE\tpostBits\tpostCanon\t"
   "rawE\trawBits\tselection_ms\trepair_ms\tcurrentE\tcandidate_count\tproposal_origin_E\tproposal_origin_bits\tretention_active\talways_original\n";
 out<<"id\tn\tmode\tdamage\trep\tarm\tbudget_ms\twall_ms\tsteps\t"
    "bestE\tbestBits\tbestCanon\tbestNonA_E\tbestNonA_Bits\tbestNonA_Canon\t"
    "source_returns\tfull_repair_calls\tmodel_cost_ms\traw_energy_calls\n";
 ev<<fixed<<setprecision(7);out<<fixed<<setprecision(7);
 for(const Scenario&s:data){
  L B=parse(align_donor(s.astr,s.bstr));const string BC=canon(bits(B));
  for(int arm=0;arm<6;arm++){
   mt19937_64 rng(hashseed(s.seed^0xdff00ULL)); // shared proposal RNG until policies diverge
   L donor=(arm==1||arm==3||arm==4)?B:arm==2?make_fake(s,s.seed):s.A;
   L current=s.X;History history(current.e);
   const bool forceRealChange=(getenv("LABS_FORCE_NONZERO") && string(getenv("LABS_FORCE_NONZERO"))=="1");
   const bool retainOriginal=(getenv("LABS_RETAIN_ORIGINAL_X") && string(getenv("LABS_RETAIN_ORIGINAL_X"))=="1");
   const bool alwaysOriginal=(getenv("LABS_ALWAYS_ORIGINAL_X") && string(getenv("LABS_ALWAYS_ORIGINAL_X"))=="1");
   int bestE=INT_MAX,bestNonA=INT_MAX,sourceReturns=0,repairs=0,iterations=0,rawCount=0;
   double inferenceTime=0;
   string bestWord,bestCan,bestOtherWord,bestOtherCan;
   auto start=clk::now(); uint64_t repSeed=hashseed(s.seed^0x44556677ULL);
   auto observe=[&](const L&repaired,const L&raw,const L&origin,int iteration,double selectms,double repairms,int count){
     string word=bits(repaired),can=canon(word);
     double t=1000*dur(start);
     ev<<s.id<<"\t"<<s.n<<"\t"<<s.mode<<"\t"<<s.damage<<"\t"<<s.rep
       <<"\t"<<arm<<"\t"<<iteration<<"\t"<<t<<"\t"<<repaired.e<<"\t"
       <<word<<"\t"<<can<<"\t"<<raw.e<<"\t"<<bits(raw)<<"\t"<<selectms<<"\t"<<repairms
       <<"\t"<<current.e<<"\t"<<count<<"\t"<<origin.e<<"\t"<<bits(origin)<<"\t"<<int(retainOriginal)<<"\t"<<int(alwaysOriginal)<<"\n";
     repairs++;if(can==s.ac)sourceReturns++;
     if(repaired.e<bestE){bestE=repaired.e;bestWord=word;bestCan=can;}
     if(can!=s.ac && repaired.e<bestNonA){
       bestNonA=repaired.e;bestOtherWord=word;bestOtherCan=can;
     }
     if(repaired.e<current.e && can!=s.ac){
       history.prevGain=current.e-repaired.e;
       current=repaired;history.best=min(history.best,current.e);history.stall=0;
     }else{history.prevGain=0;history.stall++;}
     history.tried++;
   };
   // Each arm pays for the identical strong 64-step native repair(X).
   {int steps=0;auto ts=clk::now();L t=full_repair(s.X,repSeed,steps);
    double time=1000*dur(ts);observe(t,s.X,s.X,0,0,time,1);}
   while(1000*dur(start)<budget){
     iterations++;
     const auto t0=clk::now();
     const L origin=(alwaysOriginal||(retainOriginal && (iterations%2==1)))?s.X:current;
     L chosen=origin;Feature cf{};double bestScore=1.e100;
     int candidateCount=(arm==5?1:(forceRealChange?K-1:K));
     for(int j=0;j<candidateCount;j++){
       int proposalIndex=(arm==5?int(1+rng()%5):(forceRealChange?j+1:j));
       L raw=proposal(origin,donor,rng,proposalIndex);
       rawCount++;
       double val=raw.e;
       if(arm==3||arm==4){
         auto ft=clk::now();
         Feature ff=describe(origin,raw,s.A,B,history);
         val=models.at(arm==3?"full":"base").predict(ff);
         inferenceTime+=1000*dur(ft);
       }
       if(val<bestScore){
         bestScore=val;chosen=move(raw);
       }
     }
     double selectms=1000*dur(t0);
     int steps=0;auto rt=clk::now();L repaired=full_repair(chosen,repSeed,steps);
     double repairms=1000*dur(rt);
     observe(repaired,chosen,origin,iterations,selectms,repairms,candidateCount);
     if(iterations>10000)throw runtime_error("runaway iterations");
   }
   out<<s.id<<"\t"<<s.n<<"\t"<<s.mode<<"\t"<<s.damage<<"\t"<<s.rep
      <<"\t"<<arm<<"\t"<<budget<<"\t"<<1000*dur(start)<<"\t"<<iterations
      <<"\t"<<bestE<<"\t"<<bestWord<<"\t"<<bestCan<<"\t"
      <<(bestNonA==INT_MAX?-1:bestNonA)<<"\t"<<bestOtherWord<<"\t"<<bestOtherCan
      <<"\t"<<sourceReturns<<"\t"<<repairs<<"\t"<<inferenceTime
      <<"\t"<<rawCount<<"\n";
  }
 }
 cout<<"PASS zero-oracle-costed deployment "<<data.size()<<" matched states, 6 arms\n";
}
#ifndef HIDDEN_REPAIR_NO_MAIN
int main(int argc,char**argv){
 if(argc<2)throw runtime_error("mode harvest|deploy|selftest");
 string mode=argv[1];
 if(mode=="selftest"){
  selftest();mt19937_64 rng(20261108);string s;
  for(int i=0;i<46;i++)s+=(rng()&1?'1':'0');
  L A=parse(s),B=A;for(int i=0;i<16;i++)B.flip(i);
  History h(A.e);auto f=describe(A,B,A,B,h);
  for(double x:f.f)if(!isfinite(x))throw runtime_error("bad");
  for(int j=0;j<K;j++){L v=proposal(A,B,rng,j);
    int steps=0;auto z=full_repair(v,20261108,steps);
    if(z.e!=energy_direct(z.s))throw runtime_error("invalid test repair");
  }
  cout<<"PASS complete repair, C-blind candidate feature and correlation verifier\n";
  return 0;
 }
 if(mode=="harvest" && argc==5){
  harvest(load_inputs(argv[2]),argv[3],stoi(argv[4]));return 0;
 }
 if(mode=="deploy" && argc==7){
  deploy(load_inputs(argv[2]),load_models(argv[3]),argv[4],argv[5],stoi(argv[6]));return 0;
 }
 throw runtime_error("usage: harvest INPUT OUT ROUNDS | deploy INPUT FROZEN_MODELS EVENTS SUMMARY BUDGET_MS");
}
#endif  // HIDDEN_REPAIR_NO_MAIN
