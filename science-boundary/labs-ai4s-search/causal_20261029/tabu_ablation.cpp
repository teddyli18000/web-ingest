#include "causal_lib.hpp"
void single_spin_tabu(Traj &z,RNG&r,vector<int>&last,int iter,int tenure){
 int p=-1,b=INT_MAX;
 for(int i=0;i<z.current.n;i++){
  int d=z.current.delta(i);
  if(tenure>0 && iter-last[i]<=tenure && z.current.e+d>=z.best.e)continue;
  if(d<b){b=d;p=i;}
 }
 if(p<0)p=uniform_int_distribution<int>(0,z.current.n-1)(r);
 z.current.flip(p);last[p]=iter;
 if(z.current.e<z.best.e)z.best=z.current;
 z.calls++;
}
int main(int argc,char**argv){
 if(argc<7){cerr<<"OUT N BASES SEED PHASE_MS TAIL_MS [WARM=1000]\n";return 2;}
 int n=stoi(argv[2]),G=stoi(argv[3]),warmsteps=argc>7?stoi(argv[7]):1000;
 uint64_t seed=stoull(argv[4]);double phase=stod(argv[5])/1000.,tail=stod(argv[6])/1000.;
 ofstream f(argv[1]);f<<"n,group,tenure,baseE,phaseE,finalE,phase_calls\n";
 for(int g=0;g<G;g++){
  RNG r(seed+uint64_t(g)*911117+37);
  vector<int> v(n);for(int &z:v)z=r()%2?1:-1;
  L base(v);base.descend();
  for(int t=0;t<warmsteps;t++){
   L x=base;for(int i:random_mask(n,4,r))x.flip(i);x.descend();if(x.e<base.e)base=move(x);
  }
  for(int tenure:{0,1,3,7,15,30}){
   RNG a(seed+g*77291+tenure*8821);Traj z;z.current=base;z.best=base;
   vector<int> last(n,-1000);int iter=0;
   auto t0=clk::now();while(ns(clk::now()-t0).count()<phase){single_spin_tabu(z,a,last,iter++,tenure);}
   int pe=z.best.e,pc=z.calls;z.current=z.best;
   RNG tailrng(seed+g*112123+999);run_policy(z,0,tailrng,tail,10);
   assert(energy_direct(z.best.s)==z.best.e);
   f<<n<<","<<g<<","<<tenure<<","<<base.e<<","<<pe<<","<<z.best.e<<","<<pc<<"\n";
  }
  if(g%50==0)cerr<<"N="<<n<<" g="<<g<<"\n";
 }
}
