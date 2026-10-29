#define main deform_library_main
#include "deform.cpp"
#undef main
struct Entry {int E,depth;string bits;};
int main(int argc,char **argv){
 if(argc<5){cerr<<"usage OUT.tsv anchors.tsv MAX_DEPTH CUTOFF\n";return 2;}
 auto refs=anchors(argv[2]);ofstream out(argv[1]);out<<"n\tenergy\tbits\tdepth\tcanonical\n";
 int maxDepth=stoi(argv[3]),cutoff=stoi(argv[4]);
 for(auto ref:refs)if(ref.n==99||ref.n==100){
  Sol x(ref.bits);int begin=0;
  if(ref.n%2==0){begin=skew(x.s,0,x.n-1)?0:1;if(!skew(x.s,begin,x.n-1))throw runtime_error("not near skew");}
  int m=(ref.n-1)/2;vector<pair<int,int>>pairs;
  for(int j=1;j<=m;j++)pairs.push_back({begin+m-j,begin+m+j});
  set<string>seen;long long total=0;long long levels[9]={0};int minimum[9];fill(minimum,minimum+9,INT_MAX);
  vector<Entry>found;
  auto inspect=[&](int d){total++;levels[d]++;minimum[d]=min(minimum[d],x.E);if(x.E<=cutoff){auto c=canonical(x);if(seen.insert(c).second)found.push_back({x.E,d,x.bits()});}};
  auto rec=[&](auto&&rec,int lo,int remain,int depth)->void {
   if(remain==0){inspect(depth);return;}
   for(int i=lo;i<=m-remain;i++){
    auto [a,b]=pairs[i];x.flip(a);x.flip(b);rec(rec,i+1,remain-1,depth);x.flip(b);x.flip(a);
   }
  };
  for(int d=1;d<=maxDepth;d++){rec(rec,0,d,d);cerr<<"n="<<ref.n<<" d="<<d<<" combinations="<<levels[d]<<" minE="<<minimum[d]<<" retained="<<found.size()<<"\n";}
  sort(found.begin(),found.end(),[](auto&a,auto&b){return tie(a.E,a.depth,a.bits)<tie(b.E,b.depth,b.bits);});
  int K=min(64,(int)found.size());for(int i=0;i<K;i++){auto &r=found[i];out<<ref.n<<"\t"<<r.E<<"\t"<<r.bits<<"\t"<<r.depth<<"\t"<<canonical(Sol(r.bits))<<"\n";}
  cerr<<"n="<<ref.n<<" total="<<total<<" distinct_under_cutoff="<<seen.size()<<"\n";
 }
}
