#include <algorithm>
#include <array>
#include <chrono>
#include <climits>
#include <cstdint>
#include <iostream>
#include <string>
#ifdef _OPENMP
#include <omp.h>
#endif

using Seq = std::array<int8_t, 100>;
using Corr = std::array<int, 100>;

static long long exact(const Seq& s, Corr* out = nullptr) {
    Corr c{};
    long long e = 0;
    for (int k = 1; k < 100; ++k) {
        int x = 0;
        for (int i = 0; i < 100 - k; ++i) x += int(s[i]) * int(s[i + k]);
        c[k] = x;
        e += 1LL * x * x;
    }
    if (out) *out = c;
    return e;
}

static void flip(Seq& s, Corr& c, long long& e, int p) {
    const int sp = s[p];
    for (int k = 1; k < 100; ++k) {
        int t = 0;
        if (p + k < 100) t += sp * int(s[p + k]);
        if (p - k >= 0) t += int(s[p - k]) * sp;
        if (!t) continue;
        const int d = -2 * t;
        e += 2LL * c[k] * d + 1LL * d * d;
        c[k] += d;
    }
    s[p] = -s[p];
}

static Seq parse(const std::string& text) {
    if (text.size() != 100) throw std::runtime_error("sequence must have length 100");
    Seq s{};
    for (int i = 0; i < 100; ++i) {
        if (text[i] == '+') s[i] = 1;
        else if (text[i] == '-') s[i] = -1;
        else throw std::runtime_error("sequence must contain only + and -");
    }
    return s;
}

static std::string format(const Seq& s) {
    std::string out;
    out.reserve(100);
    for (auto x : s) out.push_back(x > 0 ? '+' : '-');
    return out;
}

struct LocalResult {
    unsigned long long count = 0;
    long long best = LLONG_MAX;
    Seq seq{};
};

static void dfs(Seq& s, Corr& c, long long& e, int start, int left, LocalResult& result) {
    if (left == 0) {
        ++result.count;
        if (e < result.best) {
            result.best = e;
            result.seq = s;
        }
        return;
    }
    for (int p = start; p <= 100 - left; ++p) {
        flip(s, c, e, p);
        dfs(s, c, e, p + 1, left - 1, result);
        flip(s, c, e, p);
    }
}

int main(int argc, char** argv) {
    if (argc < 3 || argc > 4) {
        std::cerr << "usage: sphere-shell <100-char +/- sequence> <radius> [threads]\n";
        return 2;
    }
    const Seq base = parse(argv[1]);
    const int radius = std::stoi(argv[2]);
    if (radius < 1 || radius > 10) return 2;

    int threads = 1;
#ifdef _OPENMP
    threads = argc == 4 ? std::stoi(argv[3]) : omp_get_max_threads();
    omp_set_num_threads(threads);
#endif

    Corr base_corr{};
    const long long base_energy = exact(base, &base_corr);
    unsigned long long total = 0;
    long long global_best = LLONG_MAX;
    Seq global_seq = base;
    const auto started = std::chrono::steady_clock::now();

#pragma omp parallel
    {
        LocalResult local;
#pragma omp for schedule(dynamic, 1) nowait
        for (int first = 0; first <= 100 - radius; ++first) {
            Seq s = base;
            Corr c = base_corr;
            long long e = base_energy;
            flip(s, c, e, first);
            dfs(s, c, e, first + 1, radius - 1, local);
        }
#pragma omp critical
        {
            total += local.count;
            if (local.best < global_best) {
                global_best = local.best;
                global_seq = local.seq;
            }
        }
    }

    const double seconds = std::chrono::duration<double>(
        std::chrono::steady_clock::now() - started).count();
    std::cout << "BASE energy=" << base_energy << "\n";
    std::cout << "RADIUS radius=" << radius << " tested=" << total
              << " best=" << global_best << " seconds=" << seconds << "\n";
    std::cout << "BESTSEQ " << format(global_seq) << "\n";
    return 0;
}
