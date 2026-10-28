// Exact first-index shard for one O=58 Hamming-shell combinatorial pattern.
//
// This complements sphere_odd58_pattern.cpp when one pattern is too large for
// a single Actions job. Positions are split into even+, even-, odd+, odd-.
// The caller fixes the slot of the first selected even+ position. These shards
// are disjoint and their expected counts sum to the unsplit pattern count.
// Within a shard, the second even+ choice is parallelized with OpenMP so the
// largest shard still uses all runner cores.
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

using S = std::array<int8_t,100>;
using C = std::array<int,100>;

static long long exact(const S& s, C* out, long long& odd) {
    C c{};
    long long e = 0;
    odd = 0;
    for (int k = 1; k < 100; ++k) {
        int x = 0;
        for (int i = 0; i < 100 - k; ++i) x += int(s[i]) * int(s[i + k]);
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
    for (int k = 1; k < 100; ++k) {
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
    for (int i = 0; i < 100; ++i) {
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
    for (int i = 1; i <= k; ++i) x = x * (n - k + i) / i;
    return (unsigned long long)x;
}

struct Result {
    unsigned long long tested = 0, odd58 = 0;
    long long best = LLONG_MAX;
    S seq{};
};

static void enumerate_groups(int g, const std::array<std::vector<int>,4>& idx,
                             const std::array<int,4>& need, S& s, C& c,
                             long long& e, long long& odd, Result& out);

static void choose_group(int g, int at, int left,
                         const std::array<std::vector<int>,4>& idx,
                         const std::array<int,4>& need, S& s, C& c,
                         long long& e, long long& odd, Result& out) {
    if (left == 0) {
        enumerate_groups(g + 1, idx, need, s, c, e, odd, out);
        return;
    }
    const auto& v = idx[g];
    for (int j = at; j <= int(v.size()) - left; ++j) {
        flip(s, c, e, odd, v[j]);
        choose_group(g, j + 1, left - 1, idx, need, s, c, e, odd, out);
        flip(s, c, e, odd, v[j]);
    }
}

static void enumerate_groups(int g, const std::array<std::vector<int>,4>& idx,
                             const std::array<int,4>& need, S& s, C& c,
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
    if (argc != 8) {
        std::cerr << "usage: sphere-odd58-pattern-first <center> <even+> <even-> <odd+> <odd-> <first-slot> <threads>\n";
        return 2;
    }
    const S base = parse(argv[1]);
    std::array<int,4> need{};
    for (int g = 0; g < 4; ++g) need[g] = std::stoi(argv[2 + g]);
    const int first = std::stoi(argv[6]);
    const int threads = std::stoi(argv[7]);
    if (need[0] <= 0) return 2;
#ifdef _OPENMP
    omp_set_num_threads(threads);
#endif

    C bc{};
    long long bo = 0;
    const long long be = exact(base, &bc, bo);
    long long a0 = 0, b0 = 0;
    std::array<std::vector<int>,4> idx;
    for (int i = 0; i < 100; ++i) {
        if ((i & 1) == 0) {
            a0 += base[i];
            idx[base[i] > 0 ? 0 : 1].push_back(i);
        } else {
            b0 += base[i];
            idx[base[i] > 0 ? 2 : 3].push_back(i);
        }
    }
    for (int g = 0; g < 4; ++g)
        if (need[g] < 0 || need[g] > int(idx[g].size())) return 2;

    const int first_count = int(idx[0].size()) - need[0] + 1;
    if (first < 0 || first >= first_count) return 2;
    const long long a = a0 - 2*need[0] + 2*need[1];
    const long long b = b0 - 2*need[2] + 2*need[3];
    if (std::abs(a) != 2 || std::abs(b) != 2) return 2;

    unsigned long long expected = choose(int(idx[0].size()) - first - 1, need[0] - 1);
    for (int g = 1; g < 4; ++g) expected *= choose(int(idx[g].size()), need[g]);

    const auto started = std::chrono::steady_clock::now();
    Result all;
    if (need[0] == 1) {
        S s = base; C c = bc; long long e = be, odd = bo;
        flip(s, c, e, odd, idx[0][first]);
        enumerate_groups(1, idx, need, s, c, e, odd, all);
    } else {
        const int second_begin = first + 1;
        const int second_end = int(idx[0].size()) - (need[0] - 1);
        const int nsecond = std::max(0, second_end - second_begin + 1);
        std::vector<Result> partial(nsecond);
#pragma omp parallel for schedule(dynamic,1)
        for (int q = 0; q < nsecond; ++q) {
            const int second = second_begin + q;
            S s = base; C c = bc; long long e = be, odd = bo;
            flip(s, c, e, odd, idx[0][first]);
            flip(s, c, e, odd, idx[0][second]);
            choose_group(0, second + 1, need[0] - 2,
                         idx, need, s, c, e, odd, partial[q]);
        }
        for (const auto& r : partial) {
            all.tested += r.tested;
            all.odd58 += r.odd58;
            if (r.best < all.best) { all.best = r.best; all.seq = r.seq; }
        }
    }

    const double seconds = std::chrono::duration<double>(
        std::chrono::steady_clock::now() - started).count();
    std::cout << "SHARD " << need[0] << ',' << need[1] << ',' << need[2] << ',' << need[3]
              << " first=" << first << " pos=" << idx[0][first]
              << " half=" << a << ',' << b
              << " tested=" << all.tested << " expected=" << expected
              << " odd58=" << all.odd58
              << " best=" << (all.best == LLONG_MAX ? -1 : all.best)
              << " seconds=" << seconds << "\n";
    if (all.best != LLONG_MAX) std::cout << "BESTSEQ " << format(all.seq) << "\n";
    return all.tested == expected ? 0 : 1;
}
