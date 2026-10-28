// Exact targeted Hamming-shell scanner for the first non-odd-perfect layer O=58.
//
// For any N=100 sequence with odd-lag energy O=58, the sums of the even- and
// odd-position parity halves have magnitudes 2 and 2.  Relative to a supplied
// center, this lets us discard almost all subsets before touching correlations.
// We enumerate only exact-radius flip subsets whose final half sums are +/-2,
// then test O=58 and record the minimum full LABS energy exactly.
#include <algorithm>
#include <array>
#include <chrono>
#include <climits>
#include <cstdint>
#include <iostream>
#include <string>
#include <vector>
#ifdef _OPENMP
#include <omp.h>
#endif
using S = std::array<int8_t, 100>;
using C = std::array<int, 100>;

static long long exact(const S& s, C* out, long long& odd) {
    C c{};
    long long e = 0;
    odd = 0;
    for (int k = 1; k < 100; k++) {
        int x = 0;
        for (int i = 0; i < 100 - k; i++) x += int(s[i]) * int(s[i + k]);
        c[k] = x;
        const long long q = 1LL * x * x;
        e += q;
        if (k & 1) odd += q;
    }
    if (out) *out = c;
    return e;
}

static void flip(S& s, C& c, long long& e, long long& odd, int p) {
    const int sp = s[p];
    for (int k = 1; k < 100; k++) {
        int t = 0;
        if (p + k < 100) t += sp * int(s[p + k]);
        if (p - k >= 0) t += int(s[p - k]) * sp;
        if (!t) continue;
        const int d = -2 * t;
        const long long de = 2LL * c[k] * d + 1LL * d * d;
        e += de;
        if (k & 1) odd += de;
        c[k] += d;
    }
    s[p] = -s[p];
}

static S parse(const std::string& z) {
    if (z.size() != 100) throw std::runtime_error("sequence must have length 100");
    S s{};
    for (int i = 0; i < 100; i++) {
        if (z[i] == '+') s[i] = 1;
        else if (z[i] == '-') s[i] = -1;
        else throw std::runtime_error("sequence must contain only +/-");
    }
    return s;
}

static std::string format(const S& s) {
    std::string z;
    z.reserve(100);
    for (auto v : s) z += v > 0 ? '+' : '-';
    return z;
}

static unsigned long long choose(int n, int k) {
    if (k < 0 || k > n) return 0;
    __int128 x = 1;
    for (int i = 1; i <= k; i++) x = x * (n - k + i) / i;
    return (unsigned long long)x;
}

struct Pattern {
    std::array<int, 4> need{};  // even+, even-, odd+, odd- flips
    long long a = 0, b = 0;
    unsigned long long expected = 0;
};
struct Result {
    unsigned long long tested = 0, odd58 = 0;
    long long best = LLONG_MAX;
    S seq{};
};

static void enumerate_groups(int g, const std::array<std::vector<int>, 4>& idx,
                             const std::array<int, 4>& need, S& s, C& c,
                             long long& e, long long& odd, Result& out);

static void choose_group(int g, int at, int left,
                         const std::array<std::vector<int>, 4>& idx,
                         const std::array<int, 4>& need, S& s, C& c,
                         long long& e, long long& odd, Result& out) {
    if (left == 0) {
        enumerate_groups(g + 1, idx, need, s, c, e, odd, out);
        return;
    }
    const auto& v = idx[g];
    for (int j = at; j <= int(v.size()) - left; j++) {
        flip(s, c, e, odd, v[j]);
        choose_group(g, j + 1, left - 1, idx, need, s, c, e, odd, out);
        flip(s, c, e, odd, v[j]);
    }
}

static void enumerate_groups(int g, const std::array<std::vector<int>, 4>& idx,
                             const std::array<int, 4>& need, S& s, C& c,
                             long long& e, long long& odd, Result& out) {
    if (g == 4) {
        ++out.tested;
        if (odd == 58) {
            ++out.odd58;
            if (e < out.best) {
                out.best = e;
                out.seq = s;
            }
        }
        return;
    }
    choose_group(g, 0, need[g], idx, need, s, c, e, odd, out);
}

int main(int argc, char** argv) {
    if (argc < 3 || argc > 4) {
        std::cerr << "usage: sphere-odd58 <center> <radius> [threads]\n";
        return 2;
    }
    const S base = parse(argv[1]);
    const int radius = std::stoi(argv[2]);
    if (radius < 1 || radius > 20) return 2;
    int threads = argc == 4 ? std::stoi(argv[3]) : 4;
#ifdef _OPENMP
    omp_set_num_threads(threads);
#endif

    C base_corr{};
    long long base_odd = 0;
    const long long base_energy = exact(base, &base_corr, base_odd);
    long long a0 = 0, b0 = 0;
    std::array<std::vector<int>, 4> idx;
    for (int i = 0; i < 100; i++) {
        if ((i & 1) == 0) {
            a0 += base[i];
            idx[base[i] > 0 ? 0 : 1].push_back(i);
        } else {
            b0 += base[i];
            idx[base[i] > 0 ? 2 : 3].push_back(i);
        }
    }

    std::vector<Pattern> patterns;
    for (int ap = 0; ap <= radius; ap++)
        for (int am = 0; am <= radius - ap; am++)
            for (int bp = 0; bp <= radius - ap - am; bp++) {
                const int bm = radius - ap - am - bp;
                const long long a = a0 - 2 * ap + 2 * am;
                const long long b = b0 - 2 * bp + 2 * bm;
                if (std::abs(a) != 2 || std::abs(b) != 2) continue;
                Pattern p;
                p.need = {ap, am, bp, bm};
                p.a = a;
                p.b = b;
                p.expected = 1;
                for (int g = 0; g < 4; g++)
                    p.expected *= choose((int)idx[g].size(), p.need[g]);
                patterns.push_back(p);
            }

    std::vector<Result> partial(patterns.size());
    const auto started = std::chrono::steady_clock::now();
#pragma omp parallel for schedule(dynamic, 1)
    for (int pi = 0; pi < (int)patterns.size(); pi++) {
        S s = base;
        C c = base_corr;
        long long e = base_energy, odd = base_odd;
        enumerate_groups(0, idx, patterns[pi].need, s, c, e, odd, partial[pi]);
    }

    Result all;
    unsigned long long expected = 0;
    for (int pi = 0; pi < (int)patterns.size(); pi++) {
        const auto& p = patterns[pi];
        const auto& r = partial[pi];
        expected += p.expected;
        all.tested += r.tested;
        all.odd58 += r.odd58;
        if (r.best < all.best) {
            all.best = r.best;
            all.seq = r.seq;
        }
        std::cout << "PAT " << p.need[0] << ',' << p.need[1] << ','
                  << p.need[2] << ',' << p.need[3]
                  << " half=" << p.a << ',' << p.b
                  << " tested=" << r.tested << " expected=" << p.expected
                  << " odd58=" << r.odd58
                  << " best=" << (r.best == LLONG_MAX ? -1 : r.best) << "\n";
    }

    const double seconds = std::chrono::duration<double>(
        std::chrono::steady_clock::now() - started).count();
    std::cout << "SUMMARY radius=" << radius << " patterns=" << patterns.size()
              << " tested=" << all.tested << " expected=" << expected
              << " odd58=" << all.odd58
              << " best=" << (all.best == LLONG_MAX ? -1 : all.best)
              << " seconds=" << seconds << "\n";
    if (all.best != LLONG_MAX) std::cout << "BESTSEQ " << format(all.seq) << "\n";
    return all.tested == expected ? 0 : 1;
}
