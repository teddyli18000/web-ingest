#include <algorithm>
#include <array>
#include <cstdint>
#include <fstream>
#include <functional>
#include <iostream>
#include <limits>
#include <numeric>
#include <stdexcept>
#include <string>
#include <unordered_set>
#include <vector>

#ifdef _OPENMP
#include <omp.h>
#endif

namespace {
constexpr int D5 = 5;
constexpr int D10 = 10;
constexpr std::uint32_t U5 = 16807u;
constexpr std::uint32_t U10 = 282475249u;
constexpr std::uint32_t POW7[D10 + 1] = {
    1u, 7u, 49u, 343u, 2401u, 16807u,
    117649u, 823543u, 5764801u, 40353607u, 282475249u
};
constexpr std::uint32_t GROUPS10 = U10 / 7u;
constexpr std::uint32_t BASELINE_SCORE = 134753u;
constexpr std::uint32_t R_SIZE = 367u;
constexpr std::uint32_t B_SIZE = 359u;
constexpr std::uint32_t X_SIZE = 367u;

using Dig5 = std::array<std::uint8_t, D5>;

std::vector<std::uint32_t> load_ids10(const std::string& path) {
    std::ifstream in(path);
    if (!in) throw std::runtime_error("cannot open baseline id file");
    std::vector<std::uint32_t> ids;
    std::uint64_t x;
    while (in >> x) {
        if (x >= U10) throw std::runtime_error("10D id out of range");
        ids.push_back(static_cast<std::uint32_t>(x));
    }
    if (ids.size() != BASELINE_SCORE) throw std::runtime_error("unexpected baseline size");
    return ids;
}

std::uint32_t encode5(const Dig5& d) {
    std::uint32_t v = 0;
    for (auto x : d) {
        if (x >= 7) throw std::runtime_error("bad base-7 digit");
        v = v * 7u + x;
    }
    return v;
}

std::vector<std::uint32_t> load_r367(const std::string& path) {
    std::ifstream in(path);
    if (!in) throw std::runtime_error("cannot open R367 file");
    std::vector<std::uint32_t> out;
    while (true) {
        Dig5 d{};
        int x0;
        if (!(in >> x0)) break;
        d[0] = static_cast<std::uint8_t>(x0);
        for (int i = 1; i < D5; ++i) {
            int x;
            if (!(in >> x)) throw std::runtime_error("truncated R367 line");
            d[i] = static_cast<std::uint8_t>(x);
        }
        out.push_back(encode5(d));
    }
    if (out.size() != R_SIZE) throw std::runtime_error("R367 does not contain 367 words");
    return out;
}

std::array<Dig5, U5> make_digits5() {
    std::array<Dig5, U5> all{};
    for (std::uint32_t id = 0; id < U5; ++id) {
        std::uint32_t x = id;
        for (int i = D5 - 1; i >= 0; --i) {
            all[id][i] = static_cast<std::uint8_t>(x % 7u);
            x /= 7u;
        }
    }
    return all;
}

bool conflict5(std::uint32_t a, std::uint32_t b, const std::array<Dig5, U5>& digits) {
    for (int i = 0; i < D5; ++i) {
        const int x = digits[a][i];
        const int y = digits[b][i];
        const int delta = (x - y + 7) % 7;
        if (delta != 0 && delta != 1 && delta != 6) return false;
    }
    return true;
}

template <class T>
void sum_neighborhood10(std::vector<T>& a, std::vector<T>& b) {
    for (int dim = 0; dim < D10; ++dim) {
        const std::uint32_t stride = POW7[dim];
        const std::uint64_t block = static_cast<std::uint64_t>(stride) * 7u;
        #pragma omp parallel for schedule(static)
        for (std::int64_t gg = 0; gg < static_cast<std::int64_t>(GROUPS10); ++gg) {
            const std::uint64_t g = static_cast<std::uint64_t>(gg);
            const std::uint64_t block_no = g / stride;
            const std::uint32_t off = static_cast<std::uint32_t>(g % stride);
            const std::uint64_t base = block_no * block + off;
            T v[7];
            for (int k = 0; k < 7; ++k) v[k] = a[base + static_cast<std::uint64_t>(k) * stride];
            for (int k = 0; k < 7; ++k) {
                b[base + static_cast<std::uint64_t>(k) * stride] = static_cast<T>(
                    v[(k + 6) % 7] + v[k] + v[(k + 1) % 7]);
            }
        }
        a.swap(b);
    }
}

struct TwoSat {
    int n;
    std::vector<std::vector<int>> g, rg;

    explicit TwoSat(int vars) : n(vars), g(2 * vars), rg(2 * vars) {}

    static int node(int var, int state) { return 2 * var + state; }

    void edge(int a, int b) {
        g[a].push_back(b);
        rg[b].push_back(a);
    }

    void forbid(int va, int sa, int vb, int sb) {
        edge(node(va, sa), node(vb, 1 - sb));
        edge(node(vb, sb), node(va, 1 - sa));
    }

    void forbid_state(int v, int s) { edge(node(v, s), node(v, 1 - s)); }

    bool solve(std::vector<int>& assignment) {
        const int nn = 2 * n;
        std::vector<char> used(nn, 0);
        std::vector<int> order;
        order.reserve(nn);
        std::function<void(int)> dfs1 = [&](int v) {
            used[v] = 1;
            for (int to : g[v]) if (!used[to]) dfs1(to);
            order.push_back(v);
        };
        for (int v = 0; v < nn; ++v) if (!used[v]) dfs1(v);

        std::vector<int> comp(nn, -1);
        std::function<void(int, int)> dfs2 = [&](int v, int c) {
            comp[v] = c;
            for (int to : rg[v]) if (comp[to] == -1) dfs2(to, c);
        };
        int cc = 0;
        for (auto it = order.rbegin(); it != order.rend(); ++it) {
            if (comp[*it] == -1) dfs2(*it, cc++);
        }

        assignment.assign(n, 0);
        for (int v = 0; v < n; ++v) {
            if (comp[node(v, 0)] == comp[node(v, 1)]) return false;
            assignment[v] = comp[node(v, 1)] > comp[node(v, 0)] ? 1 : 0;
        }
        return true;
    }
};

std::vector<std::uint32_t> make_x(const std::vector<std::uint32_t>& r,
                                  const std::array<Dig5, U5>& digits) {
    std::vector<std::uint32_t> x;
    x.reserve(r.size());
    for (auto id : r) {
        const auto& w = digits[id];
        Dig5 t{
            static_cast<std::uint8_t>((2 - static_cast<int>(w[1]) + 7) % 7),
            w[3],
            w[0],
            static_cast<std::uint8_t>((2 - static_cast<int>(w[2]) + 7) % 7),
            w[4]
        };
        x.push_back(encode5(t));
    }
    x.at(267) = encode5(Dig5{1, 5, 6, 3, 5});
    return x;
}

std::unordered_set<std::uint32_t> deleted_r_ids() {
    const std::array<Dig5, 8> d = {{
        Dig5{1,3,4,4,6}, Dig5{3,4,0,3,5}, Dig5{5,3,1,3,4}, Dig5{4,4,6,1,6},
        Dig5{6,0,6,4,5}, Dig5{0,3,5,6,5}, Dig5{6,4,3,4,0}, Dig5{6,4,5,3,2}
    }};
    std::unordered_set<std::uint32_t> out;
    for (const auto& x : d) out.insert(encode5(x));
    return out;
}

void emit_bulk(const std::vector<std::uint32_t>& remove,
               const std::vector<std::uint32_t>& add,
               std::uint32_t r, std::uint32_t q,
               std::uint64_t tested) {
    std::cout << "{\"kind\":\"bulk\",\"method\":\"ninth-exchange-pair-2sat\","
              << "\"baseline_size\":" << BASELINE_SCORE
              << ",\"r\":" << r << ",\"q\":" << q
              << ",\"tested_pairs\":" << tested << ",\"remove\":[";
    for (std::size_t i = 0; i < remove.size(); ++i) {
        if (i) std::cout << ',';
        std::cout << remove[i];
    }
    std::cout << "],\"add\":[";
    for (std::size_t i = 0; i < add.size(); ++i) {
        if (i) std::cout << ',';
        std::cout << add[i];
    }
    std::cout << "]}\n";
}

}  // namespace

int main(int argc, char** argv) {
    try {
        if (argc != 3) {
            std::cerr << "usage: gadget9 BASELINE_IDS R367_TXT\n";
            return 2;
        }

        const auto baseline = load_ids10(argv[1]);
        const auto rset = load_r367(argv[2]);
        const auto digits = make_digits5();
        const auto deleted = deleted_r_ids();

        std::vector<std::uint32_t> bset;
        for (auto r : rset) if (!deleted.count(r)) bset.push_back(r);
        if (bset.size() != B_SIZE) throw std::runtime_error("B does not have size 359");

        std::array<char, U5> in_b{};
        for (auto b : bset) in_b[b] = 1;

        const auto xset = make_x(rset, digits);
        if (xset.size() != X_SIZE) throw std::runtime_error("X size mismatch");
        {
            std::unordered_set<std::uint32_t> seen(xset.begin(), xset.end());
            if (seen.size() != X_SIZE) throw std::runtime_error("X has duplicates");
            for (std::size_t i = 0; i < xset.size(); ++i)
                for (std::size_t j = i + 1; j < xset.size(); ++j)
                    if (conflict5(xset[i], xset[j], digits))
                        throw std::runtime_error("X is not independent");
        }

        // Exact baseline closed-neighborhood coverage over all 7^10 vertices.
        std::vector<std::uint16_t> coverage(U10, 0), scratch(U10, 0);
        for (auto id : baseline) coverage[id] = 1;
        sum_neighborhood10(coverage, scratch);
        scratch.clear();
        scratch.shrink_to_fit();

        // Closed-neighborhood coverage by B in 5D and its unique owner where applicable.
        std::array<std::uint16_t, U5> cov_b{};
        std::array<std::uint16_t, U5> owner_b{};
        owner_b.fill(std::numeric_limits<std::uint16_t>::max());
        for (std::uint32_t v = 0; v < U5; ++v) {
            std::uint16_t count = 0;
            std::uint16_t owner = std::numeric_limits<std::uint16_t>::max();
            for (std::uint16_t i = 0; i < bset.size(); ++i) {
                if (conflict5(v, bset[i], digits)) {
                    ++count;
                    owner = i;
                }
            }
            cov_b[v] = count;
            if (count == 1) owner_b[v] = owner;
        }

        std::array<std::uint16_t, X_SIZE> cov_b_x{};
        for (std::size_t i = 0; i < xset.size(); ++i) cov_b_x[i] = cov_b[xset[i]];

        std::vector<std::uint32_t> q_candidates;
        for (std::uint32_t q = 0; q < U5; ++q) {
            if (in_b[q]) continue;
            if (cov_b[q] == 1) q_candidates.push_back(q);
        }
        std::cerr << "gadget9 q_candidates=" << q_candidates.size() << "\n";

        std::uint64_t tested = 0;
        std::uint64_t unary_feasible = 0;
        std::uint64_t sat_instances = 0;

        for (auto q : q_candidates) {
            ++tested;
            const auto owner_pos = owner_b[q];
            if (owner_pos == std::numeric_limits<std::uint16_t>::max()) continue;
            const std::uint32_t r = bset[owner_pos];
            if (q == r || cov_b[r] != 1 || !conflict5(q, r, digits)) continue;

            std::vector<char> rel_r(X_SIZE), rel_q(X_SIZE);
            std::vector<int> idx_r, idx_q;
            for (int i = 0; i < static_cast<int>(X_SIZE); ++i) {
                rel_r[i] = conflict5(xset[i], r, digits);
                rel_q[i] = conflict5(xset[i], q, digits);
                if (rel_r[i]) idx_r.push_back(i);
                if (rel_q[i]) idx_q.push_back(i);
            }

            TwoSat sat(2 * X_SIZE);
            bool impossible = false;
            for (int i = 0; i < static_cast<int>(X_SIZE); ++i) {
                const std::uint32_t x = xset[i];
                const std::uint16_t removed_cover = cov_b_x[i];
                bool h_ok[2], v_ok[2];
                const std::uint32_t endpoints[2] = {r, q};
                for (int s = 0; s < 2; ++s) {
                    const std::uint32_t a = endpoints[s];
                    const std::uint32_t hid = a * U5 + x;
                    const std::uint32_t vid = x * U5 + a;
                    h_ok[s] = coverage[hid] == removed_cover;
                    v_ok[s] = coverage[vid] == removed_cover;
                    if (!h_ok[s]) sat.forbid_state(i, s);
                    if (!v_ok[s]) sat.forbid_state(X_SIZE + i, s);
                }
                if ((!h_ok[0] && !h_ok[1]) || (!v_ok[0] && !v_ok[1])) {
                    impossible = true;
                    break;
                }
            }
            if (impossible) continue;
            ++unary_feasible;

            auto add_complete = [&](const std::vector<int>& xs, int hs,
                                    const std::vector<int>& ys, int vs) {
                for (int xi : xs) {
                    for (int yi : ys) {
                        // H_x state hs conflicts with V_y state vs.
                        sat.forbid(xi, hs, X_SIZE + yi, vs);
                    }
                }
            };

            // H_x endpoint state determines relation to y; V_y endpoint state
            // determines relation to x. Each forbidden family is a complete
            // bipartite product of the corresponding relation-index sets.
            add_complete(idx_r, 0, idx_r, 0);
            add_complete(idx_q, 1, idx_r, 0);
            add_complete(idx_r, 0, idx_q, 1);
            add_complete(idx_q, 1, idx_q, 1);

            std::vector<int> assignment;
            if (!sat.solve(assignment)) continue;
            ++sat_instances;

            std::vector<std::uint32_t> remove;
            remove.reserve(2 * B_SIZE - 1);
            for (auto b : bset) {
                remove.push_back(r * U5 + b);
                if (b != r) remove.push_back(b * U5 + r);
            }
            std::sort(remove.begin(), remove.end());
            remove.erase(std::unique(remove.begin(), remove.end()), remove.end());
            if (remove.size() != 2 * B_SIZE - 1) throw std::runtime_error("remove size is not 717");

            std::unordered_set<std::uint32_t> baseline_set(baseline.begin(), baseline.end());
            for (auto id : remove) if (!baseline_set.count(id))
                throw std::runtime_error("expected removed BxB point is absent from baseline");

            std::vector<std::uint32_t> add;
            add.reserve(2 * X_SIZE);
            for (int i = 0; i < static_cast<int>(X_SIZE); ++i) {
                const std::uint32_t eh = assignment[i] ? q : r;
                const std::uint32_t ev = assignment[X_SIZE + i] ? q : r;
                add.push_back(eh * U5 + xset[i]);
                add.push_back(xset[i] * U5 + ev);
            }
            std::unordered_set<std::uint32_t> add_set(add.begin(), add.end());
            if (add_set.size() != add.size()) throw std::runtime_error("2-SAT solution has duplicate additions");

            // Recheck unary safety for selected additions and all cross H/V pairs.
            for (int i = 0; i < static_cast<int>(X_SIZE); ++i) {
                const std::uint16_t removed_cover = cov_b_x[i];
                if (coverage[add[2 * i]] != removed_cover || coverage[add[2 * i + 1]] != removed_cover)
                    throw std::runtime_error("selected addition is not freed by the row/column removal");
            }
            for (int i = 0; i < static_cast<int>(X_SIZE); ++i) {
                const std::uint32_t eh = assignment[i] ? q : r;
                for (int j = 0; j < static_cast<int>(X_SIZE); ++j) {
                    const std::uint32_t ev = assignment[X_SIZE + j] ? q : r;
                    if (conflict5(eh, xset[j], digits) && conflict5(xset[i], ev, digits))
                        throw std::runtime_error("2-SAT assignment failed cross-conflict replay");
                }
            }

            std::cerr << "gadget9 SAT r=" << r << " q=" << q
                      << " tested=" << tested
                      << " unary_feasible=" << unary_feasible << "\n";
            emit_bulk(remove, add, r, q, tested);
            return 0;
        }

        std::cerr << "gadget9 none tested=" << tested
                  << " unary_feasible=" << unary_feasible
                  << " sat_instances=" << sat_instances << "\n";
        std::cout << "{\"kind\":\"none\",\"method\":\"ninth-exchange-pair-2sat\","
                  << "\"baseline_size\":" << BASELINE_SCORE
                  << ",\"q_candidates\":" << q_candidates.size()
                  << ",\"tested_pairs\":" << tested
                  << ",\"unary_feasible\":" << unary_feasible
                  << ",\"sat_instances\":" << sat_instances << "}\n";
        return 0;
    } catch (const std::exception& e) {
        std::cerr << "error: " << e.what() << "\n";
        return 1;
    }
}
