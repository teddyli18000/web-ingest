#define main unused_generator_main
#include "lns_mask.cpp"
#undef main
int main(int argc,char**argv){
 if(argc<7){cerr<<"usage OUT N STAGE GROUPS SEED M MASKS\n";return 2;}
 ofstream f(argv[1]);int n=stoi(argv[2]),stage=stoi(argv[3]),groups=stoi(argv[4]),m=stoi(argv[6]),masks=argc>7?stoi(argv[7]):12;
 mt19937_64 init(stoull(argv[5])),seed(stoull(argv[5])+123789);
 f<<"n,group,method,m,distinct_positions,mean_jaccard,unique_endpoints,return_base,hits,maxgain,mean_pair_distance,all_raw_endpoints,all_endpoint_return_count,all_return_proportion,all_unique_per_mask_mean\n";
 for(int g=0;g<groups;g++){
  vector<int> s(n);for(int &v:s)v=(init()&1)?1:-1;L base(s);base.descend();
  for(int t=0;t<stage;t++){
   L z=base;for(int i:random_mask(n,4,init))z.flip(i);
   z.descend();if(z.e<base.e)base=move(z);
  }
  vector<int> ds(n);for(int i=0;i<n;i++)ds[i]=base.delta(i);
  auto pc=interactions(base,ds);
  for(int method=0;method<3;method++){
   mt19937_64 rng(seed()+method*177);vector<vector<int>> chosen;
   set<vector<int>> endpoints,allEndpoints;int returns=0,hits=0,maxgain=0,allReturns=0;double uniquePerMask=0;
   for(int j=0;j<masks;j++){
    vector<int> ids=method==0?random_mask(n,m,rng):(method==1?soft_mask(ds,m,rng):structural_mask(ds,pc,n,m,2,rng));
    chosen.push_back(ids);auto c=enumerate(base,ids,max(3,m/3));
    L best=c.repair;best.descend(0);
    set<vector<int>> perMask;
    for(int mode=0;mode<2;mode++){
     L x=c.repair;x.descend(mode);if(x.e<best.e)best=move(x);
     L y=c.excursion;y.descend(mode);if(y.e<best.e)best=move(y);
     for(const auto&candidate:{x.s,y.s}){allEndpoints.insert(candidate);perMask.insert(candidate);allReturns+=(candidate==base.s);}
    }
    uniquePerMask+=perMask.size();
    returns+=(best.s==base.s);hits+=(best.e<base.e);maxgain=max(maxgain,base.e-best.e);
    endpoints.insert(best.s);
   }
   set<int> positions;double jac=0,dist=0;int pairs=0;
   for(auto &v:chosen)positions.insert(v.begin(),v.end());
   for(int i=0;i<masks;i++)for(int j=i+1;j<masks;j++){
    int common=0;for(int k:chosen[i])common+=binary_search(chosen[j].begin(),chosen[j].end(),k);
    jac+=double(common)/(2*m-common);dist+=m-common;pairs++;
   }
   f<<n<<","<<g<<","<<method<<","<<m<<","<<positions.size()<<","<<jac/pairs<<","<<endpoints.size()<<","<<returns<<","<<hits<<","<<maxgain<<","<<dist/pairs<<","<<allEndpoints.size()<<","<<allReturns<<","<<double(allReturns)/(4*masks)<<","<<uniquePerMask/masks<<"\n";
  }
  if(g%100==0)cerr<<"done "<<g<<"\n";
 }
}
