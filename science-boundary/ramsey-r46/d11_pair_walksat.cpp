// Reproducible heuristic search for a fixed d=11 A/B gluing.
//
// Input: two graph6 records A (11 vertices, R(3,6)) and B (24 vertices,
// R(4,5)), a 64-bit seed, steps/restart, and optional model path.
// Variables are the 264 A--B edges.  The objective is the exact number of
// violated mixed K4 / independent-6 clauses.  A zero objective is therefore a
// genuine 36-vertex Ramsey(4,6) certificate after adding the degree-11 anchor.
// Three restarts use different initial cross densities to avoid the dense-I6
// bias seen in a single WalkSAT lane.
#include <algorithm>
#include <chrono>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <numeric>
#include <random>
#include <string>
#include <utility>
#include <vector>
using namespace std;
struct Lit { int v; bool pos; };
static vector<uint64_t> decode_g6(const string& s) {
  int n = int((unsigned char)s[0]) - 63; vector<int> bits;
  for (size_t p=1;p<s.size();++p) { int z=int((unsigned char)s[p])-63; for(int k=5;k>=0;--k) bits.push_back((z>>k)&1); }
  vector<uint64_t> a(n); int p=0;
  for(int j=1;j<n;++j) for(int i=0;i<j;++i) { if(bits.at(p)) { a[i]|=1ULL<<j; a[j]|=1ULL<<i; } ++p; }
  return a;
}
static bool clique(const vector<uint64_t>& a,const vector<int>& C){for(size_t i=0;i<C.size();++i)for(size_t j=i+1;j<C.size();++j)if(!((a[C[i]]>>C[j])&1))return false;return true;}
static bool indep(const vector<uint64_t>& a,const vector<int>& C){for(size_t i=0;i<C.size();++i)for(size_t j=i+1;j<C.size();++j)if((a[C[i]]>>C[j])&1)return false;return true;}
static vector<vector<int>> subsets(const vector<uint64_t>& a,int k,bool edge){
  vector<vector<int>> out; vector<int> C(k); int n=a.size();
  function<void(int,int)> rec=[&](int s,int d){ if(d==k){if(edge?clique(a,C):indep(a,C))out.push_back(C);return;} for(int i=s;i<=n-(k-d);++i){C[d]=i;rec(i+1,d+1);} }; rec(0,0); return out;
}
int main(int argc,char**argv){
  if(argc<5){cerr<<"usage: d11_pair_walksat A_g6 B_g6 seed steps [model]\n";return 2;}
  string ag=argv[1],bg=argv[2]; uint64_t seed=stoull(argv[3]); int step_limit=stoi(argv[4]); string model_path=argc>5?argv[5]:"";
  auto A=decode_g6(ag),B=decode_g6(bg); if(A.size()!=11||B.size()!=24){cerr<<"bad orders\n";return 2;}
  const int NA=11,NB=24,N=264; auto V=[&](int a,int b){return a*NB+b;};
  auto btri=subsets(B,3,true), aedge=subsets(A,2,true), bedge=subsets(B,2,true);
  auto ai5=subsets(A,5,false), ai4=subsets(A,4,false), bnon=subsets(B,2,false);
  auto ai3=subsets(A,3,false), bi3=subsets(B,3,false), anon=subsets(A,2,false), bi4=subsets(B,4,false);
  vector<vector<Lit>> clauses; vector<int> type;
  auto add=[&](vector<Lit> c,int t){clauses.push_back(move(c));type.push_back(t);};
  for(int a=0;a<NA;++a)for(auto&bs:btri){vector<Lit>c;for(int b:bs)c.push_back({V(a,b),false});add(move(c),0);}
  for(auto&aa:aedge)for(auto&bb:bedge){vector<Lit>c;for(int a:aa)for(int b:bb)c.push_back({V(a,b),false});add(move(c),0);}
  for(auto&aa:ai5)for(int b=0;b<NB;++b){vector<Lit>c;for(int a:aa)c.push_back({V(a,b),true});add(move(c),1);}
  for(auto&aa:ai4)for(auto&bb:bnon){vector<Lit>c;for(int a:aa)for(int b:bb)c.push_back({V(a,b),true});add(move(c),1);}
  for(auto&aa:ai3)for(auto&bb:bi3){vector<Lit>c;for(int a:aa)for(int b:bb)c.push_back({V(a,b),true});add(move(c),1);}
  for(auto&aa:anon)for(auto&bb:bi4){vector<Lit>c;for(int a:aa)for(int b:bb)c.push_back({V(a,b),true});add(move(c),1);}
  vector<vector<pair<int,bool>>> occ(N); for(int ci=0;ci<(int)clauses.size();++ci)for(auto l:clauses[ci])occ[l.v].push_back({ci,l.pos});
  mt19937_64 rng(seed); int best=1e9,bk=0,bi=0,bcross=0; vector<char> bestx; long long total_steps=0; const double ps[3]={0.20,0.27,0.34};
  for(int restart=0;restart<3&&best>0;++restart){
    vector<char>x(N);bernoulli_distribution init(ps[restart]);for(auto&z:x)z=init(rng);
    vector<int> sat(clauses.size()),uns,pos(clauses.size(),-1);
    auto add_uns=[&](int c){if(pos[c]<0){pos[c]=uns.size();uns.push_back(c);}};
    auto del_uns=[&](int c){int p=pos[c];if(p>=0){int q=uns.back();uns[p]=q;pos[q]=p;uns.pop_back();pos[c]=-1;}};
    for(int c=0;c<(int)clauses.size();++c){for(auto l:clauses[c])sat[c]+=(x[l.v]==l.pos);if(!sat[c])add_uns(c);}
    for(int it=0;it<step_limit&&best>0;++it,++total_steps){
      if((int)uns.size()<best){best=uns.size();bk=bi=0;for(int c:uns)(type[c]?bi:bk)++;bcross=count(x.begin(),x.end(),char(1));bestx=x;}
      if(uns.empty())break;
      int ci=uns[rng()%uns.size()],chosen=-1,bscore=1e9; bool noise=(rng()%100)<15;
      if(noise) chosen=clauses[ci][rng()%clauses[ci].size()].v;
      else for(auto l0:clauses[ci]){int v=l0.v,br=0,mk=0;for(auto [cj,p]:occ[v]){bool old=(x[v]==p);if(old&&sat[cj]==1)++br;if(!old&&sat[cj]==0)++mk;}int score=br-mk;if(score<bscore||(score==bscore&&(rng()&1))){bscore=score;chosen=v;}}
      bool old=x[chosen];for(auto [cj,p]:occ[chosen]){bool os=(old==p),ns=(!old==p);int before=sat[cj];sat[cj]+=int(ns)-int(os);if(before==0&&sat[cj]>0)del_uns(cj);else if(before>0&&sat[cj]==0)add_uns(cj);}x[chosen]=!old;
    }
  }
  cout<<"{\"best\":"<<best<<",\"k4\":"<<bk<<",\"i6\":"<<bi<<",\"cross_edges\":"<<bcross<<",\"clauses\":"<<clauses.size()<<",\"steps\":"<<total_steps<<",\"seed\":"<<seed<<"}"<<'\n';
  if(best==0&&!model_path.empty()){ofstream f(model_path);f<<"s SATISFIABLE\n";f<<"v ";for(int i=0;i<N;++i)f<<(bestx[i]?i+1:-(i+1))<<' ';f<<"0\n";}
  return best==0?0:1;
}
