// Exhaust the target-relevant part of a Golay-52 double-deletion/interleaving family.
//
// A public length-26 binary Golay pair generates a length-52 pair
// A52=[A26,B26], B52=[A26,-B26].  Delete two symbols from each sequence to
// obtain length-50 parity halves A,B, then interleave them into an N=100 LABS
// sequence.  Since any LABS-100 candidate has odd-lag energy >=50, a total
// target <=574 requires even-lag energy <=524.  We screen all C(52,2)^2
// deletion pairs by that exact necessary condition, then enumerate 32
// post-deletion relative symmetries preserving the screened even energy.
//
// Pass any argument to jointly alternate the original length-52 pair before
// deletion; this covers the Golay equivalence not absorbed by deletion-index
// reversal, relative sign, swap, and post-deletion joint alternation.
#include <algorithm>
#include <array>
#include <cstdint>
#include <iostream>
#include <string>
#include <tuple>
#include <vector>

using S50 = std::array<int8_t, 50>;
using C49 = std::array<int16_t, 49>;
struct V { S50 s; C49 c; int e; int d1, d2; };

static C49 ac(const S50& s) {
    C49 c{};
    for (int k = 1; k < 50; ++k) {
        int x = 0;
        for (int i = 0; i < 50-k; ++i) x += int(s[i]) * int(s[i+k]);
        c[k-1] = x;
    }
    return c;
}
static int ace(const C49& c) {
    int e = 0;
    for (auto x : c) e += x*x;
    return e;
}
static std::vector<V> delvars(const std::array<int8_t,52>& base) {
    std::vector<V> out;
    out.reserve(1326);
    for (int d1 = 0; d1 < 52; ++d1) for (int d2 = d1+1; d2 < 52; ++d2) {
        S50 s{};
        int q = 0;
        for (int i = 0; i < 52; ++i) if (i != d1 && i != d2) s[q++] = base[i];
        auto c = ac(s);
        out.push_back({s, c, ace(c), d1, d2});
    }
    return out;
}
static S50 transform(S50 s, bool reverse, bool negate, bool alternate) {
    if (reverse) std::reverse(s.begin(), s.end());
    for (int i = 0; i < 50; ++i) {
        if (negate) s[i] = -s[i];
        if (alternate && (i & 1)) s[i] = -s[i];
    }
    return s;
}
static std::tuple<int,int,int> energy(const S50& a, const S50& b) {
    std::array<int8_t,100> s{};
    for (int i = 0; i < 50; ++i) { s[2*i] = a[i]; s[2*i+1] = b[i]; }
    int e = 0, odd = 0, even = 0;
    for (int k = 1; k < 100; ++k) {
        int c = 0;
        for (int i = 0; i < 100-k; ++i) c += int(s[i]) * int(s[i+k]);
        const int q = c*c;
        e += q;
        (k & 1 ? odd : even) += q;
    }
    return {e, odd, even};
}
static std::string format(const S50& a, const S50& b) {
    std::string z;
    z.reserve(100);
    for (int i = 0; i < 50; ++i) {
        z += a[i] > 0 ? '+' : '-';
        z += b[i] > 0 ? '+' : '-';
    }
    return z;
}

int main(int argc, char**) {
    const int a26[26] = {1,1,1,1,-1,1,1,-1,-1,1,-1,1,-1,1,-1,-1,1,-1,1,1,1,-1,-1,1,1,1};
    const int b26[26] = {1,1,1,1,-1,1,1,-1,-1,1,-1,1,1,1,1,1,-1,1,-1,-1,-1,1,1,-1,-1,-1};
    std::array<int8_t,52> A{}, B{};
    for (int i = 0; i < 26; ++i) {
        A[i] = a26[i]; A[26+i] = b26[i];
        B[i] = a26[i]; B[26+i] = -b26[i];
    }
    if (argc > 1) for (int i = 1; i < 52; i += 2) { A[i] = -A[i]; B[i] = -B[i]; }

    auto va = delvars(A), vb = delvars(B);
    long long screened = 0, tested = 0;
    int best = 1 << 30, best_odd = 0, best_even = 0, bi = 0, bj = 0, best_mask = 0;
    S50 best_a{}, best_b{};

    for (int i = 0; i < (int)va.size(); ++i) for (int j = 0; j < (int)vb.size(); ++j) {
        int dot = 0;
        for (int k = 0; k < 49; ++k) dot += va[i].c[k] * vb[j].c[k];
        const int even_energy = va[i].e + vb[j].e + 2*dot;
        if (even_energy > 524) continue;
        ++screened;

        for (int ra = 0; ra < 2; ++ra)
        for (int rb = 0; rb < 2; ++rb)
        for (int nb = 0; nb < 2; ++nb)
        for (int alt = 0; alt < 2; ++alt)
        for (int sw = 0; sw < 2; ++sw) {
            S50 a = transform(va[i].s, ra, false, alt);
            S50 b = transform(vb[j].s, rb, nb, alt);
            if (sw) std::swap(a, b);
            auto [e, odd, even] = energy(a, b);
            ++tested;
            if (even != even_energy) {
                std::cerr << "even-energy consistency check failed\n";
                return 2;
            }
            if (e < best) {
                best = e; best_odd = odd; best_even = even; bi = i; bj = j;
                best_mask = ra | (rb<<1) | (nb<<2) | (alt<<3) | (sw<<4);
                best_a = a; best_b = b;
            }
        }
    }

    std::cout << "SUMMARY prealternate=" << (argc > 1 ? 1 : 0)
              << " screened=" << screened << " transformed=" << tested
              << " best=" << best << " odd=" << best_odd << " even=" << best_even
              << " delsA=" << va[bi].d1 << ',' << va[bi].d2
              << " delsB=" << vb[bj].d1 << ',' << vb[bj].d2
              << " mask=" << best_mask << " seq=" << format(best_a, best_b) << "\n";
    return 0;
}
