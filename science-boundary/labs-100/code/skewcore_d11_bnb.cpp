// Exact E<=574 target feasibility in odd-perfect d=11 (11-bit boundary + skew89 core) classes.
// Normalize s0=s1=+1 and write u_j=s_{2j+1}, v_j=s_{2j+2}. A skew89 suffix
// on positions 11..99 is centered at 55, giving u_{54-j}=u_j and
// v_{53-j}=-v_j. Odd-perfectness becomes a width-5 finite-state recurrence.
// We enumerate legal recurrence states and use a rigorous fixed-product lower
// bound for the 49 even autocorrelations. Since odd energy is exactly 50,
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
static void asn(State&st,int p,int val){if(st.used[p]){if(st.s[p]!=val)std::abort();return;}for(int j=0;j<100;j++)if(st.used[j]){int k=std::abs(p-j);if(k&&!(k&1)){st.fixed[k]+=val*int(st.s[j]);st.count[k]++;}}st.s[p]=int8_t(val);st.used[p]=1;}
static void unasn(State&st,int p){int val=st.s[p];st.used[p]=0;for(int j=0;j<100;j++)if(st.used[j]){int k=std::abs(p-j);if(k&&!(k&1)){st.fixed[k]-=val*int(st.s[j]);st.count[k]--;}}st.s[p]=0;}
static long long lb(const State&st,int cap){long long z=0;for(int k=2;k<100;k+=2){int unk=(100-k)-st.count[k],m=std::max(0,std::abs(st.fixed[k])-unk);z+=1LL*m*m;if(z>cap)return z;}return z;}
static long long ev(const State&st){long long z=0;for(int k=2;k<100;k+=2)z+=1LL*st.fixed[k]*st.fixed[k];return z;}
static std::string fmt(const State&st){std::string z;for(int i=0;i<100;i++)z+=st.s[i]>0?'+':'-';return z;}
static long long exact(const std::string&z,long long&o){std::array<int,100>s{};for(int i=0;i<100;i++)s[i]=z[i]=='+'?1:-1;long long e=0;o=0;for(int k=1;k<100;k++){int c=0;for(int i=0;i<100-k;i++)c+=s[i]*s[i+k];long long q=1LL*c*c;e+=q;if(k&1)o+=q;}return e;}
struct Ch{std::array<int,4>p{};int n=0;};
static Ch pair(State&st,int n,int un,int vn){Ch c;int pu=2*n+1,qu=2*(54-n)+1;asn(st,pu,un);c.p[c.n++]=pu;if(qu!=pu){asn(st,qu,un);c.p[c.n++]=qu;}int pv=2*n+2,qv=2*(53-n)+2;asn(st,pv,vn);c.p[c.n++]=pv;if(qv!=pv){asn(st,qv,-vn);c.p[c.n++]=qv;}st.u[n]=un;st.v[n]=vn;return c;}
static Ch center(State&st,int un){Ch c;asn(st,55,un);c.p[c.n++]=55;st.u[27]=un;st.v[27]=-st.v[26];return c;}
static void undo(State&st,const Ch&c){for(int i=c.n-1;i>=0;i--)unasn(st,c.p[i]);}
static bool legal(const State&st,int n,const std::array<int,9>&q,int un){std::array<int,11>b{};b[0]=b[1]=1;for(int i=0;i<9;i++)b[i+2]=q[i];constexpr int m=5,alpha=1,beta=-1;int j=n-m,x=0;for(int r=0;r<=m;r++)x+=b[2*r]*((j+r==n)?un:st.u[j+r]);for(int r=0;r<m;r++)x+=b[2*r+1]*st.v[j+r];if(!good(x))return false;if(n>=10){x=0;for(int r=0;r<=m;r++)x+=alpha*b[2*r]*((n-r==n)?un:st.u[n-r]);for(int r=0;r<m;r++)x+=beta*b[2*r+1]*st.v[n-r-1];if(!good(x))return false;}int t=10-n;if(t>=1&&t<=4){x=0;for(int r=0;r<=m-t;r++)x+=alpha*b[2*r]*((10-t-r==n)?un:st.u[10-t-r]);for(int r=0;r<m-t;r++)x+=beta*b[2*r+1]*st.v[10-t-r-1];if(!good(x))return false;}return true;}
static bool op(const State&st){for(int k=1;k<100;k+=2){int c=0;for(int i=0;i<100-k;i++)c+=int(st.s[i])*int(st.s[i+k]);if(!good(c))return false;}return true;}
struct Sh{std::atomic<unsigned long long>nodes{0},pruned{0},leaves{0};std::atomic<bool>found{false},timeout{false};std::string seq;long long even=1LL<<60;int cap=524;double seconds=0;std::chrono::steady_clock::time_point start;};
static void dfs(State&st,int n,const std::array<int,9>&q,Sh&sh){if(sh.found.load()||sh.timeout.load())return;auto nn=sh.nodes.fetch_add(1)+1;if((nn&0x3ffff)==0&&sh.seconds>0&&std::chrono::duration<double>(std::chrono::steady_clock::now()-sh.start).count()>=sh.seconds){sh.timeout.store(true);return;}if(lb(st,sh.cap)>sh.cap){sh.pruned.fetch_add(1);return;}if(n==28){if(!op(st))return;sh.leaves.fetch_add(1);long long e=ev(st);if(e<=sh.cap){
#pragma omp critical
{if(!sh.found.load()||e<sh.even){sh.even=e;sh.seq=fmt(st);sh.found.store(true);}}
}return;}for(int un:{-1,1})if(legal(st,n,q,un)){if(n==27){Ch c=center(st,un);dfs(st,28,q,sh);undo(st,c);}else for(int vn:{-1,1}){Ch c=pair(st,n,un,vn);dfs(st,n+1,q,sh);undo(st,c);if(sh.found.load()||sh.timeout.load())return;}}}
struct Task{State st;int n;};
static void gen(State&st,int n,int split,const std::array<int,9>&q,int cap,std::vector<Task>&out,unsigned long long&gp){if(lb(st,cap)>cap){gp++;return;}if(n==split){out.push_back({st,n});return;}for(int un:{-1,1})if(legal(st,n,q,un)){if(n==27){Ch c=center(st,un);gen(st,28,split,q,cap,out,gp);undo(st,c);}else for(int vn:{-1,1}){Ch c=pair(st,n,un,vn);gen(st,n+1,split,q,cap,out,gp);undo(st,c);}}}
int main(int argc,char**argv){std::array<int,9>q{-1,-1,1,1,-1,-1,1,1,-1};int cap=524,threads=4,split=12;double seconds=0;for(int i=1;i<argc;i++){std::string a=argv[i];auto need=[&](){if(i+1>=argc)throw std::runtime_error("missing");return std::string(argv[++i]);};if(a=="--bits"){auto x=need();if(x.size()!=9)return 2;for(int j=0;j<9;j++){if(x[j]!='+'&&x[j]!='-')return 2;q[j]=x[j]=='+'?1:-1;}}else if(a=="--cap")cap=std::stoi(need());else if(a=="--threads")threads=std::stoi(need());else if(a=="--split")split=std::stoi(need());else if(a=="--seconds")seconds=std::stod(need());else return 2;}
State base;asn(base,0,1);asn(base,1,1);for(int i=0;i<9;i++)asn(base,2+i,q[i]);for(int j=0;j<5;j++){base.u[j]=(j==0?1:q[2*j-1]);base.v[j]=q[2*j];}std::vector<Task>tasks;unsigned long long gp=0;gen(base,5,split,q,cap,tasks,gp);Sh sh;sh.cap=cap;sh.seconds=seconds;sh.pruned.store(gp);sh.start=std::chrono::steady_clock::now();std::atomic<unsigned long long>done{0};
#ifdef _OPENMP
omp_set_num_threads(threads);
#endif
#pragma omp parallel for schedule(dynamic,1)
for(size_t i=0;i<tasks.size();i++){if(sh.found.load()||sh.timeout.load())continue;State st=tasks[i].st;dfs(st,tasks[i].n,q,sh);done.fetch_add(1);}double wall=std::chrono::duration<double>(std::chrono::steady_clock::now()-sh.start).count();bool complete=!sh.timeout.load()&&!sh.found.load()&&done.load()==tasks.size();std::cout<<"RESULT bits=";for(int x:q)std::cout<<(x>0?'+':'-');std::cout<<" status="<<(sh.found.load()?"FOUND":(complete?"INFEASIBLE":"TIMEOUT"))<<" cap="<<cap<<" tasks_done="<<done.load()<<"/"<<tasks.size()<<" nodes="<<sh.nodes.load()<<" pruned="<<sh.pruned.load()<<" leaves="<<sh.leaves.load()<<" seconds="<<wall<<"\n";if(sh.found.load()){long long o=0,e=exact(sh.seq,o);std::cout<<"CERT total="<<e<<" odd="<<o<<" even="<<e-o<<" seq="<<sh.seq<<"\n";if(o!=50||e>cap+50)return 2;}return complete||sh.found.load()?0:1;}
