// Exact E<=574 feasibility for O=58 in the d=3 boundary + skew97-core family.
// Normalize s0=s1=+1. O=58 forces b2=+1. The 419,430,400 structural
// completions are searched implicitly with a rigorous even-correlation lower
// bound plus the parity-half-sum/defect-sign identity.
#include <algorithm>
#include <array>
#include <atomic>
#include <cmath>
#include <cstdint>
#include <iostream>
#include <vector>
#ifdef _OPENMP
#include <omp.h>
#endif
using S=std::array<int8_t,100>;using U=std::array<uint8_t,100>;using I=std::array<int,100>;
struct State{S s{};U used{};I corr{},count{};std::array<int,50>u{},v{};};
static inline void assign_pos(State&st,int p,int x){for(int j=(p&1);j<100;j+=2)if(st.used[j]){int k=std::abs(p-j);if(k){st.corr[k]+=x*int(st.s[j]);st.count[k]++;}}st.s[p]=x;st.used[p]=1;}
static inline void unassign_pos(State&st,int p){int x=st.s[p];st.used[p]=0;for(int j=(p&1);j<100;j+=2)if(st.used[j]){int k=std::abs(p-j);if(k){st.corr[k]-=x*int(st.s[j]);st.count[k]--;}}st.s[p]=0;}
static inline int pair_type(int a,int b){if((a==1&&b==-1)||(a==-1&&b==1))return 0;if((a==1&&b==3)||(a==3&&b==1))return 1;if((a==-1&&b==-3)||(a==-3&&b==-1))return -1;return 99;}
struct Changes{int p[4],n=0;};
static inline Changes apply_pair(State&st,int n,int un,int vn){Changes ch;int pu=2*n+1,qu=2*(50-n)+1,pv=2*n+2,qv=2*(49-n)+2;assign_pos(st,pu,un);ch.p[ch.n++]=pu;if(qu!=pu){assign_pos(st,qu,un);ch.p[ch.n++]=qu;}assign_pos(st,pv,vn);ch.p[ch.n++]=pv;if(qv!=pv){assign_pos(st,qv,-vn);ch.p[ch.n++]=qv;}st.u[n]=un;st.v[n]=vn;return ch;}
static inline void undo(State&st,const Changes&ch){for(int i=ch.n-1;i>=0;i--)unassign_pos(st,ch.p[i]);}
static inline long long lower_bound_even(const State&st){long long e=0;for(int k=2;k<100;k+=2){int unknown=(100-k)-st.count[k],m=std::max(0,std::abs(st.corr[k])-unknown);e+=1LL*m*m;if(e>516)return e;}return e;}
static inline long long exact_even(const State&st){long long e=0;for(int k=2;k<100;k+=2)e+=1LL*st.corr[k]*st.corr[k];return e;}
static inline bool odd_half_sum_possible(int n,int usum,int defect_sign){if(n==26)return true;int base=1+2*usum;int remaining_pairs=std::max(0,25-n);int lo=base-2*remaining_pairs-1,hi=base+2*remaining_pairs+1;auto ok=[&](int t){return lo<=t&&t<=hi;};if(defect_sign>0)return ok(2);if(defect_sign<0)return ok(-2);return ok(2)||ok(-2);}
struct Task{State st;int n=0,defect_sign=0,usum=0;};
static void generate(State&st,int n,int ds,int usum,int split,std::vector<Task>&out){if(lower_bound_even(st)>516||!odd_half_sum_possible(n,usum,ds))return;if(n==split){out.push_back({st,n,ds,usum});return;}for(int un:{-1,1}){int low=st.u[n-1]+st.v[n-1]+un;int high=n==1?un:(un+st.u[n-1]-st.v[n-1]);int t=pair_type(low,high);if(t==99||(t!=0&&ds!=0))continue;int nd=t?t:ds;if(n==25){st.u[25]=un;assign_pos(st,51,un);generate(st,26,nd,usum,split,out);unassign_pos(st,51);}else for(int vn:{-1,1}){auto ch=apply_pair(st,n,un,vn);generate(st,n+1,nd,usum+un,split,out);undo(st,ch);}}}
static void dfs(State&st,int n,int ds,int usum,std::atomic<bool>&found,std::atomic<unsigned long long>&nodes){if(found.load(std::memory_order_relaxed))return;nodes.fetch_add(1,std::memory_order_relaxed);if(lower_bound_even(st)>516||!odd_half_sum_possible(n,usum,ds))return;if(n==26){if(!ds)return;int bsum=1+2*usum+st.u[25];if(bsum!=2*ds)return;if(exact_even(st)<=516)found.store(true,std::memory_order_relaxed);return;}for(int un:{-1,1}){int low=st.u[n-1]+st.v[n-1]+un;int high=n==1?un:(un+st.u[n-1]-st.v[n-1]);int t=pair_type(low,high);if(t==99||(t!=0&&ds!=0))continue;int nd=t?t:ds;if(n==25){st.u[25]=un;assign_pos(st,51,un);dfs(st,26,nd,usum,found,nodes);unassign_pos(st,51);}else for(int vn:{-1,1}){auto ch=apply_pair(st,n,un,vn);dfs(st,n+1,nd,usum+un,found,nodes);undo(st,ch);if(found.load())return;}}}
int main(int argc,char**argv){int threads=4,split=9;for(int i=1;i<argc;i++){std::string a=argv[i];if(a=="--threads"&&i+1<argc)threads=std::stoi(argv[++i]);else if(a=="--split"&&i+1<argc)split=std::stoi(argv[++i]);else return 2;}State base;assign_pos(base,0,1);assign_pos(base,1,1);assign_pos(base,2,1);base.u[0]=base.v[0]=1;std::vector<Task>tasks;generate(base,1,0,0,split,tasks);std::atomic<bool>found{false};std::atomic<unsigned long long>nodes{0};
#ifdef _OPENMP
omp_set_num_threads(threads);
#endif
#pragma omp parallel for schedule(dynamic,1)
for(size_t i=0;i<tasks.size();i++){State st=tasks[i].st;dfs(st,tasks[i].n,tasks[i].defect_sign,tasks[i].usum,found,nodes);}std::cout<<"RESULT status="<<(found.load()?"FOUND":"INFEASIBLE")<<" target=574 odd=58 even_cap=516 tasks="<<tasks.size()<<" nodes="<<nodes.load()<<"\n";return found.load()?1:0;}
