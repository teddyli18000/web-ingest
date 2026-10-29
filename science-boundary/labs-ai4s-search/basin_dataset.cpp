// LABS exact-integer basin transition dataset; C++17. Compiler: g++ -O3 -std=c++17.
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <numeric>
#include <random>
#include <set>
#include <string>
#include <vector>
using namespace std;
struct Landscape {
  vector<int> s,c; int n,E;
  explicit Landscape(vector<int> v):s(move(v)),n((int)s.size()) {recompute();}
  void recompute(){c.assign(n,0);E=0;for(int k=1;k<n;k++){for(int i=0;i<n-k;i++)c[k]+=s[i]*s[i+k];E+=c[k]*c[k];}}
  int delta(int i) const {int d=0;for(int k=1;k<n;k++){int dc=0;if(i>=k)dc+=s[i-k];if(i+k<n)dc+=s[i+k];dc*=(-2*s[i]);d+=2*c[k]*dc+dc*dc;}return d;}
  void flip(int i){int d=0;for(int k=1;k<n;k++){int dc=0;if(i>=k)dc+=s[i-k];if(i+k<n)dc+=s[i+k];dc*=(-2*s[i]);d+=2*c[k]*dc+dc*dc;c[k]+=dc;}s[i]=-s[i];E+=d;}
  int relax(){int steps=0;while(true){int best=0,idx=-1;for(int i=0;i<n;i++){int d=delta(i);if(d<best){best=d;idx=i;}}if(idx<0)break;flip(idx);steps++;if(steps>1000){cerr<<"LOOP";exit(2);}}return steps;}
};
vector<int> canonical(vector<int> s){
  vector<int> best;bool first=true;
  for(int r=0;r<2;r++)for(int neg=0;neg<2;neg++)for(int alt=0;alt<2;alt++){
    vector<int> t=s;if(r)reverse(t.begin(),t.end());for(int i=0;i<(int)t.size();i++){if(neg)t[i]=-t[i];if(alt && (i%2))t[i]=-t[i];}
    if(first||t<best){best=t;first=false;}
  }return best;
}
int slowE(const vector<int>&s){int n=s.size(),e=0;for(int k=1;k<n;k++){int c=0;for(int i=0;i<n-k;i++)c+=s[i]*s[i+k];e+=c*c;}return e;}
void selftest(){
  mt19937_64 rng(54321);int tested=0;
  for(int n: {8,24,40,64,100})for(int t=0;t<70;t++){
    vector<int> s(n);for(int &v:s)v=(rng()%2)?1:-1;
    Landscape L(s);
    for(int move=0;move<5;move++){
      if(L.E!=slowE(L.s)){cerr<<"energy mismatch\n";exit(3);}
      for(int i=0;i<n;i++){
        vector<int> t=L.s;t[i]=-t[i];
        if(L.delta(i)!=slowE(t)-L.E){cerr<<"delta mismatch n="<<n<<" idx="<<i<<"\n";exit(4);}
        tested++;
      }
      L.flip(rng()%n);
      if(L.E!=slowE(L.s)){cerr<<"flip mismatch\n";exit(5);}
    }
    L.relax();if(L.E!=slowE(L.s)){cerr<<"descent mismatch\n";exit(6);}
    for(int i=0;i<n;i++)if(L.delta(i)<0){cerr<<"not local minimum\n";exit(7);}
  }
  string cert="++++++--+++++-----++-++--+--++++++++++---+-++--++++-+--++----+--+-+-+-+-++---++---++-+-++-+-++--+-+-";
  vector<int> official;for(char c:cert)official.push_back(c=='+'?1:-1);
  if(official.size()!=100||slowE(official)!=578||Landscape(official).E!=578){cerr<<"official baseline mismatch\n";exit(8);}
  cout<<"PASS "<<tested<<" independent delta tests, descent tests, N100 official E=578\n";
}
#ifndef LABS_NO_MAIN
int main(int argc,char**argv){
  if(argc==2 && string(argv[1])=="--selftest"){selftest();return 0;}
  if(argc<5){cerr<<"usage: ./gen OUTPUT N BASES SEED [CANDIDATES=12] [elite]\n";return 2;}
  ofstream f(argv[1]);int n=stoi(argv[2]),bases=stoi(argv[3]);uint64_t seed=stoull(argv[4]);int candidates=argc>5?stoi(argv[5]):12; bool elite=(argc>6 && string(argv[6])=="elite");
  mt19937_64 rng(seed);uniform_int_distribution<int> coin(0,1),bit(0,n-1);
  vector<string> names={"n","group","candidate","k","baseE","immediate","single_min","single_max","single_mean","single_sd","pair_coupling","pair_coupling_abs","pair_lag_c","pair_lag_cabs","min_gap","max_gap","mean_gap","span","end_bias","pair_sign","global_c2odd","global_c2long","global_c4","global_cabs","flip_delta_min_perturbed","flip_delta_sd_perturbed","flip_delta_negcount_perturbed","finalE","changed","improved","steps","hamming"};
  for(size_t i=0;i<names.size();i++)f<<names[i]<<(i+1==names.size()?"\n":",");
  double changed=0,improved=0,returncount=0,total=0;long long calls=0;
  for(int g=0;g<bases;g++){
    vector<int> init(n);for(int &v:init)v=coin(rng)?1:-1;
    Landscape base(init);base.relax();
    if(elite){
      // Iterated basin-hopping: 40 random four-flip moves from the current best;
      // accept only improved strict-descent endpoints. No labels from evaluation candidates.
      for(int q=0;q<40;q++){
        vector<int> spins;
        while(spins.size()<4){int p=bit(rng);if(find(spins.begin(),spins.end(),p)==spins.end())spins.push_back(p);}
        Landscape trial(base.s);for(int p:spins)trial.flip(p);trial.relax();
        if(trial.E<base.E)base=move(trial);
      }
    }
    auto origcanon=canonical(base.s);vector<int> single(n);for(int i=0;i<n;i++)single[i]=base.delta(i);
    for(int j=0;j<candidates;j++){
      int k=j<candidates/2?2:4;vector<int> indices;while((int)indices.size()<k){int x=bit(rng);if(find(indices.begin(),indices.end(),x)==indices.end())indices.push_back(x);}sort(indices.begin(),indices.end());
      Landscape z(base.s);for(int i:indices)z.flip(i);
      int immediate=z.E-base.E;double singlesum=0,singlesq=0,singlemin=1e20,singlemax=-1e20;
      for(int i:indices){singlesum+=single[i];singlesq+=single[i]*single[i];singlemin=min(singlemin,(double)single[i]);singlemax=max(singlemax,(double)single[i]);}
      double mean=singlesum/k,sd=sqrt(max(0.,singlesq/k-mean*mean));
      double paircoupl=0,paircouplabs=0,pairlag=0,pairlagabs=0,psign=0,pairs=0;
      for(int a=0;a<k;a++)for(int b=a+1;b<k;b++){
        Landscape pair(base.s);pair.flip(indices[a]);pair.flip(indices[b]);double coupling=pair.E-base.E-single[indices[a]]-single[indices[b]];
        paircoupl+=coupling;paircouplabs+=abs(coupling);int lag=indices[b]-indices[a];pairlag+=base.c[lag]*base.s[indices[a]]*base.s[indices[b]];pairlagabs+=abs(base.c[lag]);psign+=base.s[indices[a]]*base.s[indices[b]];pairs++;
      }
      int minGap=n,maxGap=0;double gapSum=0;for(int a=1;a<k;a++){int d=indices[a]-indices[a-1];minGap=min(minGap,d);maxGap=max(maxGap,d);gapSum+=d;}
      double odd=0,lon=0,c4=0,cabs=0;for(int lag=1;lag<n;lag++){double c=base.c[lag];if(lag%2)odd+=c*c;if(lag>n/2)lon+=c*c;c4+=c*c*c*c;cabs+=abs(c);}
      double gmin=1e20,gsq=0,gmean=0;int gneg=0;for(int i=0;i<n;i++){double d=z.delta(i);gmin=min(gmin,d);gmean+=d;gsq+=d*d;if(d<0)gneg++;}gmean/=n;
      double gsd=sqrt(max(0.,gsq/n-gmean*gmean));
      int steps=z.relax();calls++;bool ch=canonical(z.s)!=origcanon;bool imp=z.E<base.E;int ham=0;for(int i=0;i<n;i++)ham+=(base.s[i]!=z.s[i]);
      double data[]={double(n),double(g),double(j),double(k),double(base.E),double(immediate)/n,singlemin/n,singlemax/n,mean/n,sd/n,(paircoupl/pairs)/n,(paircouplabs/pairs)/n,pairlag/pairs/sqrt(n),pairlagabs/pairs/sqrt(n),double(minGap)/n,double(maxGap)/n,gapSum/(k-1)/n,double(indices.back()-indices.front())/n,double(indices.front()+indices.back())/n-1.,psign/pairs,odd/base.E,lon/base.E,c4/(n*n*n),cabs/(n*sqrt(n)),gmin/n,gsd/n,double(gneg)/n,double(z.E),double(ch),double(imp),double(steps),double(ham)};
      for(size_t h=0;h<names.size();h++)f<<setprecision(12)<<data[h]<<(h+1==names.size()?"\n":",");
      changed+=ch;improved+=imp;returncount+=!ch;total++;
    }
  }
  cout<<"n="<<n<<" starts="<<bases<<" candidates="<<candidates<<" rows="<<total<<" changed="<<changed/total<<" improved="<<improved/total<<"\n";
}
#endif // LABS_NO_MAIN
