// Construct near-equal-area 87x87 tilings by choosing one bridge rectangle
// and independently filling the two notched sides, matching shape sets.
// This searches new bridge positions and dimensions rather than fixing PR #62.
// g++ -O3 -std=c++20 bridge_construct.cpp -o bridge_construct
// bridge_construct seed min_area seconds max_configs left_nodes right_nodes max_left_sets
#include <bits/stdc++.h>
using namespace std;
using U=__uint128_t;
const U FULL=(((U)1)<<87)-1;
struct Rect{int x,y,w,h;};
struct Option{int shape,w,h;};
struct Config{int x,w,h,t,kl,kr,sl,sr,score;};
U masks[88][88];
vector<Option> opts;
vector<int> areas,delta;
int A,seconds,seed,maxLeftSets;
uint64_t leftNodes,rightNodes;
mt19937 rng;
chrono::steady_clock::time_point start;
inline int first(U x){uint64_t lo=(uint64_t)x;return lo?__builtin_ctzll(lo):64+__builtin_ctzll((uint64_t)(x>>64));}
struct Region {
 U rows[87]; uint64_t used=0,nodes=0,limit=0;
 int k,lo,hi; bool halted=false;
 vector<Rect> rects;
 void init(bool right,Config c,int bridge,uint64_t already,uint64_t budget){
  k=right?c.kr:c.kl;lo=right?c.t:0;hi=right?87:c.t;
  used=already|(1ULL<<bridge);nodes=0;limit=budget;halted=false;rects.clear();
  for(int y=0;y<87;y++)rows[y]=right?masks[c.t][0]:FULL^masks[c.t][0];
  for(int y=0;y<c.h;y++)
   rows[y]|=right?masks[c.x+c.w-c.t][c.t]:masks[c.t-c.x][c.x];
 }
 bool sums(int left,int target){
  int v[64],n=0;for(int i=0;i<(int)areas.size();i++)if(!(used>>i&1))v[n++]=areas[i];
  if(n<left)return false;sort(v,v+n);
  int minsum=0,maxsum=0;
  for(int i=0;i<left;i++){minsum+=v[i];maxsum+=v[n-1-i];}
  if(target<minsum||target>maxsum)return false;
  if(left>11)return true;
  bitset<256> dp[20];dp[0].set(0);int count=0;
  for(int i=0;i<(int)areas.size();i++)if(!(used>>i&1)){
   count++;for(int j=min(left,count);j>=1;j--)dp[j]|=dp[j-1]<<delta[i];
  }
  int offset=target-left*A;
  return offset>=0&&offset<256&&dp[left].test(offset);
 }
 bool fits(int x,int y,int w,int h){
  if(x+w>hi||y+h>87)return false;
  U m=masks[w][x];
  for(int yy=y;yy<y+h;yy++)if(rows[yy]&m)return false;
  return true;
 }
 template<class Callback> bool dfs(int depth,int remain,Callback&& onDone){
  nodes++;
  if((nodes&127)==0){
   if(nodes>limit||chrono::duration_cast<chrono::seconds>(
      chrono::steady_clock::now()-start).count()>=seconds){halted=true;return false;}
  }
  if(depth==k)return remain==0&&onDone(*this);
  if(!sums(k-depth,remain))return false;
  int x=-1,y=-1;
  for(int yy=0;yy<87;yy++)if(rows[yy]!=FULL){y=yy;x=first(FULL^rows[yy]);break;}
  if(x<0)return false;
  for(auto o:opts){
   if((used>>o.shape&1)||o.w>hi-lo||!fits(x,y,o.w,o.h))continue;
   U m=masks[o.w][x];
   for(int yy=y;yy<y+o.h;yy++)rows[yy]|=m;
   used|=1ULL<<o.shape;rects.push_back({x,y,o.w,o.h});
   bool found=dfs(depth+1,remain-o.w*o.h,onDone);
   rects.pop_back();used^=1ULL<<o.shape;
   for(int yy=y;yy<y+o.h;yy++)rows[yy]^=m;
   if(found)return true;
   if(halted)return false;
  }
  return false;
 }
};
int main(int argc,char**argv){
 if(argc!=8)return 2;
 seed=atoi(argv[1]);A=atoi(argv[2]);seconds=atoi(argv[3]);
 int maxConfigs=atoi(argv[4]);uint64_t budgetL=strtoull(argv[5],0,10);
 uint64_t budgetR=strtoull(argv[6],0,10);maxLeftSets=atoi(argv[7]);
 rng.seed(seed);
 for(int w=1;w<=87;w++)for(int x=0;x+w<=87;x++)
  masks[w][x]=((((U)1)<<w)-1)<<x;
 for(int w=1;w<=87;w++)for(int h=w;h<=87;h++)if(A<=w*h&&w*h<=A+17){
  int i=areas.size();if(i>=63)return 2;
  areas.push_back(w*h);delta.push_back(w*h-A);
  opts.push_back({i,w,h});
  if(w!=h)opts.push_back({i,h,w});
 }
 vector<Config> plans;
 for(int h=5;h<=13;h++)for(int w=1;w<=87;w++){
  bool eligible=false;
  for(auto o:opts)if(o.w==w&&o.h==h){eligible=true;break;}
  if(!eligible)continue;
  for(int x=0;x+w<=87;x++)for(int t=x+2;t<x+w-1;t++){
   int sl=t*87-(t-x)*h,sr=7569-w*h-sl;
   for(int kl=4;kl<=12;kl++){
    int kr=18-kl;if(kr<4||kr>14)continue;
    if(sl<kl*A||sl>kl*(A+17)||sr<kr*A||sr>kr*(A+17))continue;
    int score=abs(sl-kl*399)+abs(sr-kr*399)+2*abs(x-8)+3*abs(h-6)+abs(w-66);
    plans.push_back({x,w,h,t,kl,kr,sl,sr,score});
   }
  }
 }
 shuffle(plans.begin(),plans.end(),rng);
 for(auto &p:plans)p.score=2*p.score+int(rng()%240);
 sort(plans.begin(),plans.end(),[](auto &a,auto &b){return a.score<b.score;});
 cerr<<"SETUP seed="<<seed<<" A="<<A<<" shapes="<<areas.size()<<" bridge_configs="<<plans.size()<<"\n";
 start=chrono::steady_clock::now();
 int configs=0,sets=0;uint64_t nodesL=0,nodesR=0;
 for(auto c:plans){
  if(configs>=maxConfigs||chrono::duration_cast<chrono::seconds>(
     chrono::steady_clock::now()-start).count()>=seconds)break;
  configs++;int bridge=-1;
  for(auto o:opts)if(o.w==c.w&&o.h==c.h){bridge=o.shape;break;}
  Region left;left.init(false,c,bridge,0,budgetL);
  unordered_set<uint64_t> leftSeen;
  int thisSets=0;bool solution=false;
  left.dfs(0,c.sl,[&](Region &l){
   if(!leftSeen.insert(l.used).second)return false;
   sets++;thisSets++;
   Region right;right.init(true,c,bridge,l.used,budgetR);
   bool result=right.dfs(0,c.sr,[&](Region &r){
    vector<Rect> answer={{c.x,0,c.w,c.h}};
    answer.insert(answer.end(),l.rects.begin(),l.rects.end());
    answer.insert(answer.end(),r.rects.begin(),r.rects.end());
    cout<<"FOUND A="<<A<<" count="<<answer.size()<<" config="
        <<c.x<<","<<c.w<<","<<c.h<<","<<c.t<<"\n";
    for(auto z:answer)cout<<z.x<<","<<z.y<<","<<z.w<<","<<z.h<<" ";
    cout<<"\n";cout.flush();solution=true;return true;
   });
   nodesR+=right.nodes;
   return result||thisSets>=maxLeftSets;
  });
  nodesL+=left.nodes;
  if(solution)return 0;
  if(configs%100==0)cerr<<"PROGRESS configs="<<configs<<" left_sets="<<sets
       <<" nodesL="<<nodesL<<" nodesR="<<nodesR<<"\n";
 }
 cerr<<"END configs="<<configs<<" left_sets="<<sets<<" nodesL="<<nodesL
     <<" nodesR="<<nodesR<<"\n";
 return 1;
}
