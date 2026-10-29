// Uniform balanced-quartet motifs vs uniform random four flips.
// Depends on fresh_interactions.cpp in the same directory.
// g++ -O3 -std=c++17 motif_vs_random.cpp -o motif_vs_random
// ./motif_vs_random motif100_stage40.csv 100 4000 152290 40
#define main fresh_generator_main
#include "fresh_interactions.cpp"
#undef main
int main(int argc,char**argv){
 if(argc!=6){cerr<<"usage: output N groups seed stage\n";return 2;}
 selftest();ofstream f(argv[1]);int n=stoi(argv[2]),groups=stoi(argv[3]),stage=stoi(argv[5]);
 mt19937_64 rng(stoull(argv[4])),candidate_rng(stoull(argv[4])+884241UL);
 uniform_int_distribution<int> bit(0,n-1);vector<array<int,4>> quads;
 for(int a=0;a<n;a++)for(int b=a+1;b<n;b++)for(int c=b+1;c<n;c++){
  int d=b+c-a;if(d>c&&d<n)quads.push_back({a,b,c,d});}
 cerr<<"balanced quartets="<<quads.size()<<"\n";
 uniform_int_distribution<size_t> pick(0,quads.size()-1);
 f<<"n,group,stage,type,candidate,baseE,singles,exactDelta,steepE,firstE,steepSteps,firstSteps\n";
 for(int g=0;g<groups;g++){
  vector<int8_t> raw(n);for(auto&v:raw)v=(rng()&1)?1:-1;L base(raw);base.descent(0);
  for(int t=0;t<stage;t++){
   auto trial=base;vector<int> ids;
   while(ids.size()<4){int i=bit(rng);if(find(ids.begin(),ids.end(),i)==ids.end())ids.push_back(i);}
   for(int i:ids)trial.flip(i);trial.descent(0);if(trial.e<base.e)base=move(trial);
  }
  vector<int> de(n);for(int i=0;i<n;i++)de[i]=base.delta(i);
  // type 0 random, type 1 motif; 12 proposals each per independent base.
  for(int kind=0;kind<2;kind++)for(int j=0;j<12;j++){
   vector<int> ids;
   if(kind==1){auto q=quads[pick(candidate_rng)];ids={q[0],q[1],q[2],q[3]};}
   else{
    while(ids.size()<4){int i=bit(candidate_rng);if(find(ids.begin(),ids.end(),i)==ids.end())ids.push_back(i);}
    sort(ids.begin(),ids.end());
   }
   int singles=0;auto pert=base;
   for(int i:ids){singles+=de[i];pert.flip(i);}
   int instant=pert.e-base.e;
   auto steep=pert;int steps=steep.descent(0);auto first=pert;int stepsf=first.descent(1);
   if(g==0&&j==0)assert(directE(steep.s)==steep.e&&directE(first.s)==first.e);
   f<<n<<","<<g<<","<<stage<<","<<kind<<","<<j<<","<<base.e<<","<<singles<<","
    <<instant<<","<<steep.e<<","<<first.e<<","<<steps<<","<<stepsf<<"\n";
  }
  if(g%1000==0)cerr<<"done "<<g<<" / "<<groups<<"\n";
 }
 return 0;
}
