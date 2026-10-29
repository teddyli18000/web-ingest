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

constexpr int N=100;
constexpr int NV=51; // x_0..x_49, endpoint e=s_99
struct Term { int coeff; uint64_t mask; };
struct Equation { std::vector<Term> terms; };

static std::string u128str(unsigned __int128 x){ if(!x)return "0"; std::string s; while(x){s.push_back(char('0'+x%10));x/=10;} std::reverse(s.begin(),s.end()); return s; }
static std::vector<int> parse_support(const std::string&x,int d){
    std::vector<int>v;std::stringstream ss(x);std::string p;
    while(std::getline(ss,p,',')){int h=std::stoi(p);if(h<1||h>97||!(h&1))throw std::runtime_error("bad support");v.push_back(h);}std::sort(v.begin(),v.end());
    if((int)v.size()!=d||std::unique(v.begin(),v.end())!=v.end())throw std::runtime_error("bad support size");return v;
}
static void gen_rec(int d,int start,std::vector<int>&cur,std::vector<std::vector<int>>&out){
    if((int)cur.size()==d){out.push_back(cur);return;}for(int h=start;h<=97;h+=2){cur.push_back(h);gen_rec(d,h+2,cur,out);cur.pop_back();}
}
static std::vector<std::vector<int>> all_supports(int d){std::vector<std::vector<int>>o;std::vector<int>c;gen_rec(d,1,c,o);return o;}
static std::array<int,49> reflection_pattern(const std::vector<int>&support){
    std::array<int,49>rho{};rho.fill(1);for(int h:support){if(h==49)rho[48]*=-1;else if(h<49){rho[h-1]*=-1;rho[h]*=-1;}else{rho[98-h]*=-1;rho[99-h]*=-1;}}return rho;
}
static std::pair<int,int> map_r_position(int p,const std::array<int,49>&rho){if(p<=49)return{p,1};int j=98-p,m=(((49-j)&1)?-1:1)*rho[j];return{j,m};}
struct QTerm{int a,b,c;}; struct QEq{int lag;std::vector<QTerm>terms;};
static std::vector<QEq> make_qeq(const std::array<int,49>&lrho){
    std::array<int,99>rho{};rho.fill(1);for(int j=0;j<49;j++){rho[j]=lrho[j];rho[98-j]=lrho[j];}rho[49]=1;
    std::vector<QEq>out;out.reserve(49);
    for(int k=1;k<=97;k+=2){int q=(99-k)/2;std::vector<QTerm> raw;raw.reserve(q);
        for(int i=0;i<q;i++){int j=2*q-1-i,diff=rho[i]-rho[j];if(!diff)continue;int c=(((49-i)&1)?-1:1)*(diff/2);auto[a,ma]=map_r_position(i,lrho);auto[b,mb]=map_r_position(j,lrho);if(a>b)std::swap(a,b);raw.push_back({a,b,c*ma*mb});}
        std::sort(raw.begin(),raw.end(),[](auto&a,auto&b){return std::pair{a.a,a.b}<std::pair{b.a,b.b};});QEq e{k,{}};
        for(size_t i=0;i<raw.size();){size_t j=i;int c=0;while(j<raw.size()&&raw[j].a==raw[i].a&&raw[j].b==raw[i].b){c+=raw[j].c;j++;}if(c)e.terms.push_back({raw[i].a,raw[i].b,c});i=j;}out.push_back(std::move(e));
    }return out;
}
static std::vector<Equation> build_exact(const std::vector<int>&support,const std::array<int,49>&rho,bool addB0){
    auto qeq=make_qeq(rho);std::vector<Equation>eqs;eqs.reserve(50);
    for(auto&q:qeq){Equation e;for(auto&t:q.terms)e.terms.push_back({t.c,(1ULL<<t.a)|(1ULL<<t.b)});if(std::binary_search(support.begin(),support.end(),q.lag)){int p=99-q.lag;auto[j,m]=map_r_position(p,rho);e.terms.push_back({m,(1ULL<<j)|(1ULL<<50)});}eqs.push_back(std::move(e));}
    if(addB0){Equation e;for(int j=0;j<49;j++){int mult=(((49-j)&1)?-1:1)*rho[j];if(j&1)e.terms.push_back({1,1ULL<<j});if((98-j)&1)e.terms.push_back({mult,1ULL<<j});}e.terms.push_back({1,1ULL<<49});e.terms.push_back({1,1ULL<<50});eqs.push_back(std::move(e));}
    return eqs;
}
struct GFRow{uint64_t mask=0;int rhs=0;};
static GFRow mod4_row(const Equation&e){
    int M=0,neg=0;uint64_t mask=0;
    for(auto&t:e.terms){int a=std::abs(t.coeff);M+=a;if(a&1){if(t.coeff<0)neg^=1;mask^=t.mask;}}
    if(M&1) return {0,1};
    return {mask,((M/2)&1)^neg};
}
struct Affine { bool ok=true; int rank=0; std::vector<int>piv,freec; std::vector<GFRow>rows; };
static Affine gf2_rref(std::vector<GFRow>a){
    int r=0;std::vector<int>p;
    for(int c=0;c<NV&&r<(int)a.size();c++){int pr=-1;for(int i=r;i<(int)a.size();i++)if((a[i].mask>>c)&1){pr=i;break;}if(pr<0)continue;if(pr!=r)std::swap(a[pr],a[r]);for(int i=0;i<(int)a.size();i++)if(i!=r&&((a[i].mask>>c)&1)){a[i].mask^=a[r].mask;a[i].rhs^=a[r].rhs;}p.push_back(c);r++;}
    for(int i=r;i<(int)a.size();i++)if(a[i].mask==0&&a[i].rhs)return{false,r,{},{},{}};
    std::array<char,NV>isp{};for(int c:p)isp[c]=1;std::vector<int>f;for(int c=0;c<NV;c++)if(!isp[c])f.push_back(c);a.resize(r);return{true,r,std::move(p),std::move(f),std::move(a)};
}
static bool exact_ok(uint64_t bits,const std::vector<Equation>&eqs){
    for(auto&e:eqs){int s=0;for(auto&t:e.terms){int sign=(__builtin_parityll(bits&t.mask)?-1:1);s+=t.coeff*sign;}if(s)return false;}return true;
}
static std::array<int,100> build_seq(uint64_t bits,const std::array<int,49>&rho){
    auto val=[&](int j){return ((bits>>j)&1)?-1:1;};std::array<int,100>s{};for(int j=0;j<49;j++){s[j]=val(j);int m=(((49-j)&1)?-1:1)*rho[j];s[98-j]=m*val(j);}s[49]=val(49);s[99]=val(50);return s;
}
static long long even_energy(const std::array<int,100>&s,int cap){
    uint64_t A=0,B=0;for(int i=0;i<50;i++){if(s[2*i]>0)A|=1ULL<<i;if(s[2*i+1]>0)B|=1ULL<<i;}long long e=0;for(int r=1;r<50;r++){int len=50-r;uint64_t mask=(1ULL<<len)-1;int ca=len-2*__builtin_popcountll((A^(A>>r))&mask),cb=len-2*__builtin_popcountll((B^(B>>r))&mask),c=ca+cb;e+=1LL*c*c;if(e>cap)return e;}return e;
}
static bool verify(const std::array<int,100>&s,const std::vector<int>&support,long long E){
    long long e=0,o=0;std::vector<int>rs;std::array<int,100>c{};for(int k=1;k<100;k++){int z=0;for(int i=0;i<100-k;i++)z+=s[i]*s[i+k];c[k]=z;e+=1LL*z*z;if(k&1)o+=1LL*z*z;}for(int k=1;k<=97;k+=2)if(c[k]!=s[99-k]*s[99])rs.push_back(k);return e==E&&o==50&&rs==support;
}
static std::string fmt(const std::array<int,100>&s){std::string z;for(int x:s)z+=x>0?'+':'-';return z;}
struct Stats{uint64_t supports=0,inconsistent=0;unsigned __int128 affine=0;uint64_t exact=0,target=0;int maxnull=0;};
static Stats solve_one(const std::vector<int>&support,bool profile,std::atomic<bool>&found,std::string&foundseq,std::mutex&mu){
    Stats st;st.supports=1;auto rho=reflection_pattern(support);auto eqs=build_exact(support,rho,true);std::vector<GFRow>rows;rows.reserve(eqs.size()+2);for(auto&e:eqs)rows.push_back(mod4_row(e));
    std::vector<int>bad;for(int j=0;j<49;j++)if(rho[j]<0)bad.push_back(j);int ref=-1;for(int b:bad)if(!(b&1)){ref=b;break;}if(ref<0)throw std::runtime_error("odd defect expected even bad ref");rows.push_back({1ULL<<ref,0});rows.push_back({1ULL<<50,0});
    auto af=gf2_rref(std::move(rows));if(!af.ok){st.inconsistent=1;return st;}int f=af.freec.size();st.maxnull=f;if(f>=63)throw std::runtime_error("too many free");uint64_t total=1ULL<<f;st.affine=total;if(profile)return st;
    uint64_t bits=0;for(int r=0;r<af.rank;r++)if(af.rows[r].rhs)bits|=1ULL<<af.piv[r];std::vector<uint64_t>basis(f);for(int j=0;j<f;j++){uint64_t v=1ULL<<af.freec[j];for(int r=0;r<af.rank;r++)if((af.rows[r].mask>>af.freec[j])&1)v^=1ULL<<af.piv[r];basis[j]=v;}
    auto test=[&](){if(!exact_ok(bits,eqs))return;st.exact++;auto s=build_seq(bits,rho);int A=0,B=0;for(int i=0;i<50;i++){A+=s[2*i];B+=s[2*i+1];}int h=std::abs(A);if(B!=0||h<2||h>2*(int)support.size()||(h%4)!=2)return;st.target++;long long ev=even_energy(s,520),E=ev+50;if(ev<=520){if(!verify(s,support,E))throw std::runtime_error("verification mismatch");std::lock_guard<std::mutex>lk(mu);if(!found.load()){found=true;foundseq=fmt(s);std::cerr<<"FOUND E="<<E<<" A="<<A<<" support=";for(int x:support)std::cerr<<x<<",";std::cerr<<" seq="<<foundseq<<"\n";}}};
    uint64_t prevg=0;test();for(uint64_t i=1;i<total&&!found.load();i++){uint64_t g=i^(i>>1),diff=g^prevg;int j=__builtin_ctzll(diff);bits^=basis[j];prevg=g;test();}
    return st;
}
int main(int argc,char**argv){
    int d=5,threads=0,start=0,end=1<<30;bool profile=false;std::string one;for(int i=1;i<argc;i++){std::string a=argv[i];auto need=[&](){if(++i>=argc)throw std::runtime_error("missing arg");return std::string(argv[i]);};if(a=="--defect")d=std::stoi(need());else if(a=="--threads")threads=std::stoi(need());else if(a=="--start")start=std::stoi(need());else if(a=="--end")end=std::stoi(need());else if(a=="--support")one=need();else if(a=="--profile")profile=true;else return 2;}if(!(d&1)||d<1||d>5)return 2;auto supports=one.empty()?all_supports(d):std::vector<std::vector<int>>{parse_support(one,d)};start=std::max(0,start);end=std::min(end,(int)supports.size());if(start>=end)return 2;
#ifdef _OPENMP
    if(threads<=0)threads=omp_get_max_threads();omp_set_num_threads(threads);
#else
    threads=1;
#endif
    auto t0=std::chrono::steady_clock::now();std::atomic<bool>found{false};std::string foundseq;std::mutex mu;std::atomic<uint64_t>done{0},inc{0},exact{0},target{0};std::atomic<unsigned long long>affLo{0};int maxnull=0;
#pragma omp parallel for schedule(dynamic,8) reduction(max:maxnull)
    for(int i=start;i<end;i++){if(found.load())continue;auto s=solve_one(supports[i],profile,found,foundseq,mu);done++;inc+=s.inconsistent;affLo.fetch_add((unsigned long long)s.affine);exact+=s.exact;target+=s.target;maxnull=std::max(maxnull,s.maxnull);}
    double sec=std::chrono::duration<double>(std::chrono::steady_clock::now()-t0).count();bool complete=!found.load()&&done.load()==uint64_t(end-start);std::cout<<(profile?"PROFILE":"SUMMARY")<<" defect="<<d<<" range="<<start<<":"<<end<<" supports="<<done.load()<<" inconsistent="<<inc.load()<<" affine_enum="<<affLo.load()<<" exact="<<exact.load()<<" target="<<target.load()<<" maxnull="<<maxnull<<" complete="<<complete<<" found="<<found.load()<<" seconds="<<sec<<" threads="<<threads<<"\n";if(found.load())std::cout<<"FOUND_SEQ="<<foundseq<<"\n";return found.load()?0:(complete?0:1);
}
