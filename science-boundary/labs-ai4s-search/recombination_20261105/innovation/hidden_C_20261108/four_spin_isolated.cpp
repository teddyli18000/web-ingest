// Isolated n=4 strong classical LABS benchmark, C-blind and exact-costed.
// Based on arXiv:2610.14361v3, NOT authors' implementation or TTS reproduction.
// Isolated objective retains only products whose four endpoints are selected.
// Important: the even-gap shortcut in a historical lab100 probe is incorrect:
// a shared-vertex pair term only exists when the midpoint is selected.
#define HIDDEN_REPAIR_NO_MAIN
#include "hidden_repair.cpp"
#undef HIDDEN_REPAIR_NO_MAIN
#include <unordered_set>
#include <climits>
using namespace std;
struct Pick {vector<int> pos;vector<int> val;};
static int isolated(const vector<int>&pos,const vector<int>&v){
  int m=pos.size(),z=0;
  for(int i=0;i<m;i++)for(int j=i+1;j<m;j++)
  for(int a=i;a<m;a++)for(int b=a+1;b<m;b++){
    if(a==i && b<=j)continue; // each unordered edge pair once
    if(pos[j]-pos[i]==pos[b]-pos[a])
      z+=2*v[i]*v[j]*v[a]*v[b];
  }
  return z;
}
// Independent, slow direct C_k^2 expansion of the environment-disconnected
// Hamiltonian; included only in selftest to guard subtle quartic/midpoint bugs.
static int isolated_reference(const vector<int>&pos,const vector<int>&v,int n){
  int z=0;
  for(int k=1;k<n;k++){
    vector<pair<int,int>> q;
    for(int i=0;i<n-k;i++){
      int a=find(pos.begin(),pos.end(),i)-pos.begin();
      int b=find(pos.begin(),pos.end(),i+k)-pos.begin();
      if(a<(int)pos.size() && b<(int)pos.size())q.push_back({a,b});
    }
    for(int i=0;i<(int)q.size();i++)for(int j=i+1;j<(int)q.size();j++)
      z+=2*v[q[i].first]*v[q[i].second]*v[q[j].first]*v[q[j].second];
  }
  return z;
}
static Pick optimized4(vector<int> pos,mt19937_64&rng){
  sort(pos.begin(),pos.end());
  int m=pos.size(),best=INT_MAX;
  vector<vector<int>> ties;
  for(int code=0;code<(1<<m);code++){
    vector<int> v(m);
    for(int i=0;i<m;i++)v[i]=(code&(1<<i))?1:-1;
    int z=isolated(pos,v);
    if(z<best){best=z;ties.clear();ties.push_back(v);}
    else if(z==best)ties.push_back(v);
  }
  if(ties.empty())throw runtime_error("empty iso4 assignments");
  return Pick{pos,ties[rng()%ties.size()]};
}
static L applied(const L&base,const Pick&p,bool complement){
  L q=base;
  for(int j=0;j<(int)p.pos.size();j++){
    int wanted=complement?-p.val[j]:p.val[j];
    if(q.s[p.pos[j]]!=wanted)q.flip(p.pos[j]);
  }
  return q;
}
static vector<int> random_positions(int n,mt19937_64&rng){
  vector<int> ids(n);iota(ids.begin(),ids.end(),0);
  for(int i=0;i<4;i++)swap(ids[i],ids[i+rng()%(n-i)]);
  ids.resize(4);sort(ids.begin(),ids.end());return ids;
}
struct Tracked{
  vector<int> unselected;
  int anchor=-1;
  vector<int> next(int n,mt19937_64&rng){
    if(unselected.empty()){
      unselected.resize(n);iota(unselected.begin(),unselected.end(),0);
      shuffle(unselected.begin(),unselected.end(),rng);
      anchor=-1;
    }
    vector<int> pos;
    int to_take=(anchor<0?4:3);
    if(anchor>=0)pos.push_back(anchor);
    for(int i=0;i<to_take && !unselected.empty();i++){
      int j=int(rng()%unselected.size());pos.push_back(unselected[j]);
      unselected[j]=unselected.back();unselected.pop_back();
    }
    if(anchor<0)anchor=pos[0];
    sort(pos.begin(),pos.end());
    for(int i=1;i<(int)pos.size();i++)
      if(pos[i]==pos[i-1])throw runtime_error("tracked subset repeated spin");
    if(pos.size()<2 || pos.size()>4)throw runtime_error("tracked subset malformed");
    return pos;
  }
};
static void selftest4(){
  selftest();mt19937_64 rng(20261109);
  long long checked=0;
  for(int n=4;n<=16;n++)for(int a=0;a<n;a++)for(int b=a+1;b<n;b++)
    for(int c=b+1;c<n;c++)for(int d=c+1;d<n;d++){
      vector<int> p={a,b,c,d};
      for(int code=0;code<16;code++){
        vector<int> v(4);for(int i=0;i<4;i++)v[i]=code&(1<<i)?1:-1;
        int e=isolated(p,v),ref=isolated_reference(p,v,n);
        if(e!=ref){
          cerr<<"ISO_FAIL n="<<n<<" p="<<a<<","<<b<<","<<c<<","<<d
              <<" code="<<code<<" fast="<<e<<" ref="<<ref<<"\n";
          throw runtime_error("isolated four-spin Hamiltonian mismatch");
        }
        checked++;
      }
    }
  // Explicit historical counterexample: old even-difference predicate gave 6.
  if(isolated({0,1,2,4},{1,1,1,1})!=4)throw runtime_error("midpoint regression failed");
  for(int trial=0;trial<300;trial++){
    int n=46;vector<int> x(n);for(int &v:x)v=rng()%2?1:-1;
    L orig(x);Pick p=optimized4(random_positions(n,rng),rng);
    for(int f=0;f<2;f++){
      L y=applied(orig,p,f);
      if(y.e!=energy_direct(y.s))throw runtime_error("L delta versus direct energy");
    }
    Tracked t;for(int j=0;j<75;j++)optimized4(t.next(n,rng),rng);
  }
  cout<<"PASS iso4 direct Hamiltonian "<<checked
      <<" exhaustive subset/assignment checks, exact global energy, tracking and complement\n";
}
struct Counters{long long proposals=0,globalE=0,accepted=0,kicks=0,restarts=0,improvements=0,events=0;};
static int best_threshold(int n){return n==46?131:n==47?135:n==50?153:throw runtime_error("unsupported n");}
static void benchmark(const vector<Scenario>&states,const string&events,const string&summary,int budget){
  ofstream ev(events),out(summary);
  if(!ev||!out)throw runtime_error("cannot write fourspin result");
  ev<<"id\tn\tmode\tdamage\trep\tarm\titeration\tt_ms\tkind\tE\tbits\tcanonical\tnear10_novel\n";
  out<<"id\tn\tmode\tdamage\trep\tarm\tbudget_ms\twall_ms\tsteps\t"
       "first_repair_E\tbestE\tbestBits\tbestCanon\tbestNonAB_E\tbestNonAB_Bits\t"
       "bestNonAB_Canon\tglobal_energy_evaluations\tsubsystem_proposals\t"
       "accepted_steps\tkicks\trestarts\tdynamic_new_near10\tinitial_near10\n";
  ev<<fixed<<setprecision(7);out<<fixed<<setprecision(7);
  for(const Scenario&s:states){
    if(best_threshold(s.n)!=s.A.e || s.B.e!=s.A.e)
      throw runtime_error("source E not optimum");
    for(int arm=0;arm<6;arm++){
      const bool ms=arm>=3,fromX=arm==1||arm==2||arm==4||arm==5;
      const bool restart=arm==2||arm==5;
      const int fail_threshold=ms?90:80,proposals=ms?50:1;
      mt19937_64 rng(hashseed(s.seed^0x4199ef21ULL+uint64_t(arm%3)*671ULL+uint64_t(ms)*1000007ULL));
      Tracked tracked;
      Counters count;
      int it=0,failures=0;
      string bestword,bestcan,otherword,othercan;
      int best=INT_MAX,bestOther=INT_MAX;
      int dynNear=0,initialNear=0;
      unordered_set<string>visited={s.ac,s.bc};
      auto started=clk::now();
      uint64_t repseed=hashseed(s.seed^0x44556677ULL);
      int steps=0;L initial=full_repair(s.X,repseed,steps);
      L cur=s.X;
      // Mirrors the previously frozen single-incumbent history semantics.
      if(!fromX && initial.e<s.X.e && canon(bits(initial))!=s.ac)cur=initial;
      auto emit=[&](const L&z,const string&kind,bool is_initial){
        string w=bits(z),c=canon(w);
        int opt=best_threshold(s.n);
        bool newElite=z.e<=int(floor(opt*1.1+1e-8)) &&
                        visited.insert(c).second;
        if(newElite && c!=s.ac && c!=s.bc){
          dynNear++;if(is_initial)initialNear++;
        }
        bool newBest=z.e<best;
        if(newBest){best=z.e;bestword=w;bestcan=c;count.improvements++;}
        bool newOther=false;
        if(c!=s.ac && c!=s.bc && z.e<bestOther){
          bestOther=z.e;otherword=w;othercan=c;newOther=true;
        }
        if(newBest||newOther||newElite||is_initial){
          ev<<s.id<<"\t"<<s.n<<"\t"<<s.mode<<"\t"<<s.damage<<"\t"<<s.rep
            <<"\t"<<arm<<"\t"<<it<<"\t"<<1000*dur(started)<<"\t"<<kind
            <<"\t"<<z.e<<"\t"<<w<<"\t"<<c<<"\t"<<(newElite?1:0)<<"\n";
          count.events++;
        }
      };
      emit(initial,"initial_repair",true);
      // Paper algorithm operates directly on an isolated subsystem; unlike
      // earlier donor-mask policies it does not call native full repair again.
      while(1000*dur(started)<budget){
        it++;
        if(failures>=fail_threshold){
          if(restart){
            cur=s.X;count.restarts++;
            // Restarting from X is a structural intervention (not an extra oracle).
          }else{
            Pick q=optimized4(random_positions(s.n,rng),rng);
            cur=applied(cur,q,false);
            count.proposals++;count.accepted++;count.kicks++;
            emit(cur,"kick",false);
          }
          failures=0;
          continue;
        }
        bool improved=false;
        int value=cur.e;
        L winner=cur;
        for(int k=0;k<proposals;k++){
          vector<int> p=ms?tracked.next(s.n,rng):random_positions(s.n,rng);
          Pick q=optimized4(move(p),rng);
          L a=applied(cur,q,false),b=applied(cur,q,true);
          count.globalE+=2;count.proposals++;
          if(a.e<value || b.e<value){
            if(a.e<=b.e){value=a.e;winner=move(a);}
            else{value=b.e;winner=move(b);}
            improved=true;
          }
        }
        if(improved && value<cur.e){
          cur=move(winner);count.accepted++;failures=0;
          emit(cur,"descent",false);
        }else{failures++;}
        if(it>2000000)throw runtime_error("fourspin runaway");
        if(it%1000==0 && cur.e!=energy_direct(cur.s))
          throw runtime_error("fourspin incremental exact global error");
      }
      if(best!=energy_direct(parse(bestword).s))
        throw runtime_error("fourspin best certificate mismatch");
      out<<s.id<<"\t"<<s.n<<"\t"<<s.mode<<"\t"<<s.damage<<"\t"<<s.rep<<"\t"
        <<arm<<"\t"<<budget<<"\t"<<1000*dur(started)<<"\t"<<it<<"\t"
        <<initial.e<<"\t"<<best<<"\t"<<bestword<<"\t"<<bestcan<<"\t"
        <<(bestOther==INT_MAX?-1:bestOther)<<"\t"<<otherword<<"\t"<<othercan
        <<"\t"<<count.globalE<<"\t"<<count.proposals<<"\t"
        <<count.accepted<<"\t"<<count.kicks<<"\t"<<count.restarts
        <<"\t"<<dynNear<<"\t"<<initialNear<<"\n";
    }
  }
  cout<<"PASS C-blind exact isolated four spin "<<states.size()<<" contexts, six classical policies\n";
}
int main(int argc,char**argv){
  try{
    if(argc==2 && string(argv[1])=="selftest"){selftest4();return 0;}
    if(argc==6 && string(argv[1])=="bench"){
      benchmark(load_inputs(argv[2]),argv[3],argv[4],stoi(argv[5]));
      return 0;
    }
    cerr<<"usage: selftest | bench SCENARIO_INPUT EVENT_TSV SESSION_TSV WALL_MS\n";
    return 2;
  }catch(const exception&ex){cerr<<"ERROR: "<<ex.what()<<"\n";return 1;}
}
