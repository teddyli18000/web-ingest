// Trajectory-dependent perturbation-radius experiment. Reuses the verified exact LABS landscape.
#include <sstream>
#define LABS_NO_MAIN
#include "basin_dataset.cpp"
int main(int argc,char**argv){
 if(argc<5){cerr<<"usage: ./radius_trace OUTPUT N STARTS SEED [K_LIST=2,4,6,8] [STAGE_ONLY=-1]\n";return 2;}
 ofstream f(argv[1]);int n=stoi(argv[2]),starts=stoi(argv[3]);uint64_t seed=stoull(argv[4]);
 mt19937_64 hoprng(seed),proberng(seed^0x9E3779B97F4A7C15ULL);
 uniform_int_distribution<int> coin(0,1),hi(0,n-1),pi(0,n-1);
 int stage_only=(argc>6?stoi(argv[6]):-1);
 vector<int> radii={2,4,6,8};
 if(argc>5){radii.clear();stringstream ss(argv[5]);string z;while(getline(ss,z,',')){int k=stoi(z);if(k<1||k>n){cerr<<"invalid k";return 2;}radii.push_back(k);}}
 f<<"n,group,stage,baseE,k,candidate,perturbedE,finalE,improved,changed,steps\n";
 for(int g=0;g<starts;g++){
  vector<int> init(n);for(auto &v:init)v=coin(hoprng)?1:-1;
  Landscape base(init);base.relax();
  for(int stage=0;stage<=40;stage++){
   if((stage_only<0 && (stage==0||stage==5||stage==15||stage==40)) || stage==stage_only){
    auto orig=canonical(base.s);
    for(int k:radii)for(int j=0;j<6;j++){
     vector<int> idx;while((int)idx.size()<k){int b=pi(proberng);if(find(idx.begin(),idx.end(),b)==idx.end())idx.push_back(b);}
     Landscape x(base.s);for(int b:idx)x.flip(b);int pe=x.E;
     int steps=x.relax();bool ch=canonical(x.s)!=orig;
     f<<n<<","<<g<<","<<stage<<","<<base.E<<","<<k<<","<<j<<","<<pe<<","<<x.E<<","<<(x.E<base.E)<<","<<ch<<","<<steps<<"\n";
    }
   }
   if(stage==40)break;
   vector<int> idx;while(idx.size()<4){int b=hi(hoprng);if(find(idx.begin(),idx.end(),b)==idx.end())idx.push_back(b);}
   Landscape trial(base.s);for(int b:idx)trial.flip(b);trial.relax();
   if(trial.E<base.E)base=move(trial);
  }
 }
 cerr<<"N="<<n<<" starts="<<starts<<" done\n";
}
