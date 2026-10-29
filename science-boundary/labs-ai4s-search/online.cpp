#define main make_dataset_unused
#include "lns_mask.cpp"
#undef main
// End-to-end paired time-budget test using monotonic improve-only acceptance.
// Time starts after identical seed state at stage=40; includes all feature, mask,
// enumeration and relaxation CPU time, and excludes common precomputation of base.
int main(int argc,char**argv){
 if(argc<7){cerr<<"online OUT.csv N BASES SEED M BUDGET_MS [STAGE=40]\n";return 2;}
 ofstream f(argv[1]);int n=stoi(argv[2]),bases=stoi(argv[3]),m=stoi(argv[5]),stage=argc>7?stoi(argv[7]):40;
 double budget=stod(argv[6])/1000.;uint64_t seed=stoull(argv[4]);
 f<<"n,group,method,stage,m,startE,bestE,steps,seconds\n";
 mt19937_64 init_rng(seed);vector<int> methods={0,1,2,5,6};
 for(int g=0;g<bases;g++){
  vector<int> v(n);for(int&x:v)x=init_rng()&1?1:-1;
  L original(v);original.descend(0);
  mt19937_64 base_rng(seed + g*117781+419);
  for(int t=0;t<stage;t++){
   auto x=original;auto ids=random_mask(n,4,base_rng);
   for(int i:ids)x.flip(i);x.descend(0);
   if(x.e<original.e)original=move(x);
  }
  vector<int> order=methods;shuffle(order.begin(),order.end(),base_rng);
  for(int method:order){
   L cur=original;mt19937_64 prop(seed + g*991711+7211*method+11213);
   auto t0=clk::now();int steps=0;
   while(ns(clk::now()-t0).count()<budget){
    bool randomhop=(method==5 || (method==6 && (steps%80)!=0));
    if(randomhop){
     L trial=cur;for(int i:random_mask(n,4,prop))trial.flip(i);
     trial.descend(0);if(trial.e<cur.e)cur=move(trial);
    }else{
     vector<int> ds(n);for(int i=0;i<n;i++)ds[i]=cur.delta(i);
     vector<int> pair; if(method==2||method==6)pair=interactions(cur,ds);
     vector<int> mask;
     if(method==0)mask=random_mask(n,m,prop);
     if(method==1)mask=soft_mask(ds,m,prop);
     if(method==2||method==6)mask=structural_mask(ds,pair,n,m,2,prop);
     auto z=enumerate(cur,mask,max(3,m/3));
     L best=cur;
     for(int rule=0;rule<2;rule++){
      auto a=z.repair;a.descend(rule);if(a.e<best.e)best=move(a);
      auto b=z.excursion;b.descend(rule);if(b.e<best.e)best=move(b);
     }
     if(best.e<cur.e)cur=move(best);
    }
    steps++;
   }
   double sec=ns(clk::now()-t0).count();
   assert(energy_direct(cur.s)==cur.e);
   f<<n<<","<<g<<","<<method<<","<<stage<<","<<m<<","<<original.e<<","<<cur.e<<","<<steps<<","<<setprecision(9)<<sec<<"\n";
  }
  if(g%50==0)cerr<<"group "<<g<<" / "<<bases<<"\n";
 }
}
