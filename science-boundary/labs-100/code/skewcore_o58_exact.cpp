// Exact enumeration of the O=58 (first non-odd-perfect) layer inside
// boundary + skew-core LABS-100 families for odd boundary d=5,7,...,25.
//
// Let d=2m+1. Normalize s0=s1=+1. The suffix s_d..s_99 has odd length
// 100-d and is skew-symmetric. Write u_j=s_{2j+1}, v_j=s_{2j+2}.
// The suffix reflection is
//   u_{49+m-j} = alpha u_j, alpha=(-1)^(m+1),
//   v_{48+m-j} = beta  v_j, beta =(-1)^m.
//
// For low odd lag k=2j+1, skewness kills the suffix-suffix contribution and
// leaves the boundary form
//   T_j = sum_{r=0}^m b_{2r} u_{j+r}
//       + sum_{r=0}^{m-1} b_{2r+1} v_{j+r}.
// Pairing k with 100-k, O=58 means exactly one of the 25 pairs is
// (1,3),(3,1),(-1,-3),(-3,-1); every other pair is (1,-1) or (-1,1).
// The recurrence only needs the most recent m (u,v) pairs.
//
// O=58 also implies the two parity-half sums have magnitude 2. One parity
// sum is fixed by the boundary because the corresponding suffix pairs cancel;
// the other is accumulated exactly while enumerating the skew core. This is
// enforced at every leaf and is an independent check on the defect sign.
//
// Each accepted leaf is scored from scratch with packed-bit exact aperiodic
// autocorrelations. This file therefore computes an exact minimum energy for
// the entire normalized structural class, not merely a heuristic best.

#include <algorithm>
#include <array>
#include <cstdint>
#include <iostream>
#include <limits>
#include <string>
#include <vector>
#ifdef _OPENMP
#include <omp.h>
#endif

using U128 = unsigned __int128;

static inline int pop128(U128 x) {
    return __builtin_popcountll((uint64_t)x) +
           __builtin_popcountll((uint64_t)(x >> 64));
}
static inline void set_bit(U128& b, int p, int sign) {
    U128 mask = (U128)1 << p;
    if (sign < 0) b |= mask; else b &= ~mask;
}
static long long exact_energy(U128 b, long long* odd_out=nullptr) {
    long long e=0, odd=0;
    for (int k=1;k<100;k++) {
        int n=100-k;
        U128 mask=((U128)1<<n)-1;
        int h=pop128((b^(b>>k))&mask);
        int c=n-2*h;
        long long q=1LL*c*c;
        e+=q;
        if (k&1) odd+=q;
    }
    if (odd_out) *odd_out=odd;
    return e;
}
static std::string format(U128 b) {
    std::string s;
    s.reserve(100);
    for (int i=0;i<100;i++) s += ((b>>i)&1) ? '-' : '+';
    return s;
}
// 0 normal, +/-1 signed O=58 defect, 99 invalid.
static inline int pair_type(int a,int b) {
    if ((a==1&&b==-1)||(a==-1&&b==1)) return 0;
    if ((a==1&&b==3)||(a==3&&b==1)) return 1;
    if ((a==-1&&b==-3)||(a==-3&&b==-1)) return -1;
    return 99;
}

struct Result {
    unsigned long long leaves=0;
    long long best=(1LL<<60);
    U128 bits=0;
};

struct Solver {
    int m=0,d=0,nend=0,alpha=0,beta=0;
    std::array<int,27> b{};
    std::array<int,50> u{},v{};
    int fixed_half=0,dynamic_prefix=0;
    Result result;

    int T(int j) const {
        int x=0;
        for (int r=0;r<=m;r++) x += b[2*r]*u[j+r];
        for (int r=0;r<m;r++) x += b[2*r+1]*v[j+r];
        return x;
    }
    int low_value(int n,int un) const {
        int j=n-m,x=0;
        for (int r=0;r<=m;r++) x += b[2*r]*(r==m?un:u[j+r]);
        for (int r=0;r<m;r++) x += b[2*r+1]*v[j+r];
        return x;
    }
    int high_value(int n,int un) const {
        auto U=[&](int idx){return idx==n?un:u[idx];};
        int x=0;
        if (n<2*m) {
            int t=2*m-n;
            for (int r=0;r<=m-t;r++) x += alpha*b[2*r]*U(2*m-t-r);
            for (int r=0;r<m-t;r++) x += beta*b[2*r+1]*v[2*m-t-r-1];
        } else {
            for (int r=0;r<=m;r++) x += alpha*b[2*r]*U(n-r);
            for (int r=0;r<m;r++) x += beta*b[2*r+1]*v[n-r-1];
        }
        return x;
    }

    void dfs(int n,int defect_sign,int dynamic_pair_sum,U128 bits) {
        if (n==nend+1) {
            int ds=defect_sign;
            int first_missing=nend-m+1;
            for (int j=first_missing;j<25;j++) {
                int t=pair_type(T(j),T(49-j));
                if (t==99 || (t!=0 && ds!=0)) return;
                if (t) ds=t;
            }
            if (!ds) return;
            int center=(m%2==0 ? v[nend] : u[nend]);
            int dynamic_half=dynamic_prefix+2*dynamic_pair_sum+center;
            if (fixed_half*dynamic_half != 4*ds) return;

            result.leaves++;
            long long E=exact_energy(bits);
            if (E<result.best) { result.best=E; result.bits=bits; }
            return;
        }

        for (int un : {-1,1}) {
            int t=pair_type(low_value(n,un),high_value(n,un));
            if (t==99 || (t!=0 && defect_sign!=0)) continue;
            int next_defect=t?t:defect_sign;

            if (n==nend && (m&1)) {
                // u_n is the center; v_n was already created as the mirror of v_{n-1}.
                int vn=beta*v[n-1];
                u[n]=un; v[n]=vn;
                U128 nb=bits;
                set_bit(nb,2*n+1,un);
                dfs(n+1,next_defect,dynamic_pair_sum,nb);
            } else {
                for (int vn : {-1,1}) {
                    u[n]=un; v[n]=vn;
                    int um=49+m-n, vm=48+m-n;
                    u[um]=alpha*un; v[vm]=beta*vn;
                    U128 nb=bits;
                    set_bit(nb,2*n+1,un);
                    if (um!=n) set_bit(nb,2*um+1,alpha*un);
                    set_bit(nb,2*n+2,vn);
                    if (vm!=n) set_bit(nb,2*vm+2,beta*vn);
                    int add=0;
                    if (n<nend) add=(m%2==0?vn:un);
                    dfs(n+1,next_defect,dynamic_pair_sum+add,nb);
                }
            }
        }
    }

    Result run(int mm,unsigned mask) {
        m=mm; d=2*m+1;
        nend=24+(m+1)/2;
        alpha=(m%2==1 ? 1 : -1); // (-1)^(m+1)
        beta =(m%2==1 ? -1 : 1); // (-1)^m
        b.fill(0); b[0]=b[1]=1;
        for (int i=0;i<2*m-1;i++) b[i+2]=((mask>>(2*m-2-i))&1)?1:-1;
        for (int j=0;j<m;j++) { u[j]=b[2*j+1]; v[j]=b[2*j+2]; }

        if (m%2==0) {
            // Odd half is fixed; even half contains same-sign v pairs and center.
            fixed_half=0; for (int j=0;j<m;j++) fixed_half+=u[j];
            dynamic_prefix=1; for (int j=0;j<m;j++) dynamic_prefix+=v[j];
        } else {
            // Even half is fixed; odd half contains same-sign u pairs and center.
            fixed_half=1; for (int j=0;j<m;j++) fixed_half+=v[j];
            dynamic_prefix=0; for (int j=0;j<m;j++) dynamic_prefix+=u[j];
        }
        if (std::abs(fixed_half)!=2) return result;

        U128 bits=0;
        set_bit(bits,0,1); set_bit(bits,1,1);
        for (int i=0;i<2*m-1;i++) set_bit(bits,i+2,b[i+2]);
        dfs(m,0,0,bits);
        return result;
    }
};

int main(int argc,char**argv) {
    if (argc<2 || argc>3) return 2;
    int d=std::stoi(argv[1]);
    int threads=argc==3?std::stoi(argv[2]):4;
    if (d<5 || d>25 || !(d&1)) return 2;
    int m=(d-1)/2;
    unsigned long long prefixes=1ULL<<(2*m-1);
    std::vector<Result> results(prefixes);
#ifdef _OPENMP
    omp_set_num_threads(threads);
#endif
#pragma omp parallel for schedule(dynamic,1)
    for (unsigned long long mask=0;mask<prefixes;mask++) {
        Solver s;
        results[mask]=s.run(m,(unsigned)mask);
    }

    unsigned long long leaves=0;
    long long best=(1LL<<60);
    U128 best_bits=0;
    unsigned best_mask=0;
    int nonzero=0;
    for (unsigned long long mask=0;mask<prefixes;mask++) {
        const auto& r=results[mask];
        if (!r.leaves) continue;
        nonzero++;
        leaves+=r.leaves;
        if (r.best<best) { best=r.best; best_bits=r.bits; best_mask=(unsigned)mask; }
    }
    long long odd=0;
    long long check=best<(1LL<<60)?exact_energy(best_bits,&odd):-1;
    std::cout << "RESULT d="<<d
              << " nonzero_prefixes="<<nonzero
              << " leaves="<<leaves
              << " best="<<(best<(1LL<<60)?best:-1)
              << " odd="<<odd
              << " best_mask="<<best_mask
              << " check="<<check << "\n";
    if (best<(1LL<<60)) std::cout << "BESTSEQ "<<format(best_bits)<<"\n";
    return (best==check && odd==58)?0:2;
}
