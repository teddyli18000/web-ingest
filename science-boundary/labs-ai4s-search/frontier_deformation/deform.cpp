#include <bits/stdc++.h>
using namespace std;
struct Sol {
 int n=0,E=0;vector<int> s,c;
 Sol()=default;
 explicit Sol(string bits):n(bits.size()),s(n),c(n,0){for(int i=0;i<n;i++)s[i]=(bits[i]=='1'||bits[i]=='+')?1:-1;rebuild();}
 void rebuild(){fill(c.begin(),c.end(),0);E=0;for(int k=1;k<n;k++){for(int i=0;i<n-k;i++)c[k]+=s[i]*s[i+k]; E+=c[k]*c[k];}}
 int delta(int p)const{int z=0;for(int k=1;k<n;k++){int t=0;if(p>=k)t+=s[p-k];if(p+k<n)t+=s[p+k];int dc=-2*s[p]*t;z+=2*c[k]*dc+dc*dc;}return z;}
 double weighted(int p,const vector<double>&w)const{double z=0;for(int k=1;k<n;k++){int t=0;if(p>=k)t+=s[p-k];if(p+k<n)t+=s[p+k];int dc=-2*s[p]*t;z+=w[k]*(2*c[k]*dc+dc*dc);}return z;}
 void flip(int p){int d=delta(p);for(int k=1;k<n;k++){int t=0;if(p>=k)t+=s[p-k];if(p+k<n)t+=s[p+k];c[k]+=-2*s[p]*t;}s[p]=-s[p];E+=d;}
 string bits()const{string str;for(int x:s)str+=(x==1?'1':'0');return str;}
};
int directE(const vector<int>&s){int n=s.size(),e=0;for(int k=1;k<n;k++){int c=0;for(int i=0;i<n-k;i++)c+=s[i]*s[i+k];e+=c*c;}return e;}
string canonical(const Sol &s){string best,bs=s.bits();bool initial=true;for(int rev=0;rev<2;rev++)for(int neg=0;neg<2;neg++)for(int alt=0;alt<2;alt++){string q;for(int i=0;i<s.n;i++){int v=s.s[rev?s.n-1-i:i];if(neg)v=-v;if(alt&&i%2)v=-v;q+=(v==1?'1':'0');}if(initial||q<best)best=q,initial=false;}return best;}
bool skew(const vector<int>&s,int begin,int len){if(len%2!=1)return false;int m=len/2;for(int j=1;j<=m;j++)if(s[begin+m+j]!=((j%2)?-1:1)*s[begin+m-j])return false;return true;}
bool nearSkew(const Sol&x){if(x.n%2)return skew(x.s,0,x.n);return skew(x.s,0,x.n-1)||skew(x.s,1,x.n-1);}
struct Ref {int n,e;string bits,id;};
vector<Ref> anchors(const string&file){ifstream f(file);vector<Ref>x;Ref t;while(f>>t.n>>t.e>>t.bits>>t.id){Sol s(t.bits);if(s.E!=t.e||s.n!=t.n)throw runtime_error("anchor mismatch");x.push_back(t);}return x;}
uint64_t mix(uint64_t x){x+=0x9e3779b97f4a7c15ull;x=(x^(x>>30))*0xbf58476d1ce4e5b9ull;x=(x^(x>>27))*0x94d049bb133111ebull;return x^(x>>31);}
struct Result{Sol best,cur;int improvements=0,steps=0,final_E=0, best_step=0,best_non_skew=INT_MAX,best_odd_defect=INT_MAX, best_quenched_non_skew=INT_MAX,quench_steps=0,quench_unique=0;string quench_bits="-";};
vector<double> buildWeights(const Sol&x,const vector<double>&lagHistory,int arm,mt19937_64 &rng,double a){
 int n=x.n;vector<double>w(n,1),priority(n);
 if(arm>=4){vector<int> idx;for(int k=1;k<n;k++)idx.push_back(k);
 if(arm==6){shuffle(idx.begin(),idx.end(),rng);for(int i=0;i<n-1;i++)w[idx[i]]=(i<(n-1)/2)?1.-a:1.+a;}
 else for(int k=1;k<n;k++)w[k]=(k%2==1) ? (arm==4?1.-a:1.+a) : (arm==4?1.+a:1.-a);
 return w;}
 for(int k=1;k<n;k++){
  double c=double(x.c[k]);priority[k]=.7*c*c/(n-k)+.3*lagHistory[k];
 }
 vector<int>idx;for(int k=1;k<n;k++)idx.push_back(k);
 sort(idx.begin(),idx.end(),[&](int i,int j){return priority[i]>priority[j];});
 int take=max(2,(n-1)/5);vector<int> hi(idx.begin(),idx.begin()+take),lo(idx.end()-take,idx.end());
 if(arm==2){
  vector<int> shuffled(n-1);iota(shuffled.begin(),shuffled.end(),1);shuffle(shuffled.begin(),shuffled.end(),rng);
  hi.assign(shuffled.begin(),shuffled.begin()+take);lo.assign(shuffled.begin()+take,shuffled.begin()+take*2);
 }
 if(arm==3){for(int k:hi)w[k]=1-a;for(int k:lo)w[k]=1+a;}
 else {for(int k:hi)w[k]=1+a;for(int k:lo)w[k]=1-a;}
 return w;
}
Result tabu(Sol start,int arm,uint64_t seed,int steps,int period,int tenure,double tilt){
 mt19937_64 rng(seed);Result r;r.best=start;r.cur=start;
 auto record_structure=[&](){if(!nearSkew(r.cur))r.best_non_skew=min(r.best_non_skew,r.cur.E);bool oddperfect=true;for(int k=1;k<r.cur.n;k+=2)if(abs(r.cur.c[k])!=1)oddperfect=false;if(!oddperfect)r.best_odd_defect=min(r.best_odd_defect,r.cur.E);};
 record_structure();
 vector<int>last(start.n,-100000);vector<double>hist(start.n,0),w(start.n,1);
 set<string>seen_quenches;
 for(int it=0;it<steps;it++){
  int phase=it%period;
  if(phase==0){
   for(int k=1;k<r.cur.n;k++)hist[k]=.83*hist[k]+.17*double(r.cur.c[k])*r.cur.c[k]/(r.cur.n-k);
   if(arm>0)w=buildWeights(r.cur,hist,arm,rng,tilt);
  }
  bool deform=arm>0&&phase<period/2;
  int chosen=-1;double score=1e100;
  for(int p=0;p<r.cur.n;p++){
   int d=r.cur.delta(p);bool taboo=it-last[p]<=tenure;
   if(taboo && r.cur.E+d>=r.best.E)continue;
   double val=deform?r.cur.weighted(p,w):double(d);
   if(val<score-1e-9 || (abs(val-score)<1e-9 && (rng()&1))){score=val;chosen=p;}
  }
  if(chosen<0){chosen=rng()%r.cur.n;}
  r.cur.flip(chosen);last[chosen]=it;record_structure();
  if(r.cur.E<r.best.E){r.best=r.cur;r.improvements++;r.best_step=it+1;}
  if(phase==period/2-1 || phase==period-1){
   Sol q=r.cur;int walk=0;
   while(true){int pos=-1,bd=0;for(int j=0;j<q.n;j++){int dd=q.delta(j);if(dd<bd)bd=dd,pos=j;}
    if(pos<0)break;q.flip(pos);walk++;if(walk>q.n*5)throw runtime_error("quench loop");}
   r.quench_steps+=walk;seen_quenches.insert(canonical(q));
   if(!nearSkew(q) && q.E<r.best_quenched_non_skew){r.best_quenched_non_skew=q.E;r.quench_bits=q.bits();}
   if(q.E<r.best.E){r.best=q;r.improvements++;r.best_step=it+1;}
  }
 }
 r.steps=steps;r.final_E=r.cur.E;r.quench_unique=seen_quenches.size();return r;
}
void selftest(){mt19937_64 rng(112233);int count=0;for(int n:{13,64,80,92,96,99,100})for(int i=0;i<50;i++){
 string v;for(int j=0;j<n;j++)v+=(rng()&1?'1':'0');Sol s(v);
 if(s.E!=directE(s.s))throw runtime_error("E bad");
 for(int j=0;j<n;j++){Sol t=s;t.flip(j);if(t.E!=directE(t.s)||s.delta(j)!=t.E-s.E)throw runtime_error("delta bad");count++;}
 }
 cerr<<"PASS independent delta "<<count<<" checks\n";
}
int main(int argc,char**argv){
 if(argc<2){cerr<<"usage: --selftest; --harvest anchors.tsv OUT.tsv SEEDS STEPS; --compare CORPUS.tsv OUT.tsv REPS STEPS PERIOD TILT TENURE [MAXARM]\n";return 2;}
 string mode=argv[1];if(mode=="--selftest"){selftest();return 0;}
 if(mode=="--harvest"){
  if(argc<6)return 2;auto refs=anchors(argv[2]);ofstream out(argv[3]);int seeds=stoi(argv[4]),moves=stoi(argv[5]);
  out<<"n\tenergy\tbits\tprovenance\tparent\tseed\tnear_skew\tcanonical\n";
  set<pair<int,string>>seen;
  auto emit=[&](Sol s,string origin,string parent,int seed){string can=canonical(s);if(seen.insert({s.n,can}).second){out<<s.n<<"\t"<<s.E<<"\t"<<s.bits()<<"\t"<<origin<<"\t"<<parent<<"\t"<<seed<<"\t"<<(nearSkew(s)?1:0)<<"\t"<<can<<"\n";}};
  for(auto ref:refs){Sol anchor(ref.bits);emit(anchor,"public_anchor",ref.id,0);
   for(int j=0;j<seeds;j++){
    mt19937_64 rng(mix(9000071ull+ref.n*8831+j));
    Sol start=anchor;
    int radius=3+((j*7)%(ref.n/3));vector<int>idx(ref.n);iota(idx.begin(),idx.end(),0);shuffle(idx.begin(),idx.end(),rng);
    for(int u=0;u<radius;u++)start.flip(idx[u]);
    auto rr=tabu(start,0,mix(j*3103+ref.n),moves,400,7+((j%4)*3),0);
    if(rr.best.E<=int(ref.e*1.55))emit(rr.best,"anchor_child_tabu",ref.id,j);
    string randomBits;for(int i=0;i<ref.n;i++)randomBits+=(rng()&1?'1':'0');
    Sol randomStart(randomBits);auto rt=tabu(randomStart,0,mix(j*6163+ref.n+191),moves,400,7+((j%4)*3),0);
    if(rt.best.E<=int(ref.e*1.55))emit(rt.best,"random_start_tabu","none",j);
   }
   cerr<<"harvest n="<<ref.n<<" entries="<<seen.size()<<"\n";
  }
  return 0;
 }
 if(mode=="--compare"){
  if(argc<9)return 2;int maxarm=argc>9?stoi(argv[9]):3;
  ifstream in(argv[2]);ofstream out(argv[3]);int reps=stoi(argv[4]),moves=stoi(argv[5]),period=stoi(argv[6]),tenure=stoi(argv[8]);double tilt=stod(argv[7]);
  string line;getline(in,line);
  out<<"n\tstate_id\tprovenance\tparent\tstartE\tnear_skew\trep\tmethod\tbestE\tlastE\timprovements\tbest_step\tsteps\tbest_non_skew\tbest_odd_defect\tquench_non_skew\tquench_bits\tquench_unique\tquench_steps\n";
  int state_id=0;
  while(getline(in,line)){
   if(line.empty())continue;istringstream ss(line);int n,E,seed,near;string bits,origin,parent,can;ss>>n>>E>>bits>>origin>>parent>>seed>>near>>can;
   if(n<1||bits.size()!=size_t(n))throw runtime_error("input format");Sol x(bits);if(x.E!=E)throw runtime_error("input scorer");
   for(int rep=0;rep<reps;rep++)for(int arm=0;arm<=maxarm;arm++){
    auto v=tabu(x,arm,mix((unsigned long long)state_id*100003+rep*521+1937),moves,period,tenure,tilt);
    if(directE(v.best.s)!=v.best.E)throw runtime_error("output failed independent direct scorer");
    out<<n<<"\t"<<state_id<<"\t"<<origin<<"\t"<<parent<<"\t"<<E<<"\t"<<near<<"\t"<<rep<<"\t"<<arm<<"\t"<<v.best.E<<"\t"<<v.final_E<<"\t"<<v.improvements<<"\t"<<v.best_step<<"\t"<<moves<<"\t"<<(v.best_non_skew==INT_MAX?-1:v.best_non_skew)<<"\t"<<(v.best_odd_defect==INT_MAX?-1:v.best_odd_defect)<<"\t"<<(v.best_quenched_non_skew==INT_MAX?-1:v.best_quenched_non_skew)<<"\t"<<v.quench_bits<<"\t"<<v.quench_unique<<"\t"<<v.quench_steps<<"\n";
   }
   state_id++;
  }
  cerr<<"compared states="<<state_id<<"\n";return 0;
 }
 return 2;
}
