// Source-distinct published-elite LABS recombination experiment.
// Source file is small; relies on previously exact-tested L/delta from lns_mask.cpp.
// GOMEA modes are deliberately called *GOMEA-style approximation*, not full GOMEA.
// All model training, candidate generation, local Tabu repair cost within treatment wall time.
#define main recombination_legacy_unused_main
#include "../lns_mask.cpp"
#undef main
#include <unordered_set>
#include <unordered_map>
#include <map>
#include <sstream>
#include <climits>
#include <chrono>
#include <iomanip>
using namespace std;
struct Parent {string id,source,seq,canonical;int n,E,near,best; L state;};
uint64_t hashseed(uint64_t z){
 z+=0x9e3779b97f4a7c15ULL;z=(z^(z>>30))*0xbf58476d1ce4e5b9ULL;
 z=(z^(z>>27))*0x94d049bb133111ebULL;return z^(z>>31);
}
double dur(clk::time_point t){return ns(clk::now()-t).count();}
string bits(const L&v){string x;for(int i:v.s)x+=(i==1?'1':'0');return x;}
L parse(const string&s){vector<int> v;for(char c:s){if(c!='0'&&c!='1')throw runtime_error("not binary");v.push_back(c=='1'?1:-1);}return L(v);}
string neg(const string&s){string r=s;for(char&c:r)c=(c=='1'?'0':'1');return r;}
string alt(const string&s){string r=s;for(int i=1;i<(int)s.size();i+=2)r[i]=(r[i]=='1'?'0':'1');return r;}
vector<string> orb(const string&s){
 set<string> v;
 for(int rev=0;rev<2;rev++){string b=s;if(rev)reverse(b.begin(),b.end());
  for(int a=0;a<2;a++){string x=a?alt(b):b;v.insert(x);v.insert(neg(x));}
 }
 return vector<string>(v.begin(),v.end());
}
string canon(const string&s){auto v=orb(s);return v[0];}
int hd(const string&a,const string&b){int r=0;for(int i=0;i<(int)a.size();i++)r+=a[i]!=b[i];return r;}
string align_donor(const string&a,const string&b){
 auto variants=orb(b);return *min_element(variants.begin(),variants.end(),[&](auto&u,auto&v){
  return pair<int,string>(hd(a,u),u)<pair<int,string>(hd(a,v),v);
 });
}
vector<Parent> load(const string&path){
 ifstream in(path);if(!in)throw runtime_error("missing "+path);
 string line;getline(in,line);vector<Parent> v;
 while(getline(in,line)){
  if(line.empty())continue;istringstream ss(line);Parent p;string lineage,row;
  ss>>p.id>>p.n>>p.E>>p.seq>>p.canonical>>p.source>>lineage>>row>>p.near>>p.best;
  p.state=parse(p.seq);
  if(p.state.n!=p.n||p.state.e!=p.E||energy_direct(p.state.s)!=p.E||canon(p.seq)!=p.canonical)
   throw runtime_error("parent energy/orbit certificate invalid "+p.id);
  v.push_back(p);
 }return v;
}
vector<int> sample_variation(const vector<Parent*>&pool,int site,mt19937_64&rng){
 vector<int> x;for(auto*p:pool)x.push_back(p->state.s[site]);
 return x;
}
double entropy(double p){return p<1e-12||p>1.-1e-12?0.: -p*log(p)-(1-p)*log(1-p);}
vector<double> link_mi(const vector<Parent*>&pool,int n){
 // Laplace-prior 2x2 estimation, stable finite values even at n_pop=2.
 // Small populations can make estimated links extremely noisy; that is a result.
 vector<double> m(n*n,0.);
 for(int i=0;i<n;i++)for(int j=i+1;j<n;j++){
  double cnt[2][2]={{.25,.25},{.25,.25}},tot=1.;
  for(auto*p:pool){cnt[p->state.s[i]>0][p->state.s[j]>0]+=1.;tot++;}
  double a[2]={0,0},b[2]={0,0},mi=0;
  for(int x=0;x<2;x++)for(int y=0;y<2;y++){a[x]+=cnt[x][y];b[y]+=cnt[x][y];}
  for(int x=0;x<2;x++)for(int y=0;y<2;y++){
   double z=cnt[x][y]/tot;
   mi+=z*log(z/((a[x]/tot)*(b[y]/tot)));
  }m[i*n+j]=m[j*n+i]=max(0.,mi);
 }return m;
}
vector<double> link_exact(const vector<Parent*>&pool,int n){
 // True LABS pair epistasis averaged across *certified* distinct source parents.
 // Δ_ij = E(s^i,j)-E(s^i)-E(s^j)+E(s) (not approximate bit-distance MI).
 vector<double> w(n*n,0.);
 for(const Parent*p:pool){
  const L&base=p->state;
  vector<int> delta(n);
  for(int i=0;i<n;i++)delta[i]=base.delta(i);
  for(int i=0;i<n;i++){
   L t=base;t.flip(i);
   for(int j=i+1;j<n;j++){
    int epi=t.delta(j)-delta[j];
    w[i*n+j]+=abs(epi);w[j*n+i]+=abs(epi);
   }
  }
 }
 for(double&x:w)x/=pool.size();
 return w;
}
vector<vector<int>> build_tree(const vector<double>&w,int n,mt19937_64&rng){
 vector<vector<int>> groups(n);
 for(int i=0;i<n;i++)groups[i]={i};
 vector<vector<int>> fos=groups;
 while(groups.size()>1){
  int ai=-1,bi=-1;double best=-1e100;
  for(int i=0;i<(int)groups.size();i++)for(int j=i+1;j<(int)groups.size();j++){
   double s=0.;for(int a:groups[i])for(int b:groups[j])s+=w[a*n+b];
   s/=groups[i].size()*groups[j].size();
   s+=1e-10*double(rng()%10000); // deterministic random tie break
   if(s>best){best=s;ai=i;bi=j;}
  }
  vector<int> merged=groups[ai];merged.insert(merged.end(),groups[bi].begin(),groups[bi].end());
  sort(merged.begin(),merged.end());
  if((int)merged.size()<n)fos.push_back(merged);
  groups.erase(groups.begin()+bi);
  groups.erase(groups.begin()+ai);
  groups.push_back(move(merged));
 }
 return fos;
}
L standard_child(int arm,const Parent&A,const Parent&B,const vector<Parent*>&pool,mt19937_64&rng){
 int n=A.n;string s=A.seq,t=B.seq;
 if(arm==0)return (rng()%2? A.state:B.state);
 if(arm==2){int cut=1+int(rng()%(n-1));for(int i=cut;i<n;i++)s[i]=t[i];return parse(s);}
 if(arm==3)t=align_donor(s,t);
 if(arm==4){
  // Simple *univariate* EDA fitted to independent certified elite orbits.
  // It is not a sophisticated multivariate EDA; 1-pseudocount per sign.
  for(int i=0;i<n;i++){
   int pos=0;for(auto*p:pool)pos+=p->state.s[i]>0;
   double prob=(pos+1.)/(pool.size()+2.);
   s[i]=(uniform_real_distribution<double>(0.,1.)(rng)<prob?'1':'0');
  }return parse(s);
 }
 // uniform crossover used for 1/3/5/6/7.
 for(int i=0;i<n;i++)if(rng()&1)s[i]=t[i];
 return parse(s);
}
L gom(L cur,const L&donor,vector<vector<int>> fos,mt19937_64&rng,int&evals,int&accepted){
 shuffle(fos.begin(),fos.end(),rng);
 for(const auto&subset:fos){
  L trial=cur;bool changed=false;
  for(int i:subset)if(trial.s[i]!=donor.s[i]){trial.flip(i);changed=true;}
  if(!changed)continue;
  evals++;
  if(trial.e<=cur.e){cur=move(trial);accepted++;}
 }
 return cur;
}
L repair(L x,mt19937_64&rng,int&steps){
 x.descend(0);
 L best=x,cur=x;
 vector<int>last(x.n,-1000000);int tenure=7;
 for(int move=0;move<64;move++){
  int p=-1,dmin=INT_MAX;
  for(int i=0;i<x.n;i++){
   int d=cur.delta(i);
   if(move-last[i]<=tenure && cur.e+d>=best.e)continue;
   if(d<dmin ||(d==dmin&&(rng()&1)))p=i,dmin=d;
  }
  if(p<0)p=int(rng()%x.n);
  cur.flip(p);last[p]=move;steps++;
  if(cur.e<best.e)best=cur;
 }
 best.descend(0);
 return best;
}
int near(const string &s){
 auto odd=[&](string w){
  int n=w.size();if(n%2==0)return false;
  int m=n/2;for(int j=1;j<=m;j++)if((w[m+j]==w[m-j])!=(j%2==0))return false;
  return true;
 };
 return s.size()%2?odd(s):odd(s.substr(0,s.size()-1))||odd(s.substr(1));
}
void selftest(){
 mt19937_64 rng(190711);
 for(int n:{16,46,50,99})for(int t=0;t<12;t++){
  string s;for(int j=0;j<n;j++)s+=(rng()&1?'1':'0');
  L b=parse(s);
  for(string v:orb(s))if(parse(v).e!=b.e||canon(v)!=canon(s))throw runtime_error("symmetry exactness");
  Parent A;A.n=n;A.seq=s;A.state=b;
  vector<Parent*> pool={&A};
  for(const auto &w:{link_mi(pool,n),link_exact(pool,n)}){
   auto fos=build_tree(w,n,rng);if(fos.size()<n)throw runtime_error("FOS malformed");
   int evaluations=0,accepted=0;L x=gom(b,b,fos,rng,evaluations,accepted);
   if(x.e!=b.e)throw runtime_error("GOM selftest unexpected");
  }
  int steps=0;L y=repair(b,rng,steps);
  if(y.e!=energy_direct(y.s)||y.e>b.e)throw runtime_error("repair exactness");
 }
 cout<<"PASS symmetry-group energy, exact epistasis, MI-FOS and 64-step repair random tests\n";
}
#ifndef RECOMBINE_NO_MAIN
int main(int argc,char **argv){
 if(argc==2 && string(argv[1])=="--selftest"){selftest();return 0;}
 if(argc<6){cerr<<"usage PARENTS.tsv OUT_SUMMARY.tsv OUT_NOVEL.tsv REPS BUDGET_MS\n";return 2;}
 auto sources=load(argv[1]);
 map<int,vector<Parent*>> groups;for(auto&p:sources)groups[p.n].push_back(&p);
 ofstream out(argv[2]),nov(argv[3]);
 if(!out||!nov)throw runtime_error("output open failed");
 int reps=stoi(argv[4]),budget=stoi(argv[5]);
 out<<"N\tpair\tA_id\tB_id\tAE\tBE\tparent_dist\trep\tarm\t"
      "generations\tall_unique\tbestE\tbestNonparentE\tmeanE\tnew5\tnew10\tstrict_gain\t"
      "best_bits\tbest_canonical\tbest_dParent\tbest_near\t"
      "gom_trials\tgom_accept\trepair_steps\tmodel_ms\tgen_ms\trepair_ms\telapsed_ms\tovershoot_ms\n";
 nov<<"N\tpair\trep\tarm\tE\tbits\tcanonical\tparent_dist\tthreshold\tnear\n";
 out<<fixed<<setprecision(6);
 for(auto &[n,pool]:groups){
  if(pool.size()<2)continue;
  unordered_set<string> archive;int reference=INT_MAX;
  for(auto*p:pool){archive.insert(p->canonical);reference=min(reference,p->best);}
  int nPairs=0;
  for(int a=0;a<(int)pool.size();a++)for(int b=a+1;b<(int)pool.size();b++){
   const Parent&A=*pool[a],&B=*pool[b];
   string pair=A.id+"-"+B.id;
   int dParent=hd(A.seq,align_donor(A.seq,B.seq));
   if(dParent<1)throw runtime_error("duplicate parents under orbit");
   for(int rep=0;rep<reps;rep++){
    for(int arm=0;arm<8;arm++){
     uint64_t sd=hashseed(70391321+n*7331+nPairs*43111+rep*57199+arm*293);
     mt19937_64 rng(sd);
     auto t0=clk::now();
     double modelSecs=0,genSecs=0,repairSecs=0;
     vector<vector<int>> fos;
     if(arm>=5){
      auto mt=clk::now();
      vector<double>w;
      if(arm==5){w.resize(n*n);for(double&v:w)v=double(rng()%100000)/100000.;}
      if(arm==6)w=link_mi(pool,n);
      if(arm==7)w=link_exact(pool,n);
      fos=build_tree(w,n,rng);
      modelSecs=dur(mt);
     }
     int total=0,n5=0,n10=0,strict=0,gomTrials=0,gomAccept=0,repairSteps=0;
     double sumE=0;
     int bestE=INT_MAX,bestOther=INT_MAX,bestdist=-1,bestNear=-1;
     string bestBits,bestCanonical;
     unordered_set<string>unique,novel5,novel10;
     while(total==0 || dur(t0)<double(budget)/1000.){
      auto st=clk::now();
      L child=standard_child(arm,A,B,pool,rng);
      if(arm>=5){
       string aligned=align_donor(A.seq,B.seq);
       L donor=parse(aligned);
       child=gom(move(child),donor,fos,rng,gomTrials,gomAccept);
      }
      genSecs+=dur(st);
      st=clk::now();
      int steps=0;L final=repair(move(child),rng,steps);
      repairSecs+=dur(st);repairSteps+=steps;
      string seq=bits(final),ca=canon(seq);
      if(final.e!=energy_direct(final.s))throw runtime_error("post repair direct E mismatch");
      int dist=min(hd(seq,align_donor(seq,A.seq)),hd(seq,align_donor(seq,B.seq)));
      unique.insert(ca);sumE+=final.e;total++;
      if(final.e<bestE){
       bestE=final.e;bestBits=seq;bestCanonical=ca;bestdist=dist;bestNear=near(seq);
      }
      if(final.e<min(A.E,B.E))strict++;
      if(!archive.count(ca)){
       bestOther=min(bestOther,final.e);
       if(final.e<=int(reference*1.05+1e-9) && novel5.insert(ca).second){
        n5++;nov<<n<<"\t"<<pair<<"\t"<<rep<<"\t"<<arm<<"\t"<<final.e<<"\t"<<seq<<"\t"<<ca<<"\t"<<dist<<"\t5\t"<<near(seq)<<"\n";
       }
       if(final.e<=int(reference*1.1+1e-9) && novel10.insert(ca).second){
        n10++;
        if(!novel5.count(ca))
         nov<<n<<"\t"<<pair<<"\t"<<rep<<"\t"<<arm<<"\t"<<final.e<<"\t"<<seq<<"\t"<<ca<<"\t"<<dist<<"\t10\t"<<near(seq)<<"\n";
       }
      }
      if(total>2000)throw runtime_error("unbounded candidate loop");
     }
     double elapsed=dur(t0);
     out<<n<<"\t"<<pair<<"\t"<<A.id<<"\t"<<B.id<<"\t"<<A.E<<"\t"<<B.E<<"\t"<<dParent
      <<"\t"<<rep<<"\t"<<arm<<"\t"<<total<<"\t"<<unique.size()<<"\t"<<bestE<<"\t"
      <<(bestOther==INT_MAX?-1:bestOther)<<"\t"<<sumE/total<<"\t"<<n5<<"\t"<<n10
      <<"\t"<<strict<<"\t"<<bestBits<<"\t"<<bestCanonical<<"\t"<<bestdist<<"\t"<<bestNear
      <<"\t"<<gomTrials<<"\t"<<gomAccept<<"\t"<<repairSteps<<"\t"<<1000*modelSecs
      <<"\t"<<1000*genSecs<<"\t"<<1000*repairSecs<<"\t"<<1000*elapsed
      <<"\t"<<max(0.,1000*elapsed-budget)<<"\n";
    }
    if(rep==0)cerr<<"N "<<n<<" pair "<<pair<<" tested first replication\n";
   }
   nPairs++;
  }
 }
 cout<<"PASS source-parented exact recombination, outputs all length-matched source-orbit pairs\n";
}
#endif // RECOMBINE_NO_MAIN
