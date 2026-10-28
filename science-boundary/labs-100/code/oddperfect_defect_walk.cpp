// Instrument the calibrated odd-perfect walk by the skew-defect counts of the
// two length-99 endpoint deletions.  For an odd-perfect length-100 sequence s,
// deleting the first sign gives t=s[1:] and, for every odd k,
//
//   C_k(t) = C_k(s) - s_0 s_k in {0,+/-2}.
//
// Define d_L as the number of nonzero odd autocorrelations of t; define d_R
// analogously after deleting the last sign.  A pseudo-/near-skew endpoint has
// d_L=0 or d_R=0.  We record the best full N=100 energy reached at every
// orbit-invariant defect d=min(d_L,d_R).
//
// Reuse the already regression-tested exact odd-perfect move kernel rather
// than duplicating it.  Rename its CLI entry point inside this translation
// unit, then build a new instrumented driver below.
#define main oddperfect_outside_original_main
#include "oddperfect_outside_nss.cpp"
#undef main

#include <array>
#include <mutex>

struct DefectInfo {
    int left = -1;
    int right = -1;
    int d = -1;
};

static DefectInfo skew_defect(const S& s, const C& c) {
    int dl = 0, dr = 0;
    for (int k = 1; k < 99; k += 2) {
        const int cl = c[k] - int(s[0]) * int(s[k]);
        const int cr = c[k] - int(s[99-k]) * int(s[99]);
#ifndef NDEBUG
        if (!(cl == 0 || cl == 2 || cl == -2) ||
            !(cr == 0 || cr == 2 || cr == -2)) {
            std::cerr << "odd-perfect deletion identity failed\n";
            std::abort();
        }
#endif
        dl += (cl != 0);
        dr += (cr != 0);
    }
    return {dl, dr, std::min(dl, dr)};
}

struct DRun {
    std::array<long long,50> best{};
    std::array<S,50> seq{};
    std::array<int,50> left{};
    std::array<int,50> right{};
    long long global = (1LL<<60);
    S gs{};
    DRun() { best.fill(1LL<<60); left.fill(-1); right.fill(-1); }
};

static inline void defect_note(DRun& out, long long e, const S& s, const C& c) {
    const auto z = skew_defect(s,c);
    if (z.d >= 0 && z.d < 50 && e < out.best[z.d]) {
        out.best[z.d] = e;
        out.seq[z.d] = s;
        out.left[z.d] = z.left;
        out.right[z.d] = z.right;
    }
    if (e < out.global) { out.global = e; out.gs = s; }
}

static DRun defect_walk(S s, std::mt19937_64& rng, int steps, int tenlo, int tenhi) {
    C c{};
    long long o=0, e=exact(s,&c,&o);
    if (o != 50) throw std::runtime_error("defect walk start is not odd-perfect");
    DRun out;
    defect_note(out,e,s,c);
    std::array<int,N> tabu{};
    long long global_best=e;

    for (int st=1; st<=steps; ++st) {
        long long me=1LL<<60;
        int mp=-1,mq=-1,ties=0;
        bool any=false;
        for (int p=0;p<N;p++) {
            auto z=move_eval(s,c,p,-1);
            if(!z.ok) continue;
            any=true;
            if(st<tabu[p] && z.e>=global_best) continue;
            if(z.e<me){me=z.e;mp=p;mq=-1;ties=1;}
            else if(z.e==me && rng()%++ties==0){mp=p;mq=-1;}
        }
        for (int p=0;p<N;p++) for (int q=p+1;q<N;q++) {
            auto z=move_eval(s,c,p,q);
            if(!z.ok) continue;
            any=true;
            if((st<tabu[p]||st<tabu[q]) && z.e>=global_best) continue;
            if(z.e<me){me=z.e;mp=p;mq=q;ties=1;}
            else if(z.e==me && rng()%++ties==0){mp=p;mq=q;}
        }
        if(mp<0){if(!any)break;tabu.fill(0);continue;}
        move_apply(s,c,e,mp,mq);
        tabu[mp]=st+tenlo+int(rng()%(tenhi-tenlo+1));
        if(mq>=0)tabu[mq]=st+tenlo+int(rng()%(tenhi-tenlo+1));
        if(e<global_best) global_best=e;
        defect_note(out,e,s,c);
#ifndef NDEBUG
        if((st&1023)==0){long long oo=0;C cc{};long long ee=exact(s,&cc,&oo);if(ee!=e||oo!=50||cc!=c)std::abort();}
#endif
    }
    return out;
}

int main(int argc,char**argv){
    int runs=64,steps=80000,oddsteps=40000,threads=0,tenlo=5,tenhi=15;
    uint64_t seed=1;
    for(int i=1;i<argc;i++){
        std::string a=argv[i];
        auto need=[&](){if(i+1>=argc)throw std::runtime_error("missing value");return std::string(argv[++i]);};
        if(a=="--runs")runs=std::stoi(need());
        else if(a=="--steps")steps=std::stoi(need());
        else if(a=="--odd-steps")oddsteps=std::stoi(need());
        else if(a=="--threads")threads=std::stoi(need());
        else if(a=="--seed")seed=std::stoull(need());
        else if(a=="--tenure-lo")tenlo=std::stoi(need());
        else if(a=="--tenure-hi")tenhi=std::stoi(need());
        else throw std::runtime_error("unknown argument");
    }
#ifdef _OPENMP
    if(threads<=0)threads=omp_get_max_threads();omp_set_num_threads(threads);
#else
    threads=1;
#endif
    std::array<long long,50> best;best.fill(1LL<<60);
    std::array<S,50> bseq{};
    std::array<int,50> bleft{},bright{};bleft.fill(-1);bright.fill(-1);
    int good=0;
    auto t0=std::chrono::steady_clock::now();
#pragma omp parallel for schedule(dynamic,1)
    for(int rr=0;rr<runs;rr++){
        std::mt19937_64 rng(seed+0x9e3779b97f4a7c15ULL*uint64_t(rr+1));
        S s=randoms(rng);
        if(!make_oddperfect(s,rng,oddsteps))continue;
        DRun z=defect_walk(s,rng,steps,tenlo,tenhi);
#pragma omp critical
        {
            ++good;
            for(int d=0;d<50;d++)if(z.best[d]<best[d]){
                best[d]=z.best[d];bseq[d]=z.seq[d];bleft[d]=z.left[d];bright[d]=z.right[d];
                std::cout<<"DEFECT d="<<d<<" left="<<bleft[d]<<" right="<<bright[d]
                         <<" energy="<<best[d]<<" seq="<<fmt(bseq[d])<<"\n"<<std::flush;
            }
        }
    }
    double sec=std::chrono::duration<double>(std::chrono::steady_clock::now()-t0).count();
    std::cout<<"SUMMARY runs="<<runs<<" oddperfect_starts="<<good<<" steps="<<steps<<" seconds="<<sec<<"\n";
    for(int d=0;d<50;d++)if(best[d]<(1LL<<60))
        std::cout<<"FRONTIER d="<<d<<" left="<<bleft[d]<<" right="<<bright[d]
                 <<" energy="<<best[d]<<" seq="<<fmt(bseq[d])<<"\n";
    return 0;
}
