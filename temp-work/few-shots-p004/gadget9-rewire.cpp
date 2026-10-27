#include <algorithm>
#include <array>
#include <cstdint>
#include <fstream>
#include <functional>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <unordered_set>
#include <vector>

namespace {
constexpr int D = 5;
constexpr int N = 367;
constexpr int K0 = 8;
constexpr int K = 9;
constexpr std::uint32_t U = 16807u;
constexpr std::uint32_t TARGET = 134770u;
using Dig = std::array<std::uint8_t, D>;
using Pair = std::array<std::uint32_t, 2>;

std::uint32_t enc(const Dig& d) {
    std::uint32_t v = 0;
    for (auto x : d) v = v * 7u + x;
    return v;
}

std::array<Dig, U> make_digits() {
    std::array<Dig, U> out{};
    for (std::uint32_t id = 0; id < U; ++id) {
        auto x = id;
        for (int i = D - 1; i >= 0; --i) {
            out[id][i] = static_cast<std::uint8_t>(x % 7u);
            x /= 7u;
        }
    }
    return out;
}

bool conflict(std::uint32_t a, std::uint32_t b, const std::array<Dig, U>& digits) {
    for (int i = 0; i < D; ++i) {
        const int delta = (static_cast<int>(digits[a][i]) - static_cast<int>(digits[b][i]) + 7) % 7;
        if (delta != 0 && delta != 1 && delta != 6) return false;
    }
    return true;
}

std::vector<std::uint32_t> load_r(const std::string& path) {
    std::ifstream in(path);
    if (!in) throw std::runtime_error("cannot open R367");
    std::vector<std::uint32_t> r;
    while (true) {
        int a;
        if (!(in >> a)) break;
        Dig d{};
        d[0] = static_cast<std::uint8_t>(a);
        for (int i = 1; i < D; ++i) {
            int x;
            if (!(in >> x)) throw std::runtime_error("truncated R367");
            d[i] = static_cast<std::uint8_t>(x);
        }
        r.push_back(enc(d));
    }
    if (r.size() != N) throw std::runtime_error("R367 size mismatch");
    return r;
}

std::vector<std::uint32_t> load_baseline(const std::string& path) {
    std::ifstream in(path);
    if (!in) throw std::runtime_error("cannot open baseline ids");
    std::vector<std::uint32_t> out;
    std::uint64_t x;
    while (in >> x) out.push_back(static_cast<std::uint32_t>(x));
    if (out.size() != 134753u) throw std::runtime_error("baseline size mismatch");
    return out;
}

std::vector<std::uint32_t> make_x(const std::vector<std::uint32_t>& r,
                                  const std::array<Dig, U>& digits) {
    std::vector<std::uint32_t> x;
    x.reserve(N);
    for (auto id : r) {
        const auto& w = digits[id];
        x.push_back(enc(Dig{
            static_cast<std::uint8_t>((2 - static_cast<int>(w[1]) + 7) % 7),
            w[3], w[0],
            static_cast<std::uint8_t>((2 - static_cast<int>(w[2]) + 7) % 7),
            w[4]
        }));
    }
    x.at(267) = enc(Dig{1,5,6,3,5});
    return x;
}

std::array<Pair, K0> old_pairs() {
    return {{
        Pair{enc(Dig{1,3,4,4,6}), enc(Dig{2,3,5,4,6})},
        Pair{enc(Dig{3,4,0,3,5}), enc(Dig{2,4,6,3,5})},
        Pair{enc(Dig{5,3,1,3,4}), enc(Dig{5,3,2,3,5})},
        Pair{enc(Dig{4,4,6,1,6}), enc(Dig{5,4,6,0,6})},
        Pair{enc(Dig{6,0,6,4,5}), enc(Dig{6,1,6,5,5})},
        Pair{enc(Dig{0,3,5,6,5}), enc(Dig{6,3,5,0,5})},
        Pair{enc(Dig{6,4,3,4,0}), enc(Dig{6,4,2,4,6})},
        Pair{enc(Dig{6,4,5,3,2}), enc(Dig{6,5,5,3,1})}
    }};
}

struct TwoSat {
    int n;
    std::vector<std::vector<int>> g, rg;
    explicit TwoSat(int vars) : n(vars), g(2 * vars), rg(2 * vars) {}
    static int node(int v, int s) { return 2 * v + s; }
    void edge(int a, int b) { g[a].push_back(b); rg[b].push_back(a); }
    void forbid(int va, int sa, int vb, int sb) {
        edge(node(va, sa), node(vb, 1 - sb));
        edge(node(vb, sb), node(va, 1 - sa));
    }
    bool solve(std::vector<int>& ans) {
        const int nn = 2 * n;
        std::vector<char> seen(nn, 0);
        std::vector<int> order; order.reserve(nn);
        std::function<void(int)> d1 = [&](int v) {
            seen[v] = 1;
            for (int to : g[v]) if (!seen[to]) d1(to);
            order.push_back(v);
        };
        for (int v = 0; v < nn; ++v) if (!seen[v]) d1(v);
        std::vector<int> comp(nn, -1);
        std::function<void(int,int)> d2 = [&](int v, int c) {
            comp[v] = c;
            for (int to : rg[v]) if (comp[to] == -1) d2(to, c);
        };
        int cc = 0;
        for (auto it = order.rbegin(); it != order.rend(); ++it)
            if (comp[*it] == -1) d2(*it, cc++);
        ans.assign(n, 0);
        for (int v = 0; v < n; ++v) {
            if (comp[node(v,0)] == comp[node(v,1)]) return false;
            ans[v] = comp[node(v,1)] > comp[node(v,0)] ? 1 : 0;
        }
        return true;
    }
};

bool endpoint_transversal_possible(const std::array<Pair, K>& pairs,
                                   const std::array<Dig, U>& digits) {
    TwoSat sat(K);
    for (int j = 0; j < K; ++j) {
        for (int k = j + 1; k < K; ++k) {
            for (int s = 0; s < 2; ++s)
                for (int t = 0; t < 2; ++t)
                    if (conflict(pairs[j][s], pairs[k][t], digits))
                        sat.forbid(j, s, k, t);
        }
    }
    std::vector<int> a;
    return sat.solve(a);
}

bool solve_full(const std::array<Pair, K>& pairs,
                const std::vector<std::uint32_t>& x,
                const std::array<Dig, U>& digits,
                std::vector<int>& assignment) {
    constexpr int BLOCK = K * N;
    auto hv = [](int j, int xi) { return j * N + xi; };
    auto vv = [](int j, int xi) { return BLOCK + j * N + xi; };
    TwoSat sat(2 * BLOCK);

    // Same-X horizontal and vertical families: selected endpoints must be independent.
    for (int j = 0; j < K; ++j) {
        for (int k = j + 1; k < K; ++k) {
            for (int s = 0; s < 2; ++s) {
                for (int t = 0; t < 2; ++t) {
                    if (!conflict(pairs[j][s], pairs[k][t], digits)) continue;
                    for (int xi = 0; xi < N; ++xi) {
                        sat.forbid(hv(j, xi), s, hv(k, xi), t);
                        sat.forbid(vv(j, xi), s, vv(k, xi), t);
                    }
                }
            }
        }
    }

    std::array<std::array<std::vector<int>, 2>, K> rel;
    for (int j = 0; j < K; ++j)
        for (int s = 0; s < 2; ++s)
            for (int xi = 0; xi < N; ++xi)
                if (conflict(pairs[j][s], x[xi], digits)) rel[j][s].push_back(xi);

    // H(j,x,s) vs V(k,y,t) conflicts iff endpoint(j,s)~X[y] and X[x]~endpoint(k,t).
    for (int j = 0; j < K; ++j) {
        for (int k = 0; k < K; ++k) {
            for (int s = 0; s < 2; ++s) {
                for (int t = 0; t < 2; ++t) {
                    for (int xi : rel[k][t])
                        for (int yi : rel[j][s])
                            sat.forbid(hv(j, xi), s, vv(k, yi), t);
                }
            }
        }
    }
    return sat.solve(assignment);
}

void emit_bulk(const std::vector<std::uint32_t>& remove,
               const std::vector<std::uint32_t>& add,
               std::uint32_t r9, std::uint32_t q9,
               std::uint64_t tested, std::uint64_t full_tested) {
    std::cout << "{\"kind\":\"bulk\",\"method\":\"rewired-nine-pair-2sat\","
              << "\"baseline_size\":134753,\"target\":" << TARGET
              << ",\"r9\":" << r9 << ",\"q9\":" << q9
              << ",\"tested\":" << tested << ",\"full_tested\":" << full_tested
              << ",\"remove\":[";
    for (std::size_t i = 0; i < remove.size(); ++i) { if (i) std::cout << ','; std::cout << remove[i]; }
    std::cout << "],\"add\":[";
    for (std::size_t i = 0; i < add.size(); ++i) { if (i) std::cout << ','; std::cout << add[i]; }
    std::cout << "]}\n";
}

}  // namespace

int main(int argc, char** argv) {
    try {
        if (argc != 3) {
            std::cerr << "usage: gadget9-rewire BASELINE_IDS R367\n";
            return 2;
        }
        const auto digits = make_digits();
        const auto r = load_r(argv[2]);
        const auto baseline = load_baseline(argv[1]);
        const auto x = make_x(r, digits);
        const auto p0 = old_pairs();

        std::unordered_set<std::uint32_t> r_all(r.begin(), r.end());
        std::unordered_set<std::uint32_t> deleted;
        for (const auto& p : p0) {
            if (!r_all.count(p[0])) throw std::runtime_error("old deleted endpoint not in R");
            deleted.insert(p[0]);
        }
        if (deleted.size() != K0) throw std::runtime_error("old deleted endpoints not distinct");

        std::vector<std::uint32_t> b;
        for (auto v : r) if (!deleted.count(v)) b.push_back(v);
        if (b.size() != 359u) throw std::runtime_error("old B size mismatch");

        // Validate source invariants used by the generalized construction.
        for (const auto& p : p0)
            for (int s = 0; s < 2; ++s)
                for (auto bv : b)
                    if (conflict(p[s], bv, digits))
                        throw std::runtime_error("old pair endpoint conflicts with old B");
        for (int i = 0; i < N; ++i)
            for (int j = i + 1; j < N; ++j)
                if (conflict(x[i], x[j], digits)) throw std::runtime_error("X not independent");

        std::array<std::uint16_t, U> cov_b{};
        std::array<std::uint16_t, U> owner_b{};
        owner_b.fill(std::numeric_limits<std::uint16_t>::max());
        for (std::uint32_t q = 0; q < U; ++q) {
            std::uint16_t c = 0, owner = std::numeric_limits<std::uint16_t>::max();
            for (std::uint16_t i = 0; i < b.size(); ++i) {
                if (conflict(q, b[i], digits)) { ++c; owner = i; }
            }
            cov_b[q] = c;
            if (c == 1) owner_b[q] = owner;
        }

        std::vector<std::uint32_t> zero;
        std::array<std::vector<std::uint32_t>, 359> one;
        for (std::uint32_t q = 0; q < U; ++q) {
            if (cov_b[q] == 0) zero.push_back(q);
            else if (cov_b[q] == 1) one[owner_b[q]].push_back(q);
        }
        std::cerr << "rewire covB0=" << zero.size() << "\n";

        std::uint64_t tested = 0, transversal_ok = 0, full_tested = 0;
        constexpr int BLOCK = K * N;
        auto hv = [](int j, int xi) { return j * N + xi; };
        auto vv = [](int j, int xi) { return BLOCK + j * N + xi; };

        for (int ri = 0; ri < static_cast<int>(b.size()); ++ri) {
            const std::uint32_t r9 = b[ri];
            std::vector<std::uint32_t> qs = zero;
            qs.insert(qs.end(), one[ri].begin(), one[ri].end());
            std::sort(qs.begin(), qs.end());
            qs.erase(std::unique(qs.begin(), qs.end()), qs.end());

            for (auto q9 : qs) {
                ++tested;
                if (q9 == r9) continue;
                // q9 must be safe from B after r9 is removed.
                bool safe = true;
                for (int bi = 0; bi < static_cast<int>(b.size()); ++bi) {
                    if (bi == ri) continue;
                    if (conflict(q9, b[bi], digits)) { safe = false; break; }
                }
                if (!safe) throw std::runtime_error("covB candidate filtering bug");

                std::array<Pair, K> pairs{};
                for (int j = 0; j < K0; ++j) pairs[j] = p0[j];
                pairs[8] = Pair{r9, q9};

                if (!endpoint_transversal_possible(pairs, digits)) continue;
                ++transversal_ok;

                std::vector<int> assignment;
                ++full_tested;
                if (!solve_full(pairs, x, digits, assignment)) continue;

                std::vector<std::uint32_t> b9;
                b9.reserve(358);
                for (auto v : b) if (v != r9) b9.push_back(v);
                if (b9.size() != 358u) throw std::runtime_error("B9 size mismatch");

                std::unordered_set<std::uint32_t> candidate;
                candidate.reserve(TARGET * 2);
                for (auto a : b9) for (auto c : b9) candidate.insert(a * U + c);
                for (int j = 0; j < K; ++j) {
                    for (int xi = 0; xi < N; ++xi) {
                        const auto eh = pairs[j][assignment[hv(j,xi)]];
                        const auto ev = pairs[j][assignment[vv(j,xi)]];
                        candidate.insert(eh * U + x[xi]);
                        candidate.insert(x[xi] * U + ev);
                    }
                }
                if (candidate.size() != TARGET) continue;

                // Structural replay of every nontrivial family interaction.
                for (int xi = 0; xi < N; ++xi) {
                    for (int j = 0; j < K; ++j) {
                        const auto ehj = pairs[j][assignment[hv(j,xi)]];
                        const auto evj = pairs[j][assignment[vv(j,xi)]];
                        for (int k = j + 1; k < K; ++k) {
                            const auto ehk = pairs[k][assignment[hv(k,xi)]];
                            const auto evk = pairs[k][assignment[vv(k,xi)]];
                            if (conflict(ehj, ehk, digits) || conflict(evj, evk, digits))
                                throw std::runtime_error("same-X replay failed");
                        }
                    }
                }
                for (int j = 0; j < K; ++j) {
                    for (int k = 0; k < K; ++k) {
                        for (int xi = 0; xi < N; ++xi) {
                            const auto eh = pairs[j][assignment[hv(j,xi)]];
                            for (int yi = 0; yi < N; ++yi) {
                                const auto ev = pairs[k][assignment[vv(k,yi)]];
                                if (conflict(eh, x[yi], digits) && conflict(x[xi], ev, digits))
                                    throw std::runtime_error("cross replay failed");
                            }
                        }
                    }
                }

                std::unordered_set<std::uint32_t> base_set(baseline.begin(), baseline.end());
                std::vector<std::uint32_t> remove, add;
                for (auto id : baseline) if (!candidate.count(id)) remove.push_back(id);
                for (auto id : candidate) if (!base_set.count(id)) add.push_back(id);
                std::sort(remove.begin(), remove.end());
                std::sort(add.begin(), add.end());
                if (BASELINE_SCORE - remove.size() + add.size() != TARGET)
                    throw std::runtime_error("set difference score mismatch");

                std::cerr << "rewire SAT r9=" << r9 << " q9=" << q9
                          << " tested=" << tested << " transversal_ok=" << transversal_ok
                          << " full_tested=" << full_tested << "\n";
                emit_bulk(remove, add, r9, q9, tested, full_tested);
                return 0;
            }
        }

        std::cerr << "rewire none tested=" << tested << " transversal_ok=" << transversal_ok
                  << " full_tested=" << full_tested << "\n";
        std::cout << "{\"kind\":\"none\",\"method\":\"rewired-nine-pair-2sat\","
                  << "\"baseline_size\":134753,\"target\":" << TARGET
                  << ",\"covB0\":" << zero.size() << ",\"tested\":" << tested
                  << ",\"transversal_ok\":" << transversal_ok
                  << ",\"full_tested\":" << full_tested << "}\n";
        return 0;
    } catch (const std::exception& e) {
        std::cerr << "error: " << e.what() << "\n";
        return 1;
    }
}
