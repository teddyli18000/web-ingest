// Exact target feasibility in the odd-perfect d=3, s2=-1 skew97 family.
//
// Normalize s0=s1=+1 using global sign and standard alternation. Let
// u_j=s_{2j+1}, v_j=s_{2j+2}.  Skew97 on positions 3..99 gives
// u_{50-r}=u_r and v_{49-r}=-v_r. Odd-perfectness reduces each mirrored
// transition r=1..24 to exactly three possibilities:
//
//   F  : u_{r+1}=-u_r, v_r=-u_r
//   S+ : u_{r+1}= u_r, v_r=+1
//   S- : u_{r+1}= u_r, v_r=-1
//
// plus the free sign u_1. Hence the complete normalized branch has 2*3^24
// states. Branching in increasing r assigns the sequence from both ends
// toward the center, allowing a rigorous Prestwich fixed-product lower bound
// on all even correlations. Odd-lag energy is exactly 50 by construction.
#include <algorithm>
#include <array>
#include <atomic>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>
#ifdef _OPENMP
#include <omp.h>
#endif

constexpr int N=100;
static const std::string TEMPLATE=
"++----------++++-+++++--++++-+++--++--++++++----++++-+--+-++-+-+--++--++-+++-+--++-+-+++-+--+-+-+-+-";
using S=std::array<int8_t,N>;
using A=std::array<uint8_t,N>;
using I=std::array<int,N>;

struct State{S s{};A used{};I fixed{},count{};};

static void assign_pos(State&st,int p,int val){
 for(int j=0;j<N;j++)if(st.used[j]){
  int k=std::abs(p-j);
  if(k>0&&(k%2==0)){st.fixed[k]+=val*int(st.s[j]);st.count[k]++;}
 }
 st.s[p]=int8_t(val);st.used[p]=1;
}
static void unassign_pos(State&st,int p){
 int val=st.s[p];st.used[p]=0;
 for(int j=0;j<N;j++)if(st.used[j]){
  int k=std::abs(p-j);
  if(k>0&&(k%2==0)){st.fixed[k]-=val*int(st.s[j]);st.count[k]--;}
 }
 st.s[p]=0;
}
static long long lower_bound(const State&st,int cap){
 long long lb=0;
 for(int k=2;k<N;k+=2){
  int L=N-k,u=L-st.count[k],m=std::max(0,std::abs(st.fixed[k])-u);
  if(m&1)++m;
  lb+=1LL*m*m;if(lb>cap)return lb;
 }
 return lb;
}
static long long complete_even(const State&st){long long e=0;for(int k=2;k<N;k+=2)e+=1LL*st.fixed[k]*st.fixed[k];return e;}
static std::string fmt(const State&st){std::string z;z.reserve(N);for(int i=0;i<N;i++)z+=st.s[i]>0?'+':'-';return z;}
static long long exact(const std::string&z,long long&odd){
 std::array<int,N>s{};for(int i=0;i<N;i++)s[i]=z[i]=='+'?1:-1;
 long long e=0;odd=0;for(int k=1;k<N;k++){int c=0;for(int i=0;i<N-k;i++)c+=s[i]*s[i+k];long long q=1LL*c*c;e+=q;if(k&1)odd+=q;}return e;
}
static bool family_check(const std::string&z){
 if(z.size()!=100||z[0]!='+'||z[1]!='+'||z[2]!='-')return false;
 std::array<int,N>s{};for(int i=0;i<N;i++)s[i]=z[i]=='+'?1:-1;
 // skew97 suffix centered at global position 51
 for(int p=3;p<=50;p++){
  int q=102-p,f=((51-p)&1)?-1:1;
  if(s[q]!=f*s[p])return false;
 }
 long long odd=0;return exact(z,odd)>=0&&odd==50;
}

struct Changes{std::array<int,4> p{};int n=0;};
static Changes apply_transition(State&st,int r,int choice,int&u){
 int next,v;
 if(choice==0){next=-u;v=-u;} // F
 else if(choice==1){next=u;v=1;} // S+
 else{next=u;v=-1;} // S-
 Changes ch;
 int pv=2*r+2,qv=100-2*r;
 assign_pos(st,pv,v);ch.p[ch.n++]=pv;
 if(qv!=pv){assign_pos(st,qv,-v);ch.p[ch.n++]=qv;}
 int pu=2*r+3,qu=99-2*r;
 assign_pos(st,pu,next);ch.p[ch.n++]=pu;
 if(qu!=pu){assign_pos(st,qu,next);ch.p[ch.n++]=qu;}
 u=next;return ch;
}
static void undo(State&st,const Changes&ch){for(int i=ch.n-1;i>=0;i--)unassign_pos(st,ch.p[i]);}

static int choice_match_score(int r,int u,int choice){
 int next=choice==0?-u:u,v=choice==0?-u:(choice==1?1:-1),score=0;
 int pv=2*r+2,qv=100-2*r,pu=2*r+3,qu=99-2*r;
 auto tv=[&](int p){return TEMPLATE[p]=='+'?1:-1;};
 score+=(v==tv(pv));score+=(-v==tv(qv));score+=(next==tv(pu));score+=(next==tv(qu));return score;
}

struct Shared{
 std::atomic<unsigned long long> nodes{0},pruned{0},leaves{0};
 std::atomic<bool> found{false},timeout{false};
 std::string seq;long long even=1LL<<60;int cap=524;double seconds=0;
 std::chrono::steady_clock::time_point start;
};

static void dfs(State&st,int r,int u,Shared&sh){
 if(sh.found.load(std::memory_order_relaxed)||sh.timeout.load(std::memory_order_relaxed))return;
 auto n=sh.nodes.fetch_add(1,std::memory_order_relaxed)+1;
 if((n&0x3ffff)==0&&sh.seconds>0){double t=std::chrono::duration<double>(std::chrono::steady_clock::now()-sh.start).count();if(t>=sh.seconds){sh.timeout.store(true);return;}}
 if(lower_bound(st,sh.cap)>sh.cap){sh.pruned.fetch_add(1);return;}
 if(r==25){
  sh.leaves.fetch_add(1);long long ee=complete_even(st);
  if(ee<=sh.cap){
#pragma omp critical
   {if(!sh.found.load()||ee<sh.even){sh.even=ee;sh.seq=fmt(st);sh.found.store(true);}}
  }
  return;
 }
 std::array<int,3> ord{0,1,2};
 std::sort(ord.begin(),ord.end(),[&](int a,int b){return choice_match_score(r,u,a)>choice_match_score(r,u,b);});
 for(int choice:ord){
  int old=u;Changes ch=apply_transition(st,r,choice,u);dfs(st,r+1,u,sh);undo(st,ch);u=old;
  if(sh.found.load(std::memory_order_relaxed)||sh.timeout.load(std::memory_order_relaxed))return;
 }
}

static unsigned long long pow3(int n){unsigned long long x=1;while(n--)x*=3;return x;}

int main(int argc,char**argv){
 int threads=4,prefix=0,cap=524;double seconds=120;
 for(int i=1;i<argc;i++){
  std::string a=argv[i];auto need=[&](){if(i+1>=argc)throw std::runtime_error("missing arg");return std::string(argv[++i]);};
  if(a=="--threads")threads=std::stoi(need());else if(a=="--prefix")prefix=std::stoi(need());else if(a=="--cap")cap=std::stoi(need());else if(a=="--seconds")seconds=std::stod(need());else throw std::runtime_error("bad arg");
 }
 if(prefix<0||prefix>12||cap<0)return 2;
 if(!family_check(TEMPLATE)){std::cerr<<"template family check failed\n";return 2;}
 long long to=0,te=exact(TEMPLATE,to);if(te!=1162||to!=50){std::cerr<<"template score failure\n";return 2;}
#ifdef _OPENMP
 omp_set_num_threads(threads);
#endif
 Shared sh;sh.cap=cap;sh.seconds=seconds;sh.start=std::chrono::steady_clock::now();
 unsigned long long each=pow3(prefix),tasks=2*each;std::atomic<unsigned long long>done{0};
#pragma omp parallel for schedule(dynamic,1)
 for(unsigned long long task=0;task<tasks;task++){
  if(sh.found.load()||sh.timeout.load())continue;
  State st;assign_pos(st,0,1);assign_pos(st,1,1);assign_pos(st,2,-1);
  int u1=(task<each)?-1:1; // template root first
  assign_pos(st,3,u1);assign_pos(st,99,u1);int u=u1;
  unsigned long long code=task%each;bool ok=true;
  for(int j=0;j<prefix;j++){
   int choice=int(code%3);code/=3;Changes ch=apply_transition(st,1+j,choice,u);(void)ch;
   if(lower_bound(st,cap)>cap){ok=false;break;}
  }
  if(ok)dfs(st,1+prefix,u,sh);done.fetch_add(1);
 }
 double wall=std::chrono::duration<double>(std::chrono::steady_clock::now()-sh.start).count();
 bool complete=!sh.timeout.load()&&!sh.found.load()&&done.load()==tasks;
 std::cout<<"SUMMARY branch=d3-cminus cap="<<cap<<" prefix="<<prefix<<" complete="<<complete<<" found="<<sh.found.load()<<" timeout="<<sh.timeout.load()<<" tasks_done="<<done.load()<<"/"<<tasks<<" nodes="<<sh.nodes.load()<<" pruned="<<sh.pruned.load()<<" leaves="<<sh.leaves.load()<<" seconds="<<wall<<"\n";
 if(sh.found.load()){
  long long o=0,e=exact(sh.seq,o);std::cout<<"FOUND energy="<<e<<" odd="<<o<<" even="<<e-o<<" seq="<<sh.seq<<"\n";
  if(!family_check(sh.seq)||e>cap+50)return 2;
 }
 return complete||sh.found.load()?0:1;
}
