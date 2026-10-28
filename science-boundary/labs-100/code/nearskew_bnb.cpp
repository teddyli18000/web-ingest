// Exact branch-and-bound feasibility search for E<=574 in the canonical
// N=100 near-skew manifold.  Odd-lag energy is identically 50, so the search
// asks whether the 49 even-lag correlations can have squared sum <=524.
//
// Free skew-tail coordinates are assigned from the outside in.  At each node
// every even correlation C_k is decomposed into a fixed contribution f_k and
// u_k not-yet-fixed product terms.  Relaxing those u_k products independently
// gives the rigorous bound |C_k| >= max(0, |f_k|-u_k).
#include <algorithm>
#include <array>
#include <atomic>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <iostream>
#include <string>
#include <vector>
#ifdef _OPENMP
#include <omp.h>
#endif

constexpr int N=100;
using S=std::array<int8_t,N>;
using A=std::array<uint8_t,N>;
using I=std::array<int,N>;

struct State{
 S s{}; A used{}; I fixed{}, count{};
 int even_sum=0, even_count=0;
};

static void assign_pos(State&st,int p,int val){
 for(int j=0;j<N;j++)if(st.used[j]){int k=std::abs(p-j);if(k>0&&(k%2==0)){st.fixed[k]+=val*int(st.s[j]);st.count[k]++;}}
 st.s[p]=int8_t(val);st.used[p]=1;if((p&1)==0){st.even_sum+=val;st.even_count++;}
}
static void unassign_pos(State&st,int p){
 int val=st.s[p];st.used[p]=0;if((p&1)==0){st.even_sum-=val;st.even_count--;}
 for(int j=0;j<N;j++)if(st.used[j]){int k=std::abs(p-j);if(k>0&&(k%2==0)){st.fixed[k]-=val*int(st.s[j]);st.count[k]--;}}
 st.s[p]=0;
}
static void assign_coord(State&st,int v,int val){
 int p=1+v;assign_pos(st,p,val);
 if(v!=49){int q=99-v;int factor=(p&1)?-1:1;assign_pos(st,q,factor*val);}
}
static void unassign_coord(State&st,int v){
 if(v!=49)unassign_pos(st,99-v);unassign_pos(st,1+v);
}
static long long lower_bound(const State&st){
 long long lb=0;
 for(int k=2;k<N;k+=2){int L=N-k,u=L-st.count[k],m=std::max(0,std::abs(st.fixed[k])-u);lb+=1LL*m*m;if(lb>524)return lb;}
 return lb;
}
static long long even_energy(const State&st){long long e=0;for(int k=2;k<N;k+=2)e+=1LL*st.fixed[k]*st.fixed[k];return e;}
static bool sum_feasible(const State&st,int target){
 if(target==999)return true;int u=50-st.even_count,d=target-st.even_sum;return std::abs(d)<=u&&((d-u)&1)==0;
}
static std::string fmt(const State&st){std::string z;z.reserve(N);for(int i=0;i<N;i++)z+=st.s[i]>0?'+':'-';return z;}
static long long exact(const std::string&z,long long&odd){std::array<int,N>s{};for(int i=0;i<N;i++)s[i]=z[i]=='+'?1:-1;long long e=0;odd=0;for(int k=1;k<N;k++){int c=0;for(int i=0;i<N-k;i++)c+=s[i]*s[i+k];long long q=1LL*c*c;e+=q;if(k&1)odd+=q;}return e;}

struct Shared{
 std::atomic<unsigned long long> nodes{0},prune_bound{0},prune_sum{0},leaves{0};
 std::atomic<bool> found{false},timeout{false};
 std::string seq; long long even=1LL<<60;
 std::chrono::steady_clock::time_point start;double seconds=0;int asum=999;
};

static void dfs(State&st,int v,Shared&sh){
 if(sh.found.load(std::memory_order_relaxed)||sh.timeout.load(std::memory_order_relaxed))return;
 auto n=sh.nodes.fetch_add(1,std::memory_order_relaxed)+1;
 if((n&0x3ffff)==0&&sh.seconds>0){double t=std::chrono::duration<double>(std::chrono::steady_clock::now()-sh.start).count();if(t>=sh.seconds){sh.timeout.store(true);return;}}
 if(!sum_feasible(st,sh.asum)){sh.prune_sum.fetch_add(1);return;}
 if(lower_bound(st)>524){sh.prune_bound.fetch_add(1);return;}
 if(v==50){sh.leaves.fetch_add(1);long long ee=even_energy(st);if(ee<=524){
#pragma omp critical
 {if(!sh.found.load()||ee<sh.even){sh.even=ee;sh.seq=fmt(st);sh.found.store(true);}}
 }return;}
 assign_coord(st,v,1);dfs(st,v+1,sh);unassign_coord(st,v);
 if(sh.found.load(std::memory_order_relaxed)||sh.timeout.load(std::memory_order_relaxed))return;
 assign_coord(st,v,-1);dfs(st,v+1,sh);unassign_coord(st,v);
}

int main(int argc,char**argv){int threads=4,prefix=8,asum=999;double seconds=120;for(int i=1;i<argc;i++){std::string a=argv[i];auto need=[&](){return std::string(argv[++i]);};if(a=="--threads")threads=std::stoi(need());else if(a=="--prefix")prefix=std::stoi(need());else if(a=="--seconds")seconds=std::stod(need());else if(a=="--asum")asum=std::stoi(need());else{std::cerr<<"bad arg\n";return 2;}}
 if(prefix<0||prefix>20||asum!=999&&(asum<-20||asum>20||(asum&1))){std::cerr<<"bad parameters\n";return 2;}
#ifdef _OPENMP
 omp_set_num_threads(threads);
#endif
 // Fix s0=+1 and free coordinate v=0 to +1; global sign + alternation make
 // this symmetry normalization lossless inside the direct near-skew class.
 State base;assign_pos(base,0,1);assign_coord(base,0,1);
 Shared sh;sh.start=std::chrono::steady_clock::now();sh.seconds=seconds;sh.asum=asum;
 const unsigned long long tasks=1ULL<<prefix;std::atomic<unsigned long long>done{0};
#pragma omp parallel for schedule(dynamic,1)
 for(unsigned long long mask=0;mask<tasks;mask++){
  if(sh.found.load()||sh.timeout.load())continue;State st=base;bool ok=true;
  for(int j=0;j<prefix;j++){int v=1+j,val=((mask>>j)&1)?-1:1;assign_coord(st,v,val);if(!sum_feasible(st,asum)||lower_bound(st)>524){ok=false;break;}}
  if(ok)dfs(st,1+prefix,sh);done.fetch_add(1);
 }
 double wall=std::chrono::duration<double>(std::chrono::steady_clock::now()-sh.start).count();bool complete=!sh.timeout.load()&&!sh.found.load()&&done.load()==tasks;
 std::cout<<"SUMMARY asum="<<(asum==999?999:asum)<<" complete="<<complete<<" found="<<sh.found.load()<<" timeout="<<sh.timeout.load()<<" tasks_done="<<done.load()<<"/"<<tasks<<" nodes="<<sh.nodes.load()<<" prune_bound="<<sh.prune_bound.load()<<" prune_sum="<<sh.prune_sum.load()<<" leaves="<<sh.leaves.load()<<" seconds="<<wall<<"\n";
 if(sh.found.load()){long long odd=0,e=exact(sh.seq,odd);std::cout<<"FOUND energy="<<e<<" odd="<<odd<<" even="<<e-odd<<" seq="<<sh.seq<<"\n";if(e>574||odd!=50)return 2;return 0;}
 return complete?0:1;
}
