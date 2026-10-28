#include <algorithm>
#include <array>
#include <chrono>
#include <cstdint>
#include <iostream>
#include <limits>
#include <random>
#include <string>
#include <vector>
#ifdef _OPENMP
#include <omp.h>
#endif

using Seq = std::array<int8_t,100>;
using Corr = std::array<int,100>;

static long long energy(const Seq& s, Corr* out=nullptr) {
    Corr c{}; long long e=0;
    for(int k=1;k<100;k++) {
        int x=0; for(int i=0;i<100-k;i++) x += int(s[i])*int(s[i+k]);
        c[k]=x; e += 1LL*x*x;
    }
    if(out) *out=c; return e;
}
static long long odd_energy(const Corr& c){ long long e=0; for(int k=1;k<100;k+=2)e+=1LL*c[k]*c[k]; return e; }
static long long even_energy(const Corr& c){ long long e=0; for(int k=2;k<100;k+=2)e+=1LL*c[k]*c[k]; return e; }
static std::string fmt(const Seq&s){std::string z;z.reserve(100);for(auto v:s)z+=v>0?'+':'-';return z;}
static Seq random_seq(std::mt19937_64&r){Seq s{};for(auto&v:s)v=(r()&1)?1:-1;return s;}

static void flip(Seq&s,Corr&c,long long&e,int p){
    int sp=s[p];
    for(int k=1;k<100;k++){
        int t=0;
        if(p+k<100)t+=sp*int(s[p+k]);
        if(p-k>=0)t+=int(s[p-k])*sp;
        if(!t)continue;
        int d=-2*t; e += 2LL*c[k]*d + 1LL*d*d; c[k]+=d;
    }
    s[p]=-s[p];
}
static long long score_after_flip(const Seq&s,const Corr&c,long long e,int p,bool odd_only){
    int sp=s[p]; long long ne=odd_only?odd_energy(c):e;
    for(int k=1;k<100;k++){
        if(odd_only && !(k&1))continue;
        int t=0;
        if(p+k<100)t+=sp*int(s[p+k]);
        if(p-k>=0)t+=int(s[p-k])*sp;
        if(!t)continue;
        int d=-2*t; ne += 2LL*c[k]*d + 1LL*d*d;
    }
    return ne;
}

static bool make_odd_perfect(Seq&s,Corr&c,long long&e,std::mt19937_64&rng,int max_steps){
    std::array<int,100> order{};for(int i=0;i<100;i++)order[i]=i;
    long long oe=odd_energy(c);
    for(int step=0;step<max_steps && oe>50;step++){
        long long best=oe; int bp=-1;
        std::shuffle(order.begin(),order.end(),rng);
        for(int p:order){ long long x=score_after_flip(s,c,e,p,true); if(x<best){best=x;bp=p;} }
        if(bp>=0){ flip(s,c,e,bp); oe=best; continue; }
        // escape odd-energy local minima with a random 2-flip kick
        int a=int(rng()%100),b=int(rng()%100); if(a==b)b=(b+1)%100;
        flip(s,c,e,a); flip(s,c,e,b); oe=odd_energy(c);
    }
    return odd_energy(c)==50;
}

struct Result{long long e=(1LL<<60);Seq s{};long long accepted=0,proposed=0;};

static Result manifold_run(std::mt19937_64&rng,long long proposals,int repair_cap){
    Seq s=random_seq(rng); Corr c{}; long long e=energy(s,&c);
    for(int tries=0;tries<100 && !make_odd_perfect(s,c,e,rng,20000);tries++){s=random_seq(rng);e=energy(s,&c);}    
    if(odd_energy(c)!=50) return {};
    Result best{e,s,0,0};
    std::uniform_real_distribution<double> U(0.0,1.0);
    double T=16.0;
    for(long long it=0;it<proposals;it++){
        ++best.proposed;
        Seq cand=s; Corr cc=c; long long ce=e;
        int nf=2 + 2*int((rng()%3));
        std::array<int,100> idx{};for(int i=0;i<100;i++)idx[i]=i;std::shuffle(idx.begin(),idx.end(),rng);
        for(int j=0;j<nf;j++)flip(cand,cc,ce,idx[j]);
        bool ok=make_odd_perfect(cand,cc,ce,rng,repair_cap);
        if(!ok) continue;
        long long delta=ce-e;
        if(delta<=0 || U(rng)<std::exp(-double(delta)/T)){
            s=cand;c=cc;e=ce;++best.accepted;
            if(e<best.e){best.e=e;best.s=s;}
        }
        if((it+1)%10000==0) T=std::max(2.0,T*0.97);
    }
    Corr chk{}; long long full=energy(best.s,&chk);
    if(full!=best.e || odd_energy(chk)!=50){std::cerr<<"consistency failure\n";std::abort();}
    return best;
}

int main(int argc,char**argv){
    int runs=32,threads=0,repair=80; long long proposals=200000,target=574; uint64_t seed=1;
    for(int i=1;i<argc;i++){
        std::string a=argv[i]; auto need=[&](){if(i+1>=argc)throw std::runtime_error("missing arg");return std::string(argv[++i]);};
        if(a=="--runs")runs=std::stoi(need()); else if(a=="--threads")threads=std::stoi(need());
        else if(a=="--repair")repair=std::stoi(need()); else if(a=="--proposals")proposals=std::stoll(need());
        else if(a=="--seed")seed=std::stoull(need()); else if(a=="--target")target=std::stoll(need()); else throw std::runtime_error("unknown arg");
    }
#ifdef _OPENMP
    if(threads<=0)threads=omp_get_max_threads();omp_set_num_threads(threads);
#else
    threads=1;
#endif
    std::vector<long long> vals(runs,(1LL<<60)); Result global;
    auto t0=std::chrono::steady_clock::now();
#pragma omp parallel for schedule(dynamic,1)
    for(int r=0;r<runs;r++){
        std::mt19937_64 rng(seed+0x9e3779b97f4a7c15ULL*(uint64_t)(r+1));
        Result got=manifold_run(rng,proposals,repair); vals[r]=got.e;
#pragma omp critical
        if(got.e<global.e){global=got;std::cout<<"BEST energy="<<global.e<<" run="<<r<<" accepted="<<global.accepted<<" proposed="<<global.proposed<<" seq="<<fmt(global.s)<<"\n"<<std::flush;}
    }
    std::sort(vals.begin(),vals.end()); auto q=[&](double f){return vals[(size_t)(f*(vals.size()-1))];};
    double sec=std::chrono::duration<double>(std::chrono::steady_clock::now()-t0).count();
    std::cout<<"SUMMARY runs="<<runs<<" min="<<vals.front()<<" p10="<<q(.1)<<" median="<<q(.5)<<" p90="<<q(.9)<<" seconds="<<sec<<"\n";
    std::cout<<"FINAL energy="<<global.e<<" odd=50 even="<<(global.e-50)<<" seq="<<fmt(global.s)<<"\n";
    return global.e<=target?0:1;
}
