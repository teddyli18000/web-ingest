// Exact 0/1-helper lower-bound frontier for independently oriented front/final
// product planes in the live p008 102-gate field representation.
//
// This is stronger than distinct-target counting but still only a lower bound:
// middle correction values are charged only by abstract support, not as prelinear
// wires.  It exhausts all 3^18 front/final pairs implicitly after precomputing the
// 4^9 possible prelinear operand-union target sets and 3^9 output target sets.
//
// A target set with n non-input forms costs:
//   n     if target-only closure is possible;
//   n + 1 if one helper is sufficient;
//   >=n+2 otherwise.
// These are exact statements through one helper, hence rigorous lower bounds.

#include <array>
#include <cstdint>
#include <iostream>
#include <map>
#include <set>
#include <tuple>
#include <unordered_set>
#include <utility>
#include <vector>
#include <algorithm>

using namespace std;

struct Bits {
    array<uint64_t, 4> w{};
};

static inline void set_bit(Bits& b, int x) { b.w[x >> 6] |= 1ULL << (x & 63); }
static inline bool get_bit(const Bits& b, int x) { return (b.w[x >> 6] >> (x & 63)) & 1ULL; }
static inline int popcount(const Bits& b) {
    return __builtin_popcountll(b.w[0]) + __builtin_popcountll(b.w[1])
         + __builtin_popcountll(b.w[2]) + __builtin_popcountll(b.w[3]);
}

static bool is_input[256];
static array<pair<int,int>, 9> planes;
static array<pair<int,int>, 9> outpairs;
static const array<int,9> middle_cols = {4,1,2,14,10,8,3,5,13};

static array<uint8_t,256> closure(const Bits& targets) {
    array<uint8_t,256> available{};
    for (int i = 0; i < 8; ++i) available[1 << i] = 1;
    bool changed = true;
    while (changed) {
        changed = false;
        for (int t = 1; t < 256; ++t) {
            if (!get_bit(targets, t) || available[t]) continue;
            for (int a = 1; a < 256; ++a) {
                if (!available[a]) continue;
                int b = a ^ t;
                if (b && available[b]) {
                    available[t] = 1;
                    changed = true;
                    break;
                }
            }
        }
    }
    return available;
}

static bool closed(const Bits& targets, const array<uint8_t,256>& available) {
    for (int t = 1; t < 256; ++t)
        if (get_bit(targets, t) && !available[t]) return false;
    return true;
}

static int helper_lb_0(const Bits& targets) {
    int n = popcount(targets);
    return closed(targets, closure(targets)) ? n : n + 1;
}

static int helper_lb_1(const Bits& targets) {
    int n = popcount(targets);
    auto available = closure(targets);
    if (closed(targets, available)) return n;

    vector<int> values;
    for (int x = 1; x < 256; ++x) if (available[x]) values.push_back(x);
    bool seen[256]{};
    for (size_t i = 0; i < values.size(); ++i) {
        for (size_t j = i + 1; j < values.size(); ++j) {
            int h = values[i] ^ values[j];
            if (!h || available[h] || get_bit(targets, h) || is_input[h] || seen[h]) continue;
            seen[h] = true;
            Bits expanded = targets;
            set_bit(expanded, h);
            if (closed(targets, closure(expanded))) return n + 1;
        }
    }
    return n + 2;
}

static pair<int,int> orient(pair<int,int> p, int c) {
    int a = p.first, b = p.second;
    if (c == 0) return {a,b};
    if (c == 1) return {a,a^b};
    return {a^b,b};
}

static pair<int,int> dual_columns(pair<int,int> p, int c) {
    int a = p.first, b = p.second;
    if (c == 0) return {a,b};
    if (c == 1) return {a^b,b};
    return {a,a^b};
}

static int rank4(vector<int> v) {
    int basis[4]{}, rank = 0;
    for (int x : v) {
        int y = x;
        for (int p = 3; p >= 0; --p) if ((y >> p) & 1) {
            if (basis[p]) y ^= basis[p];
            else { basis[p] = y; ++rank; break; }
        }
    }
    return rank;
}

static int middle_support_lb(const array<int,9>& choices) {
    // Live-102 five correction values in the workspace local orientation convention.
    static const int base_correction[9] = {8,0,0,202,4,0,34,234,0};
    int wanted[4]{};
    for (int i = 0; i < 9; ++i) if (base_correction[i])
        for (int j = 0; j < 4; ++j) if ((middle_cols[i] >> j) & 1)
            wanted[j] ^= base_correction[i];

    for (int i = 0; i < 9; ++i) {
        auto [a,b] = planes[i];
        int offset = choices[i] == 0 ? 0 : (choices[i] == 1 ? a : b);
        if (offset)
            for (int j = 0; j < 4; ++j) if ((middle_cols[i] >> j) & 1)
                wanted[j] ^= offset;
    }

    vector<int> rhs;
    for (int bit = 0; bit < 8; ++bit) {
        int v = 0;
        for (int j = 0; j < 4; ++j) if ((wanted[j] >> bit) & 1) v |= 1 << j;
        if (v) rhs.push_back(v);
    }
    int rr = rank4(rhs);

    for (int support = 0; support <= 9; ++support) {
        for (int mask = 0; mask < (1 << 9); ++mask) {
            if (__builtin_popcount((unsigned)mask) != support) continue;
            vector<int> cols;
            for (int i = 0; i < 9; ++i) if ((mask >> i) & 1) cols.push_back(middle_cols[i]);
            int r = rank4(cols);
            if (r < rr) continue;
            bool ok = true;
            for (int v : rhs) {
                auto tmp = cols;
                tmp.push_back(v);
                if (rank4(tmp) > r) { ok = false; break; }
            }
            if (ok) return support;
        }
    }
    return 99;
}

int main() {
    for (int i = 0; i < 8; ++i) is_input[1 << i] = true;

    int x[8]; for (int i = 0; i < 8; ++i) x[i] = 1 << i;
    vector<int> q;
    q.push_back(x[5]^x[0]); q.push_back(x[1]^x[5]); q.push_back(q[1]^x[2]);
    q.push_back(q[2]^x[0]); q.push_back(q[2]^x[6]); q.push_back(x[0]^x[1]);
    q.push_back(q[5]^x[4]); q.push_back(q[6]^q[4]); q.push_back(q[7]^x[3]);
    q.push_back(q[8]^x[7]); q.push_back(q[9]^q[3]); q.push_back(q[9]^q[5]);
    q.push_back(q[10]^x[4]); q.push_back(q[11]^x[6]); q.push_back(q[12]^x[5]);
    q.push_back(q[12]^q[0]); q.push_back(q[14]^q[8]); q.push_back(q[16]^q[10]);
    planes = {{{q[11],q[10]},{q[3],q[12]},{q[15],q[2]},{q[8],q[7]},
               {x[6],q[17]},{q[4],x[7]},{q[13],q[16]},{q[9],q[6]},{q[0],q[14]}}};

    const int output_columns[18] = {200,230,68,227,185,8,113,183,241,
                                    17,64,245,128,16,84,1,136,19};
    for (int i = 0; i < 9; ++i) outpairs[i] = {output_columns[i], output_columns[i+9]};

    constexpr int N = 19683;
    vector<array<int,9>> choices(N);
    vector<int> middle(N), output_lb(N);
    vector<Bits> output_bits(N);
    for (int id = 0; id < N; ++id) {
        int z = id;
        for (int i = 8; i >= 0; --i) { choices[id][i] = z % 3; z /= 3; }
        middle[id] = middle_support_lb(choices[id]);
        Bits t;
        for (int i = 0; i < 9; ++i) {
            auto p = dual_columns(outpairs[i], choices[id][i]);
            for (int v : {p.first,p.second}) if (v && !is_input[v]) set_bit(t,v);
        }
        output_bits[id] = t;
        output_lb[id] = helper_lb_0(t);
    }

    constexpr int U = 262144; // 4^9: equal orientation 0/1/2, or front!=final union state 3.
    vector<int> pre_lb(U);
    vector<Bits> pre_bits(U);
    for (int id = 0; id < U; ++id) {
        int z = id;
        Bits t;
        for (int i = 8; i >= 0; --i) {
            int state = z & 3; z >>= 2;
            if (state < 3) {
                auto p = orient(planes[i], state);
                for (int v : {p.first,p.second}) if (v && !is_input[v]) set_bit(t,v);
            } else {
                auto [a,b] = planes[i];
                for (int v : {a,b,a^b}) if (v && !is_input[v]) set_bit(t,v);
            }
        }
        pre_bits[id] = t;
        pre_lb[id] = helper_lb_0(t);
    }

    auto union_id = [&](const array<int,9>& f, const array<int,9>& g) {
        int id = 0;
        for (int i = 0; i < 9; ++i) id = (id << 2) | (f[i] == g[i] ? f[i] : 3);
        return id;
    };

    unordered_set<int> union_survivors, output_survivors, front_survivors;
    long long pass0 = 0;
    for (int f = 0; f < N; ++f) for (int g = 0; g < N; ++g) {
        int u = union_id(choices[f], choices[g]);
        if (pre_lb[u] + middle[f] + output_lb[g] <= 36) {
            ++pass0;
            union_survivors.insert(u); output_survivors.insert(g); front_survivors.insert(f);
        }
    }
    if (pass0 != 464931) return 2;

    for (int u : union_survivors) pre_lb[u] = helper_lb_1(pre_bits[u]);
    for (int g : output_survivors) output_lb[g] = helper_lb_1(output_bits[g]);

    map<int,long long> score_hist, distance_hist;
    long long pass1 = 0;
    for (int f : front_survivors) for (int g : output_survivors) {
        int u = union_id(choices[f], choices[g]);
        if (!union_survivors.count(u)) continue;
        int score = pre_lb[u] + middle[f] + output_lb[g];
        if (score > 36) continue;
        ++pass1;
        ++score_hist[score];
        int d = 0; for (int i = 0; i < 9; ++i) d += choices[f][i] != choices[g][i];
        ++distance_hist[d];
    }

    const map<int,long long> expected_scores = {{35,136},{36,9625}};
    const map<int,long long> expected_distances = {{0,1557},{1,3320},{2,3770},{3,1114}};
    if (pass1 != 9761 || score_hist != expected_scores || distance_hist != expected_distances) return 3;

    cout << "pass0=" << pass0 << " pass1=" << pass1 << "\n";
    cout << "scores"; for (auto [k,v] : score_hist) cout << " " << k << ":" << v; cout << "\n";
    cout << "distance"; for (auto [k,v] : distance_hist) cout << " " << k << ":" << v; cout << "\n";
    cout << "strict_decoupled_survivors=" << (pass1 - distance_hist[0]) << "\n";
    return 0;
}
