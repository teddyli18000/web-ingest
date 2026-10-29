// Exact endpoint-support solver for N=100 odd-perfect LABS target E<=574.
// Reflection-linearize a fixed deletion-support, quotient global+alternating
// symmetries in the coordinate gauge, reject most systems by forward Gaussian
// elimination modulo 257, RREF only the survivors, and enumerate nullspaces.
#include <algorithm>
#include <array>
#include <atomic>
#include <chrono>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <mutex>
#include <numeric>
#include <sstream>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>
#ifdef _OPENMP
#include <omp.h>
#endif
constexpr int N=100, MOD=257;
static inline int modn(int x){x%=MOD;if(x<0)x+=MOD;return x;}
static inline int mod257small(int x){if(x<0)x+=514;if(x>=514)x-=514;if(x>=257)x-=257;return x;}
static int modpow(int a,int e){int64_t r=1,b=modn(a);while(e){if(e&1)r=r*b%MOD;b=b*b%MOD;e>>=1;}return int(r);}
static std::string u128str(unsigned __int128 x){if(!x)return"0";std::string s;while(x){s.push_back(char('0'+x%10));x/=10;}std::reverse(s.begin(),s.end());return s;}

static std::vector<int> parse_support(const std::string&x,int d){
 std::vector<int>v;std::stringstream ss(x);std::string p;while(std::getline(ss,p,',')){int h=std::stoi(p);if(h<1||h>97||!(h&1))throw std::runtime_error("bad support");v.push_back(h);}std::sort(v.begin(),v.end());if((int)v.size()!=d||std::unique(v.begin(),v.end())!=v.end())throw std::runtime_error("bad support size");return v;
}
static void gen_supports_rec(int d,int start,std::vector<int>&cur,std::vector<std::vector<int>>&out){
 if((int)cur.size()==d){out.push_back(cur);return;}for(int h=start;h<=97;h+=2){cur.push_back(h);gen_supports_rec(d,h+2,cur,out);cur.pop_back();}
}
static std::vector<std::vector<int>> all_supports(int d){std::vector<std::vector<int>>o;std::vector<int>c;gen_supports_rec(d,1,c,o);return o;}
static std::array<int,49> reflection_pattern(const std::vector<int>&support){
 std::array<int,49>rho{};rho.fill(1);for(int h:support){if(h==49)rho[48]*=-1;else if(h<49){rho[h-1]*=-1;rho[h]*=-1;}else{rho[98-h]*=-1;rho[99-h]*=-1;}}return rho;
}
static std::pair<int,int> map_r_position(int p,const std::array<int,49>&rho){if(p<=49)return{p,1};int j=98-p,m=(((49-j)&1)?-1:1)*rho[j];return{j,m};}
struct QTerm{int a,b,c;};struct QEq{int lag;std::vector<QTerm>terms;};
static std::vector<QEq> make_qeq(const std::array<int,49>&lrho){
 std::array<int,99>rho{};rho.fill(1);for(int j=0;j<49;j++){rho[j]=lrho[j];rho[98-j]=lrho[j];}rho[49]=1;std::vector<QEq>out;out.reserve(49);
 for(int k=1;k<=97;k+=2){int q=(99-k)/2;QEq e{k,{}};e.terms.reserve(q);for(int i=0;i<q;i++){int j=2*q-1-i,d=rho[i]-rho[j];if(!d)continue;int c=(((49-i)&1)?-1:1)*(d/2);auto[a,ma]=map_r_position(i,lrho);auto[b,mb]=map_r_position(j,lrho);if(a>b)std::swap(a,b);e.terms.push_back({a,b,c*ma*mb});}out.push_back(std::move(e));}return out;
}
struct Eq{std::vector<int>a;int b=0;};
static std::vector<Eq> build_eqs(const std::vector<int>&support,const std::array<int,49>&rho,const std::vector<QEq>&qeq,const std::array<int,50>&uc,int endpoint,std::vector<int>&good){
 good.clear();for(int j=0;j<50;j++)if(!uc[j])good.push_back(j);std::array<int,50>idx{};idx.fill(-1);for(int i=0;i<(int)good.size();i++)idx[good[i]]=i;std::vector<Eq>eqs;eqs.reserve(49);
 for(const auto&q:qeq){Eq e;e.a.assign(good.size(),0);int constant=0;for(const auto&t:q.terms){bool ba=(t.a<49&&rho[t.a]==-1),bb=(t.b<49&&rho[t.b]==-1);if(ba==bb)throw std::runtime_error("cross invariant");int bad=ba?t.a:t.b,g=ba?t.b:t.a,c=t.c*uc[bad];if(uc[g])constant+=c*uc[g];else e.a[idx[g]]+=c;}if(std::binary_search(support.begin(),support.end(),q.lag)){int p=99-q.lag;auto[j,m]=map_r_position(p,rho);int c=m*endpoint;if(uc[j])constant+=c*uc[j];else e.a[idx[j]]+=c;}e.b=-constant;eqs.push_back(std::move(e));}
 return eqs;
}
static bool forward_consistent(const std::vector<Eq>&eqs,int n){
 int m=eqs.size();std::vector<std::vector<int>>a(m,std::vector<int>(n+1));for(int i=0;i<m;i++){for(int j=0;j<n;j++)a[i][j]=modn(eqs[i].a[j]);a[i][n]=modn(eqs[i].b);}int r=0;
 for(int c=0;c<n&&r<m;c++){int pr=-1;for(int i=r;i<m;i++)if(a[i][c]){pr=i;break;}if(pr<0)continue;if(pr!=r)std::swap(a[pr],a[r]);int inv=modpow(a[r][c],MOD-2);for(int j=c;j<=n;j++)a[r][j]=int((int64_t)a[r][j]*inv%MOD);for(int i=r+1;i<m;i++)if(a[i][c]){int f=a[i][c];for(int j=c;j<=n;j++)a[i][j]=modn(a[i][j]-int((int64_t)f*a[r][j]%MOD));}r++;}
 for(int i=r;i<m;i++){bool z=true;for(int j=0;j<n;j++)if(a[i][j]){z=false;break;}if(z&&a[i][n])return false;}return true;
}
struct Rref{bool ok=true;int n=0,rank=0;std::vector<std::vector<int>>m;std::vector<int>piv,freec;};
static Rref rref(const std::vector<Eq>&eqs,int n){
 int m=eqs.size();std::vector<std::vector<int>>a(m,std::vector<int>(n+1));for(int i=0;i<m;i++){for(int j=0;j<n;j++)a[i][j]=modn(eqs[i].a[j]);a[i][n]=modn(eqs[i].b);}int r=0;std::vector<int>p;
 for(int c=0;c<n&&r<m;c++){int pr=-1;for(int i=r;i<m;i++)if(a[i][c]){pr=i;break;}if(pr<0)continue;if(pr!=r)std::swap(a[pr],a[r]);int inv=modpow(a[r][c],MOD-2);for(int j=c;j<=n;j++)a[r][j]=int((int64_t)a[r][j]*inv%MOD);for(int i=0;i<m;i++)if(i!=r&&a[i][c]){int f=a[i][c];for(int j=c;j<=n;j++)a[i][j]=modn(a[i][j]-int((int64_t)f*a[r][j]%MOD));}p.push_back(c);r++;}
 for(int i=r;i<m;i++){bool z=true;for(int j=0;j<n;j++)if(a[i][j]){z=false;break;}if(z&&a[i][n])return{false,n,r,{},{},{}};}std::vector<char>isp(n);for(int c:p)isp[c]=1;std::vector<int>f;for(int c=0;c<n;c++)if(!isp[c])f.push_back(c);a.resize(r);return{true,n,r,std::move(a),std::move(p),std::move(f)};
}
struct SupportData{std::vector<int>support;std::array<int,49>rho;std::vector<int>bad;std::vector<QEq>qeq;};
struct Prepared{int si=0,endpoint=0,n=0,rank=0,f=0;std::array<int8_t,50>uc{};std::vector<uint8_t>good,piv,freec;std::vector<uint16_t>coeff,pv0;};
static Prepared prepare(int si,int endpoint,const std::array<int8_t,50>&uc8,const SupportData&d,bool&ok){
 std::array<int,50>uc{};for(int j=0;j<50;j++)uc[j]=uc8[j];std::vector<int>good;auto eqs=build_eqs(d.support,d.rho,d.qeq,uc,endpoint,good);
 for(const auto&e:eqs){int bound=std::abs(e.b);bool any=false;for(int x:e.a){bound+=std::abs(x);any|=x!=0;}if(bound>=MOD)throw std::runtime_error("MOD too small");if(!any&&e.b){ok=false;return{};}}
 if(!forward_consistent(eqs,good.size())){ok=false;return{};}auto rr=rref(eqs,good.size());ok=rr.ok;if(!ok)return{};Prepared p;p.si=si;p.endpoint=endpoint;p.uc=uc8;p.n=rr.n;p.rank=rr.rank;p.f=rr.freec.size();for(int x:good)p.good.push_back(x);for(int x:rr.piv)p.piv.push_back(x);for(int x:rr.freec)p.freec.push_back(x);p.coeff.resize(p.rank*p.f);p.pv0.resize(p.rank);
 for(int r=0;r<p.rank;r++){int v=rr.m[r][rr.n];for(int j=0;j<p.f;j++){int c=rr.m[r][rr.freec[j]];p.coeff[r*p.f+j]=c;v=modn(v+c);}p.pv0[r]=v;}return p;
}
static std::array<int,100> build_seq(const SupportData&d,const Prepared&p,const std::vector<int>&vals){
 std::array<int,50>u{};for(int j=0;j<50;j++)if(p.uc[j])u[j]=p.uc[j];for(int i=0;i<(int)p.good.size();i++)u[p.good[i]]=vals[i];std::array<int,100>s{};for(int j=0;j<49;j++){s[j]=u[j];int m=(((49-j)&1)?-1:1)*d.rho[j];s[98-j]=m*u[j];}s[49]=u[49];s[99]=p.endpoint;return s;
}
static long long fast_even(const std::array<int,100>&s,int cap){uint64_t A=0,B=0;for(int i=0;i<50;i++){if(s[2*i]>0)A|=1ULL<<i;if(s[2*i+1]>0)B|=1ULL<<i;}long long e=0;for(int r=1;r<50;r++){int len=50-r;uint64_t mask=(1ULL<<len)-1;int ca=len-2*__builtin_popcountll((A^(A>>r))&mask),cb=len-2*__builtin_popcountll((B^(B>>r))&mask),c=ca+cb;e+=1LL*c*c;if(e>cap)return e;}return e;}
static bool verify(const std::array<int,100>&s,const std::vector<int>&support,long long E){long long e=0,o=0;std::vector<int>rs;std::array<int,100>c{};for(int k=1;k<100;k++){int z=0;for(int i=0;i<100-k;i++)z+=s[i]*s[i+k];c[k]=z;e+=1LL*z*z;if(k&1)o+=1LL*z*z;}for(int k=1;k<=97;k+=2)if(c[k]!=s[99-k]*s[99])rs.push_back(k);return e==E&&o==50&&rs==support;}
static std::string fmt(const std::array<int,100>&s){std::string z;for(int x:s)z+=x>0?'+':'-';return z;}
struct Chunk{int pi;uint64_t lo,hi;};
static void run_chunk(const Prepared&p,const SupportData&d,uint64_t lo,uint64_t hi,std::atomic<bool>&found,std::string&foundseq,std::mutex&mu,std::atomic<uint64_t>&pm,std::atomic<uint64_t>&target){
 std::vector<int>fv(p.f,-1),pv(p.rank),vals(p.n,-1);uint64_t g=lo^(lo>>1);for(int r=0;r<p.rank;r++)pv[r]=p.pv0[r];for(int j=0;j<p.f;j++)if((g>>j)&1){fv[j]=1;for(int r=0;r<p.rank;r++)if(p.coeff[r*p.f+j])pv[r]=mod257small(pv[r]-2*int(p.coeff[r*p.f+j]));}auto ispm=[](int v){return v==1||v==MOD-1;};int bad=0;for(int x:pv)bad+=!ispm(x);
 auto test=[&](){if(bad||found.load(std::memory_order_relaxed))return;pm.fetch_add(1,std::memory_order_relaxed);for(int r=0;r<p.rank;r++)vals[p.piv[r]]=pv[r]==1?1:-1;for(int j=0;j<p.f;j++)vals[p.freec[j]]=fv[j];auto s=build_seq(d,p,vals);int A=0,B=0;for(int i=0;i<50;i++){A+=s[2*i];B+=s[2*i+1];}if(A*B!=0)return;int h=std::max(std::abs(A),std::abs(B));if(h>20||(h&1))return;int cap=(h%4==0)?524:520;target.fetch_add(1,std::memory_order_relaxed);long long ev=fast_even(s,cap);if(ev>cap)return;long long E=ev+50;if(!verify(s,d.support,E))throw std::runtime_error("verification mismatch");std::lock_guard<std::mutex>lk(mu);if(!found.load()){found=true;foundseq=fmt(s);std::cerr<<"FOUND E="<<E<<" A="<<A<<" B="<<B<<" seq="<<foundseq<<"\n";}};
 uint64_t pg=g;test();for(uint64_t i=lo+1;i<hi&&!found.load(std::memory_order_relaxed);i++){uint64_t ng=i^(i>>1),diff=ng^pg;int j=__builtin_ctzll(diff),delta=((ng>>j)&1)?2:-2;fv[j]=((ng>>j)&1)?1:-1;for(int r=0;r<p.rank;r++){int c=p.coeff[r*p.f+j];if(c){bool was=ispm(pv[r]);pv[r]=mod257small(pv[r]-c*delta);bool now=ispm(pv[r]);bad+=int(!now)-int(!was);}}pg=ng;test();}
}
int main(int argc,char**argv){
 int d=3,threads=0,start=0,end=1<<30;uint64_t chunk=1ULL<<18;bool profile=false;std::string one;for(int i=1;i<argc;i++){std::string a=argv[i];auto need=[&](){if(++i>=argc)throw std::runtime_error("missing arg");return std::string(argv[i]);};if(a=="--defect")d=std::stoi(need());else if(a=="--threads")threads=std::stoi(need());else if(a=="--start")start=std::stoi(need());else if(a=="--end")end=std::stoi(need());else if(a=="--chunk")chunk=std::stoull(need());else if(a=="--support")one=need();else if(a=="--profile")profile=true;else return 2;}if(d<1||d>4)return 2;auto supports=one.empty()?all_supports(d):std::vector<std::vector<int>>{parse_support(one,d)};start=std::max(0,start);end=std::min(end,(int)supports.size());if(start>=end)return 2;
#ifdef _OPENMP
 if(threads<=0)threads=omp_get_max_threads();omp_set_num_threads(threads);
#else
 threads=1;
#endif
 std::vector<SupportData>sd;sd.reserve(end-start);for(int oi=start;oi<end;oi++){SupportData x;x.support=supports[oi];x.rho=reflection_pattern(x.support);for(int j=0;j<49;j++)if(x.rho[j]<0)x.bad.push_back(j);x.qeq=make_qeq(x.rho);sd.push_back(std::move(x));}
 uint64_t systems=0,inconsistent=0;unsigned __int128 totalenum=0;int maxnull=0;std::vector<Prepared>prep;std::vector<Chunk>chunks;auto t0=std::chrono::steady_clock::now();
 for(int si=0;si<(int)sd.size();si++){auto&x=sd[si];int ref=-1;for(int b:x.bad)if(!(b&1)){ref=b;break;}bool evenref=ref>=0;if(!evenref)ref=x.bad[0];std::vector<int>other;for(int b:x.bad)if(b!=ref)other.push_back(b);int masks=1<<other.size();for(int mask=0;mask<masks;mask++){std::array<int8_t,50>uc{};uc[ref]=1;for(int j=0;j<(int)other.size();j++)uc[other[j]]=((mask>>j)&1)?1:-1;if(!evenref)uc[0]=1;int epn=evenref?1:2;for(int ei=0;ei<epn;ei++){int endpoint=evenref?1:(ei?1:-1);systems++;bool ok=false;auto p=prepare(si,endpoint,uc,x,ok);if(!ok){inconsistent++;continue;}maxnull=std::max(maxnull,p.f);uint64_t n=1ULL<<p.f;totalenum+=n;if(!profile){int pi=prep.size();prep.push_back(std::move(p));for(uint64_t z=0;z<n;z+=chunk)chunks.push_back({pi,z,std::min(n,z+chunk)});}}}}
 double prepsec=std::chrono::duration<double>(std::chrono::steady_clock::now()-t0).count();if(profile){std::cout<<"PROFILE defect="<<d<<" range="<<start<<":"<<end<<" supports="<<sd.size()<<" systems="<<systems<<" inconsistent="<<inconsistent<<" consistent="<<(systems-inconsistent)<<" enum="<<u128str(totalenum)<<" maxnull="<<maxnull<<" prep_seconds="<<prepsec<<"\n";return 0;}
 std::atomic<bool>found{false};std::atomic<uint64_t>done{0},pm{0},target{0};std::string foundseq;std::mutex mu;auto t1=std::chrono::steady_clock::now();
#pragma omp parallel for schedule(dynamic,1)
 for(size_t i=0;i<chunks.size();i++){if(found.load())continue;auto c=chunks[i];auto&p=prep[c.pi];run_chunk(p,sd[p.si],c.lo,c.hi,found,foundseq,mu,pm,target);done++;}
 double enumsec=std::chrono::duration<double>(std::chrono::steady_clock::now()-t1).count();bool complete=!found.load()&&done.load()==chunks.size();std::cout<<"SUMMARY defect="<<d<<" range="<<start<<":"<<end<<" supports="<<sd.size()<<" systems="<<systems<<" inconsistent="<<inconsistent<<" prepared="<<prep.size()<<" chunks="<<done.load()<<"/"<<chunks.size()<<" complete="<<complete<<" found="<<found.load()<<" enum="<<u128str(totalenum)<<" pm_candidates="<<pm.load()<<" target_checked="<<target.load()<<" maxnull="<<maxnull<<" prep_seconds="<<prepsec<<" enum_seconds="<<enumsec<<" threads="<<threads<<"\n";if(found.load())std::cout<<"FOUND_SEQ="<<foundseq<<"\n";return found.load()?0:(complete?0:1);
}
