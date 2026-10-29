// Exact target search for the odd-perfect N=100 endpoint-defect-1 layer.
//
// Safe normalization inherited from oddperfect_outer_bnb.cpp:
//   sum(even positions)=a=2, sum(odd positions)=b=0, and s_1=+1.
// Defect 1 cannot occur on the left deletion because d_L is even, so the
// right deletion R=s[0..98] has exactly one nonzero odd autocorrelation.
//
// For a fixed defect lag h, a mod-4 reflection argument determines the entire
// skew-reflection defect pattern of R. Only one or two specified mirror pairs
// violate skew symmetry. After substituting those relations, the 49 odd
// autocorrelation equations of R contain at most four pair-products each.
// This reduces the normalized search to 50 binary variables.
//
// See ../results/2026-10-29-defect1-reflection-reduction.md for the proof.

#include <algorithm>
#include <array>
#include <atomic>
#include <chrono>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <map>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>
#ifdef _OPENMP
#include <omp.h>
#endif

constexpr int N = 100;
using Seq = std::array<int8_t, N>;
using Used = std::array<uint8_t, N>;
using Ints = std::array<int, N>;

struct State {
    Seq s{};
    Used used{};
    Ints fixed{}, count{};
    int sumA = 0, sumB = 0, countA = 0, countB = 0;
};

static void assign_pos(State& st, int p, int val) {
    if (st.used[p]) {
        if (st.s[p] != val) throw std::runtime_error("assignment conflict");
        return;
    }
    for (int j = 0; j < N; ++j) if (st.used[j]) {
        const int k = std::abs(p - j);
        if (k) {
            st.fixed[k] += val * int(st.s[j]);
            st.count[k]++;
        }
    }
    st.s[p] = int8_t(val);
    st.used[p] = 1;
    if ((p & 1) == 0) { st.sumA += val; st.countA++; }
    else { st.sumB += val; st.countB++; }
}

static void unassign_pos(State& st, int p) {
    if (!st.used[p]) return;
    const int val = st.s[p];
    if ((p & 1) == 0) { st.sumA -= val; st.countA--; }
    else { st.sumB -= val; st.countB--; }
    st.used[p] = 0;
    for (int j = 0; j < N; ++j) if (st.used[j]) {
        const int k = std::abs(p - j);
        if (k) {
            st.fixed[k] -= val * int(st.s[j]);
            st.count[k]--;
        }
    }
    st.s[p] = 0;
}

static bool sum_feasible(int cur, int used, int target) {
    const int rem = 50 - used;
    const int need = target - cur;
    return std::abs(need) <= rem && ((need - rem) & 1) == 0;
}

static bool reachable(int fixed, int unknown, int target) {
    const int d = target - fixed;
    return std::abs(d) <= unknown && ((d - unknown) & 1) == 0;
}

struct Term { int a, b, c; };
struct Equation {
    int lag = 0;
    int constant = 0;
    std::vector<Term> terms;
};

static std::array<int, 49> reflection_pattern(int h) {
    std::array<int, 49> rho{};
    rho.fill(1);
    if (h == 49) {
        rho[48] = -1;
    } else if (h < 49) {
        rho[h - 1] = -1;
        rho[h] = -1;
    } else {
        rho[98 - h] = -1;
        rho[99 - h] = -1;
    }
    return rho;
}

static std::pair<int,int> map_r_position(int p, const std::array<int,49>& rho) {
    if (p <= 49) return {p, 1};
    const int j = 98 - p;
    const int mult = (((49 - j) & 1) ? -1 : 1) * rho[j];
    return {j, mult};
}

static std::vector<Equation> make_equations(int h) {
    const auto left_rho = reflection_pattern(h);
    std::array<int,99> rho{};
    rho.fill(1);
    for (int j = 0; j < 49; ++j) {
        rho[j] = left_rho[j];
        rho[98 - j] = left_rho[j];
    }
    rho[49] = 1;

    std::vector<Equation> out;
    for (int k = 1; k <= 97; k += 2) {
        const int q = (99 - k) / 2;
        std::map<std::pair<int,int>, int> acc;
        int constant = 0;
        for (int i = 0; i < q; ++i) {
            const int j = 2 * q - 1 - i;
            const int diff = rho[i] - rho[j];
            if (!diff) continue;
            const int coeff = (((49 - i) & 1) ? -1 : 1) * (diff / 2);
            auto [a, ma] = map_r_position(i, left_rho);
            auto [b, mb] = map_r_position(j, left_rho);
            int c = coeff * ma * mb;
            if (a == b) {
                constant += c;
            } else {
                if (a > b) std::swap(a, b);
                acc[{a, b}] += c;
            }
        }
        Equation e;
        e.lag = k;
        e.constant = constant;
        for (const auto& [ab, c] : acc) if (c) e.terms.push_back({ab.first, ab.second, c});
        out.push_back(std::move(e));
    }
    return out;
}

static bool odd_deletion_equations_feasible(
    const State& st, const std::vector<Equation>& eqs, int defect_lag) {
    for (const auto& e : eqs) {
        int fixed = e.constant;
        int unknown = 0;
        for (const auto& t : e.terms) {
            if (st.used[t.a] && st.used[t.b])
                fixed += t.c * int(st.s[t.a]) * int(st.s[t.b]);
            else
                unknown += std::abs(t.c);
        }
        if (e.lag == defect_lag) {
            if (st.used[99]) {
                if (!reachable(fixed, unknown, -int(st.s[99]))) return false;
            } else if (!reachable(fixed, unknown, -1) &&
                       !reachable(fixed, unknown, +1)) {
                return false;
            }
        } else if (!reachable(fixed, unknown, 0)) {
            return false;
        }
    }
    return true;
}

static bool prune(const State& st, const std::vector<Equation>& eqs,
                  int defect_lag, int even_cap) {
    if (!sum_feasible(st.sumA, st.countA, 2) ||
        !sum_feasible(st.sumB, st.countB, 0)) return true;

    const int forced_pos = 99 - defect_lag;
    if (st.used[forced_pos] && st.s[forced_pos] != 1) return true;

    if (!odd_deletion_equations_feasible(st, eqs, defect_lag)) return true;

    int sum_lo = 0, sum_hi = 0;
    long long lb = 0;
    for (int k = 2; k < N; k += 2) {
        const int unknown = (N - k) - st.count[k];
        sum_lo += st.fixed[k] - unknown;
        sum_hi += st.fixed[k] + unknown;
        int mag = std::max(0, std::abs(st.fixed[k]) - unknown);
        if (mag & 1) ++mag;
        lb += 1LL * mag * mag;
        if (lb > even_cap) return true;
    }
    if (-48 < sum_lo || -48 > sum_hi || ((-48 - sum_lo) & 1)) return true;
    return false;
}

static std::string format(const State& st) {
    std::string z;
    z.reserve(N);
    for (int i = 0; i < N; ++i) z += st.s[i] > 0 ? '+' : '-';
    return z;
}

static long long exact_check(const std::string& z, long long& odd,
                             int& a, int& b, int& dl, int& dr, int& right_lag) {
    std::array<int,N> s{}, c{};
    for (int i = 0; i < N; ++i) s[i] = z[i] == '+' ? 1 : -1;
    long long energy = 0;
    odd = 0;
    for (int k = 1; k < N; ++k) {
        int x = 0;
        for (int i = 0; i < N - k; ++i) x += s[i] * s[i + k];
        c[k] = x;
        energy += 1LL * x * x;
        if (k & 1) odd += 1LL * x * x;
    }
    a = b = 0;
    for (int i = 0; i < 50; ++i) { a += s[2*i]; b += s[2*i+1]; }
    dl = dr = 0;
    right_lag = -1;
    for (int k = 1; k <= 97; k += 2) {
        dl += (c[k] != s[0] * s[k]);
        const bool bad = (c[k] != s[99-k] * s[99]);
        dr += bad;
        if (bad) right_lag = k;
    }
    return energy;
}

struct Var { int p, q, multiplier; };

static std::vector<Var> make_variables(int h) {
    const auto rho = reflection_pattern(h);
    std::vector<Var> vars;
    vars.push_back({99, -1, 0});
    for (int j = 0; j < 49; ++j) if (j != 1) {
        const int mult = (((49 - j) & 1) ? -1 : 1) * rho[j];
        vars.push_back({j, 98 - j, mult});
    }
    vars.push_back({49, -1, 0});
    return vars;
}

static bool assign_var(State& st, const Var& v, int value, std::vector<int>& added) {
    if (st.used[v.p] && st.s[v.p] != value) return false;
    if (!st.used[v.p]) { assign_pos(st, v.p, value); added.push_back(v.p); }
    if (v.q >= 0) {
        const int qvalue = v.multiplier * value;
        if (st.used[v.q] && st.s[v.q] != qvalue) return false;
        if (!st.used[v.q]) { assign_pos(st, v.q, qvalue); added.push_back(v.q); }
    }
    return true;
}

static void undo_added(State& st, std::vector<int>& added) {
    for (int i = int(added.size()) - 1; i >= 0; --i) unassign_pos(st, added[i]);
    added.clear();
}

struct Shared {
    std::atomic<unsigned long long> nodes{0}, pruned{0}, leaves{0};
    std::atomic<bool> found{false}, timeout{false};
    std::string seq;
    int h = 1, cap = 524;
    double seconds = 0;
    std::chrono::steady_clock::time_point start;
};

static void dfs(State& st, const std::vector<Var>& vars,
                const std::vector<Equation>& eqs, int depth, Shared& sh) {
    if (sh.found.load(std::memory_order_relaxed) ||
        sh.timeout.load(std::memory_order_relaxed)) return;

    const auto n = sh.nodes.fetch_add(1, std::memory_order_relaxed) + 1;
    if ((n & 0x3ffff) == 0 && sh.seconds > 0 &&
        std::chrono::duration<double>(std::chrono::steady_clock::now() - sh.start).count() >= sh.seconds) {
        sh.timeout.store(true);
        return;
    }

    if (prune(st, eqs, sh.h, sh.cap)) {
        sh.pruned.fetch_add(1);
        return;
    }

    if (depth == int(vars.size())) {
        sh.leaves.fetch_add(1);
        const auto z = format(st);
        long long odd = 0;
        int a = 0, b = 0, dl = 0, dr = 0, right_lag = -1;
        const long long e = exact_check(z, odd, a, b, dl, dr, right_lag);
        if (e <= 574 && odd == 50 && a == 2 && b == 0 &&
            dr == 1 && right_lag == sh.h) {
#pragma omp critical
            {
                if (!sh.found.load()) {
                    sh.seq = z;
                    sh.found.store(true);
                }
            }
        }
        return;
    }

    for (int value : {-1, +1}) {
        std::vector<int> added;
        if (assign_var(st, vars[depth], value, added))
            dfs(st, vars, eqs, depth + 1, sh);
        undo_added(st, added);
        if (sh.found.load() || sh.timeout.load()) return;
    }
}

static void generate_prefix(State& st, const std::vector<Var>& vars,
                            const std::vector<Equation>& eqs,
                            int depth, int target_depth, int h, int cap,
                            std::vector<State>& out) {
    if (prune(st, eqs, h, cap)) return;
    if (depth == target_depth) {
        out.push_back(st);
        return;
    }
    for (int value : {-1, +1}) {
        std::vector<int> added;
        if (assign_var(st, vars[depth], value, added))
            generate_prefix(st, vars, eqs, depth + 1, target_depth, h, cap, out);
        undo_added(st, added);
    }
}

int main(int argc, char** argv) {
    int h = 1, cap = 524, prefix = 10, threads = 4, shards = 1, shard = 0;
    double seconds = 1800;
    for (int i = 1; i < argc; ++i) {
        const std::string a = argv[i];
        auto need = [&]() {
            if (i + 1 >= argc) throw std::runtime_error("missing argument after " + a);
            return std::string(argv[++i]);
        };
        if (a == "--lag") h = std::stoi(need());
        else if (a == "--cap") cap = std::stoi(need());
        else if (a == "--prefix") prefix = std::stoi(need());
        else if (a == "--threads") threads = std::stoi(need());
        else if (a == "--shards") shards = std::stoi(need());
        else if (a == "--shard") shard = std::stoi(need());
        else if (a == "--seconds") seconds = std::stod(need());
        else return 2;
    }
    if (h < 1 || h > 97 || !(h & 1) || prefix < 1 ||
        shards < 1 || shard < 0 || shard >= shards) return 2;

    const auto rho = reflection_pattern(h);
    const auto eqs = make_equations(h);
    const auto vars = make_variables(h);
    if (prefix > int(vars.size())) prefix = int(vars.size());

    State base;
    assign_pos(base, 1, +1);
    const int mirror_mult = (((49 - 1) & 1) ? -1 : 1) * rho[1];
    assign_pos(base, 97, mirror_mult);

    std::vector<State> all;
    generate_prefix(base, vars, eqs, 0, prefix, h, cap, all);
    std::vector<State> tasks;
    for (size_t i = 0; i < all.size(); ++i)
        if (int(i % shards) == shard) tasks.push_back(all[i]);

#ifdef _OPENMP
    omp_set_num_threads(threads);
#endif

    Shared sh;
    sh.h = h;
    sh.cap = cap;
    sh.seconds = seconds;
    sh.start = std::chrono::steady_clock::now();
    std::atomic<unsigned long long> done{0};

#pragma omp parallel for schedule(dynamic,1)
    for (size_t i = 0; i < tasks.size(); ++i) {
        if (sh.found.load() || sh.timeout.load()) continue;
        State st = tasks[i];
        dfs(st, vars, eqs, prefix, sh);
        done.fetch_add(1);
    }

    const double wall = std::chrono::duration<double>(
        std::chrono::steady_clock::now() - sh.start).count();
    const bool complete = !sh.timeout.load() && !sh.found.load() && done.load() == tasks.size();

    std::cout << "SUMMARY lag=" << h
              << " vars=" << vars.size()
              << " equations=" << eqs.size()
              << " prefix=" << prefix
              << " shard=" << shard << "/" << shards
              << " all_tasks=" << all.size()
              << " tasks_done=" << done.load() << "/" << tasks.size()
              << " nodes=" << sh.nodes.load()
              << " pruned=" << sh.pruned.load()
              << " leaves=" << sh.leaves.load()
              << " complete=" << complete
              << " found=" << sh.found.load()
              << " timeout=" << sh.timeout.load()
              << " seconds=" << wall << "\n";

    if (sh.found.load()) std::cout << "FOUND seq=" << sh.seq << "\n";
    return (complete || sh.found.load()) ? 0 : 1;
}
