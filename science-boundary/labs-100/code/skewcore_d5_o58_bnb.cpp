// Exact E<=574 feasibility for the first odd-defect layer (odd energy O=58)
// inside the d=5 boundary + skew95-core family.
//
// Normalize s0=s1=+1 with the standard global-sign/alternation symmetries.
// Write u_j=s_{2j+1}, v_j=s_{2j+2}.  A skew95 suffix on positions 5..99
// obeys u_{51-j}=-u_j and v_{50-j}=v_j (center v_25=s_52).
//
// For low odd lag k=2j+1, C_k is the five-term boundary form
//   u_j + v_j + b2*u_{j+1} + b3*v_{j+1} + b4*u_{j+2}.
// Its paired high-lag correlation is available at the same recurrence step.
// O=58 means exactly one of the 25 opposite odd-lag pairs is
//   (1,3),(3,1),(-1,-3),(-3,-1),
// while every other pair is (1,-1) or (-1,1).
//
// The skew95 reflection makes the odd-position half-sum exactly 1+b3, so O=58
// forces b3=+1.  If the unique defect pair is positive/negative then ab=+/-4;
// with b=2 this forces the even-position half-sum a=+/-2 respectively.
// These sign-sum constraints are used as exact pruning conditions.
//
// For the LABS target E<=574, O=58 leaves even-lag energy <=516.  The BnB
// tracks all currently fixed same-parity products.  For an even lag k, if F_k
// is the fixed sum and U_k products are still unknown, every completion has
// |C_k| >= max(0,|F_k|-U_k).  Summing these squares is a rigorous lower bound.
//
// A debug/independent structural witness used while developing this code is:
// ++-+------+---+---+---+---+---+---+---+---+---+---+-++++-+++-+++-+++-+++-+++-+++-+++-+++-+++-+++-+-+
// It has exact total energy 33630, odd energy 58, half-sums (-2,2), and the
// unique defect pair at k=5.  The target search below does not rely on it.

#include <algorithm>
#include <array>
#include <atomic>
#include <cmath>
#include <cstdint>
#include <iostream>
#include <string>
#include <vector>
#ifdef _OPENMP
#include <omp.h>
#endif

using S = std::array<int8_t,100>;
using U = std::array<uint8_t,100>;
using I = std::array<int,100>;

struct State {
    S s{};
    U used{};
    I corr{}, count{}; // even-lag fixed product sums / fixed product counts
    std::array<int,50> u{}, v{};
};

static inline void assign_pos(State& st, int p, int x) {
    // Only same-parity positions contribute to even-lag correlations.
    for (int j = (p & 1); j < 100; j += 2) if (st.used[j]) {
        int k = std::abs(p - j);
        if (k) {
            st.corr[k] += x * int(st.s[j]);
            st.count[k]++;
        }
    }
    st.s[p] = int8_t(x);
    st.used[p] = 1;
}

static inline void unassign_pos(State& st, int p) {
    int x = st.s[p];
    st.used[p] = 0;
    for (int j = (p & 1); j < 100; j += 2) if (st.used[j]) {
        int k = std::abs(p - j);
        if (k) {
            st.corr[k] -= x * int(st.s[j]);
            st.count[k]--;
        }
    }
    st.s[p] = 0;
}

// 0 = normal pair, +1/-1 = positive/negative O=58 defect, 99 = forbidden.
static inline int pair_type(int a, int b) {
    if ((a == 1 && b == -1) || (a == -1 && b == 1)) return 0;
    if ((a == 1 && b == 3) || (a == 3 && b == 1)) return 1;
    if ((a == -1 && b == -3) || (a == -3 && b == -1)) return -1;
    return 99;
}

struct Changes { std::array<int,4> p{}; int n = 0; };

static inline Changes apply_pair(State& st, int n, int un, int vn) {
    Changes ch;
    const int pu = 2*n + 1, qu = 103 - 2*n;
    const int pv = 2*n + 2, qv = 102 - 2*n;
    assign_pos(st, pu, un); ch.p[ch.n++] = pu;
    if (qu != pu) { assign_pos(st, qu, -un); ch.p[ch.n++] = qu; }
    assign_pos(st, pv, vn); ch.p[ch.n++] = pv;
    if (qv != pv) { assign_pos(st, qv, vn); ch.p[ch.n++] = qv; }
    st.u[n] = un; st.v[n] = vn;
    return ch;
}

static inline void undo(State& st, const Changes& ch) {
    for (int i = ch.n - 1; i >= 0; --i) unassign_pos(st, ch.p[i]);
}

static inline long long lower_bound_even(const State& st) {
    long long e = 0;
    for (int k = 2; k < 100; k += 2) {
        int unknown = (100 - k) - st.count[k];
        int m = std::max(0, std::abs(st.corr[k]) - unknown);
        e += 1LL * m * m;
        if (e > 516) return e;
    }
    return e;
}

static inline long long exact_even(const State& st) {
    long long e = 0;
    for (int k = 2; k < 100; k += 2) e += 1LL * st.corr[k] * st.corr[k];
    return e;
}

// vsum is sum(v_j) over assigned reflected-pair variables j=2..n-1, j<25.
static inline bool even_half_sum_possible(int n, int b2, int b4, int vsum, int defect_sign) {
    if (n == 26) return true; // v25 is already assigned and is checked exactly at leaf.
    int base = 1 + b2 + b4 + 2*vsum;
    int remaining_pairs = std::max(0, 25 - n); // v_n..v_24
    int lo = base - 2*remaining_pairs - 1;      // final +/- center v25
    int hi = base + 2*remaining_pairs + 1;
    auto possible = [&](int target) { return lo <= target && target <= hi; };
    if (defect_sign > 0) return possible(2);
    if (defect_sign < 0) return possible(-2);
    return possible(2) || possible(-2);
}

struct Task {
    State st;
    int n = 0, defect_sign = 0, b2 = 0, b3 = 1, b4 = 0, vsum = 0;
};

static void generate_tasks(State& st, int n, int defect_sign,
                           int b2, int b3, int b4, int vsum, int split,
                           std::vector<Task>& out) {
    if (lower_bound_even(st) > 516 ||
        !even_half_sum_possible(n, b2, b4, vsum, defect_sign)) return;
    if (n == split) {
        out.push_back({st, n, defect_sign, b2, b3, b4, vsum});
        return;
    }
    for (int un : {-1,1}) {
        int low = st.u[n-2] + st.v[n-2] + b2*st.u[n-1] + b3*st.v[n-1] + b4*un;
        int high;
        if (n == 2) high = -un; // C_99
        else if (n == 3) high = -un + st.v[n-1] - b2*st.u[n-1]; // C_97
        else high = -un + st.v[n-1] - b2*st.u[n-1]
                    + b3*st.v[n-2] - b4*st.u[n-2];
        int t = pair_type(low, high);
        if (t == 99 || (t != 0 && defect_sign != 0)) continue;
        int next_defect = t ? t : defect_sign;
        for (int vn : {-1,1}) {
            Changes ch = apply_pair(st, n, un, vn);
            generate_tasks(st, n+1, next_defect, b2, b3, b4,
                           vsum + (n < 25 ? vn : 0), split, out);
            undo(st, ch);
        }
    }
}

static void dfs(State& st, int n, int defect_sign,
                int b2, int b3, int b4, int vsum,
                std::atomic<bool>& found,
                std::atomic<unsigned long long>& nodes) {
    if (found.load(std::memory_order_relaxed)) return;
    nodes.fetch_add(1, std::memory_order_relaxed);
    if (lower_bound_even(st) > 516 ||
        !even_half_sum_possible(n, b2, b4, vsum, defect_sign)) return;

    if (n == 26) {
        // Last opposite odd-lag pair C_49,C_51.
        int low = st.u[24] + st.v[24] + (b2-b4)*st.u[25] + b3*st.v[25];
        int high = (1-b2)*st.u[25] + st.v[25] + b3*st.v[24] - b4*st.u[24];
        int t = pair_type(low, high);
        if (t == 99) return;
        int next_defect = defect_sign;
        if (t != 0) {
            if (next_defect != 0) return;
            next_defect = t;
        }
        if (next_defect == 0) return;

        int asum = 1 + b2 + b4 + 2*vsum + st.v[25];
        if (asum != 2*next_defect) return;
        if (exact_even(st) <= 516) found.store(true, std::memory_order_relaxed);
        return;
    }

    for (int un : {-1,1}) {
        int low = st.u[n-2] + st.v[n-2] + b2*st.u[n-1] + b3*st.v[n-1] + b4*un;
        int high;
        if (n == 2) high = -un;
        else if (n == 3) high = -un + st.v[n-1] - b2*st.u[n-1];
        else high = -un + st.v[n-1] - b2*st.u[n-1]
                    + b3*st.v[n-2] - b4*st.u[n-2];
        int t = pair_type(low, high);
        if (t == 99 || (t != 0 && defect_sign != 0)) continue;
        int next_defect = t ? t : defect_sign;
        for (int vn : {-1,1}) {
            Changes ch = apply_pair(st, n, un, vn);
            dfs(st, n+1, next_defect, b2, b3, b4,
                vsum + (n < 25 ? vn : 0), found, nodes);
            undo(st, ch);
            if (found.load(std::memory_order_relaxed)) return;
        }
    }
}

int main(int argc, char** argv) {
    int threads = 4, split = 10;
    for (int i = 1; i < argc; ++i) {
        std::string a = argv[i];
        if (a == "--threads" && i+1 < argc) threads = std::stoi(argv[++i]);
        else if (a == "--split" && i+1 < argc) split = std::stoi(argv[++i]);
        else return 2;
    }

    // O=58 plus skew95 forces b3=+1, so only four normalized prefixes remain.
    std::vector<Task> tasks;
    for (int b2 : {-1,1}) {
        int b3 = 1;
        for (int b4 : {-1,1}) {
            State st;
            assign_pos(st,0,1); assign_pos(st,1,1); assign_pos(st,2,b2);
            assign_pos(st,3,b3); assign_pos(st,4,b4);
            st.u[0]=1; st.v[0]=b2; st.u[1]=b3; st.v[1]=b4;
            generate_tasks(st,2,0,b2,b3,b4,0,split,tasks);
        }
    }

    std::atomic<bool> found{false};
    std::atomic<unsigned long long> nodes{0};
#ifdef _OPENMP
    omp_set_num_threads(threads);
#endif
#pragma omp parallel for schedule(dynamic,1)
    for (size_t i = 0; i < tasks.size(); ++i) {
        if (found.load(std::memory_order_relaxed)) continue;
        State st = tasks[i].st;
        dfs(st, tasks[i].n, tasks[i].defect_sign,
            tasks[i].b2, tasks[i].b3, tasks[i].b4, tasks[i].vsum,
            found, nodes);
    }

    std::cout << "RESULT status=" << (found.load() ? "FOUND" : "INFEASIBLE")
              << " target=574 odd=58 even_cap=516"
              << " tasks=" << tasks.size() << " nodes=" << nodes.load() << "\n";
    return found.load() ? 1 : 0;
}
