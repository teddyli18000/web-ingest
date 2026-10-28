// Exact E<=574 target feasibility in odd-perfect d=13 (13-bit boundary + skew87 core) classes.
// Normalize s0=s1=+1 and write u_j=s_{2j+1}, v_j=s_{2j+2}. A skew87 suffix
// on positions 13..99 is centered at 56, giving u_{55-j}=-u_j and
// v_{54-j}=v_j. Odd-perfectness becomes a width-6 finite-state recurrence.
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
using S=std::array<int8_t,100>;using U=std::array<uint8_t,100>;using I=std::array<int,100>;static bool good(int x){return x==1||x==-1;}
struct St{S s{};U used{};I f{},cnt{};std::array<int,50>u{},v{};};
static void asn(St&st,int p,int x){if(st.used[p]){if(st.s[p]!=x)std::abort();return;}for(int j=0;j<100;j++)if(st.used[j]){int k=std::abs(p-j);if(k&&!(k&1)){st.f[k]+=x*int(st.s[j]);st.cnt[k]++;}}st.s[p]=int8_t(x);st.used[p]=1;}
static void unasn(St&st,int p){int x=st.s[p];st.used[p]=0;for(int j=0;j<100;j++)if(st.used[j]){int k=std::abs(p-j);if(k&&!(k&1)){st.f[k]-=x*int(st.s[j]);st.cnt[k]--;}}st.s[p]=0;}
static long long lb(const St&st,int cap){long long z=0;for(int k=2;k<100;k+=2){int u=(100-k)-st.cnt[k],m=std::max(0,std::abs(st.f[k])-u);z+=1LL*m*m;if(z>cap)return z;}return z;}
static long long ev(const St&st){long long z=0;for(int k=2;k<100;k+=2)z+=1LL*st.f[k]*st.f[k];return z;}
static bool op(const St&st){for(int k=1;k<100;k+=2){int c=0;for(int i=0;i<100-k;i++)c+=int(st.s[i])*int(st.s[i+k]);if(!good(c))return false;}return true;}
struct Ch{std::array<int,4>p{};int n=0;};
static Ch pair(St&st,int n,int un,int vn){Ch c;int pu=2*n+1,qu=2*(55-n)+1;asn(st,pu,un);c.p[c.n++]=pu;if(qu!=pu){asn(st,qu,-un);c.p[c.n++]=qu;}int pv=2*n+2,qv=2*(54-n)+2;asn(st,pv,vn);c.p[c.n++]=pv;if(qv!=pv){asn(st,qv,vn);c.p[c.n++]=qv;}st.u[n]=un;st.v[n]=vn;return c;}
static void undo(St&st,const Ch&c){for(int i=c.n-1;i>=0;i--)unasn(st,c.p[i]);}
static bool legal(const St&st,int n,const std::array<int,11>&q,int un){std::array<int,13>b{};b[0]=b[1]=1;for(int i=0;i<11;i++)b[i+2]=q[i];constexpr int m=6,alpha=-1,beta=1;int j=n-m,x=0;for(int r=0;r<=m;r++)x+=b[2*r]*((j+r==n)?un:st.u[j+r]);for(int r=0;r<m;r++)x+=b[2*r+1]*st.v[j+r];if(!good(x))return false;if(n>=12){x=0;for(int r=0;r<=m;r++)x+=alpha*b[2*r]*((n-r==n)?un:st.u[n-r]);for(int r=0;r<m;r++)x+=beta*b[2*r+1]*st.v[n-r-1];if(!good(x))return false;}int t=12-n;if(t>=1&&t<=5){x=0;for(int r=0;r<=m-t;r++)x+=alpha*b[2*r]*((12-t-r==n)?un:st.u[12-t-r]);for(int r=0;r<m-t;r++)x+=beta*b[2*r+1]*st.v[12-t-r-1];if(!good(x))return false;}return true;}
struct Sh{std::atomic<unsigned long long>nodes{0},pruned{0},leaves{0};std::atomic<bool>found{false},timeout{false};int cap=524;double seconds=0;std::chrono::steady_clock::time_point t;};
static void dfs(St&st,int n,const std::array<int,11>&q,Sh&sh){if(sh.found.load()||sh.timeout.load())return;auto nn=sh.nodes.fetch_add(1)+1;if((nn&0x3ffff)==0&&sh.seconds>0&&std::chrono::duration<double>(std::chrono::steady_clock::now()-sh.t).count()>=sh.seconds){sh.timeout.store(true);return;}if(lb(st,sh.cap)>sh.cap){sh.pruned++;return;}if(n==28){if(!op(st))return;sh.leaves++;if(ev(st)<=sh.cap)sh.found.store(true);return;}for(int un:{-1,1})if(legal(st,n,q,un))for(int vn:{-1,1}){auto c=pair(st,n,un,vn);dfs(st,n+1,q,sh);undo(st,c);if(sh.found.load()||sh.timeout.load())return;}}
struct Task{St st;int n;};
static void gen(St&st,int n,int split,const std::array<int,11>&q,int cap,std::vector<Task>&out,unsigned long long&gp){if(lb(st,cap)>cap){gp++;return;}if(n==split){out.push_back({st,n});return;}for(int un:{-1,1})if(legal(st,n,q,un))for(int vn:{-1,1}){auto c=pair(st,n,un,vn);gen(st,n+1,split,q,cap,out,gp);undo(st,c);}}
int main(int ac,char**av){std::array<int,11>q{-1,-1,1,1,-1,-1,1,1,-1,-1,1};int cap=524,threads=4,split=13;double seconds=0;for(int i=1;i<ac;i++){std::string a=av[i];auto need=[&](){if(i+1>=ac)throw std::runtime_error("missing");return std::string(av[++i]);};if(a=="--bits"){auto x=need();if(x.size()!=11)return 2;for(int j=0;j<11;j++){if(x[j]!='+'&&x[j]!='-')return 2;q[j]=x[j]=='+'?1:-1;}}else if(a=="--threads")threads=std::stoi(need());else if(a=="--split")split=std::stoi(need());else if(a=="--seconds")seconds=std::stod(need());else if(a=="--cap")cap=std::stoi(need());else return 2;}
St base;asn(base,0,1);asn(base,1,1);for(int i=0;i<11;i++)asn(base,2+i,q[i]);for(int j=0;j<6;j++){base.u[j]=(j==0?1:q[2*j-1]);base.v[j]=q[2*j];}std::vector<Task>tasks;unsigned long long gp=0;gen(base,6,split,q,cap,tasks,gp);Sh sh;sh.cap=cap;sh.seconds=seconds;sh.pruned.store(gp);sh.t=std::chrono::steady_clock::now();std::atomic<unsigned long long>done{0};
#ifdef _OPENMP
omp_set_num_threads(threads);
#endif
#pragma omp parallel for schedule(dynamic,1)
for(size_t i=0;i<tasks.size();i++){if(sh.found.load()||sh.timeout.load())continue;St st=tasks[i].st;dfs(st,tasks[i].n,q,sh);done++;}double sec=std::chrono::duration<double>(std::chrono::steady_clock::now()-sh.t).count();bool complete=!sh.found.load()&&!sh.timeout.load()&&done.load()==tasks.size();std::cout<<"RESULT bits=";for(int x:q)std::cout<<(x>0?'+':'-');std::cout<<" status="<<(sh.found.load()?"FOUND":(complete?"INFEASIBLE":"TIMEOUT"))<<" cap="<<cap<<" tasks_done="<<done.load()<<"/"<<tasks.size()<<" nodes="<<sh.nodes.load()<<" pruned="<<sh.pruned.load()<<" leaves="<<sh.leaves.load()<<" seconds="<<sec<<"\n";return complete||sh.found.load()?0:1;}
