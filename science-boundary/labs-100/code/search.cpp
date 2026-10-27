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

static long long score_exact(const Seq& s, Corr* out=nullptr) {
    Corr c{};
    long long e=0;
    for (int k=1;k<100;k++) {
        int x=0;
        for (int i=0;i<100-k;i++) x += int(s[i])*int(s[i+k]);
        c[k]=x; e += 1LL*x*x;
    }
    if(out) *out=c;
    return e;
}

static long long eval_flip(const Seq& s, const Corr& c, long long e, int p) {
    long long ne=e;
    const int sp=s[p];
    for(int k=1;k<100;k++) {
        int t=0;
        if(p+k<100) t += sp*int(s[p+k]);
        if(p-k>=0) t += int(s[p-k])*sp;
        if(!t) continue;
        int d=-2*t;
        ne += 2LL*c[k]*d + 1LL*d*d;
    }
    return ne;
}

static void do_flip(Seq& s, Corr& c, long long& e, int p) {
    const int sp=s[p];
    for(int k=1;k<100;k++) {
        int t=0;
        if(p+k<100) t += sp*int(s[p+k]);
        if(p-k>=0) t += int(s[p-k])*sp;
        if(!t) continue;
        int d=-2*t;
        e += 2LL*c[k]*d + 1LL*d*d;
        c[k] += d;
    }
    s[p] = -s[p];
}

static Seq parse_seq(const std::string& x) {
    if(x.size()!=100) throw std::runtime_error("sequence must have length 100");
    Seq s{};
    for(int i=0;i<100;i++) {
        if(x[i]=='+') s[i]=1;
        else if(x[i]=='-') s[i]=-1;
        else throw std::runtime_error("sequence must contain only + and -");
    }
    return s;
}

static std::string fmt(const Seq& s) {
    std::string x; x.reserve(100);
    for(int i=0;i<100;i++) x.push_back(s[i]>0?'+':'-');
    return x;
}

static Seq random_seq(std::mt19937_64& rng) {
    Seq s{};
    for(auto &v:s) v=(rng()&1)?1:-1;
    return s;
}

static Seq perturb(Seq s, std::mt19937_64& rng, int flips) {
    std::array<int,100> idx{}; for(int i=0;i<100;i++) idx[i]=i;
    std::shuffle(idx.begin(), idx.end(), rng);
    for(int i=0;i<flips;i++) s[idx[i]]=-s[idx[i]];
    return s;
}

struct Result { long long e; Seq s; long long steps; };

static Result tabu_run(Seq s, std::mt19937_64& rng, long long max_steps, int tenure_lo, int tenure_hi,
                       int kick_every, int kick_size, long long target) {
    Corr c{}; long long e=score_exact(s,&c);
    Result best{e,s,0};
    std::array<long long,100> tabu_until{};
    std::uniform_int_distribution<int> ten(tenure_lo,tenure_hi);
    std::array<int,100> order{}; for(int i=0;i<100;i++) order[i]=i;
    long long last_improve=0;
    for(long long step=1;step<=max_steps;step++) {
        long long move_e=std::numeric_limits<long long>::max();
        int move=-1;
        std::shuffle(order.begin(), order.end(), rng);
        for(int z=0;z<100;z++) {
            int p=order[z];
            long long ne=eval_flip(s,c,e,p);
            bool tabu = step < tabu_until[p];
            if(tabu && ne>=best.e) continue;
            if(ne<move_e) {move_e=ne; move=p;}
        }
        if(move<0) {
            tabu_until.fill(0); --step; continue;
        }
        do_flip(s,c,e,move);
        tabu_until[move]=step+ten(rng);
        if(e<best.e) {
            best={e,s,step}; last_improve=step;
            if(best.e<=target) return best;
        }
        if(kick_every>0 && step-last_improve>=kick_every) {
            std::array<int,100> idx{}; for(int i=0;i<100;i++) idx[i]=i;
            std::shuffle(idx.begin(), idx.end(), rng);
            for(int j=0;j<kick_size;j++) do_flip(s,c,e,idx[j]);
            tabu_until.fill(0);
            last_improve=step;
        }
#ifndef NDEBUG
        if((step & 0x3fff)==0) {
            long long check=score_exact(s,nullptr);
            if(check!=e) { std::cerr<<"incremental mismatch "<<e<<" "<<check<<"\n"; std::abort(); }
        }
#endif
    }
    return best;
}

int main(int argc, char** argv) {
    const std::string incumbent_str="++++++--+++++-----++-++--+--++++++++++---+-++--++++-+--++----+--+-+-+-+-++---++---++-+-++-+-++--+-+-";
    int runs=200, threads=0, tenure_lo=6, tenure_hi=16, kick_every=3000, kick_size=12;
    long long steps=300000, target=574;
    uint64_t seed=1;
    std::string mode="mixed";
    for(int i=1;i<argc;i++) {
        std::string a=argv[i];
        auto need=[&](){ if(i+1>=argc) throw std::runtime_error("missing value after "+a); return std::string(argv[++i]); };
        if(a=="--runs") runs=std::stoi(need());
        else if(a=="--steps") steps=std::stoll(need());
        else if(a=="--seed") seed=std::stoull(need());
        else if(a=="--threads") threads=std::stoi(need());
        else if(a=="--mode") mode=need();
        else if(a=="--tenure-lo") tenure_lo=std::stoi(need());
        else if(a=="--tenure-hi") tenure_hi=std::stoi(need());
        else if(a=="--kick-every") kick_every=std::stoi(need());
        else if(a=="--kick-size") kick_size=std::stoi(need());
        else if(a=="--target") target=std::stoll(need());
        else throw std::runtime_error("unknown arg: "+a);
    }
    if(threads<=0) {
#ifdef _OPENMP
        threads=omp_get_max_threads();
#else
        threads=1;
#endif
    }
#ifdef _OPENMP
    omp_set_num_threads(threads);
#endif
    Seq incumbent=parse_seq(incumbent_str);
    if(score_exact(incumbent,nullptr)!=578) throw std::runtime_error("incumbent score check failed");
    long long global_best=578; Seq global_seq=incumbent;
    auto t0=std::chrono::steady_clock::now();
#pragma omp parallel for schedule(dynamic,1) if(runs>1)
    for(int r=0;r<runs;r++) {
        std::mt19937_64 rng(seed + 0x9e3779b97f4a7c15ULL*(uint64_t)(r+1));
        Seq start{};
        if(mode=="random") start=random_seq(rng);
        else if(mode=="incumbent") start=perturb(incumbent,rng, 10 + int(rng()%31));
        else { start = (r%2==0) ? random_seq(rng) : perturb(incumbent,rng, 10 + int(rng()%41)); }
        Result got=tabu_run(start,rng,steps,tenure_lo,tenure_hi,kick_every,kick_size,target);
#pragma omp critical
        {
            if(got.e<global_best) {
                global_best=got.e; global_seq=got.s;
                std::cout << "BEST energy="<<global_best<<" run="<<r<<" step="<<got.steps<<" seq="<<fmt(global_seq)<<"\n" << std::flush;
            }
        }
    }
    auto t1=std::chrono::steady_clock::now();
    double sec=std::chrono::duration<double>(t1-t0).count();
    std::cout<<"FINAL energy="<<global_best<<" seconds="<<sec<<" seq="<<fmt(global_seq)<<"\n";
    return global_best<=target?0:1;
}
