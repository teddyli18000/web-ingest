// Exact necessary-condition screen for the most favorable unresolved six-AND p008 core case.
//
// The live 102-gate AES S-box falls to 101 if its fixed 18-gate four-input/nine-factor
// core is replaced by 6 AND + 11 XOR/XNOR gates.  All five-AND cases and all
// quotient-rank-five six-AND cases are already excluded.  This program studies the
// remaining rank-four-completion / six-independent-AND / rank-six family under the
// strongest possible direct-target exposure: exactly four of the six raw AND outputs
// are themselves required tail factors.  Four is the maximum because the nine target
// residues span a four-dimensional quotient space T while the six raw AND residues
// are independent.
//
// With four raw target ANDs there are exactly two helper ANDs.  The first AND must be
// a helper (every target has algebraic degree three), and the second helper must add
// the second quotient dimension outside T; otherwise six independent raw AND classes
// cannot span a rank-six envelope containing T.  The other four ANDs must output four
// exact target functions for the selected zero-state completion.
//
// The search is deliberately MORE permissive than a physical circuit:
//   * every affine function of currently available primitive sources, with either
//     constant phase, may be used as an AND operand;
//   * each distinct non-source affine operand form is charged only one linear gate,
//     even if its actual XOR/XNOR realization would need helpers;
//   * after six ANDs, each remaining non-raw target affine form is likewise charged
//     only one gate, without enforcing a realizable linear schedule.
// Therefore a completed zero-hit case is a rigorous exclusion for 6 AND + <=11
// linear gates in the raw-target-count-four branch.  A hit would only be a necessary
// witness and would require exact scheduling before becoming a circuit.

#include <algorithm>
#include <array>
#include <chrono>
#include <cstdint>
#include <iostream>
#include <map>
#include <set>
#include <unordered_map>
#include <vector>

using namespace std;
using Clock = chrono::steady_clock;

constexpr uint16_t ONES = 0xffff;
constexpr uint16_t CARE_NONZERO = 0xfffe;
constexpr int MAX_LINEAR = 11;
static array<uint16_t, 65536> STRIP;

uint16_t mobius16(uint16_t x) {
    uint32_t y = x;
    y ^= (y & 0x5555u) << 1;
    y ^= (y & 0x3333u) << 2;
    y ^= (y & 0x0f0fu) << 4;
    y ^= (y & 0x00ffu) << 8;
    return uint16_t(y & 0xffffu);
}

uint16_t strip_affine(uint16_t x) {
    uint16_t a = mobius16(x);
    a &= uint16_t(~0x0117u);  // remove 1,x0,x1,x2,x3
    return mobius16(a);
}

uint16_t var(int i) {
    uint16_t v = 0;
    for (int x = 0; x < 16; ++x)
        if ((x >> i) & 1) v |= uint16_t(1u << x);
    return v;
}

using Basis = vector<uint16_t>;

Basis canonical_basis(const Basis &vecs) {
    array<uint16_t, 16> rows{};
    for (uint16_t x0 : vecs) {
        uint16_t y = x0;
        while (y) {
            int p = 31 - __builtin_clz((unsigned)y);
            if (rows[p]) {
                y ^= rows[p];
                continue;
            }
            for (int q = p - 1; q >= 0; --q)
                if (rows[q] && ((y >> q) & 1)) y ^= rows[q];
            if (!y) break;
            p = 31 - __builtin_clz((unsigned)y);
            for (int q = p + 1; q < 16; ++q)
                if (rows[q] && ((rows[q] >> p) & 1)) rows[q] ^= y;
            rows[p] = y;
            break;
        }
    }
    Basis out;
    for (uint16_t x : rows)
        if (x) out.push_back(x);
    return out;
}

uint16_t reduce_by_basis(uint16_t x, const Basis &b) {
    uint16_t y = x;
    for (auto it = b.rbegin(); it != b.rend(); ++it) {
        int p = 31 - __builtin_clz((unsigned)*it);
        if ((y >> p) & 1) y ^= *it;
    }
    return y;
}

array<uint16_t, 4> INPUTS;
array<uint16_t, 9> BASE_TARGETS;

void init_targets() {
    for (int x = 0; x < 65536; ++x) STRIP[x] = strip_affine(uint16_t(x));
    for (int i = 0; i < 4; ++i) INPUTS[i] = var(i);
    auto [a, b, c, d] = INPUTS;
    uint16_t q42 = a & b;
    uint16_t q43 = q42 ^ c;
    uint16_t q44 = q43 & d;
    uint16_t q45 = b ^ q44;
    uint16_t q46 = q42 & c;
    uint16_t q47 = d ^ q46;
    uint16_t q48 = a & q47;
    uint16_t q49 = q43 ^ q48;
    uint16_t q50 = q48 ^ b;
    uint16_t q51 = q49 & q50;
    uint16_t q52 = q51 ^ a;
    uint16_t q53 = q52 ^ q49;
    uint16_t q54 = q45 & q53;
    uint16_t q55 = q54 ^ q47;
    uint16_t q56 = q55 ^ q49;
    uint16_t q57 = q53 ^ q45;
    uint16_t q58 = q56 ^ q57;
    uint16_t q59 = q55 ^ q45;
    BASE_TARGETS = {q45, q59, q52, q57, q53, q49, q58, q55, q56};
}

struct Completion {
    int pattern = 0;
    array<uint16_t, 9> actual{};
    array<uint16_t, 9> residue{};
    Basis target_space;
};

vector<Completion> rank4_cases;

void init_cases() {
    for (int pattern = 0; pattern < 512; ++pattern) {
        Completion c;
        c.pattern = pattern;
        Basis residues;
        for (int i = 0; i < 9; ++i) {
            int phase = (pattern >> i) & 1;
            // The fixed tail keeps all nonzero-state values exact and frees only x=0.
            c.actual[i] = BASE_TARGETS[i] ^ (phase ? uint16_t(1) : uint16_t(0));
            c.residue[i] = STRIP[c.actual[i]];
            residues.push_back(c.residue[i]);
        }
        c.target_space = canonical_basis(residues);
        if (c.target_space.size() == 4) rank4_cases.push_back(c);
    }
    sort(rank4_cases.begin(), rank4_cases.end(),
         [](const Completion &a, const Completion &b) { return a.pattern < b.pattern; });
    if (rank4_cases.size() != 16) throw runtime_error("expected 16 rank-four completions");
}

struct Form {
    uint16_t mask;
    uint8_t constant;
};

uint16_t encode_form(Form f) {
    return uint16_t((f.mask << 1) | f.constant);
}

bool is_free_form(uint16_t encoded) {
    uint16_t mask = encoded >> 1;
    return (encoded & 1) == 0 && mask && !(mask & (mask - 1));
}

using Mandatory = vector<uint16_t>;

Mandatory add_form(Mandatory m, uint16_t form) {
    if (is_free_form(form)) return m;
    auto it = lower_bound(m.begin(), m.end(), form);
    if (it == m.end() || *it != form) m.insert(it, form);
    return m;
}

struct AffineSpace {
    vector<uint16_t> truths;
    unordered_map<uint16_t, Form> form;
};

AffineSpace affine_space(const array<uint16_t, 6> &raw, int depth) {
    vector<pair<uint16_t, uint16_t>> pairs{{0, 0}};
    for (int i = 0; i < 4; ++i) {
        size_t n = pairs.size();
        for (size_t j = 0; j < n; ++j)
            pairs.push_back({uint16_t(pairs[j].first ^ INPUTS[i]),
                             uint16_t(pairs[j].second | (1u << i))});
    }
    for (int i = 0; i < depth; ++i) {
        size_t n = pairs.size();
        for (size_t j = 0; j < n; ++j)
            pairs.push_back({uint16_t(pairs[j].first ^ raw[i]),
                             uint16_t(pairs[j].second | (1u << (4 + i)))});
    }

    AffineSpace out;
    out.truths.reserve(pairs.size() * 2);
    out.form.reserve(pairs.size() * 2);
    for (auto [truth, mask] : pairs) {
        out.truths.push_back(truth);
        out.form[truth] = {mask, 0};
        out.truths.push_back(uint16_t(truth ^ ONES));
        out.form[uint16_t(truth ^ ONES)] = {mask, 1};
    }
    sort(out.truths.begin(), out.truths.end());
    out.truths.erase(unique(out.truths.begin(), out.truths.end()), out.truths.end());
    return out;
}

struct State {
    array<uint16_t, 6> raw{};  // actual, not normalized, raw AND truth tables
    Basis nonlinear_basis;
    Mandatory mandatory;
    uint16_t raw_target_mask = 0;
    int depth = 0;
    int helpers = 0;
};

struct Stats {
    unsigned long long nodes = 0;
    unsigned long long target_edges = 0;
    unsigned long long helper_edges = 0;
    unsigned long long complete_raw_sequences = 0;
    unsigned long long hits_le_11 = 0;
    int minimum_mandatory = 999;
};

Completion CURRENT;

void dfs(const State &s, Stats &stats) {
    ++stats.nodes;

    if (s.depth == 6) {
        if (s.helpers != 2 || __builtin_popcount((unsigned)s.raw_target_mask) != 4) return;
        ++stats.complete_raw_sequences;

        AffineSpace a = affine_space(s.raw, s.depth);
        Mandatory full = s.mandatory;
        for (int i = 0; i < 9; ++i) {
            if ((s.raw_target_mask >> i) & 1) continue;
            auto it = a.form.find(CURRENT.actual[i]);
            if (it == a.form.end()) return;
            full = add_form(move(full), encode_form(it->second));
            if ((int)full.size() > MAX_LINEAR) return;
        }
        stats.minimum_mandatory = min(stats.minimum_mandatory, (int)full.size());
        if ((int)full.size() <= MAX_LINEAR) ++stats.hits_le_11;
        return;
    }

    int remaining = 6 - s.depth;
    int needed_targets = 4 - __builtin_popcount((unsigned)s.raw_target_mask);
    int needed_helpers = 2 - s.helpers;
    if (needed_targets + needed_helpers != remaining) return;

    AffineSpace a = affine_space(s.raw, s.depth);

    // Enumerate products once at this physical state.  We intentionally keep all
    // operand representations because different affine forms have different mandatory costs.
    unordered_map<uint16_t, vector<pair<uint16_t, uint16_t>>> products;
    products.reserve(a.truths.size() * 2);
    for (size_t i = 1; i < a.truths.size(); ++i) {
        for (size_t j = 0; j < i; ++j) {
            uint16_t left = a.truths[i];
            uint16_t right = a.truths[j];
            uint16_t product = uint16_t(left & right);
            if (!product) continue;
            bool is_remaining_target = false;
            for (int t = 0; t < 9; ++t) {
                if (!((s.raw_target_mask >> t) & 1) && product == CURRENT.actual[t]) {
                    is_remaining_target = true;
                    break;
                }
            }
            if (is_remaining_target || s.helpers < 2)
                products[product].push_back({left, right});
        }
    }

    // A target-AND must output the exact completion function and add an independent
    // nonlinear class.  Four such classes will then form a basis of T.
    if (needed_targets > 0) {
        for (int t = 0; t < 9; ++t) {
            if ((s.raw_target_mask >> t) & 1) continue;
            uint16_t residue = CURRENT.residue[t];
            if (!reduce_by_basis(residue, s.nonlinear_basis)) continue;
            auto pit = products.find(CURRENT.actual[t]);
            if (pit == products.end()) continue;
            for (auto [left, right] : pit->second) {
                State next = s;
                next.raw[next.depth] = CURRENT.actual[t];
                ++next.depth;
                next.raw_target_mask |= uint16_t(1u << t);
                next.nonlinear_basis.push_back(residue);
                next.nonlinear_basis = canonical_basis(next.nonlinear_basis);
                next.mandatory = add_form(move(next.mandatory), encode_form(a.form.at(left)));
                next.mandatory = add_form(move(next.mandatory), encode_form(a.form.at(right)));
                if ((int)next.mandatory.size() > MAX_LINEAR) continue;
                ++stats.target_edges;
                dfs(next, stats);
            }
        }
    }

    // There are exactly two non-target helper ANDs.  Gate 1 is necessarily a helper.
    // The second helper must add a class outside span(current,T), because all remaining
    // raw gates are targets in T and the final raw quotient rank must be six.
    if (needed_helpers > 0) {
        Basis joined = s.nonlinear_basis;
        joined.insert(joined.end(), CURRENT.target_space.begin(), CURRENT.target_space.end());
        joined = canonical_basis(joined);

        for (auto &entry : products) {
            uint16_t product = entry.first;
            uint16_t residue = STRIP[product];
            if (!residue || !reduce_by_basis(residue, s.nonlinear_basis)) continue;

            if (s.helpers == 0) {
                if (s.depth != 0) continue;  // first gate is the first helper
            } else {
                if (joined.size() != 5 || !reduce_by_basis(residue, joined)) continue;
            }

            bool exact_target = false;
            for (uint16_t target : CURRENT.actual)
                if (product == target) {
                    exact_target = true;
                    break;
                }
            if (exact_target) continue;  // count it in the target branch, never as helper

            for (auto [left, right] : entry.second) {
                State next = s;
                next.raw[next.depth] = product;
                ++next.depth;
                ++next.helpers;
                next.nonlinear_basis.push_back(residue);
                next.nonlinear_basis = canonical_basis(next.nonlinear_basis);
                next.mandatory = add_form(move(next.mandatory), encode_form(a.form.at(left)));
                next.mandatory = add_form(move(next.mandatory), encode_form(a.form.at(right)));
                if ((int)next.mandatory.size() > MAX_LINEAR) continue;
                ++stats.helper_edges;
                dfs(next, stats);
            }
        }
    }
}

string bits9(int p) {
    string s;
    for (int i = 8; i >= 0; --i) s.push_back(((p >> i) & 1) ? '1' : '0');
    return s;
}

int main(int argc, char **argv) {
    init_targets();
    init_cases();
    int case_index = argc > 1 ? stoi(argv[1]) : 0;
    if (case_index < 0 || case_index >= (int)rank4_cases.size()) return 2;
    CURRENT = rank4_cases[case_index];

    State start;
    Stats stats;
    auto began = Clock::now();
    dfs(start, stats);
    double seconds = chrono::duration<double>(Clock::now() - began).count();

    cout << "{\"case\":" << case_index
         << ",\"completion_pattern\":" << CURRENT.pattern
         << ",\"completion_binary\":\"" << bits9(CURRENT.pattern) << "\""
         << ",\"nodes\":" << stats.nodes
         << ",\"target_edges\":" << stats.target_edges
         << ",\"helper_edges\":" << stats.helper_edges
         << ",\"complete_raw_sequences\":" << stats.complete_raw_sequences
         << ",\"minimum_mandatory\":"
         << (stats.minimum_mandatory == 999 ? -1 : stats.minimum_mandatory)
         << ",\"hits_le_11\":" << stats.hits_le_11
         << ",\"seconds\":" << seconds << "}" << '\n';

    return stats.hits_le_11 ? 1 : 0;
}
