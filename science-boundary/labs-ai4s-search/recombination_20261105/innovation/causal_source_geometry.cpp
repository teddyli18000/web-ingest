// Source-parent information test: binary crossover is mutation on donor
// disagreement sites. Compare real donor D vs permuted D, ordinary H-matched
// mutation, true-E mask swaps, small-radius elite restart and costed prequench.
// All outcomes use the SAME original-LABS steepest + 64 Tabu + steepest repair.
#define INNOVATION_NO_MAIN
#include "innovation.cpp"
#undef INNOVATION_NO_MAIN
#include <unordered_set>
#include <iomanip>
#include <climits>
using namespace std;

struct Ctx {
 L a;
 vector<int>D,Q,DP,QP;
 int n,d,h,r,H;
 Ctx(const Parent&A,const Parent&B,mt19937_64&rng):a(A.state),n(A.n){
  L b=parse(align_donor(A.seq,B.seq));
  if(b.n!=n||b.e!=B.E)throw runtime_error("donor orbit invalid");
  for(int i=0;i<n;i++)(a.s[i]!=b.s[i]?D:Q).push_back(i);
  d=D.size();h=d/2;r=n<=47?4:(n==50?8:6);H=h+r;
  if(d<8||h<2||r>=int(Q.size())||H>=n-2)throw runtime_error("nonmixable");
  DP=random_mask(n,d,rng);
  vector<char>seen(n,0);for(int i:DP)seen[i]=1;
  for(int i=0;i<n;i++)if(!seen[i])QP.push_back(i);
  if(QP.size()!=Q.size())throw runtime_error("placebo mismatch");
 }
};
struct CGen{L s;int proposals=0,accepted=0,quench=0,initialDiff=0;
 explicit CGen(const L&x):s(x){}};
L frommask(const Ctx&p,const vector<char>&x){
 L z=p.a;for(int i=0;i<p.n;i++)if(x[i])z.flip(i);return z;
}
vector<char> groupmask(const Ctx&p,bool real,mt19937_64&rng){
 const auto&d=real?p.D:p.DP;const auto&q=real?p.Q:p.QP;
 auto dx=choose(d.size(),p.h,rng),qy=choose(q.size(),p.r,rng);
 vector<char>selected(p.n,0);
 for(int i=0;i<int(d.size());i++)if(dx[i])selected[d[i]]=1;
 for(int i=0;i<int(q.size());i++)if(qy[i])selected[q[i]]=1;
 return selected;
}
void groupmove(const Ctx&p,bool real,vector<char>&x,L&z,mt19937_64&rng){
 const auto&d=real?p.D:p.DP;const auto&q=real?p.Q:p.QP;
 vector<int>one,zero;
 for(int pos:d)(x[pos]?one:zero).push_back(pos);
 int i=one[rng()%one.size()],j=zero[rng()%zero.size()];
 x[i]=0;x[j]=1;z.flip(i);z.flip(j);
 one.clear();zero.clear();
 for(int pos:q)(x[pos]?one:zero).push_back(pos);
 i=one[rng()%one.size()];j=zero[rng()%zero.size()];
 x[i]=0;x[j]=1;z.flip(i);z.flip(j);
}
void fullmove(vector<char>&x,L&z,mt19937_64&rng){
 int i=pick(x,1,rng),j=pick(x,0,rng);
 x[i]=0;x[j]=1;z.flip(i);z.flip(j);
}
int smallr(mt19937_64&rng){const int radii[]={2,4,8,12};return radii[rng()%4];}
CGen propose_causal(const Ctx&p,int arm,mt19937_64&rng){
 CGen o(p.a);
 if(arm==0)return o;
 bool grp=(arm==2||arm==3||arm==4||arm==5||arm==9);
 bool real=(arm==2||arm==4||arm==9);
 bool climb=(arm==4||arm==5||arm==6||arm==8);
 bool quench=(arm==9||arm==10);
 int radius=(arm==7||arm==8)?smallr(rng):p.H;
 auto mask=grp?groupmask(p,real,rng):choose(p.n,radius,rng);
 L current=frommask(p,mask),best=current;
 if(climb){
  int bestE=best.e;
  for(int step=0;step<24;step++){
   auto proposed=mask;L t=current;
   if(grp)groupmove(p,real,proposed,t,rng);
   else fullmove(proposed,t,rng);
   o.proposals++;
   if(t.e<current.e){current=t;mask=move(proposed);o.accepted++;}
   if(t.e<bestE){best=t;bestE=t.e;}
  }
 }
 if(quench){
  int bestQuench=INT_MAX;
  for(int k=0;k<4;k++){
   auto m=grp?groupmask(p,true,rng):choose(p.n,radius,rng);
   L candidate=frommask(p,m),z=candidate;
   o.proposals++;z.descend(0);o.quench++;
   if(z.e<bestQuench){bestQuench=z.e;best=candidate;}
  }
 }
 o.s=move(best);o.initialDiff=hd(bits(o.s),bits(p.a));
 if(arm!=7&&arm!=8&&o.initialDiff!=p.H)throw runtime_error("wrong Hamming radius");
 if((arm==7||arm==8)&&o.initialDiff!=radius)throw runtime_error("wrong small radius");
 if(o.s.e!=energy_direct(o.s.s))throw runtime_error("wrong candidate energy");
 return o;
}
void test_causal(){
 selftest();mt19937_64 rng(81521);int seen=0;
 for(int n:{46,47,50,59,60,92,99})for(int r=0;r<5;r++){
  Parent A,B;A.n=B.n=n;
  for(int i=0;i<n;i++){A.seq+=(rng()&1?'1':'0');B.seq+=(rng()&1?'1':'0');}
  A.state=parse(A.seq);B.state=parse(B.seq);A.E=A.state.e;B.E=B.state.e;
  Ctx p(A,B,rng);
  for(int arm=0;arm<11;arm++){
   auto t=propose_causal(p,arm,rng);assert(energy_direct(t.s.s)==t.s.e);
   if(arm==2||arm==4||arm==9||arm==3||arm==5){
    const auto &d=(arm==3||arm==5)?p.DP:p.D;
    const auto &q=(arm==3||arm==5)?p.QP:p.Q;
    int cd=0,cq=0;
    for(int i:d)cd+=(t.s.s[i]!=p.a.s[i]);
    for(int i:q)cq+=(t.s.s[i]!=p.a.s[i]);
    if(cd!=p.h||cq!=p.r)throw runtime_error("group cardinality");
   }
   int moves=0;auto after=repair(t.s,rng,moves);
   if(moves!=64||after.e!=energy_direct(after.s))throw runtime_error("postrepair score");
   seen++;
  }
 }
 cout<<"PASS "<<seen<<" exact candidate, placebo-matched mask, and shared repair tests\n";
}
int main(int argc,char**argv){
 if(argc==2 && string(argv[1])=="--selftest"){test_causal();return 0;}
 if(argc<6){cerr<<"usage PARENTS.tsv SESSIONS.tsv NOVEL.tsv REPS BUDGET_MS\n";return 2;}
 auto parents=load(argv[1]);map<int,vector<Parent*>>groups;
 for(auto&p:parents)groups[p.n].push_back(&p);
 int reps=stoi(argv[4]),budget=stoi(argv[5]);
 ofstream out(argv[2]),nov(argv[3]);
 if(!out||!nov)throw runtime_error("output open");
 out<<"N\tpair\tA_id\tB_id\tAE\tBE\trep\tarm\tbaseId\tD\tQ\th\tr\tH\tgenerations\t"
    "avg_initial_E\tavg_repaired_E\tbestE\tbestBits\tbestCanon\tbestParentDist\t"
    "bestPreE\tbestPreBits\tbestPreDistanceFromBase\tnew5\tnew10\tnew15\tnew20\t"
    "strictGain\tproposals\taccepted\tquenches\tmodelMs\tgenerationMs\trepairMs\telapsedMs\n";
 nov<<"N\tpair\trep\tarm\tE\tbits\tcanonical\tpreE\tpreBits\tparentDist\tpreDistanceBase\n";
 out<<fixed<<setprecision(6);
 for(auto&[n,pool]:groups){
  if(pool.size()<2)continue;
  unordered_set<string>registered;int bestKnown=INT_MAX;
  for(auto*p:pool){registered.insert(p->canonical);bestKnown=min(bestKnown,p->best);}
  int pairIndex=0;
  for(int i=0;i<(int)pool.size();i++)for(int j=i+1;j<(int)pool.size();j++){
   const Parent &left=*pool[i],&right=*pool[j];string pair=left.id+"-"+right.id;
   for(int rep=0;rep<reps;rep++){
    auto seed=hashseed(91238123ULL+n*983ULL+pairIndex*37511ULL+rep*33013ULL);
    bool dir=seed&1;
    const Parent &A=dir?right:left,&B=dir?left:right;
    for(int arm=0;arm<11;arm++){
     mt19937_64 rng(hashseed(seed+101711ULL+arm*47231ULL));
     auto start=clk::now();auto mt=clk::now();
     Ctx ctx(A,B,rng);
     double model=ns(clk::now()-mt).count(),genTime=0,repairTime=0,sumPre=0,sumRepair=0;
     int gens=0,near5=0,near10=0,near15=0,near20=0,strict=0,props=0,accept=0,qs=0;
     int bestE=INT_MAX,bestDist=INT_MAX,bestPre=0,bestPreDist=0;
     string bestBits,bestCanon,bestPreBits;
     unordered_set<string>newSet;
     while(gens==0||ns(clk::now()-start).count()*1000<budget){
      auto t=clk::now();auto p=propose_causal(ctx,arm,rng);
      genTime+=ns(clk::now()-t).count();props+=p.proposals;accept+=p.accepted;qs+=p.quench;
      int preE=p.s.e,preD=p.initialDiff;string preBits=bits(p.s);sumPre+=preE;
      t=clk::now();int steps=0;L z=repair(p.s,rng,steps);
      repairTime+=ns(clk::now()-t).count();
      if(steps!=64||z.e!=energy_direct(z.s))throw runtime_error("terminal score fail");
      gens++;sumRepair+=z.e;
      string bs=bits(z),ca=canon(bs);
      int dist=min(distance_to_parent_orbit(bs,left.seq),distance_to_parent_orbit(bs,right.seq));
      if(z.e<bestE){bestE=z.e;bestBits=bs;bestCanon=ca;bestDist=dist;
       bestPre=preE;bestPreBits=preBits;bestPreDist=preD;}
      if(z.e<min(left.E,right.E))strict++;
      if(!registered.count(ca)&&z.e<=bestKnown*1.2&&newSet.insert(ca).second){
       near20++;near15+=(z.e<=bestKnown*1.15);
       near10+=(z.e<=bestKnown*1.1);near5+=(z.e<=bestKnown*1.05);
       nov<<n<<"\t"<<pair<<"\t"<<rep<<"\t"<<arm<<"\t"<<z.e<<"\t"<<bs
        <<"\t"<<ca<<"\t"<<preE<<"\t"<<preBits<<"\t"<<dist<<"\t"<<preD<<"\n";
      }
      if(gens>20000)throw runtime_error("runaway timing");
     }
     out<<n<<"\t"<<pair<<"\t"<<left.id<<"\t"<<right.id<<"\t"<<left.E<<"\t"<<right.E
      <<"\t"<<rep<<"\t"<<arm<<"\t"<<A.id<<"\t"<<ctx.d<<"\t"<<ctx.Q.size()
      <<"\t"<<ctx.h<<"\t"<<ctx.r<<"\t"<<ctx.H<<"\t"<<gens
      <<"\t"<<sumPre/gens<<"\t"<<sumRepair/gens<<"\t"<<bestE
      <<"\t"<<bestBits<<"\t"<<bestCanon<<"\t"<<bestDist
      <<"\t"<<bestPre<<"\t"<<bestPreBits<<"\t"<<bestPreDist
      <<"\t"<<near5<<"\t"<<near10<<"\t"<<near15<<"\t"<<near20
      <<"\t"<<strict<<"\t"<<props<<"\t"<<accept<<"\t"<<qs
      <<"\t"<<1000*model<<"\t"<<1000*genTime<<"\t"<<1000*repairTime
      <<"\t"<<1000*ns(clk::now()-start).count()<<"\n";
    }
   }
   pairIndex++;
   cerr<<"N "<<n<<" pair "<<pairIndex<<"/"<<pool.size()*(pool.size()-1)/2<<" certified\n";
  }
 }
 cout<<"PASS source-orbit-identical-budget causal comparison completed\n";
}
