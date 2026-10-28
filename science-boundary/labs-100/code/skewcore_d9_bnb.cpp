// Exact E<=574 target feasibility in odd-perfect d=9 (9-bit boundary + skew91 core) classes.
// Normalize s0=s1=+1 and write u_j=s_{2j+1}, v_j=s_{2j+2}. A skew91 suffix
// on positions 9..99 is centered at 54, giving u_{53-j}=-u_j and
// v_{52-j}=v_j. Odd-perfectness is a width-4 finite-state recurrence.
// We enumerate only legal recurrence states and use a rigorous fixed-product
// lower bound for all 49 even autocorrelations. Odd energy is exactly 50, so
// even-energy cap 524 is equivalent to total LABS energy <=574.
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
using S=std::array<int8_t,100>;using U=std::array<uint8_t,100>;using I=std::array<int,100>;
static bool good(int x){return x==1||x==-1;}
struct State{S s{};U used{};I fixed{},count{};std::array<int,50>u{},v{};};
static void assign_pos(State&st,int p,int val){for(int j=0;j<100;j++)if(st.used[j]){int k=std::abs(p-j);if(k&&!(k&1)){st.fixed[k]+=val*int(st.s[j]);st.count[k]++;}}st.s[p]=int8_t(val);st.used[p]=1;}
static void unassign_pos(State&st,int p){int val=st.s[p];st.used[p]=0;for(int j=0;j<100;j++)if(st.used[j]){int k=std::abs(p-j);if(k&&!(k&1)){st.fixed[k]-=val*int(st.s[j]);st.count[k]--;}}st.s[p]=0;}
static long long lower_bound(const State&st,int cap){long long z=0;for(int k=2;k<100;k+=2){int unk=(100-k)-st.count[k];int m=std::max(0,std::abs(st.fixed[k])-unk);z+=1LL*m*m;if(z>cap)return z;}return z;}
static long long complete_even(const State&st){long long z=0;for(int k=2;k<100;k+=2)z+=1LL*st.fixed[k]*st.fixed[k];return z;}
static std::string fmt(const State&st){std::string z;z.reserve(100);for(int i=0;i<100;i++)z+=st.s[i]>0?'+':'-';return z;}
static long long exact(const std::string&z,long long&odd){std::array<int,100>s{};for(int i=0;i<100;i++)s[i]=z[i]=='+'?1:-1;long long e=0;odd=0;for(int k=1;k<100;k++){int c=0;for(int i=0;i<100-k;i++)c+=s[i]*s[i+k];long long q=1LL*c*c;e+=q;if(k&1)odd+=q;}return e;}
struct Ch{std::array<int,4>p{};int n=0;};
static Ch apply_pair(State&st,int n,int un,int vn){Ch ch;int pu=2*n+1,qu=2*(53-n)+1;assign_pos(st,pu,un);ch.p[ch.n++]=pu;if(qu!=pu){assign_pos(st,qu,-un);ch.p[ch.n++]=qu;}int pv=2*n+2,qv=2*(52-n)+2;assign_pos(st,pv,vn);ch.p[ch.n++]=pv;if(qv!=pv){assign_pos(st,qv,vn);ch.p[ch.n++]=qv;}st.u[n]=un;st.v[n]=vn;return ch;}
static void undo(State&st,const Ch&ch){for(int i=ch.n-1;i>=0;i--)unassign_pos(st,ch.p[i]);}
static bool legal_u(const State&st,int n,const std::array<int,7>&q,int un){std::array<int,9>b{};b[0]=b[1]=1;for(int i=0;i<7;i++)b[i+2]=q[i];int x=0,j=n-4;for(int r=0;r<=4;r++)x+=b[2*r]*((j+r==n)?un:st.u[j+r]);for(int r=0;r<4;r++)x+=b[2*r+1]*st.v[j+r];if(!good(x))return false;if(n>=8){x=0;for(int r=0;r<=4;r++)x+=-b[2*r]*((n-r==n)?un:st.u[n-r]);for(int r=0;r<4;r++)x+=b[2*r+1]*st.v[n-r-1];if(!good(x))return false;}int t=8-n;if(t>=1&&t<=3){x=0;for(int r=0;r<=4-t;r++)x+=-b[2*r]*((8-t-r==n)?un:st.u[8-t-r]);for(int r=0;r<4-t;r++)x+=b[2*r+1]*st.v[8-t-r-1];if(!good(x))return false;}return true;}
static bool oddperfect(const State&st){for(int k=1;k<100;k+=2){int c=0;for(int i=0;i<100-k;i++)c+=int(st.s[i])*int(st.s[i+k]);if(!good(c))return false;}return true;}
struct Shared{std::atomic<unsigned long long>nodes{0},pruned{0},leaves{0};std::atomic<bool>found{false},timeout{false};std::string seq;long long even=1LL<<60;int cap=524;double seconds=0;std::chrono::steady_clock::time_point start;};
static void dfs(State&st,int n,const std::array<int,7>&q,Shared&sh){if(sh.found.load()||sh.timeout.load())return;auto nn=sh.nodes.fetch_add(1)+1;if((nn&0x3ffff)==0&&sh.seconds>0){double t=std::chrono::duration<double>(std::chrono::steady_clock::now()-sh.start).count();if(t>=sh.seconds){sh.timeout.store(true);return;}}if(lower_bound(st,sh.cap)>sh.cap){sh.pruned.fetch_add(1);return;}if(n==27){if(!oddperfect(st))return;sh.leaves.fetch_add(1);long long ev=complete_even(st);if(ev<=sh.cap){
#pragma omp critical
{if(!sh.found.load()||ev<sh.even){sh.even=ev;sh.seq=fmt(st);sh.found.store(true);}}
}return;}for(int un:{-1,1})if(legal_u(st,n,q,un))for(int vn:{-1,1}){Ch ch=apply_pair(st,n,un,vn);dfs(st,n+1,q,sh);undo(st,ch);if(sh.found.load()||sh.timeout.load())return;}}
struct Task{State st;int n;};
static void gen(State&st,int n,int split,const std::array<int,7>&q,int cap,std::vector<Task>&out,unsigned long long&gp){if(lower_bound(st,cap)>cap){gp++;return;}if(n==split){out.push_back({st,n});return;}for(int un:{-1,1})if(legal_u(st,n,q,un))for(int vn:{-1,1}){Ch ch=apply_pair(st,n,un,vn);gen(st,n+1,split,q,cap,out,gp);undo(st,ch);}}
int main(int argc,char**argv){std::array<int,7>q{-1,-1,-1,1,-1,-1,1};int cap=524,threads=4,split=11;double seconds=0;for(int i=1;i<argc;i++){std::string a=argv[i];auto need=[&](){if(i+1>=argc)throw std::runtime_error("missing");return std::string(argv[++i]);};if(a=="--bits"){std::string x=need();if(x.size()!=7)throw std::runtime_error("bits");for(int j=0;j<7;j++){if(x[j]!='+'&&x[j]!='-')throw std::runtime_error("bits");q[j]=x[j]=='+'?1:-1;}}else if(a=="--cap")cap=std::stoi(need());else if(a=="--threads")threads=std::stoi(need());else if(a=="--split")split=std::stoi(need());else if(a=="--seconds")seconds=std::stod(need());else throw std::runtime_error("arg");}
State base;assign_pos(base,0,1);assign_pos(base,1,1);for(int i=0;i<7;i++)assign_pos(base,2+i,q[i]);base.u[0]=1;base.v[0]=q[0];base.u[1]=q[1];base.v[1]=q[2];base.u[2]=q[3];base.v[2]=q[4];base.u[3]=q[5];base.v[3]=q[6];std::vector<Task>tasks;unsigned long long gp=0;gen(base,4,split,q,cap,tasks,gp);Shared sh;sh.cap=cap;sh.seconds=seconds;sh.pruned.store(gp);sh.start=std::chrono::steady_clock::now();std::atomic<unsigned long long>done{0};
#ifdef _OPENMP
omp_set_num_threads(threads);
#endif
#pragma omp parallel for schedule(dynamic,1)
for(size_t i=0;i<tasks.size();i++){if(sh.found.load()||sh.timeout.load())continue;State st=tasks[i].st;dfs(st,tasks[i].n,q,sh);done.fetch_add(1);}double wall=std::chrono::duration<double>(std::chrono::steady_clock::now()-sh.start).count();bool complete=!sh.timeout.load()&&!sh.found.load()&&done.load()==tasks.size();std::cout<<"RESULT bits=";for(int x:q)std::cout<<(x>0?'+':'-');std::cout<<" status="<<(sh.found.load()?"FOUND":(complete?"INFEASIBLE":"TIMEOUT"))<<" cap="<<cap<<" tasks_done="<<done.load()<<"/"<<tasks.size()<<" nodes="<<sh.nodes.load()<<" pruned="<<sh.pruned.load()<<" leaves="<<sh.leaves.load()<<" seconds="<<wall<<"\n";if(sh.found.load()){long long odd=0,e=exact(sh.seq,odd);std::cout<<"CERT total="<<e<<" odd="<<odd<<" even="<<e-odd<<" seq="<<sh.seq<<"\n";if(odd!=50||e>cap+50)return 2;}return complete||sh.found.load()?0:1;}
