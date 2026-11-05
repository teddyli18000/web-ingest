// Independently seeded LABS elite inheritance: exact donor-mask joint optimization.
// Fixed at least 25% contribution from *each aligned parent* before repair.
// Compare exact autocorrelation envelope corridor with permuted-envelope placebo.
// Same true objective local repair and equal 120ms per pair/arm/seed.
// Reuses independently tested L/delta + archived 8-fold symmetry from recombine.cpp.
#define RECOMBINE_NO_MAIN
#include "recombine.cpp"
#undef RECOMBINE_NO_MAIN
#include <climits>
#include <cmath>
#include <unordered_set>
#include <sstream>
#include <numeric>

struct MaskProblem {
 L A,B;
 vector<int>D;
 int lo,hi;
 vector<int> envelope;
 explicit MaskProblem(const Parent&a,const Parent&b):A(a.state),B(parse(align_donor(a.seq,b.seq))){
  if(A.n!=B.n)throw runtime_error("unequal parent length");
  for(int i=0;i<A.n;i++)if(A.s[i]!=B.s[i])D.push_back(i);
  int d=D.size();
  if(d<8)throw runtime_error("source orbits not far enough to inherit distinct donor components");
  lo=max(2,(d+3)/4);hi=d-lo;
  envelope.resize(A.n);
  for(int k=1;k<A.n;k++)envelope[k]=max(abs(A.c[k]),abs(B.c[k]));
 }
 L state(const vector<char>&x)const{
  L s=A;
  for(int i=0;i<(int)D.size();i++)if(x[i])s.flip(D[i]);
  return s;
 }
 double corridor(const L&x, const vector<int>&env)const{
  double bad=0;
  for(int k=1;k<x.n;k++){
   int d=max(0,abs(x.c[k])-env[k]);bad+=d*d;
  }
  return double(x.e)+.75*bad;
 }
};
int countmask(const vector<char>&x){return accumulate(x.begin(),x.end(),0);}
vector<char> randmask(const MaskProblem&m,mt19937_64&rng){
 int d=m.D.size(),k=m.lo+int(rng()%((m.hi-m.lo)+1));
 vector<int>idx(d);iota(idx.begin(),idx.end(),0);
 for(int i=0;i<k;i++)swap(idx[i],idx[i+int(rng()%(d-i))]);
 vector<char>x(d,0);for(int i=0;i<k;i++)x[idx[i]]=1;
 return x;
}
vector<char> segmentmask(const MaskProblem&m,mt19937_64&rng){
 int d=m.D.size();
 for(int trials=0;trials<30;trials++){
  int begin=int(rng()%m.A.n),len=1+int(rng()%m.A.n);
  vector<char>x(d,0);int k=0;
  for(int i=0;i<d;i++){
   int p=m.D[i];if((p-begin+m.A.n)%m.A.n<len){x[i]=1;k++;}
  }
  if(k>=m.lo && k<=m.hi)return x;
 }
 return randmask(m,rng);
}
vector<char> fromstate(const MaskProblem&m,const L&x){
 vector<char>v(m.D.size(),0);
 for(int i=0;i<(int)m.D.size();i++)v[i]=m.A.s[m.D[i]]!=x.s[m.D[i]];
 return v;
}
void mask_swap(vector<char>&v, L&child,const MaskProblem&m,int a,int b){
 if(a==b||v[a]==v[b])throw runtime_error("invalid fixed-cardinality mask swap");
 child.flip(m.D[a]);child.flip(m.D[b]);
 v[a]^=1;v[b]^=1;
}
int step_choice(mt19937_64&rng,const vector<char>&mask,int state){
 vector<int>cand;
 for(int i=0;i<(int)mask.size();i++)if(mask[i]==state)cand.push_back(i);
 if(cand.empty())throw runtime_error("empty selection");
 return cand[rng()%cand.size()];
}
struct Result {L child;int evals=0,accepts=0;int cardinal=0;Result(const L&a):child(a){}};
Result propose(int arm,const MaskProblem&m,const vector<Parent*>&pool,mt19937_64&rng,
               const vector<vector<int>>*fos, const vector<int>&env){
 Result result(m.A);
 if(arm==0){result.child=(rng()&1)?m.A:m.B;return result;}
 vector<char>x=(arm==2)?segmentmask(m,rng):randmask(m,rng);
 L cur=m.state(x);
 if(arm==1||arm==2){result.child=cur;result.cardinal=countmask(x);return result;}
 double bestScore=(arm==7||arm==8)?m.corridor(cur,env):cur.e;
 L best=cur;int k=x.size(),fail=0;
 if(arm==3||arm==4){
  if(fos==nullptr)throw runtime_error("missing FOS");
  auto list=*fos;shuffle(list.begin(),list.end(),rng);
  for(const auto&indices:list){
   vector<char>z=x;int card=countmask(z);
   // Alternate FOS donors A/B; avoid only expanding B until hitting upper bound.
   int target=int(rng()&1);
   for(int pos:indices){
    if(m.A.s[pos]==m.B.s[pos])continue;
    int i=int(lower_bound(m.D.begin(),m.D.end(),pos)-m.D.begin());
    if(i>=k||m.D[i]!=pos)throw runtime_error("D set lookup mismatch");
    if(int(z[i])!=target){card+=target?1:-1;z[i]=char(target);}
   }
   if(card>m.hi||card<m.lo||z==x)continue;
   L proposal=m.state(z);result.evals++;
   if(proposal.e<=cur.e){
    x=move(z);cur=move(proposal);result.accepts++;
   }
  }
  result.child=cur;result.cardinal=countmask(x);return result;
 }
 // All four Johnson-graph controls use identical two-bit incremental evaluation,
 // exactly 24 proposed swaps per generated offspring (plus same repair).
 for(int iteration=0;iteration<24;iteration++){
  int i=step_choice(rng,x,1),j=step_choice(rng,x,0);
  L trial=cur;
  trial.flip(m.D[i]);trial.flip(m.D[j]);result.evals++;
  double cost=(arm==7||arm==8)?m.corridor(trial,env):trial.e;
  if(cost<bestScore){best=trial;bestScore=cost;}
  if(arm==5 || cost<(arm==7||arm==8?m.corridor(cur,env):cur.e)){
   mask_swap(x,cur,m,i,j);result.accepts++;fail=0;
  }else fail++;
  if(arm!=5 && fail>=12){
   x=randmask(m,rng);cur=m.state(x);fail=0;
   double v=(arm==7||arm==8)?m.corridor(cur,env):cur.e;
   if(v<bestScore){best=cur;bestScore=v;}
  }
 }
 result.child=best;result.cardinal=countmask(fromstate(m,best));return result;
}
int distance_to_parent_orbit(const string&s,const string&parent){
 int best=INT_MAX;
 for(const auto &z:orb(parent))best=min(best,hd(s,z));
 return best;
}
void test_inheritance(){
 selftest();
 mt19937_64 rng(4210011);
 for(int n:{46,59,99}){
  string s,t;
  for(int i=0;i<n;i++){s+=(rng()&1?'1':'0');t+=(rng()&1?'1':'0');}
  Parent a,b;a.seq=s;b.seq=t;a.state=parse(s);b.state=parse(t);a.n=b.n=n;
  MaskProblem problem(a,b);
  vector<Parent*>pool={&a,&b};
  auto mi=build_tree(link_mi(pool,n),n,rng);
  auto ep=build_tree(link_exact(pool,n),n,rng);
  for(int arm=0;arm<9;arm++){
   auto tmp=propose(arm,problem,pool,rng,arm==3?&mi:(arm==4?&ep:nullptr),problem.envelope);
   if(tmp.child.e!=energy_direct(tmp.child.s))throw runtime_error("exact mismatch in mask test");
   if(arm!=0 && (tmp.cardinal<problem.lo||tmp.cardinal>problem.hi))
    throw runtime_error("donor contribution cardinality violated");
  }
 }
 cout<<"PASS constrained-mask and exact-energy selftest\n";
}
int main(int argc,char**argv){
 if(argc==2 && string(argv[1])=="--selftest"){test_inheritance();return 0;}
 if(argc<6){cerr<<"usage: PARENTS.tsv SUMMARY.tsv ELITE.tsv REPS BUDGET_MS\n";return 2;}
 vector<Parent>all=load(argv[1]);
 map<int,vector<Parent*>>byN;
 for(auto &s:all)byN[s.n].push_back(&s);
 int reps=stoi(argv[4]),budget=stoi(argv[5]);
 ofstream summary(argv[2]),children(argv[3]);
 if(!summary||!children)throw runtime_error("cannot open outputs");
 summary<<"N\tpair\tA_id\tB_id\tAE\tBE\tdiff_count\trep\tarm\tgenerations\t"
         "avg_childE\tbestE\tbestBits\tbestCanon\tbestParentDist\tbestNovelE\t"
         "near10_unique\tnear15_unique\tnear20_unique\tnew_global_better\t"
         "pre_mix_valid\tmask_evals\tmask_accepted\tmodel_ms\tgeneration_ms\trepair_ms\telapsed_ms\n";
 children<<"N\tpair\trep\tarm\tE\tbits\tcanon\tparentDist\trelativePercent\tnear\n";
 summary<<fixed<<setprecision(6);
 for(const auto&[n,group]:byN){
  if(group.size()<2)continue;
  unordered_set<string>parents;
  int knownE=INT_MAX;
  for(auto *a:group)parents.insert(a->canonical),knownE=min(knownE,a->best);
  int pairNum=0;
  for(int ia=0;ia<(int)group.size();ia++)for(int ib=ia+1;ib<(int)group.size();ib++){
   const Parent&A=*group[ia],&B=*group[ib];
   MaskProblem problem(A,B);
   string pair=A.id+"-"+B.id;
   vector<Parent*> source=group;
   for(int rep=0;rep<reps;rep++){
    for(int arm=0;arm<9;arm++){
     mt19937_64 rng(hashseed(552113+n*7181+pairNum*71221+rep*5519+arm*30911));
     auto begun=clk::now();
     vector<vector<int>>fos;vector<int>env=problem.envelope;
     double modelSec=0,genSec=0,repSec=0;
     if(arm==3||arm==4){
      auto init=clk::now();
      fos=build_tree(arm==3?link_mi(source,n):link_exact(source,n),n,rng);
      modelSec=dur(init);
     }
     if(arm==8){
      // Lag-label-shuffled placebo with identical range of envelope magnitudes.
      auto init=clk::now();
      shuffle(env.begin()+1,env.end(),rng);
      modelSec=dur(init);
     }
     int num=0,n10=0,n15=0,n20=0,globalBetter=0,preValid=0;
     int evals=0,accept=0,bestE=INT_MAX,bestNovel=INT_MAX,bestParentDist=-1;
     double sum=0;
     string bestBits,bestCanon;
     unordered_set<string>found10,found15,found20;
     while(num==0||dur(begun)<budget/1000.){
      auto tm=clk::now();
      Result p=propose(arm,problem,source,rng,arm==3||arm==4?&fos:nullptr,env);
      genSec+=dur(tm);
      if(arm!=0 && (p.cardinal<problem.lo||p.cardinal>problem.hi))
       throw runtime_error("invalid pre-repair mixed donor cardinality");
      if(arm!=0)preValid++;
      evals+=p.evals;accept+=p.accepts;
      tm=clk::now();
      int steps=0;L v=repair(move(p.child),rng,steps);
      repSec+=dur(tm);
      if(energy_direct(v.s)!=v.e)throw runtime_error("bad repaired true E");
      string bs=bits(v),ca=canon(bs);
      sum+=v.e;num++;
      int d=min(distance_to_parent_orbit(bs,A.seq),distance_to_parent_orbit(bs,B.seq));
      if(v.e<bestE){bestE=v.e;bestBits=bs;bestCanon=ca;bestParentDist=d;}
      if(v.e<min(A.E,B.E))globalBetter++;
      if(!parents.count(ca)){
       bestNovel=min(bestNovel,v.e);
       if(v.e<=knownE*1.2 && found20.insert(ca).second){
        n20++;
        if(v.e<=knownE*1.15 && found15.insert(ca).second)n15++;
        if(v.e<=knownE*1.1 && found10.insert(ca).second)n10++;
        // Persist each unique <=20% result, including <=10% once.
        children<<n<<"\t"<<pair<<"\t"<<rep<<"\t"<<arm<<"\t"<<v.e<<"\t"<<bs
          <<"\t"<<ca<<"\t"<<d<<"\t"<<100.*(v.e/double(knownE)-1.)
          <<"\t"<<near(bs)<<"\n";
       }
      }
      if(num>2000)throw runtime_error("invalid duration loop");
     }
     summary<<n<<"\t"<<pair<<"\t"<<A.id<<"\t"<<B.id<<"\t"<<A.E<<"\t"<<B.E
      <<"\t"<<problem.D.size()<<"\t"<<rep<<"\t"<<arm<<"\t"<<num<<"\t"
      <<sum/num<<"\t"<<bestE<<"\t"<<bestBits<<"\t"<<bestCanon<<"\t"<<bestParentDist
      <<"\t"<<(bestNovel==INT_MAX?-1:bestNovel)<<"\t"
      <<n10<<"\t"<<n15<<"\t"<<n20<<"\t"<<globalBetter<<"\t"
      <<preValid<<"\t"<<evals<<"\t"<<accept<<"\t"
      <<1000*modelSec<<"\t"<<1000*genSec<<"\t"<<1000*repSec
      <<"\t"<<1000*dur(begun)<<"\n";
    }
   }
   pairNum++;
   cerr<<"complete N="<<n<<" pair "<<pairNum<<"/"<<group.size()*(group.size()-1)/2<<"\n";
  }
 }
 cout<<"PASS costed true LABS donor-conditional inheritance\n";
}
