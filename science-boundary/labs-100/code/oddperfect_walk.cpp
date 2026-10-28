// Search the broad N=100 manifold with parity-minimal odd-lag energy.
//
// Phase 1: from a random unrestricted sequence, tabu-search only the odd-lag
// energy until all 50 odd autocorrelations have magnitude 1 (odd energy 50).
// Phase 2: stay exactly on that manifold and tabu-search one-/two-bit moves
// whose resulting odd autocorrelations are still all +/-1. Candidate moves are
// rejected as soon as one odd lag violates the condition, then scored on the
// even lags. Debug builds periodically recompute the full energy independently.
#include <algorithm>
#include <array>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <iostream>
#include <limits>
#include <random>
#include <stdexcept>
#include <string>
#include <vector>
#ifdef _OPENMP
#include <omp.h>
#endif

using S = std::array<int8_t, 100>;
using C = std::array<int, 100>;
constexpr int N = 100;
static const std::string INC =
    "++++++--+++++-----++-++--+--++++++++++---+-++--++++-+--++----+--+-+-+-+-++---++---++-+-++-+-++--+-+-";

static long long exact(const S& s, C* out = nullptr, long long* oddout = nullptr) {
    C c{};
    long long e = 0, o = 0;
    for (int k = 1; k < N; k++) {
        int x = 0;
        for (int i = 0; i < N - k; i++) x += int(s[i]) * int(s[i + k]);
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
    for (int i = 0; i < N; i++) {
        if (z[i] == '+') s[i] = 1;
        else if (z[i] == '-') s[i] = -1;
        else throw std::runtime_error("sequence must contain only + and -");
    }
    return s;
}

static std::string fmt(const S& s) {
    std::string z;
    z.reserve(N);
    for (auto v : s) z += v > 0 ? '+' : '-';
    return z;
}

static S randoms(std::mt19937_64& r) {
    S s{};
    for (auto& v : s) v = (r() & 1) ? 1 : -1;
    return s;
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
    for (int k = 1; k < N; k++) {
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
    for (int st = 1; st <= max_steps; st++) {
        long long be = 1LL << 60;
        int bp = -1, ties = 0;
        for (int p = 0; p < N; p++) {
            const long long ne = odd_flip_eval(s, c, o, p);
            if (st < tabu[p] && ne >= best) continue;
            if (ne < be) {
                be = ne;
                bp = p;
                ties = 1;
            } else if (ne == be && r() % ++ties == 0) {
                bp = p;
            }
        }
        if (bp < 0) {
            tabu.fill(0);
            continue;
        }
        flip1(s, c, e, o, bp);
        tabu[bp] = st + 5 + int(r() % 11);
        if (o < best) best = o;
        if (o == 50) return true;
    }
    return false;
}

struct Eval {
    bool ok = false;
    long long e = 0;
};

// Evaluate a one- or two-bit move from an odd-perfect state.  If q<0 this is
// a one-bit move.  For a pair, the p-q product is incident to both flipped
// variables but is unchanged, so subtract its double-counted contribution.
static Eval move_eval(const S& s, const C& c, int p, int q) {
    long long even = 0;
    const int pqprod = q >= 0 ? int(s[p]) * int(s[q]) : 0;
    const int dist = q >= 0 ? std::abs(q - p) : -1;
    for (int k = 1; k < N; k += 2) {
        int t = contrib(s, p, k);
        if (q >= 0) t += contrib(s, q, k);
        if (q >= 0 && k == dist) t -= 2 * pqprod;
        const int cp = c[k] - 2 * t;
        if (std::abs(cp) != 1) return {};
    }
    for (int k = 2; k < N; k += 2) {
        int t = contrib(s, p, k);
        if (q >= 0) t += contrib(s, q, k);
        if (q >= 0 && k == dist) t -= 2 * pqprod;
        const int cp = c[k] - 2 * t;
        even += 1LL * cp * cp;
    }
    return {true, 50 + even};
}

static void move_apply(S& s, C& c, long long& e, int p, int q) {
    const int pqprod = q >= 0 ? int(s[p]) * int(s[q]) : 0;
    const int dist = q >= 0 ? std::abs(q - p) : -1;
    long long ne = 0;
    for (int k = 1; k < N; k++) {
        int t = contrib(s, p, k);
        if (q >= 0) t += contrib(s, q, k);
        if (q >= 0 && k == dist) t -= 2 * pqprod;
        const int cp = c[k] - 2 * t;
        c[k] = cp;
        ne += 1LL * cp * cp;
    }
    s[p] = -s[p];
    if (q >= 0) s[q] = -s[q];
    e = ne;
}

struct Result {
    long long e;
    S s;
    int step;
    long long evals;
};

static Result walk(S s, std::mt19937_64& r, int steps, int tenlo, int tenhi,
                   long long target) {
    C c{};
    long long o = 0;
    long long e = exact(s, &c, &o);
    if (o != 50) throw std::runtime_error("start is not odd-perfect");
    long long best = e;
    S bs = s;
    std::array<int, N> tabu{};
    long long evals = 0;
    int beststep = 0;

    for (int st = 1; st <= steps; st++) {
        long long me = 1LL << 60;
        int mp = -1, mq = -1, ties = 0;
        bool any_ok = false;

        for (int p = 0; p < N; p++) {
            const auto z = move_eval(s, c, p, -1);
            evals++;
            if (!z.ok) continue;
            any_ok = true;
            if (st < tabu[p] && z.e >= best) continue;
            if (z.e < me) {
                me = z.e;
                mp = p;
                mq = -1;
                ties = 1;
            } else if (z.e == me && r() % ++ties == 0) {
                mp = p;
                mq = -1;
            }
        }

        for (int p = 0; p < N; p++) {
            for (int q = p + 1; q < N; q++) {
                const auto z = move_eval(s, c, p, q);
                evals++;
                if (!z.ok) continue;
                any_ok = true;
                if ((st < tabu[p] || st < tabu[q]) && z.e >= best) continue;
                if (z.e < me) {
                    me = z.e;
                    mp = p;
                    mq = q;
                    ties = 1;
                } else if (z.e == me && r() % ++ties == 0) {
                    mp = p;
                    mq = q;
                }
            }
        }

        if (mp < 0) {
            if (!any_ok) return {best, bs, beststep, evals};
            tabu.fill(0);
            continue;
        }

        move_apply(s, c, e, mp, mq);
        tabu[mp] = st + tenlo + int(r() % (tenhi - tenlo + 1));
        if (mq >= 0) tabu[mq] = st + tenlo + int(r() % (tenhi - tenlo + 1));
        if (e < best) {
            best = e;
            bs = s;
            beststep = st;
            if (best <= target) return {best, bs, st, evals};
        }

#ifndef NDEBUG
        if ((st & 1023) == 0) {
            long long oo = 0;
            const long long ee = exact(s, nullptr, &oo);
            if (ee != e || oo != 50) {
                std::cerr << "incremental mismatch\n";
                std::abort();
            }
        }
#endif
    }
    return {best, bs, beststep, evals};
}

int main(int argc, char** argv) {
    int runs = 8, steps = 20000, oddsteps = 20000, threads = 0;
    int tenlo = 5, tenhi = 15;
    uint64_t seed = 1;
    long long target = 574;
    std::string mode = "random";

    for (int i = 1; i < argc; i++) {
        const std::string a = argv[i];
        auto need = [&]() {
            if (i + 1 >= argc) throw std::runtime_error("missing value after " + a);
            return std::string(argv[++i]);
        };
        if (a == "--runs") runs = std::stoi(need());
        else if (a == "--steps") steps = std::stoi(need());
        else if (a == "--odd-steps") oddsteps = std::stoi(need());
        else if (a == "--seed") seed = std::stoull(need());
        else if (a == "--threads") threads = std::stoi(need());
        else if (a == "--tenure-lo") tenlo = std::stoi(need());
        else if (a == "--tenure-hi") tenhi = std::stoi(need());
        else if (a == "--mode") mode = need();
        else if (a == "--target") target = std::stoll(need());
        else throw std::runtime_error("unknown argument: " + a);
    }

#ifdef _OPENMP
    if (threads <= 0) threads = omp_get_max_threads();
    omp_set_num_threads(threads);
#else
    threads = 1;
#endif

    const S inc = parse(INC);
    long long io = 0;
    if (exact(inc, nullptr, &io) != 578 || io != 50)
        throw std::runtime_error("incumbent check failed");

    long long global_best = 1LL << 60;
    S global_seq = inc;
    std::vector<long long> vals(runs, 1LL << 60);
    const auto t0 = std::chrono::steady_clock::now();

#pragma omp parallel for schedule(dynamic, 1)
    for (int rr = 0; rr < runs; rr++) {
        std::mt19937_64 r(seed + 0x9e3779b97f4a7c15ULL * uint64_t(rr + 1));
        S s;
        if (mode == "incumbent") {
            s = inc;
        } else if (mode == "random") {
            s = randoms(r);
            if (!make_oddperfect(s, r, oddsteps)) {
                vals[rr] = -1;
                continue;
            }
        } else {
            throw std::runtime_error("mode must be random or incumbent");
        }
        const auto z = walk(s, r, steps, tenlo, tenhi, target);
        vals[rr] = z.e;
#pragma omp critical
        {
            if (z.e < global_best) {
                global_best = z.e;
                global_seq = z.s;
                std::cout << "BEST energy=" << global_best << " run=" << rr
                          << " step=" << z.step << " seq=" << fmt(global_seq)
                          << "\n" << std::flush;
            }
        }
    }

    const double seconds = std::chrono::duration<double>(
        std::chrono::steady_clock::now() - t0).count();
    std::vector<long long> good;
    for (auto v : vals) if (v >= 0) good.push_back(v);
    std::sort(good.begin(), good.end());
    std::cout << "SUMMARY mode=" << mode << " runs=" << runs
              << " steps=" << steps << " best=" << global_best
              << " median=" << (good.empty() ? -1 : good[good.size() / 2])
              << " seconds=" << seconds << " seq=" << fmt(global_seq) << "\n";
    return global_best <= target ? 0 : 1;
}
