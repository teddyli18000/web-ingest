// Parallel prize-guided large-neighborhood search for a 368-set in C7^5.
//
// The state is only an independent set Y outside a certified 315-point core C.
// Its completed independent set is Y union (C \ N_C(Y)), with exact score
//
//     315 + |Y| - |N_C(Y)|.
//
// Thus a target-368 witness is exactly prize |Y|-|N_C(Y)| >= 53.  A force-add
// move inserts one or two outside vertices and simultaneously evicts every
// currently selected outside conflict; all newly unblocked core vertices return
// implicitly.  This is a projected large neighborhood rather than ordinary
// one-vertex MIS search on the full graph.
//
// Input is produced by c7p5_core_prize_ls_export.py.  The search is heuristic;
// every reported target is independently replayed before writing it.

#include <algorithm>
#include <array>
#include <atomic>
#include <chrono>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <mutex>
#include <numeric>
#include <random>
#include <stdexcept>
#include <string>
#include <unordered_set>
#include <vector>
#ifdef _OPENMP
#include <omp.h>
#endif

namespace {
constexpr int Q=7,D=5,U=16807,CORE=315,TARGET=368,TARGET_PRIZE=TARGET-CORE;
constexpr int P7[D]={1,7,49,343,2401};

std::array<int,D> dec(int v){std::array<int,D>a{};for(int i=0;i<D;++i)a[i]=(v/P7[i])%Q;return a;}
int enc(const std::array<int,D>&a){int v=0;for(int i=0;i<D;++i)v+=a[i]*P7[i];return v;}
bool conflict5(int a,int b){if(a==b)return true;for(int i=0;i<D;++i){int x=(a/P7[i])%Q,y=(b/P7[i])%Q,z=(x-y+Q)%Q;if(z!=0&&z!=1&&z!=Q-1)return false;}return true;}

template<class F> void for_neigh(int v,F&&f){auto a=dec(v);std::array<int,D>d{};for(int code=0;code<243;++code){int t=code;bool zero=true;for(int i=0;i<D;++i){d[i]=t%3-1;t/=3;if(d[i])zero=false;}if(zero)continue;std::array<int,D>b{};for(int i=0;i<D;++i)b[i]=(a[i]+d[i]+Q)%Q;f(enc(b));}}

struct Input{std::vector<int>core;std::vector<std::vector<int>>seeds;};
Input load_input(const std::string&p){std::ifstream in(p);if(!in)throw std::runtime_error("input");int nc;in>>nc;if(nc!=CORE)throw std::runtime_error("core count");Input x;x.core.resize(nc);for(auto&v:x.core)in>>v;int ns;in>>ns;if(ns<=0)throw std::runtime_error("seed count");for(int s=0;s<ns;++s){int n;in>>n;if(n!=367)throw std::runtime_error("seed size");std::vector<int>a(n);for(auto&v:a)in>>v;x.seeds.push_back(std::move(a));}return x;}

struct Graph{
 std::array<int,U> coreIndex{},outIndex{};
 std::vector<int>outside;
 std::vector<std::vector<int>>adj;
 std::vector<std::vector<uint16_t>>support;
};
Graph build_graph(const std::vector<int>&core){Graph g;g.coreIndex.fill(-1);g.outIndex.fill(-1);for(int i=0;i<CORE;++i){int v=core[i];if(v<0||v>=U||g.coreIndex[v]>=0)throw std::runtime_error("core ids");g.coreIndex[v]=i;}for(int v=0;v<U;++v)if(g.coreIndex[v]<0){g.outIndex[v]=g.outside.size();g.outside.push_back(v);}g.adj.resize(g.outside.size());g.support.resize(g.outside.size());for(int i=0;i<(int)g.outside.size();++i){int v=g.outside[i];for_neigh(v,[&](int u){int c=g.coreIndex[u];if(c>=0)g.support[i].push_back((uint16_t)c);else {int j=g.outIndex[u];if(j>=0)g.adj[i].push_back(j);}});std::sort(g.adj[i].begin(),g.adj[i].end());std::sort(g.support[i].begin(),g.support[i].end());}return g;}

bool independent_ids(const std::vector<int>&S){std::unordered_set<int>q(S.begin(),S.end());if(q.size()!=S.size())return false;for(int v:S){bool bad=false;for_neigh(v,[&](int u){if(q.count(u))bad=true;});if(bad)return false;}return true;}

struct State{
 const Graph*g=nullptr;
 std::vector<uint8_t>in;
 std::vector<int>sel,pos;
 std::array<int,CORE>cnt{};
 int active=0,score=0;
 void clear(){std::fill(in.begin(),in.end(),0);sel.clear();std::fill(pos.begin(),pos.end(),-1);cnt.fill(0);active=score=0;}
 void add_raw(int v){if(in[v])throw std::runtime_error("add selected");in[v]=1;pos[v]=sel.size();sel.push_back(v);for(auto c:g->support[v])if(cnt[c]++==0)++active;++score;score-=0;}
 void remove_raw(int v){if(!in[v])throw std::runtime_error("remove missing");int p=pos[v],w=sel.back();sel[p]=w;pos[w]=p;sel.pop_back();pos[v]=-1;in[v]=0;for(auto c:g->support[v])if(--cnt[c]==0)--active;--score;}
 void recompute_score(){score=(int)sel.size()-active;}
};

struct Scratch{
 std::array<int16_t,CORE>d{};std::array<uint32_t,CORE>stamp{};uint32_t epoch=1;
 std::vector<uint32_t>rmstamp;uint32_t rmepoch=1;
 explicit Scratch(int n):rmstamp(n,0){}
 void next(){if(++epoch==0){stamp.fill(0);epoch=1;}}
 void nextrm(){if(++rmepoch==0){std::fill(rmstamp.begin(),rmstamp.end(),0);rmepoch=1;}}
};

void touch(Scratch&s,int c,int z,std::vector<int>&t){if(s.stamp[c]!=s.epoch){s.stamp[c]=s.epoch;s.d[c]=0;t.push_back(c);}s.d[c]+=z;}

struct Eval{int delta=-1000000;int a=-1,b=-1;std::vector<int>removed;};

Eval eval_insert(const State&st,int a,int b,Scratch&sc){Eval e;e.a=a;e.b=b;if(a<0||st.in[a]||(b>=0&&(st.in[b]||b==a)))return e;if(b>=0&&conflict5(st.g->outside[a],st.g->outside[b]))return e;sc.nextrm();std::vector<int>rm;rm.reserve(16);auto collect=[&](int v){for(int u:st.g->adj[v])if(st.in[u]&&sc.rmstamp[u]!=sc.rmepoch){sc.rmstamp[u]=sc.rmepoch;rm.push_back(u);}};collect(a);if(b>=0)collect(b);sc.next();std::vector<int>t;t.reserve(64);for(int u:rm)for(auto c:st.g->support[u])touch(sc,c,-1,t);for(auto c:st.g->support[a])touch(sc,c,+1,t);if(b>=0)for(auto c:st.g->support[b])touch(sc,c,+1,t);int db=0;for(int c:t){int before=st.cnt[c],after=before+sc.d[c];if(after<0)throw std::runtime_error("negative core count");db+=(after>0)-(before>0);}e.delta=(b>=0?2:1)-(int)rm.size()-db;e.removed=std::move(rm);return e;}

int eval_remove(const State&st,int u){if(u<0||!st.in[u])return -1000000;int freed=0;for(auto c:st.g->support[u])if(st.cnt[c]==1)++freed;return -1+freed;}

void apply_insert(State&st,const Eval&e){for(int u:e.removed)if(st.in[u])st.remove_raw(u);st.add_raw(e.a);if(e.b>=0)st.add_raw(e.b);st.recompute_score();}

void init_seed(State&st,const std::vector<int>&seed){st.clear();for(int id:seed){int v=st.g->outIndex[id];if(v>=0)st.add_raw(v);}st.recompute_score();if(st.score!=52)throw std::runtime_error("seed completion prize drift");}

std::vector<int> complete_ids(const State&st,const std::vector<int>&core){std::vector<int>out;out.reserve(CORE+st.sel.size());for(int u:st.sel)out.push_back(st.g->outside[u]);for(int c=0;c<CORE;++c)if(st.cnt[c]==0)out.push_back(core[c]);std::sort(out.begin(),out.end());return out;}

struct Shared{std::atomic<int>best{52};std::mutex mu;std::vector<int>bestIds;std::atomic<bool>found{false};};

void search_thread(int tid,const Graph&g,const Input&inp,double seconds,uint64_t baseSeed,Shared&sh){std::mt19937_64 rng(baseSeed+0x9e3779b97f4a7c15ULL*(tid+1));std::uniform_real_distribution<double>uni(0.0,1.0);State st;st.g=&g;st.in.assign(g.outside.size(),0);st.pos.assign(g.outside.size(),-1);Scratch sc(g.outside.size());std::vector<uint64_t>tabu(g.outside.size(),0);uint64_t iter=0,restarts=0,lastBestIter=0;int localBest=52;auto deadline=std::chrono::steady_clock::now()+std::chrono::duration<double>(seconds);auto reset=[&](){const auto&seed=inp.seeds[(tid+restarts)%inp.seeds.size()];init_seed(st,seed);std::fill(tabu.begin(),tabu.end(),0);localBest=std::max(localBest,st.score);lastBestIter=iter;++restarts;};reset();
 while(std::chrono::steady_clock::now()<deadline&&!sh.found.load(std::memory_order_relaxed)){
  ++iter;Eval best;int remBest=-1000000,remU=-1;const int SAMPLE=96;for(int k=0;k<SAMPLE;++k){int v=rng()%g.outside.size();if(st.in[v])continue;auto e=eval_insert(st,v,-1,sc);if(tabu[v]>iter&&st.score+e.delta<=localBest)continue;if(e.delta>best.delta||(e.delta==best.delta&&(rng()&1)))best=std::move(e);}for(int k=0;k<24&&!st.sel.empty();++k){int u=st.sel[rng()%st.sel.size()];int d=eval_remove(st,u);if(d>remBest){remBest=d;remU=u;}}
  if((iter&15)==0){for(int k=0;k<24;++k){int a=rng()%g.outside.size(),b=rng()%g.outside.size();if(a==b||st.in[a]||st.in[b])continue;auto e=eval_insert(st,a,b,sc);if((tabu[a]>iter||tabu[b]>iter)&&st.score+e.delta<=localBest)continue;if(e.delta>best.delta||(e.delta==best.delta&&(rng()&1)))best=std::move(e);}}
  bool did=false;if(remBest>best.delta&&remU>=0){bool accept=remBest>=0||(remBest==-1&&iter-lastBestIter>400&&uni(rng)<0.10);if(accept){st.remove_raw(remU);st.recompute_score();tabu[remU]=iter+7+(rng()%31);did=true;}}
  if(!did&&best.a>=0){bool accept=best.delta>=0||(best.delta==-1&&iter-lastBestIter>300&&uni(rng)<0.14)||(best.delta==-2&&iter-lastBestIter>1500&&uni(rng)<0.025);if(accept){for(int u:best.removed)tabu[u]=iter+11+(rng()%41);apply_insert(st,best);did=true;}}
  if(!did&&iter-lastBestIter>3000){int v=rng()%g.outside.size();if(!st.in[v]){auto e=eval_insert(st,v,-1,sc);if(e.a>=0&&e.delta>=-5){for(int u:e.removed)tabu[u]=iter+5+(rng()%23);apply_insert(st,e);did=true;}}}
  if(st.score>localBest){localBest=st.score;lastBestIter=iter;int old=sh.best.load();while(st.score>old&&!sh.best.compare_exchange_weak(old,st.score)){}if(st.score>=sh.best.load()){auto ids=complete_ids(st,inp.core);if((int)ids.size()!=CORE+st.score||!independent_ids(ids))throw std::runtime_error("best replay");std::lock_guard<std::mutex>lk(sh.mu);if((int)ids.size()>=CORE+sh.best.load())sh.bestIds=ids;}if(st.score>=TARGET_PRIZE){auto ids=complete_ids(st,inp.core);if(ids.size()>=TARGET&&independent_ids(ids)){std::lock_guard<std::mutex>lk(sh.mu);sh.bestIds=ids;sh.found.store(true);break;}}}
  if(iter-lastBestIter>50000)reset();
 }
 std::cerr<<"thread="<<tid<<" iterations="<<iter<<" restarts="<<restarts<<" local_best="<<localBest<<"\n";
}
}

int main(int argc,char**argv)try{
 if(argc<5){std::cerr<<"usage: c7p5_core_prize_ls INPUT OUT_IDS SECONDS THREADS [SEED]\n";return 2;}auto inp=load_input(argv[1]);double secs=std::stod(argv[3]);int threads=std::stoi(argv[4]);uint64_t seed=argc>5?std::stoull(argv[5]):2026103001ULL;if(secs<=0||threads<1)throw std::runtime_error("args");auto g=build_graph(inp.core);for(auto&s:inp.seeds)if(!independent_ids(s))throw std::runtime_error("input seed replay");Shared sh;sh.bestIds=inp.seeds.front();auto t0=std::chrono::steady_clock::now();
#ifdef _OPENMP
#pragma omp parallel num_threads(threads)
 {search_thread(omp_get_thread_num(),g,inp,secs,seed,sh);}
#else
 search_thread(0,g,inp,secs,seed,sh);
#endif
 auto elapsed=std::chrono::duration<double>(std::chrono::steady_clock::now()-t0).count();std::vector<int>best;{std::lock_guard<std::mutex>lk(sh.mu);best=sh.bestIds;}if(!independent_ids(best))throw std::runtime_error("final replay");std::ofstream out(argv[2]);for(int v:best)out<<v<<'\n';out.close();std::cout<<"{\"method\":\"parallel-core-prize-projected-ls\",\"found\":"<<(best.size()>=TARGET?"true":"false")<<",\"best_size\":"<<best.size()<<",\"best_prize\":"<<(int(best.size())-CORE)<<",\"threads\":"<<threads<<",\"elapsed_seconds\":"<<elapsed<<",\"outside_vertices\":"<<g.outside.size()<<",\"seed_count\":"<<inp.seeds.size()<<"}\n";return 0;
}catch(const std::exception&e){std::cerr<<"error: "<<e.what()<<"\n";return 1;}
