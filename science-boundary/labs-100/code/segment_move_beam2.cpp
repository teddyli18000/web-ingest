// Two-step nonlocal bridge: enumerate the complete one-move segment
// neighborhood, select low-energy structurally distinct intermediates,
// then enumerate each selected intermediate's complete segment neighborhood.
// Capped beam is a construction experiment, NOT an exhaustive radius-two proof.
#define main segment_main_unused
#include "segment_move_exact.cpp"
#undef main
#include <unordered_map>
#include <vector>
#include <set>
struct Key {
 uint64_t lo,hi;
 bool operator==(Key const& x) const {return lo==x.lo&&hi==x.hi;}
};
struct Hash{
 size_t operator()(Key const& x) const {
  return x.lo*0x9e3779b97f4a7c15ULL^(x.hi*0xbf58476d1ce4e5b9ULL);
 }
};
Key key(U x){return {(uint64_t)x,(uint64_t)(x>>64)};}
struct Node{int e;U s;int type,i,j,k,flags;};
bool operator<(Node const&a,Node const&b){return a.e<b.e;}
U rev(U s){
 U out=0;for(int i=0;i<100;i++)if((s>>i)&1)out|=U(1)<<(99-i);return out;
}
U alt(U s){for(int i=1;i<100;i+=2)s^=U(1)<<i;return s;}
int main(int argc,char**argv){
 int beam=argc>1?stoi(argv[1]):32,threshold=argc>2?stoi(argv[2]):950;
 for(int k=1;k<100;k++)mask[k]=(U(1)<<(100-k))-1;
 U base=fromstr(inc),full=(U(1)<<100)-1;
 set<U> trivial;
 for(U v:{base,rev(base)})for(U w:{v,alt(v)}){
  trivial.insert(w);trivial.insert(w^full);
 }
 unordered_map<Key,Node,Hash> seen;seen.reserve(50000);
 auto add=[&](U s,int type,int i,int j,int k,int f){
  int e=E(s);
  if(e>threshold||trivial.count(s))return;
  Key q=key(s);
  if(seen.find(q)==seen.end())
    seen.emplace(q,Node{e,s,type,i,j,k,f});
 };
 auto begin=chrono::steady_clock::now();
 for(int i=0;i<100;i++)
  for(int j=i+2;j<=100;j++)
   for(int f=0;f<2;f++)add(reverse_segment(base,i,j,f),0,i,j,0,f);
 for(int i=0;i<100;i++)
  for(int j=i+1;j<100;j++)
   for(int k=j+1;k<=100;k++)
    for(int f=0;f<4;f++)
     add(swap_segment(base,i,j,k,f&1,f>>1),1,i,j,k,f);
 vector<Node> ordered;
 for(auto& kv:seen)ordered.push_back(kv.second);
 sort(ordered.begin(),ordered.end());
 vector<Node> seeds;
 for(auto const& node:ordered){
  bool diverse=true;
  for(auto const& prev:seeds)
   if(pc(prev.s^node.s)<16){diverse=false;break;}
  if(diverse)seeds.push_back(node);
  if((int)seeds.size()==beam)break;
 }
 cerr<<"STAGE1 uniqueLE"<<threshold<<"="<<seen.size()
     <<" best="<<(ordered.empty()?-1:ordered.front().e)
     <<" beam="<<seeds.size()<<"\n";
 int best=INT_MAX,distinctLE578=0;U winner=0;
 #pragma omp parallel for num_threads(4) schedule(dynamic,1)
 for(int u=0;u<(int)seeds.size();u++){
  auto n=seeds[u];
  int local=INT_MAX;U ls=0;long long low=0;
  auto probe=[&](U v){
   int e=E(v);
   if(trivial.count(v))return;
   if(e<=578)low++;
   if(e<local){local=e;ls=v;}
  };
  for(int i=0;i<100;i++)
   for(int j=i+2;j<=100;j++)
    for(int f=0;f<2;f++)probe(reverse_segment(n.s,i,j,f));
  for(int i=0;i<100;i++)
   for(int j=i+1;j<100;j++)
    for(int k=j+1;k<=100;k++)
     for(int f=0;f<4;f++)
      probe(swap_segment(n.s,i,j,k,f&1,f>>1));
  #pragma omp critical
  {
   distinctLE578+=low;
   if(local<best){
    best=local;winner=ls;
    cerr<<"STAGE2_nontrivial from="<<n.e
        <<" rank="<<u<<" result="<<best
        <<" seq="<<fmt(winner)<<"\n";
   }
  }
 }
 cout<<"SUMMARY candidates1="<<seen.size()
     <<" beam="<<seeds.size()
     <<" best2Nontrivial="<<best
     <<" witnessNontrivialLE578="<<distinctLE578
     <<" ms="<<chrono::duration_cast<chrono::milliseconds>(
        chrono::steady_clock::now()-begin).count()
     <<" seq="<<fmt(winner)<<"\n";
}
