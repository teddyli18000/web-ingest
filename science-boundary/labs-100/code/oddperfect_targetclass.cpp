#include <algorithm>
#include <array>
#include <chrono>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <random>
#include <string>
#include <vector>
#ifdef _OPENMP
#include <omp.h>
#endif

// Search the O=50 congruence class compatible with a total energy of 574.
// For N=100, E=574 requires global sign product +1.  In the odd-perfect
// layer (all odd |C_k|=1), the two parity-half products must then both be -1.
// Phase 1 finds random odd-perfect states and keeps only that target class.
// Phase 2 uses same-parity double flips, which preserve both half products,
// and accepts only moves that remain exactly odd-perfect.
using S = std::array<int8_t, 100>;
using C = std::array<int, 100>;
constexpr int N = 100;
static const std::string INC =
    "++++++--+++++-----++-++--+--++++++++++---+-++--++++-+--++----+--+-+-+-+-++---++---++-+-++-+-++--+-+-";

static long long exact(const S& s, C* out = nullptr, long long* oddout = nullptr) {
    C c{};
    long long e = 0, o = 0;
    for (int k = 1; k < N; ++k) {
        int x = 0;
        for (int i = 0; i < N - k; ++i) x += int(s[i]) * int(s[i + k]);
        c[k] = x;
        const long long q = 1LL * x * x;
        e += q;
        if (k & 1) o += q;
    }
    if (out) *out = c;
    if (oddout) *oddout = o;
    return e;
}

static S parse(const std::string& z) {
    if (z.size() != N) throw std::runtime_error("sequence length must be 100");
    S s{};
    for (int i = 0; i < N; ++i) {
        if (z[i] == '+') s[i] = 1;
        else if (z[i] == '-') s[i] = -1;
        else throw std::runtime_error("sequence must contain only + and -");
    }
    return s;
}

static std::string fmt(const S& s) {
    std::string z;
    z.reserve(N);
    for (auto x : s) z += x > 0 ? '+' : '-';
    return z;
}

static S random_seq(std::mt19937_64& r) {
    S s{};
    for (auto& x : s) x = (r() & 1) ? 1 : -1;
    return s;
}

static int half_product(const S& s, int parity) {
    int p = 1;
    for (int i = parity; i < N; i += 2) p *= s[i];
    return p;
}

static inline int contrib(const S& s, int p, int k) {
    int t = 0;
    const int sp = s[p];
    if (p + k < N) t += sp * int(s[p + k]);
    if (p - k >= 0) t += int(s[p - k]) * sp;
    return t;
}

static long long odd_flip_eval(const S& s, const C& c, long long o, int p) {
    long long no = o;
    for (int k = 1; k < N; k += 2) {
        const int d = -2 * contrib(s, p, k);
        if (d) no += 2LL * c[k] * d + 1LL * d * d;
    }
    return no;
}

static void flip1(S& s, C& c, long long& e, long long& o, int p) {
    for (int k = 1; k < N; ++k) {
        const int d = -2 * contrib(s, p, k);
        if (!d) continue;
        const long long de = 2LL * c[k] * d + 1LL * d * d;
        e += de;
        if (k & 1) o += de;
        c[k] += d;
    }
    s[p] = -s[p];
}

static bool make_oddperfect(S& s, std::mt19937_64& r, int max_steps) {
    C c{};
    long long o = 0;
    long long e = exact(s, &c, &o);
    long long best = o;
    std::array<int, N> tabu{};
    for (int st = 1; st <= max_steps; ++st) {
        long long be = 1LL << 60;
        int bp = -1, ties = 0;
        for (int p = 0; p < N; ++p) {
            const long long ne = odd_flip_eval(s, c, o, p);
            if (st < tabu[p] && ne >= best) continue;
            if (ne < be) {
                be = ne; bp = p; ties = 1;
            } else if (ne == be && r() % ++ties == 0) {
                bp = p;
            }
        }
        if (bp < 0) { tabu.fill(0); continue; }
        flip1(s, c, e, o, bp);
        tabu[bp] = st + 5 + int(r() % 11);
        if (o < best) best = o;
        if (o == 50) return true;
    }
    return false;
}

struct Eval { bool ok = false; long long e = 0; };

static Eval pair_eval(const S& s, const C& c, int p, int q) {
    long long even = 0;
    const int pq = int(s[p]) * int(s[q]);
    const int dist = q - p;
    for (int k = 1; k < N; k += 2) {
        int t = contrib(s, p, k) + contrib(s, q, k);
        if (k == dist) t -= 2 * pq;
        const int cp = c[k] - 2 * t;
        if (std::abs(cp) != 1) return {};
    }
    for (int k = 2; k < N; k += 2) {
        int t = contrib(s, p, k) + contrib(s, q, k);
        if (k == dist) t -= 2 * pq;
        const int cp = c[k] - 2 * t;
        even += 1LL * cp * cp;
    }
    return {true, 50 + even};
}

static void pair_apply(S& s, C& c, long long& e, int p, int q) {
    const int pq = int(s[p]) * int(s[q]);
    const int dist = q - p;
    long long ne = 0;
    for (int k = 1; k < N; ++k) {
        int t = contrib(s, p, k) + contrib(s, q, k);
        if (k == dist) t -= 2 * pq;
        const int cp = c[k] - 2 * t;
        c[k] = cp;
        ne += 1LL * cp * cp;
    }
    s[p] = -s[p];
    s[q] = -s[q];
    e = ne;
}

struct Result { long long e; S s; int step; };

static Result walk(S s, std::mt19937_64& r, int steps, int tenure_lo, int tenure_hi) {
    C c{};
    long long o = 0;
    long long e = exact(s, &c, &o);
    if (o != 50 || half_product(s, 0) != -1 || half_product(s, 1) != -1)
        throw std::runtime_error("bad target-class start");

    long long best = e;
    S best_s = s;
    int best_step = 0;
    std::array<int, N> tabu{};

    for (int st = 1; st <= steps; ++st) {
        long long move_e = 1LL << 60;
        int mp = -1, mq = -1, ties = 0;
        for (int p = 0; p < N; ++p) {
            for (int q = p + 1; q < N; ++q) {
                // Two flips preserve each half product iff p,q have the same parity.
                if ((p & 1) != (q & 1)) continue;
                const auto z = pair_eval(s, c, p, q);
                if (!z.ok) continue;
                if ((st < tabu[p] || st < tabu[q]) && z.e >= best) continue;
                if (z.e < move_e) {
                    move_e = z.e; mp = p; mq = q; ties = 1;
                } else if (z.e == move_e && r() % ++ties == 0) {
                    mp = p; mq = q;
                }
            }
        }
        if (mp < 0) { tabu.fill(0); continue; }
        pair_apply(s, c, e, mp, mq);
        tabu[mp] = st + tenure_lo + int(r() % (tenure_hi - tenure_lo + 1));
        tabu[mq] = st + tenure_lo + int(r() % (tenure_hi - tenure_lo + 1));
        if (e < best) {
            best = e; best_s = s; best_step = st;
            if (best <= 574) return {best, best_s, best_step};
        }
#ifndef NDEBUG
        if ((st & 1023) == 0) {
            long long oo = 0;
            const long long ee = exact(s, nullptr, &oo);
            if (ee != e || oo != 50 || half_product(s, 0) != -1 || half_product(s, 1) != -1) {
                std::cerr << "consistency failure\n";
                std::abort();
            }
        }
#endif
    }
    return {best, best_s, best_step};
}

int main(int argc, char** argv) {
    int runs = 32, steps = 50000, odd_steps = 40000, threads = 4;
    int tenure_lo = 5, tenure_hi = 15;
    uint64_t seed = 1;
    std::string mode = "random";
    for (int i = 1; i < argc; ++i) {
        const std::string a = argv[i];
        auto need = [&]() {
            if (i + 1 >= argc) throw std::runtime_error("missing argument after " + a);
            return std::string(argv[++i]);
        };
        if (a == "--runs") runs = std::stoi(need());
        else if (a == "--steps") steps = std::stoi(need());
        else if (a == "--odd-steps") odd_steps = std::stoi(need());
        else if (a == "--threads") threads = std::stoi(need());
        else if (a == "--seed") seed = std::stoull(need());
        else if (a == "--mode") mode = need();
        else if (a == "--tenure-lo") tenure_lo = std::stoi(need());
        else if (a == "--tenure-hi") tenure_hi = std::stoi(need());
        else throw std::runtime_error("unknown argument: " + a);
    }
#ifdef _OPENMP
    omp_set_num_threads(threads);
#endif

    const S incumbent = parse(INC);
    S barrier = incumbent;
    C bc{};
    long long bo = 0;
    long long be = exact(barrier, &bc, &bo);
    flip1(barrier, bc, be, bo, 0);
    if (be != 774 || bo != 50 || half_product(barrier, 0) != -1 || half_product(barrier, 1) != -1)
        throw std::runtime_error("target-class barrier check failed");
    std::cerr << "BARRIER e=" << be << " o=" << bo << " hp=-1,-1\n";

    long long global_best = 1LL << 60;
    S global_s = barrier;
    std::vector<long long> vals(runs, -1);
    const auto t0 = std::chrono::steady_clock::now();

#pragma omp parallel for schedule(dynamic, 1)
    for (int rr = 0; rr < runs; ++rr) {
        std::mt19937_64 r(seed + 0x9e3779b97f4a7c15ULL * uint64_t(rr + 1));
        S s{};
        if (mode == "barrier") {
            s = barrier;
        } else if (mode == "random") {
            bool ok = false;
            for (int tries = 0; tries < 100 && !ok; ++tries) {
                s = random_seq(r);
                if (make_oddperfect(s, r, odd_steps) &&
                    half_product(s, 0) == -1 && half_product(s, 1) == -1) ok = true;
            }
            if (!ok) continue;
        } else {
            throw std::runtime_error("mode must be random or barrier");
        }

        const auto z = walk(s, r, steps, tenure_lo, tenure_hi);
        vals[rr] = z.e;
#pragma omp critical
        {
            if (z.e < global_best) {
                global_best = z.e;
                global_s = z.s;
                std::cout << "BEST e=" << global_best << " run=" << rr
                          << " step=" << z.step << " seq=" << fmt(global_s) << "\n" << std::flush;
            }
        }
    }

    std::vector<long long> good;
    for (auto v : vals) if (v >= 0) good.push_back(v);
    std::sort(good.begin(), good.end());
    const double sec = std::chrono::duration<double>(std::chrono::steady_clock::now() - t0).count();
    std::cout << "SUMMARY good=" << good.size() << " best=" << global_best
              << " median=" << (good.empty() ? -1 : good[good.size() / 2])
              << " seconds=" << sec << " hp=" << half_product(global_s, 0)
              << "," << half_product(global_s, 1) << " seq=" << fmt(global_s) << "\n";
    return global_best <= 574 ? 0 : 1;
}
