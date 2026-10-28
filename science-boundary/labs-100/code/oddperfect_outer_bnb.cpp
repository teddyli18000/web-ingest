// Exact outer-in branch-and-bound for odd-perfect N=100 LABS target layers.
//
// Safe symmetry normalization:
//   * odd-perfect implies a*b=0 for parity-half sums A,B;
//   * use reversal to put the zero sum in B;
//   * multiply the even half by -1 if needed to make a=sum(A)>=0;
//   * multiply the odd half by -1 if needed to set B_0=s_1=+1.
// These are standard LABS symmetries.  A_0=s_0 MUST remain free when a>0.
//
// Search assigns positions from both ends toward the center.  At every partial
// state all odd correlations are tested for reachability of +/-1, while the
// even correlations use the standard fixed-product/unknown-product lower
// bound against the requested even-energy cap (524 for E<=574).  The exact
// even-correlation sum implied by the half sums is also enforced.
//
// Endpoint defect d=min(d_L,d_R): deleting s_0 or s_99 from an odd-perfect
// sequence leaves a length-99 sequence whose odd correlations are 0 or +/-2.
// d_L and d_R count the nonzero ones.  With b=0, d_L is always even, while
// d_R >= a/2 and d_R == a/2 (mod 2).  These facts are used as exact pruning.
#include <algorithm>
#include <array>
#include <atomic>
#include <chrono>
#include <cstdint>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>
#ifdef _OPENMP
#include <omp.h>
#endif

constexpr int N=100;
using S=std::array<int8_t,N>;
using U=std::array<uint8_t,N>;
using I=std::array<int,N>;

struct State{
 S s{}; U used{}; I fixed{},count{};
 int sumA=0,sumB=0,countA=0,countB=0;
};

static void assign_pos(State&st,int p,int val){
 for(int j=0;j<N;j++) if(st.used[j]){
  int k=std::abs(p-j); if(k){st.fixed[k]+=val*int(st.s[j]);st.count[k]++;}
 }
 st.s[p]=int8_t(val);st.used[p]=1;
 if((p&1)==0){st.sumA+=val;st.countA++;}else{st.sumB+=val;st.countB++;}
}
static void unassign_pos(State&st,int p){
 int val=st.s[p];
 if((p&1)==0){st.sumA-=val;st.countA--;}else{st.sumB-=val;st.countB--;}
 st.used[p]=0;
 for(int j=0;j<N;j++) if(st.used[j]){
  int k=std::abs(p-j); if(k){st.fixed[k]-=val*int(st.s[j]);st.count[k]--;}
 }
 st.s[p]=0;
}
static bool sum_feasible(int cur,int used,int target){
 int rem=50-used,need=target-cur;
 return std::abs(need)<=rem && ((need-rem)&1)==0;
}
static long long even_lb(const State&st,int cap){
 long long lb=0;
 for(int k=2;k<N;k+=2){
  int L=N-k,u=L-st.count[k],m=std::max(0,std::abs(st.fixed[k])-u);
  if(m&1)++m; // completed even correlations have even parity
  lb+=1LL*m*m;if(lb>cap)return lb;
 }
 return lb;
}
static bool even_sum_feasible(const State&st,int target){
 int lo=0,hi=0;
 for(int k=2;k<N;k+=2){int u=(N-k)-st.count[k];lo+=st.fixed[k]-u;hi+=st.fixed[k]+u;}
 return target>=lo && target<=hi && (((target-lo)&1)==0);
}
static bool odd_feasible(const State&st){
 for(int k=1;k<N;k+=2){
  int u=(N-k)-st.count[k],f=st.fixed[k];
  int need=std::min(std::abs(1-f),std::abs(-1-f));
  if(need>u)return false;
 }
 return true;
}
struct DefNow{int dl=0,dr=0,remain=0;};
static DefNow defect_now(const State&st){
 DefNow z;
 for(int k=1;k<=97;k+=2){
  int L=N-k;
  if(st.count[k]!=L){z.remain++;continue;}
  if(!st.used[0]||!st.used[k]||!st.used[99-k]||!st.used[99]){z.remain++;continue;}
  int c=st.fixed[k];
  z.dl+=(c!=int(st.s[0])*int(st.s[k]));
  z.dr+=(c!=int(st.s[99-k])*int(st.s[99]));
 }
 return z;
}
static bool defect_feasible(const State&st,int asum,int d){
 bool left_eq=(d%2==0); // final d_L is even
 int amin=asum/2;
 bool right_eq=(d>=amin && ((d-amin)&1)==0); // d_R parity/minimum
 if(!left_eq&&!right_eq)return false;
 DefNow z=defect_now(st);
 // Both final defect counts must be at least d.
 if(z.dl+z.remain<d||z.dr+z.remain<d)return false;
 // At least one side must finish exactly d.
 if(!left_eq&&z.dr>d)return false;
 if(!right_eq&&z.dl>d)return false;
 if(left_eq&&right_eq&&z.dl>d&&z.dr>d)return false;
 return true;
}
static bool prune(const State&st,int asum,int cap,int defect){
 if(!sum_feasible(st.sumA,st.countA,asum)||!sum_feasible(st.sumB,st.countB,0))return true;
 if(!odd_feasible(st))return true;
 int esum=(asum*asum-100)/2;
 if(!even_sum_feasible(st,esum))return true;
 if(even_lb(st,cap)>cap)return true;
 if(!defect_feasible(st,asum,defect))return true;
 return false;
}

static std::string fmt(const State&st){std::string z;z.reserve(N);for(int i=0;i<N;i++)z+=st.s[i]>0?'+':'-';return z;}
static long long exact(const std::string&z,long long&odd,int&a,int&b,int&dl,int&dr){
 std::array<int,N>s{},c{};for(int i=0;i<N;i++)s[i]=z[i]=='+'?1:-1;
 long long e=0;odd=0;
 for(int k=1;k<N;k++){int x=0;for(int i=0;i<N-k;i++)x+=s[i]*s[i+k];c[k]=x;long long q=1LL*x*x;e+=q;if(k&1)odd+=q;}
 a=b=0;for(int i=0;i<50;i++){a+=s[2*i];b+=s[2*i+1];}
 dl=dr=0;for(int k=1;k<=97;k+=2){dl+=(c[k]!=s[0]*s[k]);dr+=(c[k]!=s[99-k]*s[99]);}
 return e;
}

struct Shared{
 std::atomic<unsigned long long>nodes{0},pruned{0},leaves{0};
 std::atomic<bool>found{false},timeout{false};
 std::string seq;long long even=1LL<<60;int asum=0,cap=524,defect=1;double seconds=0;
 std::chrono::steady_clock::time_point start;
};
static void dfs(State&st,int p,Shared&sh){
 if(sh.found.load(std::memory_order_relaxed)||sh.timeout.load(std::memory_order_relaxed))return;
 auto n=sh.nodes.fetch_add(1,std::memory_order_relaxed)+1;
 if((n&0x3ffff)==0&&sh.seconds>0){
  double t=std::chrono::duration<double>(std::chrono::steady_clock::now()-sh.start).count();
  if(t>=sh.seconds){sh.timeout.store(true);return;}
 }
 if(prune(st,sh.asum,sh.cap,sh.defect)){sh.pruned.fetch_add(1);return;}
 if(p==50){
  sh.leaves.fetch_add(1);long long ee=0;for(int k=2;k<N;k+=2)ee+=1LL*st.fixed[k]*st.fixed[k];
  DefNow z=defect_now(st);
  if(st.sumA==sh.asum&&st.sumB==0&&ee<=sh.cap&&std::min(z.dl,z.dr)==sh.defect){
#pragma omp critical
   {if(!sh.found.load()||ee<sh.even){sh.even=ee;sh.seq=fmt(st);sh.found.store(true);}}
  }
  return;
 }
 std::array<int,2>pos{p,99-p};std::vector<int>todo;for(int q:pos)if(!st.used[q])todo.push_back(q);
 int combos=1<<todo.size();
 for(int mask=0;mask<combos;mask++){
  for(int j=0;j<(int)todo.size();j++)assign_pos(st,todo[j],(mask>>j&1)?1:-1);
  dfs(st,p+1,sh);
  for(int j=(int)todo.size()-1;j>=0;j--)unassign_pos(st,todo[j]);
  if(sh.found.load(std::memory_order_relaxed)||sh.timeout.load(std::memory_order_relaxed))return;
 }
}
static void gen_prefix(State&st,int p,int depth,int asum,int cap,int defect,std::vector<State>&out){
 if(prune(st,asum,cap,defect))return;
 if(p==depth){out.push_back(st);return;}
 std::array<int,2>pos{p,99-p};std::vector<int>todo;for(int q:pos)if(!st.used[q])todo.push_back(q);
 int combos=1<<todo.size();
 for(int mask=0;mask<combos;mask++){
  for(int j=0;j<(int)todo.size();j++)assign_pos(st,todo[j],(mask>>j&1)?1:-1);
  gen_prefix(st,p+1,depth,asum,cap,defect,out);
  for(int j=(int)todo.size()-1;j>=0;j--)unassign_pos(st,todo[j]);
 }
}

int main(int argc,char**argv){
 int asum=2,defect=1,cap=524,threads=4,prefix=7,shards=1,shard=0;double seconds=600;
 for(int i=1;i<argc;i++){
  std::string a=argv[i];auto need=[&](){if(i+1>=argc)throw std::runtime_error("missing argument");return std::string(argv[++i]);};
  if(a=="--asum")asum=std::stoi(need());else if(a=="--defect")defect=std::stoi(need());else if(a=="--cap")cap=std::stoi(need());else if(a=="--threads")threads=std::stoi(need());else if(a=="--prefix")prefix=std::stoi(need());else if(a=="--seconds")seconds=std::stod(need());else if(a=="--shards")shards=std::stoi(need());else if(a=="--shard")shard=std::stoi(need());else return 2;
 }
 if(asum<0||asum>20||(asum&1)||defect<0||defect>49||prefix<1||prefix>20||shards<1||shard<0||shard>=shards)return 2;
 // B_0=s_1=+1 is safe after using reversal to make b=0 and independent
 // parity-half sign symmetries to make a>=0 and B_0 positive.  A_0 is free.
 State base;assign_pos(base,1,1);
 std::vector<State>all;gen_prefix(base,0,prefix,asum,cap,defect,all);
 std::vector<State>tasks;for(size_t i=0;i<all.size();i++)if((int)(i%shards)==shard)tasks.push_back(all[i]);
#ifdef _OPENMP
 omp_set_num_threads(threads);
#endif
 Shared sh;sh.asum=asum;sh.defect=defect;sh.cap=cap;sh.seconds=seconds;sh.start=std::chrono::steady_clock::now();
 std::atomic<unsigned long long>done{0};
#pragma omp parallel for schedule(dynamic,1)
 for(size_t i=0;i<tasks.size();i++){
  if(sh.found.load()||sh.timeout.load())continue;
  State st=tasks[i];dfs(st,prefix,sh);done.fetch_add(1);
 }
 double wall=std::chrono::duration<double>(std::chrono::steady_clock::now()-sh.start).count();
 bool complete=!sh.timeout.load()&&!sh.found.load()&&done.load()==tasks.size();
 std::cout<<"SUMMARY asum="<<asum<<" defect="<<defect<<" cap="<<cap<<" prefix="<<prefix<<" shard="<<shard<<"/"<<shards<<" all_tasks="<<all.size()<<" complete="<<complete<<" found="<<sh.found.load()<<" timeout="<<sh.timeout.load()<<" tasks_done="<<done.load()<<"/"<<tasks.size()<<" nodes="<<sh.nodes.load()<<" pruned="<<sh.pruned.load()<<" leaves="<<sh.leaves.load()<<" seconds="<<wall<<"\n";
 if(sh.found.load()){
  long long o=0;int aa=0,b=0,dl=0,dr=0;long long e=exact(sh.seq,o,aa,b,dl,dr);
  std::cout<<"FOUND energy="<<e<<" odd="<<o<<" even="<<e-o<<" asum="<<aa<<" bsum="<<b<<" defL="<<dl<<" defR="<<dr<<" seq="<<sh.seq<<"\n";
  if(e>cap+50||o!=50||aa!=asum||b!=0||std::min(dl,dr)!=defect)return 2;
 }
 return complete||sh.found.load()?0:1;
}
