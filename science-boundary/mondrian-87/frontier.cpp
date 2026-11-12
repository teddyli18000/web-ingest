// Unrestricted constructive exact-cover search for Mondrian-87.
// Search never assumes a separator or a prescribed adjacency topology.
// Compile: g++ -std=c++20 -O3 -o frontier frontier.cpp
// Run: ./frontier SEED PIECES LOW_AREA HIGH_AREA SECONDS NODE_BUDGET
#include <bits/stdc++.h>
using namespace std;
using U = __uint128_t;
struct Opt {uint8_t s,w,h;};
struct Rect {int x,y,w,h;};
const U FULL = (((U)1)<<87)-1;
U mask[88][88],rows[87];
vector<Opt> choices;
vector<int> area,delta;
vector<Rect> placed;
uint64_t nodes=0,used=0,cap;
int pieces,lower,seconds;
bool abort_search=false;
mt19937 rng;
chrono::steady_clock::time_point began;
inline int ctz(U x){uint64_t a=(uint64_t)x;return a?__builtin_ctzll(a):64+__builtin_ctzll((uint64_t)(x>>64));}
void initialize(int a,int k,int seed){
 lower=a;pieces=k;rng.seed(seed);
 choices.clear();area.clear();delta.clear();placed.clear();used=nodes=0;abort_search=false;
 memset(rows,0,sizeof(rows));
 for(int w=1;w<=87;w++)for(int h=w;h<=87;h++)if(lower<=w*h&&w*h<=lower+17){
  int i=area.size();if(i>=63)exit(2);
  area.push_back(w*h);delta.push_back(w*h-lower);
  choices.push_back({(uint8_t)i,(uint8_t)w,(uint8_t)h});
  if(w!=h)choices.push_back({(uint8_t)i,(uint8_t)h,(uint8_t)w});
 }
 shuffle(choices.begin(),choices.end(),rng);
}
inline bool fits(int x,int y,int w,int h){
 if(x+w>87||y+h>87)return false;
 U m=mask[w][x];for(int j=y;j<y+h;j++)if(rows[j]&m)return false;
 return true;
}
inline bool area_possible(int left,int target){
 int v[100],n=0;
 for(int i=0;i<(int)area.size();i++)if(!(used>>i&1))v[n++]=area[i];
 if(n<left)return false;
 sort(v,v+n);
 int mini=0,maxi=0;
 for(int j=0;j<left;j++){mini+=v[j];maxi+=v[n-1-j];}
 if(target<mini||target>maxi)return false;
 if(left>9)return true;
 bitset<200> dp[32];dp[0].set(0);
 int count=0;
 for(int i=0;i<(int)area.size();i++)if(!(used>>i&1)){
  count++;
  for(int j=min(left,count);j>=1;j--)dp[j]|=dp[j-1]<<delta[i];
 }
 int offset=target-left*lower;
 return offset>=0&&offset<200&&dp[left].test(offset);
}
inline bool gaps_possible(int y,int h){
 U reachable=1;
 for(int i=0;i<(int)area.size();i++)if(!(used>>i&1)){
  for(auto o:choices)if(o.s==i){
   reachable|=(reachable<<o.w)|(reachable<<o.h);
   reachable&=((((U)1)<<88)-1);break;
  }
 }
 for(int yy=y;yy<y+h;yy++){
  U blank=FULL^rows[yy];
  while(blank){
   int x=ctz(blank),n=0;U z=blank>>x;
   while(z&1){n++;z>>=1;}
   if(!(reachable&(((U)1)<<n)))return false;
   blank&=~mask[n][x];
  }
 }
 return true;
}
bool dfs(int depth,int remainder){
 if(abort_search)return false;
 nodes++;
 if(depth==pieces){
  if(remainder)return false;
  cout<<"FOUND pieces="<<pieces<<" area=["<<lower<<","<<lower+17<<"] nodes="<<nodes<<"\n";
  for(auto r:placed)cout<<r.x<<","<<r.y<<","<<r.w<<","<<r.h<<" ";
  cout<<"\n";cout.flush();return true;
 }
 if((nodes&255)==0&&(nodes>cap||
    chrono::duration_cast<chrono::seconds>(chrono::steady_clock::now()-began).count()>seconds)){
  abort_search=true;return false;
 }
 if(!area_possible(pieces-depth,remainder))return false;
 int x=-1,y=-1;
 for(int j=0;j<87;j++)if(rows[j]!=FULL){y=j;x=ctz(FULL^rows[j]);break;}
 if(x<0)return false;
 for(auto o:choices){
  if(used>>o.s&1||!fits(x,y,o.w,o.h))continue;
  U m=mask[o.w][x];for(int j=y;j<y+o.h;j++)rows[j]|=m;
  used|=1ULL<<o.s;placed.push_back({x,y,o.w,o.h});
  bool feasible=(depth<6||gaps_possible(y,o.h));
  if(feasible&&dfs(depth+1,remainder-o.w*o.h))return true;
  placed.pop_back();used^=1ULL<<o.s;
  for(int j=y;j<y+o.h;j++)rows[j]^=m;
 }
 return false;
}
int main(int argc,char**argv){
 if(argc!=7)return 2;
 int seed=atoi(argv[1]),k=atoi(argv[2]),amin=atoi(argv[3]),amax=atoi(argv[4]);
 seconds=atoi(argv[5]);cap=strtoull(argv[6],nullptr,10);
 for(int w=1;w<=87;w++)for(int x=0;x+w<=87;x++)
  mask[w][x]=((((U)1)<<w)-1)<<x;
 vector<int> windows;for(int a=amin;a<=amax;a++)windows.push_back(a);
 shuffle(windows.begin(),windows.end(),mt19937(seed));
 for(int a:windows){
  initialize(a,k,seed+a);began=chrono::steady_clock::now();
  bool done=dfs(0,7569);
  cerr<<"seed="<<seed<<" k="<<k<<" A="<<a<<" shapes="<<area.size()
      <<" states="<<nodes<<" found="<<done<<" elapsed="
      <<chrono::duration<double>(chrono::steady_clock::now()-began).count()<<"\n";
  if(done)return 0;
 }
 return 1;
}
