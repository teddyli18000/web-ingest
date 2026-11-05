// Symmetry orientation as a joint variable in source-elite LABS recombination.
// Uses already audited exactly Hamming-matched true-vs-virtual generator and
// common 64-step Tabu+steepest postrepair. Neither target third-optimum nor
// oracle successes are used to choose any orientation.
#define VIRTUAL_DONOR_NO_MAIN
#include "virtual_donor.cpp"
#undef VIRTUAL_DONOR_NO_MAIN
#include <algorithm>
#include <iomanip>
#include <unordered_set>
using namespace std;

struct AlignOption{
 Inherit p;
 string bbits;
 int d=0;
 long long signed_corr_sqdiff=0;
 AlignOption(const Parent&A,const Parent&B,int fixedK):
  p(A,B,false),bbits(B.seq),d(int(p.D.size())){
  p.half=fixedK;
  for(int k=1;k<p.A.n;k++){
   long long q=static_cast<long long>(p.A.c[k])-p.B.c[k];
   signed_corr_sqdiff+=q*q;
  }
 }
};
vector<AlignOption> options(const Parent&A,const Parent&B,int fixedK,int r){
 vector<AlignOption> all;
 for(const string&b:orb(B.seq)){
  Parent oriented=B;
  oriented.seq=b;oriented.state=parse(b);oriented.E=oriented.state.e;
  AlignOption v(A,oriented,fixedK);
  if(int(v.p.D.size())<=fixedK || int(v.p.Q.size())<r)
   throw runtime_error("orientation cannot support registered same-radius masks");
  all.push_back(v);
 }
 if(all.size()<2)throw runtime_error("too few independent symmetry variants");
 return all;
}
int index_min_hd(const vector<AlignOption>&v){
 int best=0;
 for(int i=1;i<int(v.size());i++)
  if(pair<int,string>(v[i].d,v[i].bbits)<pair<int,string>(v[best].d,v[best].bbits))best=i;
 return best;
}
int index_max_hd(const vector<AlignOption>&v){
 int best=0;
 for(int i=1;i<int(v.size());i++)
  if(v[i].d>v[best].d ||(v[i].d==v[best].d&&v[i].bbits<v[best].bbits))best=i;
 return best;
}
int index_signed(const vector<AlignOption>&v,bool least){
 int best=0;
 for(int i=1;i<int(v.size());i++){
  auto a=make_tuple(v[i].signed_corr_sqdiff,v[i].d,v[i].bbits);
  auto b=make_tuple(v[best].signed_corr_sqdiff,v[best].d,v[best].bbits);
  if((least&&a<b)||(!least&&make_tuple(-get<0>(a),get<1>(a),get<2>(a))<
                            make_tuple(-get<0>(b),get<1>(b),get<2>(b))))best=i;
 }
 return best;
}
int index_scout(vector<AlignOption>&v,bool steepest,mt19937_64&rng,int&probes){
 double best=1.e100;int which=0;
 for(int i=0;i<int(v.size());i++){
  for(int t=0;t<(steepest?1:2);t++){
   Mask m=sample(v[i].p,rng,true);
   L x=instantiate(v[i].p,m);
   if(steepest)x.descend(0);
   probes++;
   if(x.e<best){best=x.e;which=i;}
  }
 }
 return which;
}
void test_alignment(){
 test_virtual();
 mt19937_64 rng(571239);
 for(int n:{46,47,50,60,99}){
  Parent A,B;A.n=B.n=n;
  for(int i=0;i<n;i++){A.seq+=(rng()&1?'1':'0');B.seq+=(rng()&1?'1':'0');}
  A.state=parse(A.seq);B.state=parse(B.seq);A.E=A.state.e;B.E=B.state.e;
  Inherit base(A,B);int d=base.D.size(),k=d/2;
  auto v=options(A,B,k,base.innovation);
  for(int choice:{index_min_hd(v),index_max_hd(v),index_signed(v,true),index_signed(v,false)}){
   if(choice<0||choice>=int(v.size()))throw runtime_error("bad alignment index");
  }
  int probes=0;
  for(bool steep:{false,true}){
   int i=index_scout(v,steep,rng,probes);
   Candidate c=construct(5,A,v[i].p,d,rng);
   if(c.state.e!=energy_direct(c.state.s)||hd(bits(c.state),A.seq)!=k+base.innovation)
     throw runtime_error("independently exact geometry error");
  }
 }
 cout<<"PASS all 8-fold alignment/same-radius invariants and full source-independent repair\n";
}
int main(int argc,char**argv){
 if(argc==2&&string(argv[1])=="--selftest"){test_alignment();return 0;}
 if(argc<7){cerr<<"usage PARENTS SESSIONS NOVEL REPS BUDGET_MS PAIR [OFFSET]\n";return 2;}
 auto parents=load(argv[1]);map<string,const Parent*>mapid;
 for(const auto&z:parents)mapid[z.id]=&z;
 string pair=argv[6];auto cut=pair.find('-');
 if(cut==string::npos||!mapid.count(pair.substr(0,cut))||!mapid.count(pair.substr(cut+1)))
  throw runtime_error("unknown source parent pair");
 const Parent&A=*mapid[pair.substr(0,cut)],&B=*mapid[pair.substr(cut+1)];
 if(A.n!=B.n)throw runtime_error("different lengths");
 Inherit base(A,B);int n=A.n,d0=base.D.size(),k=d0/2,r=base.innovation;
 int reps=stoi(argv[4]),budget=stoi(argv[5]),offset=argc>7?stoi(argv[7]):20000;
 auto options0=options(A,B,k,r);
 int baselineIdx=index_min_hd(options0);
 if(options0[baselineIdx].d!=d0)throw runtime_error("wrong legacy nearest symmetry");
 unordered_set<string>sourceRegistry;
 int bestKnown=INT_MAX;
 for(const Parent&p:parents)if(p.n==n){sourceRegistry.insert(p.canonical);bestKnown=min(bestKnown,p.best);}
 ofstream out(argv[2]),nov(argv[3]);
 if(!out||!nov)throw runtime_error("bad path");
 out<<"N\tpair\tA_id\tB_id\tAE\tBE\tD0\tfixed_mask_hamming\trep\tarm\tgenerations\t"
      "avg_repaired_E\tbestE\tbestBits\tbestCanon\tbestSymDistance\t"
      "new5\tnew10\tnew20\tbestNovelE\t"
      "scouts\tmask_proposals\tgeneration_ms\tmodel_ms\trepair_ms\telapsed_ms\n";
 nov<<"N\tpair\trep\tarm\tE\tbits\tcanon\tnearest_source_distance\tthreshold5\tthreshold10\tthreshold20\n";
 out<<fixed<<setprecision(6);
 for(int rep=offset;rep<offset+reps;rep++){
  for(int arm=0;arm<9;arm++){
   mt19937_64 rng(hashseed(53113997ULL+n*6739ULL+d0*3319ULL+rep*91111ULL+arm*70001ULL));
   auto start=clk::now(),mt=clk::now();
   auto v=options(A,B,k,r);
   int choice=baselineIdx,scouts=0;
   if(arm==1)choice=index_signed(v,true);
   if(arm==2)choice=index_signed(v,false);
   if(arm==4)choice=index_max_hd(v);
   if(arm==5)choice=index_scout(v,false,rng,scouts);
   if(arm==8)choice=index_scout(v,true,rng,scouts);
   double model=ns(clk::now()-mt).count();
   int gens=0,proposals=0,nov5=0,nov10=0,nov20=0,bestE=INT_MAX,bnov=INT_MAX,dist=-1;
   double sum=0,genSec=0,repairSec=0;
   string bestBits,bestCanon;
   unordered_set<string>novel;
   while(gens==0||ns(clk::now()-start).count()*1000<budget){
    auto t=clk::now();
    Candidate raw(A.state);
    if(arm==7)raw=construct(0,A,base,d0,rng);
    else if(arm==6)raw=construct(6,A,base,d0,rng);
    else{
     int selected=arm==3?int(rng()%v.size()):choice;
     raw=construct(5,A,v[selected].p,d0,rng);
    }
    genSec+=ns(clk::now()-t).count();
    proposals+=raw.operations;
    t=clk::now();int moves=0;L z=repair(raw.state,rng,moves);
    repairSec+=ns(clk::now()-t).count();
    if(moves!=64||z.e!=energy_direct(z.s))throw runtime_error("postrepair exact LABS score mismatch");
    string s=bits(z),ca=canon(s);
    int dd=min(distance_to_parent_orbit(s,A.seq),distance_to_parent_orbit(s,B.seq));
    sum+=z.e;gens++;
    if(z.e<bestE){bestE=z.e;bestBits=s;bestCanon=ca;dist=dd;}
    if(!sourceRegistry.count(ca)){
     bnov=min(bnov,z.e);
     if(z.e<=1.2*bestKnown+1e-8 && novel.insert(ca).second){
      bool f=z.e<=1.05*bestKnown+1e-8,h=z.e<=1.10*bestKnown+1e-8;
      nov5+=f;nov10+=h;nov20++;
      nov<<n<<"\t"<<pair<<"\t"<<rep<<"\t"<<arm<<"\t"<<z.e<<"\t"<<s
         <<"\t"<<ca<<"\t"<<dd<<"\t"<<f<<"\t"<<h<<"\t1\n";
     }
    }
    if(gens>3000)throw runtime_error("infinite deadline loop");
   }
   out<<n<<"\t"<<pair<<"\t"<<A.id<<"\t"<<B.id<<"\t"<<A.E<<"\t"<<B.E
      <<"\t"<<d0<<"\t"<<k+r<<"\t"<<rep<<"\t"<<arm<<"\t"<<gens
      <<"\t"<<sum/gens<<"\t"<<bestE<<"\t"<<bestBits<<"\t"<<bestCanon<<"\t"<<dist
      <<"\t"<<nov5<<"\t"<<nov10<<"\t"<<nov20<<"\t"<<(bnov==INT_MAX?-1:bnov)
      <<"\t"<<scouts<<"\t"<<proposals<<"\t"<<1000*genSec<<"\t"<<1000*model
      <<"\t"<<1000*repairSec<<"\t"<<1000*ns(clk::now()-start).count()<<"\n";
  }
 }
 cout<<"PASS symmetry-aware source-elite operator generation and costed common repair "<<pair<<"\n";
}
