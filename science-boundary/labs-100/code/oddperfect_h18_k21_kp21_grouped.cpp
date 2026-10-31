// Exact grouped Q exclusion for odd-perfect (18,0), K=21, kp=21,kc=0.
// Input: every compressed HIT emitted by oddperfect_h18_k21_compressed 21 0.
// There are only 30 zero-support orbits.  For each support, p affects the
// affine-invariant Q only through SG=sum G_j^2.  The fibre equation depends
// only on alpha (the four zero positions) and gamma, not on p signs.
// With H_j=NPAF_alpha(j)+NPAF_gamma(j), exact projection gives
//   2 Q = SG + SH, SH=sum H_j^2.
// Thus the conservative relaxation min_p SG + min_fibre SH <=114 is necessary
// for E<=570.  gamma global sign is safely quotiented here because c=0 and,
// independently, SH is unchanged by gamma->-gamma.
#include <bits/stdc++.h>
#include <omp.h>
using namespace std; static const int N=25; using A=array<int,N>; using Vec=array<int16_t,N>;
struct VH{size_t operator()(Vec const&v)const noexcept{uint64_t h=1469598103934665603ULL;for(auto x:v){h^=(uint16_t)(x+64);h*=1099511628211ULL;}return h;}};
Vec comm(const A&a,const A&g){Vec f{};auto add=[&](int e,int v){if(e>=0)f[e]+=v;else f[e+N]-=v;};for(int i=0;i<N;i++)if(a[i])for(int j=0;j<N;j++)if(g[j]){add(i-j,a[i]*g[j]);add(j-i,-g[j]*a[i]);}return f;}
vector<uint32_t> solve_gamma(const A&alpha){int fix=0;vector<int>v;for(int i=1;i<N;i++)v.push_back(i);int n1=12,n2=12;array<Vec,N>col{};for(int j=0;j<N;j++){A e{};e[j]=1;col[j]=comm(alpha,e);}unordered_map<Vec,vector<uint16_t>,VH>mp;mp.reserve(8192);for(uint32_t m=0;m<(1u<<n1);m++){Vec z=col[fix];for(int t=0;t<n1;t++){int s=(m>>t&1)?1:-1;for(int r=0;r<N;r++)z[r]+=s*col[v[t]][r];}mp[z].push_back((uint16_t)m);}vector<uint32_t>sol;sol.reserve(20000);for(uint32_t m=0;m<(1u<<n2);m++){Vec z{};for(int t=0;t<n2;t++){int s=(m>>t&1)?1:-1;for(int r=0;r<N;r++)z[r]+=s*col[v[n1+t]][r];}for(auto&x:z)x=-x;auto it=mp.find(z);if(it==mp.end())continue;for(uint16_t lm:it->second){uint32_t mask=1u;for(int t=0;t<n1;t++)if(lm>>t&1)mask|=1u<<v[t];for(int t=0;t<n2;t++)if(m>>t&1)mask|=1u<<v[n1+t];sol.push_back(mask);}}return sol;}
int npaf_alpha(const A&a,int r){int s=0;for(int i=0;i<N;i++){int j=i+r;if(j<N)s+=a[i]*a[j];else s-=a[i]*a[j-N];}return s;}
inline int npaf_bits(uint32_t x,int r){int n=N-r;uint32_t mn=(1u<<n)-1,mr=(1u<<r)-1;int non=n-2*__builtin_popcount((x^(x>>r))&mn);int wrap=r-2*__builtin_popcount(((x>>(N-r))^x)&mr);return non-wrap;}
int sg_of_p(const A&p){int s=0;for(int r=1;r<=12;r++){int g=0;for(int i=0;i<N;i++)g+=p[i]*p[(i+r)%N];s+=g*g;}return s;}
struct Group{uint32_t zmask=0;int minSG=1000000000,count=0;};
int main(int argc,char**argv){if(argc<2)return 2;ifstream f(argv[1]);string line;map<uint32_t,Group> gm;int hits=0;while(getline(f,line)){if(line.rfind("HIT ",0))continue;auto a=line.find("p=")+2,b=line.find("|c=");string ps=line.substr(a,b-a);replace(ps.begin(),ps.end(),',',' ');stringstream sp(ps);A p{};uint32_t z=0;for(int i=0;i<N;i++){sp>>p[i];if(!p[i])z|=1u<<i;}if(__builtin_popcount(z)!=4)abort();int sg=sg_of_p(p);auto &g=gm[z];g.zmask=z;g.count++;g.minSG=min(g.minSG,sg);hits++;}cout<<"KP21_GROUPS hits="<<hits<<" supports="<<gm.size()<<"\n";if(hits!=3933||gm.size()!=30)return 3;vector<Group>groups;for(auto &kv:gm)groups.push_back(kv.second);atomic<long long>alphas{0},half{0},qpass{0};atomic<int>minMargin{INT_MAX},minSHglobal{INT_MAX};
#pragma omp parallel for schedule(dynamic,1)
for(int gi=0;gi<(int)groups.size();gi++){auto G=groups[gi];vector<int>zpos;for(int i=0;i<N;i++)if(G.zmask>>i&1)zpos.push_back(i);long long lhalf=0,lpass=0;int lminSH=INT_MAX;for(int am=0;am<16;am++){A alpha{};for(int t=0;t<4;t++)alpha[zpos[t]]=(am>>t&1)?1:-1;alphas++;int ha[13]{};for(int r=1;r<=12;r++)ha[r]=npaf_alpha(alpha,r);auto sols=solve_gamma(alpha);lhalf+=sols.size();for(uint32_t x:sols){int sh=0;for(int r=1;r<=12;r++){int h=ha[r]+npaf_bits(x,r);sh+=h*h;}lminSH=min(lminSH,sh);if(G.minSG+sh<=114)lpass++;}}half+=lhalf;qpass+=lpass;int old=minSHglobal.load();while(lminSH<old&&!minSHglobal.compare_exchange_weak(old,lminSH)){}int marg=G.minSG+lminSH-114;old=minMargin.load();while(marg<old&&!minMargin.compare_exchange_weak(old,marg)){}
#pragma omp critical
cout<<"GROUP z="<<G.zmask<<" pcount="<<G.count<<" minSG="<<G.minSG<<" minSH="<<lminSH<<" margin="<<marg<<" halfgamma="<<lhalf<<" qpass="<<lpass<<"\n";}
cout<<"KP21_KP21_QSUMMARY supports="<<groups.size()<<" alphas="<<alphas<<" half_gamma_solutions="<<half<<" Q_feasible_halfgamma="<<qpass<<" minSH="<<minSHglobal<<" min_margin="<<minMargin<<"\n";if(alphas!=480||half!=149828||qpass!=0||minSHglobal!=50||minMargin!=26)return 4;cout<<"EXACT_EXCLUSION h18_K21_kp21_kc0_Ele570\n";}
