#include <array>
#include <cstdint>
#include <iostream>
#include <limits>
#include <string>

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

static std::string format(const Seq& s) {
    std::string out;
    out.reserve(100);
    for (auto x : s) out.push_back(x > 0 ? '+' : '-');
    return out;
}

static long long best_energy;
static Seq best_seq;
static unsigned long long count_seen = 0;

static void dfs(Seq& s, Corr& c, long long& e, int start, int left) {
    if (left == 0) {
        ++count_seen;
        if (e < best_energy) {
            best_energy = e;
            best_seq = s;
            std::cout << "BEST energy=" << best_energy << " count=" << count_seen
                      << " seq=" << format(best_seq) << "\n";
        }
        return;
    }
    for (int p = start; p <= 100 - left; ++p) {
        flip(s, c, e, p);
        dfs(s, c, e, p + 1, left - 1);
        flip(s, c, e, p);
    }
}

int main(int argc, char** argv) {
    if (argc != 3) {
        std::cerr << "usage: sphere <100-char +/- sequence> <max-radius>\n";
        return 2;
    }
    const std::string text = argv[1];
    const int max_radius = std::stoi(argv[2]);
    if (text.size() != 100 || max_radius < 1 || max_radius > 8) return 2;

    Seq base{};
    for (int i = 0; i < 100; ++i) {
        if (text[i] == '+') base[i] = 1;
        else if (text[i] == '-') base[i] = -1;
        else return 2;
    }

    Corr base_corr{};
    const long long base_energy = exact(base, &base_corr);
    best_energy = base_energy;
    best_seq = base;
    std::cout << "BASE energy=" << base_energy << "\n";

    for (int radius = 1; radius <= max_radius; ++radius) {
        auto s = base;
        auto c = base_corr;
        auto e = base_energy;
        const auto before = count_seen;
        dfs(s, c, e, 0, radius);
        std::cout << "RADIUS radius=" << radius
                  << " tested=" << (count_seen - before)
                  << " cumulative=" << count_seen
                  << " best=" << best_energy << "\n";
    }
    return 0;
}
