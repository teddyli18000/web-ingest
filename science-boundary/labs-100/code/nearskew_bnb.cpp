// Exact branch-and-bound feasibility search in the canonical N=100 near-skew
// manifold. Odd-lag energy is identically 50; by default the search asks
// whether the 49 even-lag correlations can have squared sum <=524 (E<=574).
//
// Free skew-tail coordinates are assigned from the outside in. At each node
// every even correlation C_k is decomposed into fixed and free products. The
// rigorous lower bound combines:
//   1. Prestwich fixed-product relaxation;
//   2. Prestwich cancellation/reinforcement pairs among free products;
//   3. Wiggenbrock C_k + C_{N-k} (mod 4) residues when the opposite lag is fixed;
//   4. exact near-skew residue C_k == 1-s_k (mod 4) when position k is fixed;
//   5. exact sum C_even=(a^2-100)/2 plus a convex interval relaxation;
//   6. class-level arithmetic from d_k=C_k/2 parity and energy mod 8.
//
// All added structure is used only to shrink a relaxation, never to remove a
// realizable completion. A complete traversal is therefore a proof for the
// requested sign-sum class.
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
#ifdef _OPENMP
#include <omp.h>
#endif

constexpr int N=100;
static const std::string INC="++++++--+++++-----++-++--+--++++++++++---+-++--++++-+--++----+--+-+-+-+-++---++---++-+-++-+-++--+-+-";
using S=std::array<int8_t,N>;
using A=std::array<uint8_t,N>;
using I=std::array<int,N>;

struct State{
 S s{};
 A used{};
 I fixed{},count{};
 // For even lag k, pair[k] counts triples (q-k,q,q+k) whose endpoints
 // are fixed and middle q is free. cancel[k] is the subset with opposite
 // endpoint signs, whose two free products cancel identically.
 I pair{},cancel{};
 int even_sum=0,even_count=0;
};
static int template_coord(int v){return INC[1+v]=='+'?1:-1;}

static void add_endpoint_pairs(State&st,int p,int val,int delta){
 // delta=+1 when p becomes fixed, -1 when p ceases to be fixed.
 for(int k=2;k<N;k+=2){
  if(p+2*k<N){int q=p+k,r=p+2*k;if(!st.used[q]&&st.used[r]){st.pair[k]+=delta;if(val!=st.s[r])st.cancel[k]+=delta;}}
  if(p-2*k>=0){int q=p-k,r=p-2*k;if(!st.used[q]&&st.used[r]){st.pair[k]+=delta;if(val!=st.s[r])st.cancel[k]+=delta;}}
 }
}
static void remove_middle_pairs_before_assign(State&st,int p){
 for(int k=2;k<N;k+=2)if(p-k>=0&&p+k<N&&st.used[p-k]&&st.used[p+k]){
  st.pair[k]--;if(st.s[p-k]!=st.s[p+k])st.cancel[k]--;
 }
}
static void add_middle_pairs_after_unassign(State&st,int p){
 for(int k=2;k<N;k+=2)if(p-k>=0&&p+k<N&&st.used[p-k]&&st.used[p+k]){
  st.pair[k]++;if(st.s[p-k]!=st.s[p+k])st.cancel[k]++;
 }
}

static void assign_pos(State&st,int p,int val){
 // Before p becomes fixed it may be the free middle of a cancellation or
 // reinforcement pair; those pairs disappear. Then p may become a fixed
 // endpoint of new pairs.
 remove_middle_pairs_before_assign(st,p);
 add_endpoint_pairs(st,p,val,+1);
 for(int j=0;j<N;j++)if(st.used[j]){int k=std::abs(p-j);if(k>0&&(k%2==0)){st.fixed[k]+=val*int(st.s[j]);st.count[k]++;}}
 st.s[p]=int8_t(val);st.used[p]=1;if((p&1)==0){st.even_sum+=val;st.even_count++;}
#ifndef NDEBUG
 for(int k=2;k<N;k+=2){int f=(N-k)-st.count[k];if(st.cancel[k]<0||st.pair[k]<st.cancel[k]||2*st.pair[k]>f){std::cerr<<"pair invariant failed assign k="<<k<<"\n";std::abort();}}
#endif
}
static void unassign_pos(State&st,int p){
 int val=st.s[p];
 // Remove pairs for which p is currently a fixed endpoint.
 add_endpoint_pairs(st,p,val,-1);
 st.used[p]=0;if((p&1)==0){st.even_sum-=val;st.even_count--;}
 for(int j=0;j<N;j++)if(st.used[j]){int k=std::abs(p-j);if(k>0&&(k%2==0)){st.fixed[k]-=val*int(st.s[j]);st.count[k]--;}}
 // Once p is free it may become the middle of a new pair.
 add_middle_pairs_after_unassign(st,p);
 st.s[p]=0;
#ifndef NDEBUG
 for(int k=2;k<N;k+=2){int f=(N-k)-st.count[k];if(st.cancel[k]<0||st.pair[k]<st.cancel[k]||2*st.pair[k]>f){std::cerr<<"pair invariant failed unassign k="<<k<<"\n";std::abort();}}
#endif
}
static void assign_coord(State&st,int v,int val){int p=1+v;assign_pos(st,p,val);if(v!=49){int q=99-v;int factor=(p&1)?-1:1;assign_pos(st,q,factor*val);}}
static void unassign_coord(State&st,int v){if(v!=49)unassign_pos(st,99-v);unassign_pos(st,1+v);}

static int mod4(int x){int r=x%4;return r<0?r+4:r;}
static int min_abs_residue(int lo,int hi,int residue){
 int first=lo+mod4(residue-lo);if(first>hi)return 1<<20;
 int last=first+4*((hi-first)/4);
 if(first<=0&&last>=0){if(residue==0)return 0;return 2;}
 return std::min(std::abs(first),std::abs(last));
}

static int effective_free(const State&st,int k){
 int f=(N-k)-st.count[k];
 return f-2*st.cancel[k];
}

static bool known_residue(const State&st,int k,int&residue){
 bool have=false;int r=0;
 auto merge=[&](int x){x=mod4(x);if(!have){have=true;r=x;}else if(r!=x){r=-1;}};
 // Specialized near-skew identity.
 if(st.used[k])merge(st.s[k]>0?0:2);
 // Wiggenbrock: C_k + C_{N-k} == N (mod 4).  When C_{N-k} is fixed,
 // this determines C_k modulo four. C_{N-k} has exactly k product terms.
 int kk=N-k;
 if(kk>0&&st.count[kk]==k)merge(N-st.fixed[kk]);
 // Prestwich reinforcement: if every free product belongs to a two-edge
 // cancellation/reinforcement pair, the free contribution has fixed residue.
 int f=(N-k)-st.count[k];
 if(f==2*st.pair[k]){
  int reinf=st.pair[k]-st.cancel[k];
  merge(st.fixed[k]+2*reinf);
 }
 if(r<0){residue=-1;return true;} // inconsistent residues => impossible node
 residue=r;return have;
}

static long long product_lower_bound(const State&st,int cap){
 long long lb=0;
 for(int k=2;k<N;k+=2){
  int u=effective_free(st,k),lo=st.fixed[k]-u,hi=st.fixed[k]+u,m,res=0;
  bool have=known_residue(st,k,res);
  if(have&&res<0)return cap+4LL;
  if(have)m=min_abs_residue(lo,hi,res);
  else{m=std::max(0,std::abs(st.fixed[k])-u);if(m&1)++m;}
  lb+=1LL*m*m;if(lb>cap)return lb;
 }
 return lb;
}

static bool sum_feasible(const State&st,int target){
 if(target==999)return true;int u=50-st.even_count,d=target-st.even_sum;return std::abs(d)<=u&&((d-u)%2==0);
}

// Convex interval relaxation subject to the exact sum of all even
// correlations. Cancellation pairs shrink each independent interval before
// this joint minimization; residue constraints are handled independently by
// product_lower_bound.
static long long coupled_lower_bound(const State&st,int asum,int cap){
 if(asum==999)return product_lower_bound(st,cap);
 const int target_y=(asum*asum-100)/4;
 std::array<int,49> lo{},hi{},y{};int n=0,sumlo=0,sumhi=0,cur=0;long long sq=0;
 for(int k=2;k<N;k+=2){int u=effective_free(st,k),f=st.fixed[k],l=(f-u)/2,h=(f+u)/2;lo[n]=l;hi[n]=h;int q=0;if(q<l)q=l;else if(q>h)q=h;y[n]=q;sumlo+=l;sumhi+=h;cur+=q;sq+=1LL*q*q;++n;}
 if(target_y<sumlo||target_y>sumhi)return 1LL<<50;
 while(cur<target_y){int best=-1,cost=std::numeric_limits<int>::max();for(int i=0;i<n;i++)if(y[i]<hi[i]){int z=2*y[i]+1;if(z<cost){cost=z;best=i;}}if(best<0)return 1LL<<50;sq+=cost;++y[best];++cur;if(4*sq>cap)return 4*sq;}
 while(cur>target_y){int best=-1,cost=std::numeric_limits<int>::max();for(int i=0;i<n;i++)if(y[i]>lo[i]){int z=-2*y[i]+1;if(z<cost){cost=z;best=i;}}if(best<0)return 1LL<<50;sq+=cost;--y[best];--cur;if(4*sq>cap)return 4*sq;}
 return 4*sq;
}

static long long balanced_sq(int n,int total){
 if(n==0)return total==0?0:(1LL<<50);
 int q=total/n,r=total%n;if(r<0){r+=n;--q;}
 return 1LL*(n-r)*q*q+1LL*r*(q+1)*(q+1);
}
static long long same_parity_sq(int n,int total,int parity){
 if(n==0)return total==0?0:(1LL<<50);
 int x=total-n*parity;if(x&1)return 1LL<<50;int z=x/2;
 return 4*balanced_sq(n,z)+4LL*parity*z+1LL*n*parity;
}
static long long class_arithmetic_lb(int asum,int cap){
 int m=(50-asum)/2;if(m<0||m>49)return cap+4LL;
 int target=(asum*asum-100)/4;
 long long qcap=cap/4;
 int R=(int)std::floor(std::sqrt((double)m*qcap));
 long long best=1LL<<50;
 for(int so=-R;so<=R;so++){
  long long v=same_parity_sq(m,so,1)+same_parity_sq(49-m,target-so,0);
  if(v<best)best=v;
 }
 return best==(1LL<<50)?cap+4LL:4*best;
}
static int effective_cap(int asum,int cap){
 if(asum==999)return cap;int m=(50-asum)/2;if(m<0||m>49)return -1;
 int residue=4*(m&1),rem=(cap-residue)%8;if(rem<0)rem+=8;return cap-rem;
}

static long long even_energy(const State&st){long long e=0;for(int k=2;k<N;k+=2)e+=1LL*st.fixed[k]*st.fixed[k];return e;}
static std::string fmt(const State&st){std::string z;z.reserve(N);for(int i=0;i<N;i++)z+=st.s[i]>0?'+':'-';return z;}
static long long exact(const std::string&z,long long&odd){std::array<int,N>s{};for(int i=0;i<N;i++)s[i]=z[i]=='+'?1:-1;long long e=0;odd=0;for(int k=1;k<N;k++){int c=0;for(int i=0;i<N-k;i++)c+=s[i]*s[i+k];long long q=1LL*c*c;e+=q;if(k&1)odd+=q;}return e;}

struct Shared{std::atomic<unsigned long long> nodes{0},prune_bound{0},prune_sum{0},leaves{0};std::atomic<bool> found{false},timeout{false};std::string seq;long long even=1LL<<60;std::chrono::steady_clock::time_point start;double seconds=0;int asum=999,cap=524;};

static void dfs(State&st,int v,Shared&sh){
 if(sh.found.load(std::memory_order_relaxed)||sh.timeout.load(std::memory_order_relaxed))return;
 auto n=sh.nodes.fetch_add(1,std::memory_order_relaxed)+1;
 if((n&0x3ffff)==0&&sh.seconds>0){double t=std::chrono::duration<double>(std::chrono::steady_clock::now()-sh.start).count();if(t>=sh.seconds){sh.timeout.store(true);return;}}
 if(!sum_feasible(st,sh.asum)){sh.prune_sum.fetch_add(1);return;}
 if(product_lower_bound(st,sh.cap)>sh.cap){sh.prune_bound.fetch_add(1);return;}
 if(sh.asum!=999&&coupled_lower_bound(st,sh.asum,sh.cap)>sh.cap){sh.prune_bound.fetch_add(1);return;}
 if(v==50){sh.leaves.fetch_add(1);long long ee=even_energy(st);if(ee<=sh.cap){
#pragma omp critical
 {if(!sh.found.load()||ee<sh.even){sh.even=ee;sh.seq=fmt(st);sh.found.store(true);}}
 }return;}
 int first=template_coord(v);assign_coord(st,v,first);dfs(st,v+1,sh);unassign_coord(st,v);
 if(sh.found.load(std::memory_order_relaxed)||sh.timeout.load(std::memory_order_relaxed))return;
 assign_coord(st,v,-first);dfs(st,v+1,sh);unassign_coord(st,v);
}

int main(int argc,char**argv){
 int threads=4,prefix=8,asum=999,rawcap=524;double seconds=120;
 for(int i=1;i<argc;i++){std::string a=argv[i];auto need=[&](){if(i+1>=argc)throw std::runtime_error("missing arg");return std::string(argv[++i]);};if(a=="--threads")threads=std::stoi(need());else if(a=="--prefix")prefix=std::stoi(need());else if(a=="--seconds")seconds=std::stod(need());else if(a=="--asum")asum=std::stoi(need());else if(a=="--cap")rawcap=std::stoi(need());else{std::cerr<<"bad arg\n";return 2;}}
 if(prefix<0||prefix>20||rawcap<0||(asum!=999&&(asum<-50||asum>50||(asum&1)))){std::cerr<<"bad parameters\n";return 2;}
#ifdef _OPENMP
 omp_set_num_threads(threads);
#endif
 if(template_coord(0)!=1){std::cerr<<"template normalization mismatch\n";return 2;}
 int cap=effective_cap(asum,rawcap);long long arith=(asum==999?0:class_arithmetic_lb(asum,cap));
 if(cap<0||arith>cap){std::cout<<"SUMMARY asum="<<asum<<" rawcap="<<rawcap<<" cap="<<cap<<" class_lb="<<arith<<" complete=1 found=0 timeout=0 tasks_done=0/0 nodes=0 prune_bound=0 prune_sum=0 leaves=0 seconds=0 arith_excluded=1\n";return 0;}
 State base;assign_pos(base,0,1);assign_coord(base,0,1);
 Shared sh;sh.start=std::chrono::steady_clock::now();sh.seconds=seconds;sh.asum=asum;sh.cap=cap;
 const unsigned long long tasks=1ULL<<prefix;std::atomic<unsigned long long>done{0};
#pragma omp parallel for schedule(dynamic,1)
 for(unsigned long long mask=0;mask<tasks;mask++){
  if(sh.found.load()||sh.timeout.load())continue;State st=base;bool ok=true;
  for(int j=0;j<prefix;j++){int v=1+j,t=template_coord(v),val=((mask>>j)&1)?-t:t;assign_coord(st,v,val);if(!sum_feasible(st,asum)||product_lower_bound(st,cap)>cap||(asum!=999&&coupled_lower_bound(st,asum,cap)>cap)){ok=false;break;}}
  if(ok)dfs(st,1+prefix,sh);done.fetch_add(1);
 }
 double wall=std::chrono::duration<double>(std::chrono::steady_clock::now()-sh.start).count();bool complete=!sh.timeout.load()&&!sh.found.load()&&done.load()==tasks;
 std::cout<<"SUMMARY asum="<<(asum==999?999:asum)<<" rawcap="<<rawcap<<" cap="<<cap<<" class_lb="<<arith<<" complete="<<complete<<" found="<<sh.found.load()<<" timeout="<<sh.timeout.load()<<" tasks_done="<<done.load()<<"/"<<tasks<<" nodes="<<sh.nodes.load()<<" prune_bound="<<sh.prune_bound.load()<<" prune_sum="<<sh.prune_sum.load()<<" leaves="<<sh.leaves.load()<<" seconds="<<wall<<" arith_excluded=0\n";
 if(sh.found.load()){long long odd=0,e=exact(sh.seq,odd);std::cout<<"FOUND energy="<<e<<" odd="<<odd<<" even="<<e-odd<<" seq="<<sh.seq<<"\n";if(e>cap+50||odd!=50)return 2;return 0;}
 return complete?0:1;
}
