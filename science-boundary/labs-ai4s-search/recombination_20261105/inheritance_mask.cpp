// Forced two-parent LABS inheritance: every proposal initially takes ~half the
// differing sites from *each* of two genuinely distinct certified elite parents.
// This is a different action space from unconditional 12-bit mask perturbations.
#define main lns_inheritance_unused_main
#include "../lns_mask.cpp"
#undef main
#include <map>
#include <unordered_set>
#include <sstream>
#include <climits>
#include <iomanip>
using namespace std;

struct P {string id,bits,canonical;int n,E;L state;};
L parse_bits(const string&s){vector<int>x;for(char c:s)x.push_back(c=='1'?1:-1);return L(x);}
string tobits(const L&s){string t;for(int v:s.s)t+=(v>0?'1':'0');return t;}
string invert(const string&s){string x=s;for(char&c:x)c=(c=='1'?'0':'1');return x;}
string alternate(const string&s){string x=s;for(int i=1;i<(int)s.size();i+=2)x[i]=(x[i]=='1'?'0':'1');return x;}
vector<string> orbit(string s){
 set<string>v;for(int j=0;j<2;j++){
  string a=s;if(j)reverse(a.begin(),a.end());
  for(int k=0;k<2;k++){string b=k?alternate(a):a;v.insert(b);v.insert(invert(b));}
 }return vector<string>(v.begin(),v.end());
}
string canon(string s){return orbit(s)[0];}
int hamm(const string&a,const string&b){int x=0;for(int i=0;i<(int)a.size();i++)x+=(a[i]!=b[i]);return x;}
string align(const string&a,const string&b){
 auto z=orbit(b);return *min_element(z.begin(),z.end(),[&](const string&u,const string&v){
  return pair<int,string>(hamm(a,u),u)<pair<int,string>(hamm(a,v),v);
 });
}
int distance_orbit(const string&s,const string&a){int d=100000;for(auto&b:orbit(a))d=min(d,hamm(s,b));return d;}
vector<P> parents(const string&fname){
 ifstream f(fname);if(!f)throw runtime_error("missing input");
 string line;getline(f,line);vector<P>v;
 while(getline(f,line)){
  istringstream is(line);P z;string source,lineage,srcrow,near,best;
  is>>z.id>>z.n>>z.E>>z.bits>>z.canonical>>source>>lineage>>srcrow>>near>>best;
  z.state=parse_bits(z.bits);
  if(z.n!=(int)z.bits.size()||z.E!=z.state.e||energy_direct(z.state.s)!=z.E
    ||z.canonical!=canon(z.bits))throw runtime_error("bad source");
  v.push_back(z);
 }return v;
}
uint64_t scramble(uint64_t x){x+=0x9e3779b97f4a7c15ULL;x=(x^(x>>30))*0xbf58476d1ce4e5b9ULL;x=(x^(x>>27))*0x94d049bb133111ebULL;return x^(x>>31);}
double elapsed(clk::time_point t){return ns(clk::now()-t).count();}
vector<char> random_selection(int D,int h,mt19937_64&rng){
 vector<int>idx(D);iota(idx.begin(),idx.end(),0);
 for(int i=0;i<h;i++)swap(idx[i],idx[i+int(rng()%(D-i))]);
 vector<char>x(D);for(int i=0;i<h;i++)x[idx[i]]=1;return x;
}
L child_from(const L&A,const vector<int>&diff,const vector<char>&sel){
 L x=A;for(int i=0;i<(int)diff.size();i++)if(sel[i])x.flip(diff[i]);return x;
}
double corridor(const L&x,const vector<double>&target){
 double v=x.e;for(int k=1;k<x.n;k++)v+=.25*(x.c[k]-target[k])*(x.c[k]-target[k]);
 return v;
}
L quench_tabu(L input,mt19937_64&rng,int&tabuMoves){
 input.descend(0);
 L current=input,best=input;
 vector<int>last(input.n,-1000000);
 for(int it=0;it<64;it++){
  int pick=-1,low=INT_MAX;
  for(int j=0;j<input.n;j++){
   int d=current.delta(j);
   if(it-last[j]<=7 && current.e+d>=best.e)continue;
   if(d<low ||(d==low&&(rng()&1)))pick=j,low=d;
  }
  if(pick<0)pick=int(rng()%input.n);
  current.flip(pick);last[pick]=it;tabuMoves++;
  if(current.e<best.e)best=current;
 }
 best.descend(0);
 return best;
}
void test(){
 mt19937_64 rng(5099);
 for(int N:{24,46,59,99})for(int k=0;k<15;k++){
  string a,b;for(int j=0;j<N;j++){a+=(rng()&1?'1':'0');b+=(rng()&1?'1':'0');}
  string aligned=align(a,b);int D=hamm(a,aligned);
  vector<int> diff;for(int i=0;i<N;i++)if(a[i]!=aligned[i])diff.push_back(i);
  if(D<2)continue;
  auto sel=random_selection(D,D/2,rng);
  L A=parse_bits(a),child=child_from(A,diff,sel);
  if(hamm(a,tobits(child))!=D/2||hamm(aligned,tobits(child))!=D-D/2
     ||energy_direct(child.s)!=child.e)throw runtime_error("inheritance exactness");
  int steps=0;L post=quench_tabu(child,rng,steps);
  if(steps!=64||energy_direct(post.s)!=post.e)throw runtime_error("quench exactness");
 }
 cout<<"PASS forced-two-parent donor positions, all eight LABS symmetries and exact postrepair energies\n";
}
int main(int argc,char**argv){
 if(argc==2&&string(argv[1])=="--selftest"){test();return 0;}
 if(argc<6){cerr<<"usage PARENTS.tsv OUT.tsv REPS BUDGET_MS MODE_COUNT\n";return 2;}
 auto source=parents(argv[1]);map<int,vector<P*>>groups;
 for(auto &p:source)groups[p.n].push_back(&p);
 ofstream f(argv[2]);if(!f)throw runtime_error("output failed");
 int reps=stoi(argv[3]),budgetMs=stoi(argv[4]),methods=stoi(argv[5]);
 f<<"N\tpair\trep\tmode\tEA\tEB\tD\tH\tmask_search_E\tmask_bits\tmask_target_score\t"
   "mask_distance_to_A\tmask_distance_to_B\tquench_E\tquench_bits\tfinal_E\tfinal_min_orbit_distance\t"
   "novel_strict\tnew_within5\tnew_within10\tcandidates_evaluated\tquench_evaluations\t"
   "repair_tabu_moves\tfinal_bits\tfinal_canonical\tsearch_ms\trepair_ms\telapsed_ms\n";
 f<<fixed<<setprecision(6);
 for(auto &[n,pool]:groups){
  if(pool.size()<2)continue;
  int bestref=INT_MAX;
  unordered_set<string>family;for(auto *p:pool){family.insert(p->canonical);bestref=min(bestref,p->E);}
  for(int ia=0;ia<(int)pool.size();ia++)for(int ib=ia+1;ib<(int)pool.size();ib++){
   P &A=*pool[ia],&B=*pool[ib];string bAlign=align(A.bits,B.bits);
   vector<int>diff;
   for(int i=0;i<n;i++)if(A.bits[i]!=bAlign[i])diff.push_back(i);
   int D=diff.size(),H=D/2;
   if(D<8)throw runtime_error("unreliable source pair, insufficient orbit separation");
   L donor=parse_bits(bAlign);
   vector<double>target(n);
   for(int k=1;k<n;k++)target[k]=0.5*(A.state.c[k]+donor.c[k]);
   string pair=A.id+"-"+B.id;
   for(int rep=0;rep<reps;rep++)for(int mode=0;mode<methods;mode++){
    mt19937_64 rng(scramble(9071103ULL+n*1009ULL+ia*1633ULL+ib*10333ULL+rep*10301ULL+mode*9137ULL));
    auto t0=clk::now();int evaluated=0,quenchEval=0,stalled=0;
    auto sel=random_selection(D,H,rng);
    L cur=child_from(A.state,diff,sel);
    L selected=cur;
    double value=(mode==3?corridor(cur,target):double(cur.e));
    if(mode==4){
      L descent=cur;descent.descend(0);quenchEval++;
      int dist=min(distance_orbit(tobits(descent),A.bits),distance_orbit(tobits(descent),B.bits));
      value=double(descent.e)+(dist<max(2,D/4)?10000.:0.);
    }
    double bestVal=value;int bestSearchE=selected.e;
    int chosenRepairs=0;
    while(elapsed(t0)*1000 < 0.75*budgetMs){
     vector<char>candidateSel=sel;
     L trial=cur;
     if(mode==0){
       candidateSel=random_selection(D,H,rng);
       trial=child_from(A.state,diff,candidateSel);
     } else{
       int outj=int(rng()%D),inj=int(rng()%D);
       while(candidateSel[outj]!=1)outj=int(rng()%D);
       while(candidateSel[inj]!=0)inj=int(rng()%D);
       candidateSel[outj]=0;candidateSel[inj]=1;
       trial.flip(diff[outj]);trial.flip(diff[inj]);
     }
     evaluated++;
     double score=mode==3?corridor(trial,target):double(trial.e);
     if(mode==4){
       L post=trial;post.descend(0);quenchEval++;
       int dist=min(distance_orbit(tobits(post),A.bits),distance_orbit(tobits(post),B.bits));
       score=double(post.e)+(dist<max(2,D/4)?10000.:0.);
     }
     if(score<bestVal){bestVal=score;selected=trial;bestSearchE=trial.e;}
     if(mode==1 || mode==0 || score<value){
       cur=move(trial);sel=move(candidateSel);value=score;stalled=0;
     } else stalled++;
     if((mode==2||mode==3||mode==4)&&stalled>=400){
       sel=random_selection(D,H,rng);cur=child_from(A.state,diff,sel);
       value=mode==3?corridor(cur,target):double(cur.e);
       if(mode==4){
        L post=cur;post.descend(0);quenchEval++;
        int dist=min(distance_orbit(tobits(post),A.bits),distance_orbit(tobits(post),B.bits));
        value=double(post.e)+(dist<max(2,D/4)?10000.:0.);
       }
       stalled=0;
     }
    }
    double searchMs=1000*elapsed(t0);
    auto tRepair=clk::now();
    L quench=selected;quench.descend(0);
    int steps=0;L repaired=quench_tabu(selected,rng,steps);
    double repairMs=1000*elapsed(tRepair),totalMs=1000*elapsed(t0);
    if(energy_direct(repaired.s)!=repaired.e||energy_direct(selected.s)!=selected.e
       ||energy_direct(quench.s)!=quench.e||hamm(tobits(selected),A.bits)!=H
       ||hamm(tobits(selected),bAlign)!=D-H||steps!=64)
      throw runtime_error("independent exact score or inheritance mask invariant failed");
    string finalBits=tobits(repaired),ca=canon(finalBits);
    int finalD=min(distance_orbit(finalBits,A.bits),distance_orbit(finalBits,B.bits));
    int novel=!family.count(ca);
    f<<n<<"\t"<<pair<<"\t"<<rep<<"\t"<<mode<<"\t"<<A.E<<"\t"<<B.E<<"\t"<<D<<"\t"<<H
     <<"\t"<<bestSearchE<<"\t"<<tobits(selected)<<"\t"<<bestVal<<"\t"<<H<<"\t"<<D-H<<"\t"<<quench.e<<"\t"<<tobits(quench)
     <<"\t"<<repaired.e<<"\t"<<finalD<<"\t"<<(repaired.e<min(A.E,B.E))
     <<"\t"<<(novel && repaired.e<=int(bestref*1.05+1e-9))
     <<"\t"<<(novel && repaired.e<=int(bestref*1.10+1e-9))
     <<"\t"<<evaluated<<"\t"<<quenchEval<<"\t"<<steps<<"\t"<<finalBits<<"\t"<<ca
     <<"\t"<<searchMs<<"\t"<<repairMs<<"\t"<<totalMs<<"\n";
   }
   cerr<<"completed N="<<n<<" pair="<<pair<<" D="<<D<<"\n";
  }
 }
 cout<<"PASS exact fixed-biparent half-inheritance and post-Tabu true LABS scoring\n";
}
