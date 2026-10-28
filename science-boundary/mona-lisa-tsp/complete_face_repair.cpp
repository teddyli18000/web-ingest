// Exhaustive sparse-graph two-cycle repairs of EVERY alternating 4-face.
// Standard C++17, deterministic, no external dependencies.
// A priori this is a restricted 4-opt family; never claim global optimality.
#include <algorithm>
#include <array>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>
using namespace std;
using Edge=pair<int,int>;
struct Weighted {int a,b,w;};
struct Face {int gain; array<Edge,2> olde,newe;};
struct Move {int net=-2000000000; int face=-1; Edge old1,old2,new1,new2;};
static inline Edge norm(int a,int b){return a<b?Edge(a,b):Edge(b,a);}
static inline uint64_t idx(Edge e){return (uint64_t(e.first)<<17)|uint64_t(e.second);}
static void require(bool b,const string& msg){if(!b) throw runtime_error(msg);}
class Search {
public:
 int n;
 vector<int> tour;
 vector<Weighted> graph;
 vector<vector<int>> incident;
 vector<array<int,2>> adj;
 vector<int> label;
 unordered_map<uint64_t,int> weights;
 vector<Face> faces;
 int64_t initial=0;
 explicit Search(const string& g,const string& f,const string& t){
  ifstream gt(t);require(bool(gt),"can't open baseline");
  gt>>n;require(n==100000,"bad n");
  tour.resize(n);adj.resize(n);label.resize(n);
  vector<int> seen(n,0);
  for(auto &x:tour){gt>>x;require(x>=0&&x<n&&!seen[x]++,"invalid base tour");}
  for(int i=0;i<n;i++){
   adj[tour[i]]={tour[(i+n-1)%n],tour[(i+1)%n]};
  }
  ifstream gf(g);require(bool(gf),"can't open graph");
  int n2,m;gf>>n2>>m;require(n2==n&&m==248972,"graph header");
  graph.resize(m);incident.resize(n);weights.reserve(m*2);
  for(int i=0;i<m;i++){
   auto &e=graph[i];gf>>e.a>>e.b>>e.w;
   require(e.a>=0&&e.b>=0&&e.a<n&&e.b<n&&e.a!=e.b,"edge");
   require(weights.emplace(idx(norm(e.a,e.b)),e.w).second,"duplicate edge");
   incident[e.a].push_back(i);incident[e.b].push_back(i);
  }
  for(int i=0;i<n;i++)initial+=wt(norm(tour[i],tour[(i+1)%n]));
  require(initial==5757191,"baseline length mismatch");
  ifstream ff(f);require(bool(ff),"can't open faces");
  int nf;ff>>nf;require(nf>279&&nf<34000,"bad face count");
  faces.resize(nf);
  for(int i=0;i<nf;i++){
   auto &z=faces[i];ff>>z.gain;
   int a,b,c,d,u,v,w,x;
   ff>>a>>b>>c>>d>>u>>v>>w>>x;
   z.olde={norm(a,b),norm(c,d)};
   z.newe={norm(u,v),norm(w,x)};
   require(wt(z.olde[0])+wt(z.olde[1])-wt(z.newe[0])-wt(z.newe[1])==z.gain,"face gain mismatch");
  }
 }
 int wt(Edge e) const{
  auto it=weights.find(idx(e));
  require(it!=weights.end(),"missing edge weight");
  return it->second;
 }
 void eraseEdge(Edge e){
  for(int x=0;x<2;x++){
   if(adj[e.first][x]==e.second){adj[e.first][x]=-1;break;}
  }
  for(int x=0;x<2;x++){
   if(adj[e.second][x]==e.first){adj[e.second][x]=-1;break;}
  }
  require(adj[e.first][0]==-1||adj[e.first][1]==-1,"erase failed first");
  require(adj[e.second][0]==-1||adj[e.second][1]==-1,"erase failed second");
 }
 void addEdge(Edge e){
  bool u=false,v=false;
  for(int x=0;x<2;x++)if(adj[e.first][x]==-1){adj[e.first][x]=e.second;u=true;break;}
  for(int x=0;x<2;x++)if(adj[e.second][x]==-1){adj[e.second][x]=e.first;v=true;break;}
  require(u&&v,"add edge failed");
 }
 void modify(const array<Edge,2>& olde,const array<Edge,2>& newe){
  for(const auto& e:olde)eraseEdge(e);
  for(const auto& e:newe)addEdge(e);
 }
 vector<int> walk(int start,int group){
  int prev=-1,cur=start;
  vector<int> vs;
  while(label[cur]==0){
   label[cur]=group;vs.push_back(cur);
   auto a=adj[cur];
   require(a[0]>=0&&a[1]>=0,"bad degree");
   int nxt=a[0]!=prev?a[0]:a[1];
   prev=cur;cur=nxt;
   require((int)vs.size()<=n,"cycle overflow");
  }
  require(cur==start,"cycle didn't close");
  return vs;
 }
 bool inverse(const Face& f,Edge old1,Edge old2,Edge new1,Edge new2){
  array<Edge,2> old={old1,old2};
  array<Edge,2> ne={new1,new2};
  sort(old.begin(),old.end());sort(ne.begin(),ne.end());
  auto inverseOld=f.newe,inverseNew=f.olde;
  sort(inverseOld.begin(),inverseOld.end());sort(inverseNew.begin(),inverseNew.end());
  return old==inverseOld&&ne==inverseNew;
 }
 vector<int> makeTour(){
  vector<int> out;out.reserve(n);
  vector<unsigned char> visited(n,0);
  int start=tour[0],cur=start,prev=-1;
  while(!visited[cur]){
   visited[cur]=1;out.push_back(cur);
   auto a=adj[cur];
   int nxt=a[0]!=prev?a[0]:a[1];
   prev=cur;cur=nxt;
  }
  require((int)out.size()==n&&cur==start,"not a Hamiltonian cycle");
  return out;
 }
 int64_t length(const vector<int>& xs){
  int64_t sum=0;
  for(int i=0;i<n;i++)sum+=wt(norm(xs[i],xs[(i+1)%n]));
  return sum;
 }
 void output(const string& summary,const string& neutrals,const string& tourFile,int start,int stop){
  int tested=0,splits=0,connected=0,neutral=0,positive=0,negative=0;
  int noCross=0;
  int maxNet=-1000000000, bestRank=-1;
  Move best;
  ofstream neutralOut(neutrals);
  for(int index=start;index<stop;index++){
   auto& face=faces[index];
   modify(face.olde,face.newe);
   fill(label.begin(),label.end(),0);
   auto first=walk(face.olde[0].first,1);
   tested++;
   if((int)first.size()==n){
    connected++;
    if(face.gain>0){
     best={face.gain,index,{-1,-1},{-1,-1},{-1,-1},{-1,-1}};
     maxNet=face.gain;bestRank=index;positive++;
    }
    modify(face.newe,face.olde);
    continue;
   }
   splits++;
   int otherStart=-1;
   for(auto e:face.olde)for(int x:{e.first,e.second})
    if(label[x]==0)otherStart=x;
   for(auto e:face.newe)for(int x:{e.first,e.second})
    if(label[x]==0)otherStart=x;
   require(otherStart>=0,"no other cycle entry");
   auto second=walk(otherStart,2);
   require((int)first.size()+(int)second.size()==n,"split sizes");
   int small=(first.size()<second.size())?1:2;
   const auto &vertices=(small==1?first:second);
   Move local;
   for(int u:vertices){
    for(int gi:incident[u]){
     const auto &ce=graph[gi];
     int v=(ce.a==u)?ce.b:ce.a;
     if(label[v]==small)continue;
     require(label[v]!=0,"missing label");
     auto au=adj[u],av=adj[v];
     for(int pu:au)for(int pv:av){
      Edge old1=norm(u,pu),old2=norm(v,pv);
      Edge new1=norm(u,v),new2=norm(pu,pv);
      auto it=weights.find(idx(new2));
      if(it==weights.end())continue;
      if(inverse(face,old1,old2,new1,new2))continue;
      int gain=face.gain+wt(old1)+wt(old2)-ce.w-it->second;
      if(gain>local.net){
       local={gain,index,old1,old2,new1,new2};
      }
     }
    }
   }
   if(local.face<0){noCross++;}
   else if(local.net>=0){
    if(local.net>0)positive++;else neutral++;
    if(local.net>maxNet){best=local;maxNet=local.net;bestRank=index;}
    if(local.net==0){
     // Symmetric difference of the split flip and the repair;
     // retains only nontrivial changed edges of final complete route.
     vector<Edge> flipped={face.olde[0],face.olde[1],face.newe[0],face.newe[1],
       local.old1,local.old2,local.new1,local.new2};
     sort(flipped.begin(),flipped.end());
     vector<Edge> toggled;
     for(int k=0;k<(int)flipped.size();){
      int j=k+1;while(j<(int)flipped.size()&&flipped[j]==flipped[k])j++;
      if((j-k)%2)toggled.push_back(flipped[k]);
      k=j;
     }
     vector<Edge> old,ne;
     for(auto e:toggled){
      bool isbase=(adj[e.first][0]==e.second||adj[e.first][1]==e.second);
      // Current adj is face-flipped: classify using original baseline
      // membership from old face edge and repair position instead.
      // Recovered via precomputed original baseline adjacency, see baseedges.
      if(baseedges.find(idx(e))!=baseedges.end())old.push_back(e);
      else ne.push_back(e);
     }
     require(!old.empty()&&old.size()==ne.size(),"nontrivial neutral edit");
     neutralOut<<index<<" "<<face.gain<<" "<<old.size();
     for(auto e:old)neutralOut<<" "<<e.first<<" "<<e.second;
     for(auto e:ne)neutralOut<<" "<<e.first<<" "<<e.second;
     neutralOut<<"\n";
    }
   }else negative++;
   modify(face.newe,face.olde);
  }
  if(best.face>=0&&maxNet>0){
   const auto& face=faces[best.face];
   modify(face.olde,face.newe);
   if(best.old1.first>=0) {
    array<Edge,2> old={best.old1,best.old2};
    array<Edge,2> ne={best.new1,best.new2};
    modify(old,ne);
   }
   auto route=makeTour();
   require(length(route)==initial-maxNet,"new tour score mismatch");
   ofstream dst(tourFile);
   for(int x:route)dst<<(x+1)<<"\n";
  }
  ofstream s(summary);
  s<<"{\"start\":"<<start<<",\"stop\":"<<stop<<",\"faces_tested\":"<<tested
    <<",\"faces_splitting\":"<<splits<<",\"faces_still_connected\":"<<connected
    <<",\"neutral_best_repairs\":"<<neutral<<",\"strictly_improving_face_repairs\":"<<positive
    <<",\"negative_best_repairs\":"<<negative<<",\"faces_with_no_nontrivial_repair\":"<<noCross
    <<",\"best_net_gain\":"<<maxNet<<",\"best_face_index\":"<<bestRank
    <<",\"candidate_written\":"<<(maxNet>0?"true":"false")<<"}\n";
  cout<<"RESULT start="<<start<<" stop="<<stop<<" n="<<tested
    <<" split="<<splits<<" neutral="<<neutral<<" positive="<<positive
    <<" maxgain="<<maxNet<<" noRepair="<<noCross<<"\n";
 }
 unordered_map<uint64_t,char> baseedges;
 void initbase(){
  baseedges.reserve(n*2);
  for(int i=0;i<n;i++)baseedges[idx(norm(tour[i],tour[(i+1)%n]))]=1;
 }
};
int main(int argc,char** argv){
 try{
  require(argc==9,"usage: executable graph.txt faces.txt tour.txt START COUNT summary.json neutral.tsv candidate.txt");
  Search S(argv[1],argv[2],argv[3]);S.initbase();
  int st=stoi(argv[4]),cnt=stoi(argv[5]);require(st>=0&&cnt>=0,"bad range");
  int en=min(st+cnt,(int)S.faces.size());
  S.output(argv[6],argv[7],argv[8],st,en);
  return 0;
 }catch(const exception& e){cerr<<"FAILED: "<<e.what()<<"\n";return 1;}
}
