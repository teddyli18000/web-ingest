// Exact BnB for the full N=100 odd-perfect target layer in A/B interleaving
// coordinates. Searches canonical b=0, a>=0 classes under an even-energy cap.
//
// Strengthening over the older generic outer BnB:
//   1) opposite odd-lag correlations are required jointly to finish as
//      (+1,-1) or (-1,+1), instead of only being individually reachable;
//   2) the even-energy lower bound is the exact separable-convex minimum
//      subject to the exact correlation-sum identity, rather than independent
//      per-correlation minima plus a separate sum-interval check.
#include <algorithm>
#include <array>
#include <atomic>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <iostream>
#include <limits>
#include <queue>
#include <stdexcept>
#include <string>
#include <vector>
#ifdef _OPENMP
#include <omp.h>
#endif

constexpr int N = 100;
using S = std::array<int8_t, N>;
using U = std::array<uint8_t, N>;
using I = std::array<int, N>;

struct State {
    S s{};
    U used{};
    I fixed{}, count{};
    int sumA = 0, sumB = 0, countA = 0, countB = 0;
};

static void assign_pos(State& st, int p, int val) {
    for (int j = 0; j < N; ++j) if (st.used[j]) {
        const int k = std::abs(p - j);
        if (k) {
            st.fixed[k] += val * int(st.s[j]);
            st.count[k]++;
        }
    }
    st.s[p] = int8_t(val);
    st.used[p] = 1;
    if ((p & 1) == 0) {
        st.sumA += val;
        st.countA++;
    } else {
        st.sumB += val;
        st.countB++;
    }
}

static void unassign_pos(State& st, int p) {
    const int val = st.s[p];
    if ((p & 1) == 0) {
        st.sumA -= val;
        st.countA--;
    } else {
        st.sumB -= val;
        st.countB--;
    }
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
    return std::abs(need) <= rem && (((need - rem) & 1) == 0);
}

static bool reach(int fixed, int unknown, int target) {
    const int d = target - fixed;
    return std::abs(d) <= unknown && (((d + unknown) & 1) == 0);
}

// Odd-perfect plus C_k+C_{100-k}=0 (mod 4) means every opposite odd pair
// must finish as (+1,-1) or (-1,+1). This is stronger than checking each
// correlation independently.
static bool odd_joint_feasible(const State& st) {
    for (int k = 1; k < 50; k += 2) {
        const int j = N - k;
        const int u1 = (N - k) - st.count[k];
        const int f1 = st.fixed[k];
        const int u2 = k - st.count[j];
        const int f2 = st.fixed[j];
        const bool plus = reach(f1, u1, 1) && reach(f2, u2, -1);
        const bool minus = reach(f1, u1, -1) && reach(f2, u2, 1);
        if (!plus && !minus) return false;
    }
    return true;
}

static long long even_independent_lb(const State& st, int cap) {
    long long lb = 0;
    for (int k = 2; k < N; k += 2) {
        const int L = N - k;
        const int u = L - st.count[k];
        int m = std::max(0, std::abs(st.fixed[k]) - u);
        if (m & 1) ++m; // completed even correlations have even parity
        lb += 1LL * m * m;
        if (lb > cap) return lb;
    }
    return lb;
}

// Exact minimum of sum C_k^2 over every interval/parity completion of the 49
// even correlations, additionally enforcing their exact total sum. This
// ignores sequence realizability, so it is a rigorous lower bound.
static long long even_convex_lb(const State& st, int asum, int cap) {
    // d_k=C_{2r}/2 are integers and sum d_k=(a^2-100)/4.
    const int target = (asum * asum - 100) / 4;
    struct Var { int d, lo, hi; };
    std::array<Var, 49> vars{};
    int n = 0, cur = 0, minsum = 0, maxsum = 0;
    long long cost = 0;

    for (int k = 2; k < N; k += 2) {
        const int L = N - k;
        const int u = L - st.count[k];
        const int f = st.fixed[k];
        const int lo = (f - u) / 2;
        const int hi = (f + u) / 2;
        if (lo > hi) return cap + 1;
        int d = 0;
        if (d < lo) d = lo;
        if (d > hi) d = hi;
        vars[n++] = {d, lo, hi};
        cur += d;
        minsum += lo;
        maxsum += hi;
        cost += 1LL * d * d;
    }

    if (target < minsum || target > maxsum) return cap + 1;
    using P = std::pair<int, int>; // marginal cost, variable index
    std::priority_queue<P, std::vector<P>, std::greater<P>> pq;

    if (cur < target) {
        for (int i = 0; i < n; ++i)
            if (vars[i].d < vars[i].hi) pq.push({2 * vars[i].d + 1, i});
        while (cur < target) {
            if (pq.empty()) return cap + 1;
            auto [mc, i] = pq.top();
            pq.pop();
            cost += mc;
            vars[i].d++;
            cur++;
            if (4 * cost > cap) return 4 * cost;
            if (vars[i].d < vars[i].hi)
                pq.push({2 * vars[i].d + 1, i});
        }
    } else if (cur > target) {
        for (int i = 0; i < n; ++i)
            if (vars[i].d > vars[i].lo) pq.push({-2 * vars[i].d + 1, i});
        while (cur > target) {
            if (pq.empty()) return cap + 1;
            auto [mc, i] = pq.top();
            pq.pop();
            cost += mc;
            vars[i].d--;
            cur--;
            if (4 * cost > cap) return 4 * cost;
            if (vars[i].d > vars[i].lo)
                pq.push({-2 * vars[i].d + 1, i});
        }
    }
    return 4 * cost;
}

static bool prune(const State& st, int asum, int cap, int depth) {
    if (!sum_feasible(st.sumA, st.countA, asum) ||
        !sum_feasible(st.sumB, st.countB, 0)) return true;
    if (!odd_joint_feasible(st)) return true;
    if (even_independent_lb(st, cap) > cap) return true;
    // The sum-coupled bound is more expensive. At shallow depth it equals the
    // cheap relaxation almost everywhere, so delay it until some border is set.
    if (depth >= 6 && even_convex_lb(st, asum, cap) > cap) return true;
    return false;
}

static std::string fmt(const State& st) {
    std::string z;
    z.reserve(N);
    for (int i = 0; i < N; ++i) z += st.s[i] > 0 ? '+' : '-';
    return z;
}

static long long exact(const std::string& z, long long& odd, int& a, int& b) {
    std::array<int, N> s{};
    for (int i = 0; i < N; ++i) s[i] = z[i] == '+' ? 1 : -1;
    long long e = 0;
    odd = 0;
    for (int k = 1; k < N; ++k) {
        int c = 0;
        for (int i = 0; i < N - k; ++i) c += s[i] * s[i + k];
        e += 1LL * c * c;
        if (k & 1) odd += 1LL * c * c;
    }
    a = b = 0;
    for (int i = 0; i < 50; ++i) {
        a += s[2 * i];
        b += s[2 * i + 1];
    }
    return e;
}

struct Shared {
    std::atomic<unsigned long long> nodes{0}, pruned{0}, leaves{0};
    std::atomic<bool> found{false}, timeout{false};
    std::string seq;
    long long even = 1LL << 60;
    int asum = 0, cap = 524;
    double seconds = 0;
    std::chrono::steady_clock::time_point start;
};

static void dfs(State& st, int p, Shared& sh) {
    if (sh.found.load(std::memory_order_relaxed) ||
        sh.timeout.load(std::memory_order_relaxed)) return;
    const auto nn = sh.nodes.fetch_add(1, std::memory_order_relaxed) + 1;
    if ((nn & 0x3ffff) == 0 && sh.seconds > 0) {
        const double t = std::chrono::duration<double>(
            std::chrono::steady_clock::now() - sh.start).count();
        if (t >= sh.seconds) {
            sh.timeout.store(true);
            return;
        }
    }
    if (prune(st, sh.asum, sh.cap, p)) {
        sh.pruned.fetch_add(1, std::memory_order_relaxed);
        return;
    }
    if (p == 50) {
        sh.leaves.fetch_add(1, std::memory_order_relaxed);
        long long ee = 0;
        for (int k = 2; k < N; k += 2) ee += 1LL * st.fixed[k] * st.fixed[k];
        if (st.sumA == sh.asum && st.sumB == 0 && ee <= sh.cap) {
#pragma omp critical
            {
                if (!sh.found.load() || ee < sh.even) {
                    sh.even = ee;
                    sh.seq = fmt(st);
                    sh.found.store(true);
                }
            }
        }
        return;
    }

    const std::array<int, 2> pos{p, 99 - p};
    std::vector<int> todo;
    for (int q : pos) if (!st.used[q]) todo.push_back(q);
    const int combos = 1 << todo.size();
    for (int mask = 0; mask < combos; ++mask) {
        for (int j = 0; j < int(todo.size()); ++j)
            assign_pos(st, todo[j], (mask >> j & 1) ? 1 : -1);
        dfs(st, p + 1, sh);
        for (int j = int(todo.size()) - 1; j >= 0; --j) unassign_pos(st, todo[j]);
        if (sh.found.load(std::memory_order_relaxed) ||
            sh.timeout.load(std::memory_order_relaxed)) return;
    }
}

static void gen_prefix(State& st, int p, int depth, int asum, int cap,
                       std::vector<State>& out) {
    if (prune(st, asum, cap, p)) return;
    if (p == depth) {
        out.push_back(st);
        return;
    }
    const std::array<int, 2> pos{p, 99 - p};
    std::vector<int> todo;
    for (int q : pos) if (!st.used[q]) todo.push_back(q);
    const int combos = 1 << todo.size();
    for (int mask = 0; mask < combos; ++mask) {
        for (int j = 0; j < int(todo.size()); ++j)
            assign_pos(st, todo[j], (mask >> j & 1) ? 1 : -1);
        gen_prefix(st, p + 1, depth, asum, cap, out);
        for (int j = int(todo.size()) - 1; j >= 0; --j) unassign_pos(st, todo[j]);
    }
}

// Regression check: every prefix of a known complete sequence must survive
// when the cap is its true even energy and the half sums match.
static bool check_seq(const std::string& z) {
    if (z.size() != 100) return false;
    long long odd = 0;
    int a = 0, b = 0;
    const long long e = exact(z, odd, a, b);
    const int cap = int(e - odd);
    State st;
    assign_pos(st, 1, z[1] == '+' ? 1 : -1);
    if (st.s[1] != 1) {
        std::cerr << "check expects B0=+1 normalized sequence\n";
        return false;
    }
    for (int p = 0; p < 50; ++p) {
        for (int q : std::array<int, 2>{p, 99 - p})
            if (!st.used[q]) assign_pos(st, q, z[q] == '+' ? 1 : -1);
        if (prune(st, a, cap, p + 1)) {
            std::cerr << "CHECK_PRUNED p=" << p << " e=" << e
                      << " odd=" << odd << " cap=" << cap
                      << " a=" << a << " b=" << b << "\n";
            return false;
        }
    }
    std::cerr << "CHECK_OK e=" << e << " odd=" << odd << " cap=" << cap
              << " a=" << a << " b=" << b << "\n";
    return odd == 50 && b == 0;
}

int main(int argc, char** argv) {
    int asum = 8, cap = 524, threads = 4, prefix = 7, shards = 1, shard = 0;
    double seconds = 30;
    std::string check;
    for (int i = 1; i < argc; ++i) {
        const std::string x = argv[i];
        auto need = [&]() {
            if (i + 1 >= argc) throw std::runtime_error("missing argument");
            return std::string(argv[++i]);
        };
        if (x == "--asum") asum = std::stoi(need());
        else if (x == "--cap") cap = std::stoi(need());
        else if (x == "--threads") threads = std::stoi(need());
        else if (x == "--prefix") prefix = std::stoi(need());
        else if (x == "--seconds") seconds = std::stod(need());
        else if (x == "--shards") shards = std::stoi(need());
        else if (x == "--shard") shard = std::stoi(need());
        else if (x == "--check") check = need();
        else return 2;
    }
    if (!check.empty()) return check_seq(check) ? 0 : 2;
    if (asum < 0 || asum > 20 || (asum % 4) || prefix < 1 || prefix > 20 ||
        shards < 1 || shard < 0 || shard >= shards) return 2;

    // Safe odd-perfect normalization: b=0, a>=0, B0=+1. A0 remains free.
    State base;
    assign_pos(base, 1, 1);
    std::vector<State> all;
    gen_prefix(base, 0, prefix, asum, cap, all);
    std::vector<State> tasks;
    for (size_t i = 0; i < all.size(); ++i)
        if (int(i % shards) == shard) tasks.push_back(all[i]);

#ifdef _OPENMP
    omp_set_num_threads(threads);
#endif
    Shared sh;
    sh.asum = asum;
    sh.cap = cap;
    sh.seconds = seconds;
    sh.start = std::chrono::steady_clock::now();
    std::atomic<unsigned long long> done{0};

#pragma omp parallel for schedule(dynamic, 1)
    for (size_t i = 0; i < tasks.size(); ++i) {
        if (sh.found.load() || sh.timeout.load()) continue;
        State st = tasks[i];
        dfs(st, prefix, sh);
        done.fetch_add(1);
    }

    const double wall = std::chrono::duration<double>(
        std::chrono::steady_clock::now() - sh.start).count();
    const bool complete = !sh.timeout.load() && !sh.found.load() &&
                          done.load() == tasks.size();
    std::cout << "SUMMARY asum=" << asum << " cap=" << cap
              << " prefix=" << prefix << " shard=" << shard << "/" << shards
              << " all_tasks=" << all.size() << " complete=" << complete
              << " found=" << sh.found.load() << " timeout=" << sh.timeout.load()
              << " tasks_done=" << done.load() << "/" << tasks.size()
              << " nodes=" << sh.nodes.load() << " pruned=" << sh.pruned.load()
              << " leaves=" << sh.leaves.load() << " seconds=" << wall << "\n";

    if (sh.found.load()) {
        long long odd = 0;
        int a = 0, b = 0;
        const long long e = exact(sh.seq, odd, a, b);
        std::cout << "FOUND energy=" << e << " odd=" << odd
                  << " even=" << e - odd << " asum=" << a << " bsum=" << b
                  << " seq=" << sh.seq << "\n";
        if (e > cap + 50 || odd != 50 || a != asum || b != 0) return 2;
    }
    return complete || sh.found.load() ? 0 : 1;
}
