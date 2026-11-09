// Native elite-parent repair-conditioned mask-space search, including full
// original steepest->Tabu64->steepest repair for every evaluated candidate.
// Actual computer time and all candidate scorings charged to session.
// Predeclared experiment: see basin_search/README.md.
#define INNOVATION_NO_MAIN
#include "../innovation.cpp"
#undef INNOVATION_NO_MAIN
#include <unordered_map>
#include <unordered_set>
#include <iomanip>
#include <climits>
#include <memory>
#include <sstream>
using namespace std;

struct Ctx {
  L A; vector<int>D,Q; int h=0,r=0; bool fake=false;
  Ctx(const Parent&a,const Parent&b,bool virtualB,mt19937_64&rng):A(a.state),fake(virtualB){
    L B=parse(align_donor(a.seq,b.seq));
    if(B.n!=A.n || B.e!=b.E) throw runtime_error("invalid aligned elite donor");
    if(fake){
      vector<int>ind(A.n);iota(ind.begin(),ind.end(),0);
      shuffle(ind.begin(),ind.end(),rng);
      int d=0;for(int i=0;i<A.n;i++)d+=(A.s[i]!=B.s[i]);
      vector<char>v(A.n,0);for(int i=0;i<d;i++)v[ind[i]]=1;
      for(int i=0;i<A.n;i++)(v[i]?D:Q).push_back(i);
    }else{
      for(int i=0;i<A.n;i++)(A.s[i]!=B.s[i]?D:Q).push_back(i);
    }
    h=D.size()/2;r=A.n<=47?4:(A.n==50?8:6);
    if(D.size()<8 || h<1 || r<1 || r>=int(Q.size()))
      throw runtime_error("unmixable true/virtual pair");
  }
};
struct Candidate {
  Mask mask;L raw,after;
  string canonword,word;
  int repairs=0;
  Candidate(Mask m,L raw0,L after0,string canonical0,string word0):
      mask(move(m)),raw(move(raw0)),after(move(after0)),
      canonword(move(canonical0)),word(move(word0)){}
};
uint64_t hashchild(const string&x,uint64_t seed){
  uint64_t h=1469598103934665603ull ^ hashseed(seed);
  for(unsigned char c:x){h^=uint64_t(c);h*=1099511628211ull;}
  return hashseed(h);
}
Mask initial_mask(const Ctx&p,mt19937_64&rng){
  Mask m;m.d=choose(int(p.D.size()),p.h,rng);m.q=choose(int(p.Q.size()),p.r,rng);return m;
}
L from_mask(const Ctx&p,const Mask&m){
  L x=p.A;
  for(int i=0;i<int(p.D.size());i++)if(m.d[i])x.flip(p.D[i]);
  for(int j=0;j<int(p.Q.size());j++)if(m.q[j])x.flip(p.Q[j]);
  return x;
}
Candidate score_candidate(const Ctx&p,Mask m,uint64_t repeatSeed){
  L raw=from_mask(p,m);
  string pre=bits(raw);
  mt19937_64 rng(hashchild(pre,repeatSeed));
  int steps=0;
  L t=repair(raw,rng,steps);
  if(steps!=64||t.e!=energy_direct(t.s))throw runtime_error("repair failure");
  string word=bits(t);
  return Candidate(move(m),move(raw),move(t),canon(word),word);
}
bool source_novel(const Candidate&c,const unordered_set<string>&registry){
  return registry.find(c.canonword)==registry.end();
}
bool better(const Candidate&cand,const Candidate&current,int arm,const unordered_set<string>&reg,int limit){
  if(arm==4){
    bool a=source_novel(cand,reg)&&cand.after.e<=limit;
    bool b=source_novel(current,reg)&&current.after.e<=limit;
    if(a!=b)return a;
  }
  return cand.after.e<current.after.e;
}
struct Stats{
  int evals=0,rawMoves=0,accepted=0,restarts=0,bestE=INT_MAX,bestNovelE=INT_MAX;
  int novel5=0,novel10=0,novel20=0,nearParent=0,novelAll=0;
  int preBestE=INT_MAX,bestDist=0;
  double meanE=0,meanRaw=0,usedSeconds=0;
  string bestBits,bestCanon,bestNovelBits,bestNovelCanon;
  unordered_set<string>visited,unique10,unique5;
};
void inspect(const Candidate&c,const Parent&A,const Parent&B,int optimum,
             const unordered_set<string>&reg,Stats&s,
             ofstream&out,int rep,int arm,const string&pair){
  int e=c.after.e;
  s.evals++;s.meanE+=e;s.meanRaw+=c.raw.e;
  if(e<s.bestE){
    s.bestE=e;s.bestBits=c.word;s.bestCanon=c.canonword;s.preBestE=c.raw.e;
    s.bestDist=min(distance_to_parent_orbit(c.word,A.seq),distance_to_parent_orbit(c.word,B.seq));
  }
  if(reg.count(c.canonword)){s.nearParent++;return;}
  bool first=s.visited.insert(c.canonword).second;
  s.novelAll+=first;
  if(e<s.bestNovelE){s.bestNovelE=e;s.bestNovelBits=c.word;s.bestNovelCanon=c.canonword;}
  if(e<=optimum*1.2 && first){
    // report every distinct new within 20%, but emit once per session.
    if(s.unique10.count(c.canonword))return;
    s.novel20++;
    bool ten=e<=optimum*1.1,five=e<=optimum*1.05;
    if(ten)s.novel10++,s.unique10.insert(c.canonword);
    if(five)s.novel5++,s.unique5.insert(c.canonword);
    out<<A.n<<"\t"<<pair<<"\t"<<rep<<"\t"<<arm<<"\t"<<e<<"\t"<<c.word
       <<"\t"<<c.canonword<<"\t"<<c.raw.e<<"\t"<<bits(c.raw)<<"\t"
       <<min(distance_to_parent_orbit(c.word,A.seq),distance_to_parent_orbit(c.word,B.seq))
       <<"\n";
  }
}
void search_session(const Parent&A,const Parent&B,int arm,int rep,int pairidx,
                    int ms,const unordered_set<string>&reg,int optimum,
                    ofstream&out,ofstream&nov,const string&pair){
  uint64_t seed=hashseed(20261108ULL+uint64_t(pairidx)*910313ULL+
         uint64_t(rep)*100109ULL);
  mt19937_64 rng(hashseed(seed + uint64_t(arm)*102983ull));
  const auto t0=clk::now();
  const bool virt=arm==3;
  Ctx p(A,B,virt,rng);
  Stats st; unique_ptr<Candidate> current;
  int noaccept=0;
  int iteration=0;
  while(iteration==0||1000*ns(clk::now()-t0).count()<ms){
    iteration++;
    Mask m=initial_mask(p,rng);
    if(arm==5){
      // Distinct strong single-elite restart; mask encoding is irrelevant to mutation.
      L x=p.A;
      const int radii[]={2,4,8,12};
      int k=radii[rng()%4];
      for(int pos:random_mask(p.A.n,k,rng))x.flip(pos);
      mt19937_64 rr(hashchild(bits(x),seed));
      int moves=0;L t=repair(x,rr,moves);
      if(moves!=64||t.e!=energy_direct(t.s))throw runtime_error("source restart invalid");
      Candidate c(move(m),move(x),move(t),"","");
      c.word=bits(c.after);c.canonword=canon(c.word);
      inspect(c,A,B,optimum,reg,st,nov,rep,arm,pair);
      continue;
    }
    if(arm==1){
      // Existing raw E exact joint D/Q swaps. Only the chosen raw candidate
      // undergoes expensive original-objective Tabu repair.
      L cur=from_mask(p,m),best=cur;
      for(int it=0;it<24;it++){
        Mask trial=m;L alt=cur;
        int i=pick(trial.d,1,rng),j=pick(trial.d,0,rng);
        trial.d[i]=0;trial.d[j]=1;alt.flip(p.D[i]);alt.flip(p.D[j]);
        i=pick(trial.q,1,rng);j=pick(trial.q,0,rng);
        trial.q[i]=0;trial.q[j]=1;alt.flip(p.Q[i]);alt.flip(p.Q[j]);
        st.rawMoves++;
        if(alt.e<cur.e){cur=alt;m=move(trial);}
        if(alt.e<best.e)best=alt;
      }
      // best may be trial of final iteration, reconstruct mask by brute
      // comparison to A, preserving exact D/Q counts.
      Mask bm;
      bm.d.assign(p.D.size(),0);bm.q.assign(p.Q.size(),0);
      for(int i=0;i<int(p.D.size());i++)bm.d[i]=best.s[p.D[i]]!=p.A.s[p.D[i]];
      for(int i=0;i<int(p.Q.size());i++)bm.q[i]=best.s[p.Q[i]]!=p.A.s[p.Q[i]];
      Candidate c=score_candidate(p,move(bm),seed);
      inspect(c,A,B,optimum,reg,st,nov,rep,arm,pair);
      continue;
    }
    if(arm==0){
      Candidate c=score_candidate(p,move(m),seed);
      inspect(c,A,B,optimum,reg,st,nov,rep,arm,pair);
      continue;
    }
    if(!current || noaccept>=12){
      current=make_unique<Candidate>(score_candidate(p,move(m),seed));
      inspect(*current,A,B,optimum,reg,st,nov,rep,arm,pair);
      st.restarts++;noaccept=0;
      continue;
    }
    Mask trial=current->mask;
    L v=current->raw;
    // One exact donor+consensus 4-bit exchange per repaired candidate.
    int i=pick(trial.d,1,rng),j=pick(trial.d,0,rng);
    trial.d[i]=0;trial.d[j]=1;v.flip(p.D[i]);v.flip(p.D[j]);
    i=pick(trial.q,1,rng);j=pick(trial.q,0,rng);
    trial.q[i]=0;trial.q[j]=1;v.flip(p.Q[i]);v.flip(p.Q[j]);
    Candidate c=score_candidate(p,move(trial),seed);
    inspect(c,A,B,optimum,reg,st,nov,rep,arm,pair);
    if(better(c,*current,arm,reg,int(optimum*1.2))){
      current=make_unique<Candidate>(move(c));st.accepted++;noaccept=0;
    }else noaccept++;
  }
  st.usedSeconds=ns(clk::now()-t0).count();
  out<<A.n<<"\t"<<pair<<"\t"<<A.id<<"\t"<<B.id<<"\t"<<rep<<"\t"<<arm
     <<"\t"<<st.evals<<"\t"<<st.rawMoves<<"\t"<<st.accepted<<"\t"<<st.restarts
     <<"\t"<<st.bestE<<"\t"<<st.bestBits<<"\t"<<st.bestCanon<<"\t"<<st.bestDist
     <<"\t"<<(st.bestNovelE==INT_MAX?-1:st.bestNovelE)
     <<"\t"<<st.bestNovelBits<<"\t"<<st.bestNovelCanon
     <<"\t"<<st.novel5<<"\t"<<st.novel10<<"\t"<<st.novel20
     <<"\t"<<st.novelAll<<"\t"<<st.nearParent
     <<"\t"<<st.meanE/max(1,st.evals)<<"\t"<<st.meanRaw/max(1,st.evals)
     <<"\t"<<fixed<<setprecision(6)<<1000*st.usedSeconds<<"\n";
}
void test_basin(){
  selftest();mt19937_64 rng(20261108);int tests=0;
  for(int n:{46,47,50,59,60,92,99}){
    Parent a,b;a.id="A";b.id="B";a.n=b.n=n;
    for(int i=0;i<n;i++){a.seq+=rng()%2?'1':'0';b.seq+=rng()%2?'1':'0';}
    a.state=parse(a.seq);b.state=parse(b.seq);a.E=a.state.e;b.E=b.state.e;
    for(int fake=0;fake<=1;fake++){
      Ctx p(a,b,fake,rng);
      for(int z=0;z<5;z++){
        Mask m=initial_mask(p,rng);
        L x=from_mask(p,m);
        int ctD=0,ctQ=0;
        for(int i:p.D)ctD+=x.s[i]!=p.A.s[i];
        for(int j:p.Q)ctQ+=x.s[j]!=p.A.s[j];
        if(ctD!=p.h||ctQ!=p.r||x.e!=energy_direct(x.s))throw runtime_error("mask failure");
        auto c=score_candidate(p,move(m),rng());
        if(c.after.e!=energy_direct(c.after.s))throw runtime_error("conditional fate mismatch");
        tests++;
      }
    }
  }
  cout<<"PASS "<<tests<<" native exact parent/virtual and full postrepair mask checks\n";
}
int main(int argc,char **argv){
  if(argc==2 && string(argv[1])=="--selftest"){test_basin();return 0;}
  if(argc<6){cerr<<"usage PARENTS.tsv RESULTS.tsv NOVEL.tsv REPS BUDGET_MS [REP_OFFSET]\n";return 2;}
  auto parents=load(argv[1]);map<string,Parent*>id;
  unordered_map<int,unordered_set<string>>registry;map<int,int>optim;
  for(auto&p:parents){id[p.id]=&p;registry[p.n].insert(p.canonical);
    if(!optim.count(p.n)||p.best<optim[p.n])optim[p.n]=p.best;}
  const vector<pair<string,string>>pairs={{"c46_0","c46_1"},{"c47_0","c47_2"},
   {"c50_0","c50_1"},{"c59_0","c59_2"},{"c60_1","c60_4"},
   {"c60_0","c60_3"},{"c60_2","c60_5"},{"c92_0","c92_1"},{"c99_0","c99_1"}};
  int reps=stoi(argv[4]),ms=stoi(argv[5]),offset=(argc>6?stoi(argv[6]):0);
  ofstream out(argv[2]),nov(argv[3]);
  if(!out||!nov)throw runtime_error("open output failed");
  out<<"N\tpair\tA_id\tB_id\trep\tarm\tevaluated\traw_moves\taccepted\trestarts\t"
    "bestE\tbestBits\tbestCanon\tbestDist\tbestNovelE\tbestNovelBits\tbestNovelCanon\t"
    "novel5\tnovel10\tnovel20\tall_novel_orbits\tparent_returns\tmean_repair_E\tmean_raw_E\telapsed_ms\n";
  nov<<"N\tpair\trep\tarm\tE\tbits\tcanonical\trawE\trawBits\tclosestParentDist\n";
  for(int ip=0;ip<int(pairs.size());ip++){
    auto [an,bn]=pairs[ip];if(!id.count(an)||!id.count(bn))throw runtime_error("missing frozen parent");
    const Parent &A=*id.at(an),&B=*id.at(bn);
    if(A.n!=B.n)throw runtime_error("cross N");
    for(int rep=offset;rep<offset+reps;rep++)for(int arm=0;arm<6;arm++)
      search_session(A,B,arm,rep,ip,ms,registry[A.n],optim[A.n],out,nov,an+"-"+bn);
    cerr<<"COMPLETE "<<an<<" / "<<bn<<" source-orbit fixed pairs\n";
  }
  cout<<"PASS full-cost true/virtual B basin-conditioned donor mask experiment\n";
}
