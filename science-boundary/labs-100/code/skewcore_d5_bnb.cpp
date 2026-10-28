// Exact target feasibility for the odd-perfect d=5 skew95 family.
//
// Normalize s0=s1=+1. Let u_j=s_{2j+1}, v_j=s_{2j+2}. For a skew95
// suffix on positions 5..99 (center 52):
//   u_{51-j}=-u_j, j=2..25
//   v_{50-j}= v_j, j=2..24.
// With prefix (+,+,b2,b3,b4), every odd correlation k=2j+1<=95 is
//   b0*u_j + b1*v_j + b2*u_{j+1} + b3*v_{j+1} + b4*u_{j+2},
// and odd-perfectness requires this to be +/-1. Pairing each condition with
// its skew mirror yields a width-2 finite-state recurrence. This program
// enumerates that complete normalized family implicitly and applies a
// Prestwich fixed-product lower bound to the 49 even correlations. A cap of
// 524 is exactly the Few Shots E<=574 target because odd energy is 50.
#include <array>
#include <atomic>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>
#ifdef _OPENMP
#include <omp.h>
#endif

using S=std::array<int8_t,100>;
using U=std::array<uint8_t,100>;
using I=std::array<int,100>;
static bool good(int x){return x==1||x==-1;}

struct State{
 S s{}; U used{}; I fixed{},count{}; std::array<int,50> u{},v{};
};
static void assign_pos(State&st,int p,int val){
 for(int j=0;j<100;j++)if(st.used[j]){
  int k=std::abs(p-j);
  if(k>0 && (k%2==0)){st.fixed[k]+=val*int(st.s[j]);st.count[k]++;}
 }
 st.s[p]=int8_t(val); st.used[p]=1;
}
static void unassign_pos(State&st,int p){
 int val=st.s[p]; st.used[p]=0;
 for(int j=0;j<100;j++)if(st.used[j]){
  int k=std::abs(p-j);
  if(k>0 && (k%2==0)){st.fixed[k]-=val*int(st.s[j]);st.count[k]--;}
 }
 st.s[p]=0;
}
static long long lower_bound(const State&st,int cap){
 long long z=0;
 for(int k=2;k<100;k+=2){
  int unknown=(100-k)-st.count[k];
  int m=std::max(0,std::abs(st.fixed[k])-unknown);
  z+=1LL*m*m;
  if(z>cap)return z;
 }
 return z;
}
static long long complete_even(const State&st){
 long long z=0;for(int k=2;k<100;k+=2)z+=1LL*st.fixed[k]*st.fixed[k];return z;
}
static std::string fmt(const State&st){
 std::string z;z.reserve(100);for(int i=0;i<100;i++)z+=st.s[i]>0?'+':'-';return z;
}
static long long exact_total(const std::string&z,long long&odd){
 std::array<int,100>s{};for(int i=0;i<100;i++)s[i]=z[i]=='+'?1:-1;
 long long e=0;odd=0;
 for(int k=1;k<100;k++){int c=0;for(int i=0;i<100-k;i++)c+=s[i]*s[i+k];long long q=1LL*c*c;e+=q;if(k&1)odd+=q;}
 return e;
}

struct Changes{std::array<int,4> p{};int n=0;};
static Changes apply_pair(State&st,int n,int un,int vn){
 Changes ch;
 int pu=2*n+1,qu=104-pu;
 assign_pos(st,pu,un);ch.p[ch.n++]=pu;
 if(qu!=pu){assign_pos(st,qu,-un);ch.p[ch.n++]=qu;}
 int pv=2*n+2,qv=104-pv;
 assign_pos(st,pv,vn);ch.p[ch.n++]=pv;
 if(qv!=pv){assign_pos(st,qv,vn);ch.p[ch.n++]=qv;}
 st.u[n]=un;st.v[n]=vn;return ch;
}
static void undo(State&st,const Changes&ch){for(int i=ch.n-1;i>=0;i--)unassign_pos(st,ch.p[i]);}

static bool legal_u(const State&st,int n,int b2,int b3,int b4,int un){
 int direct=st.u[n-2]+st.v[n-2]+b2*st.u[n-1]+b3*st.v[n-1]+b4*un;
 if(!good(direct))return false;
 if(n>=4){
  int mirror=-un+st.v[n-1]-b2*st.u[n-1]+b3*st.v[n-2]-b4*st.u[n-2];
  if(!good(mirror))return false;
 }
 // k=97 uses only prefix positions 0..2.
 if(n==3){int t48=-un+st.v[2]-b2*st.u[2];if(!good(t48))return false;}
 return true;
}

struct Shared{
 std::atomic<unsigned long long> nodes{0},pruned{0},leaves{0};
 std::atomic<bool> found{false},timeout{false};
 std::string seq; long long even=1LL<<60; double seconds=0; int cap=524;
 std::chrono::steady_clock::time_point start;
};
static void dfs(State&st,int n,int b2,int b3,int b4,Shared&sh){
 if(sh.found.load(std::memory_order_relaxed)||sh.timeout.load(std::memory_order_relaxed))return;
 auto nn=sh.nodes.fetch_add(1,std::memory_order_relaxed)+1;
 if((nn&0x3ffff)==0 && sh.seconds>0){
  double t=std::chrono::duration<double>(std::chrono::steady_clock::now()-sh.start).count();
  if(t>=sh.seconds){sh.timeout.store(true);return;}
 }
 if(lower_bound(st,sh.cap)>sh.cap){sh.pruned.fetch_add(1,std::memory_order_relaxed);return;}
 if(n==26){
  // Central odd constraints k=49,51 after applying the skew reflection.
  int t24=st.u[24]+st.v[24]+(b2-b4)*st.u[25]+b3*st.v[25];
  int t25=(1-b2)*st.u[25]+st.v[25]+b3*st.v[24]-b4*st.u[24];
  if(!good(t24)||!good(t25))return;
  sh.leaves.fetch_add(1,std::memory_order_relaxed);
  long long ev=complete_even(st);
  if(ev<=sh.cap){
#pragma omp critical
   {if(!sh.found.load()||ev<sh.even){sh.even=ev;sh.seq=fmt(st);sh.found.store(true);}}
  }
  return;
 }
 for(int un:{-1,1})if(legal_u(st,n,b2,b3,b4,un)){
  for(int vn:{-1,1}){
   Changes ch=apply_pair(st,n,un,vn);dfs(st,n+1,b2,b3,b4,sh);undo(st,ch);
   if(sh.found.load(std::memory_order_relaxed)||sh.timeout.load(std::memory_order_relaxed))return;
  }
 }
}
struct Task{State st;int n;};
static void generate_tasks(State&st,int n,int split,int b2,int b3,int b4,int cap,std::vector<Task>&out,unsigned long long&pruned){
 if(lower_bound(st,cap)>cap){pruned++;return;}
 if(n==split){out.push_back({st,n});return;}
 for(int un:{-1,1})if(legal_u(st,n,b2,b3,b4,un))for(int vn:{-1,1}){
  Changes ch=apply_pair(st,n,un,vn);generate_tasks(st,n+1,split,b2,b3,b4,cap,out,pruned);undo(st,ch);
 }
}

int main(int argc,char**argv){
 int b2=-1,b3=-1,b4=1,cap=524,threads=4,split=9;double seconds=0;
 for(int i=1;i<argc;i++){
  std::string a=argv[i];auto need=[&](){if(i+1>=argc)throw std::runtime_error("missing arg");return std::string(argv[++i]);};
  if(a=="--b2")b2=std::stoi(need());else if(a=="--b3")b3=std::stoi(need());else if(a=="--b4")b4=std::stoi(need());
  else if(a=="--cap")cap=std::stoi(need());else if(a=="--seconds")seconds=std::stod(need());else if(a=="--threads")threads=std::stoi(need());
  else if(a=="--split")split=std::stoi(need());else throw std::runtime_error("bad arg");
 }
 if((std::abs(b2)!=1)||(std::abs(b3)!=1)||(std::abs(b4)!=1)||cap<0||split<2||split>20)return 2;
 State base;assign_pos(base,0,1);assign_pos(base,1,1);assign_pos(base,2,b2);assign_pos(base,3,b3);assign_pos(base,4,b4);
 base.u[0]=1;base.v[0]=b2;base.u[1]=b3;base.v[1]=b4;
 std::vector<Task>tasks;unsigned long long generation_pruned=0;
 generate_tasks(base,2,split,b2,b3,b4,cap,tasks,generation_pruned);
 Shared sh;sh.cap=cap;sh.seconds=seconds;sh.pruned.store(generation_pruned);sh.start=std::chrono::steady_clock::now();
#ifdef _OPENMP
 omp_set_num_threads(threads);
#endif
 std::atomic<unsigned long long> done{0};
#pragma omp parallel for schedule(dynamic,1)
 for(size_t i=0;i<tasks.size();i++){
  if(sh.found.load()||sh.timeout.load())continue;
  State st=tasks[i].st;dfs(st,tasks[i].n,b2,b3,b4,sh);done.fetch_add(1);
 }
 double wall=std::chrono::duration<double>(std::chrono::steady_clock::now()-sh.start).count();
 bool complete=!sh.timeout.load()&&!sh.found.load()&&done.load()==tasks.size();
 const char* status=sh.found.load()?"FOUND":(complete?"INFEASIBLE":"TIMEOUT");
 std::cout<<"RESULT branch="<<b2<<","<<b3<<","<<b4<<" status="<<status<<" cap="<<cap
          <<" tasks_done="<<done.load()<<"/"<<tasks.size()<<" nodes="<<sh.nodes.load()<<" pruned="<<sh.pruned.load()
          <<" leaves="<<sh.leaves.load()<<" seconds="<<wall<<"\n";
 if(sh.found.load()){
  long long odd=0,tot=exact_total(sh.seq,odd);
  std::cout<<"CERT even="<<sh.even<<" total="<<tot<<" odd="<<odd<<" seq="<<sh.seq<<"\n";
  if(odd!=50||tot!=sh.even+50||tot>cap+50)return 2;
 }
 return (complete||sh.found.load())?0:1;
}
