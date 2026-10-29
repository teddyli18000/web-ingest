// Matched target deformation: encourage departure from the skew-pair manifold,
// with a random-pair placebo of the same cardinality and zero initial mismatch.
// Depends on exact integer LABS scorer in deform.cpp.
// g++ -O3 -std=c++17 structural_deform.cpp -o structural_deform
// ./structural_deform OUT.tsv IN.tsv REPS STEPS LAMBDA TARGET TENURE PERIOD
#define main deform_lib_main
#include "deform.cpp"
#undef main
struct PairRule{int n;vector<int> mate,expect;int edges=0;
 PairRule(const Sol&x,bool placebo,mt19937_64&rng):n(x.n),mate(n,-1),expect(n,0){
  int begin=0;
  if(n%2==0 && !skew(x.s,0,n-1))begin=1;
  int mid=begin+(n-1)/2;vector<pair<int,int>>ps;
  for(int j=1;j<=(n-1)/2;j++)ps.push_back({mid-j,mid+j});
  if(placebo){vector<int>v;for(auto q:ps){v.push_back(q.first);v.push_back(q.second);}shuffle(v.begin(),v.end(),rng);ps.clear();for(int i=0;i+1<(int)v.size();i+=2)ps.push_back({v[i],v[i+1]});}
  for(auto [a,b]:ps){mate[a]=b;mate[b]=a;int sign=placebo?x.s[a]*x.s[b]:((abs(a-mid)%2)?-1:1);expect[a]=expect[b]=sign;}edges=ps.size();
 }
 int defect(const Sol&x)const{int d=0;for(int i=0;i<n;i++)if(mate[i]>=0 && i<mate[i])d+=x.s[i]*x.s[mate[i]]!=expect[i];return d;}
 int flip_delta(const Sol&x,int i)const{if(mate[i]<0)return 0;bool bad=x.s[i]*x.s[mate[i]]!=expect[i];return bad?-1:+1;}
};
Sol relax(Sol x){for(int t=0;t<1000;t++){int bd=0,p=-1;for(int i=0;i<x.n;i++){int d=x.delta(i);if(d<bd){bd=d;p=i;}}if(p<0)return x;x.flip(p);}throw runtime_error("quench exceeded");}
int main(int argc,char**argv){
 if(argc<9){cerr<<"usage: OUT.tsv IN.tsv REPS STEPS LAMBDA TARGET TENURE PERIOD [MAXSTATES]\n";return 2;}
 string out=argv[1],file=argv[2];int reps=stoi(argv[3]),steps=stoi(argv[4]),lambda=stoi(argv[5]),target=stoi(argv[6]),tenure=stoi(argv[7]),period=stoi(argv[8]),maxstates=argc>9?stoi(argv[9]):INT_MAX;
 ifstream in(file);ofstream f(out);string line;getline(in,line);
 f<<"n\tstate\tstartE\tstartD\trep\tmethod\tbestE\tbest_quenchedE\tbest_quenchedDefect\tbest_non_near_quenchE\tunique_quenches\tactual_steps\n";
 int id=0;
 while(id<maxstates && getline(in,line)){
  if(line.empty())continue;istringstream ss(line);int n,E,seed,near;string bits,origin,parent,canon;ss>>n>>E>>bits>>origin>>parent>>seed>>near>>canon;Sol base(bits);if(base.E!=E)throw runtime_error("score mismatch");
  for(int rep=0;rep<reps;rep++)for(int method=0;method<3;method++){
   mt19937_64 rng(mix(id*991217ull+rep*17171ull+943)),prng(mix(id*123123ull+rep*81611ull+737));auto rule=PairRule(base,method==2,prng);
   Sol x=base,best=base;int startD=rule.defect(base);vector<int>last(n,-10000);set<string>ends;int bqe=INT_MAX,bqd=-1,bne=INT_MAX;
   for(int t=0;t<steps;t++){
    bool deformed=(method!=0)&&(t%period<period/2);
    int dcur=rule.defect(x),p=-1;double bs=1e99;
    for(int i=0;i<n;i++){
     int dE=x.delta(i);if(t-last[i]<=tenure && x.E+dE>=best.E)continue;
     double v=dE;
     if(deformed){int dd=rule.flip_delta(x,i);v-=lambda*(min(target+startD,dcur+dd)-min(target+startD,dcur));}
     if(v<bs-1e-9 || (abs(v-bs)<1e-9 && (rng()&1))){bs=v;p=i;}
    }
    if(p<0)p=rng()%n;x.flip(p);last[p]=t;if(x.E<best.E)best=x;
    if(t%period==period/2-1 || t%period==period-1){
      Sol q=relax(x);if(q.E<best.E)best=q;
      ends.insert(canonical(q));
      if(q.E<bqe){bqe=q.E;bqd=rule.defect(q);}
      if(!nearSkew(q))bne=min(bne,q.E);
    }
   }
   if(directE(best.s)!=best.E)throw runtime_error("invalid result");
   f<<n<<"\t"<<id<<"\t"<<base.E<<"\t"<<startD<<"\t"<<rep<<"\t"<<method<<"\t"<<best.E<<"\t"<<bqe<<"\t"<<bqd<<"\t"<<(bne==INT_MAX?-1:bne)<<"\t"<<ends.size()<<"\t"<<steps<<"\n";
  }
  cerr<<"done "<<id<<" N="<<n<<" E="<<base.E<<"\n";id++;
 }
}
