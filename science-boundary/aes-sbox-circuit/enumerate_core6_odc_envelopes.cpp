// Exact nonlinear-envelope census for the fixed-interface six-AND p008 core.
//
// Exhausts all 512 zero-state completions of the live nine-factor relation,
// identifies the 16 rank-four target spaces and the common rank-five target space,
// then enumerates every reachable six-dimensional nonlinear envelope containing
// each target space.  This is a quotient-level exact census, not a physical-gate
// realizability claim.
#include <algorithm>
#include <array>
#include <cstdint>
#include <iostream>
#include <map>
#include <set>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>
using namespace std;

static array<uint16_t, 65536> STRIP;

uint16_t mobius16(uint16_t x) {
    uint32_t y = x;
    y ^= (y & 0x5555u) << 1;
    y ^= (y & 0x3333u) << 2;
    y ^= (y & 0x0F0Fu) << 4;
    y ^= (y & 0x00FFu) << 8;
    return uint16_t(y & 0xFFFFu);
}

uint16_t strip_affine(uint16_t x) {
    uint16_t a = mobius16(x);
    a &= uint16_t(~0x0117u);  // remove 1,x0,x1,x2,x3 ANF monomials
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
    for (int p = 0; p < 16; ++p)
        if (rows[p]) out.push_back(rows[p]);
    return out;
}

uint16_t reduce_by_basis(uint16_t x, const Basis &b) {
    uint16_t y = x;
    for (auto it = b.rbegin(); it != b.rend(); ++it) {
        uint16_t v = *it;
        int p = 31 - __builtin_clz((unsigned)v);
        if ((y >> p) & 1) y ^= v;
    }
    return y;
}

vector<uint16_t> span_values(const Basis &b) {
    vector<uint16_t> out{0};
    for (uint16_t v : b) {
        size_t n = out.size();
        for (size_t i = 0; i < n; ++i) out.push_back(out[i] ^ v);
    }
    return out;
}

string key_basis(const Basis &b) {
    string s;
    s.resize(1 + 2 * b.size());
    s[0] = char(b.size());
    for (size_t i = 0; i < b.size(); ++i) {
        s[1 + 2 * i] = char(b[i] & 255);
        s[2 + 2 * i] = char(b[i] >> 8);
    }
    return s;
}

array<uint16_t, 4> INPUTS;
Basis LINEAR_BASIS;
array<uint16_t, 9> TARGETS;

void init_targets() {
    for (int i = 0; i < 4; ++i) INPUTS[i] = var(i);
    LINEAR_BASIS = canonical_basis(Basis(INPUTS.begin(), INPUTS.end()));
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
    TARGETS = {q45, q59, q52, q57, q53, q49, q58, q55, q56};
}

unordered_map<string, vector<uint16_t>> candidate_cache;

const vector<uint16_t> &candidate_residues(const Basis &b) {
    string k = key_basis(b);
    auto it = candidate_cache.find(k);
    if (it != candidate_cache.end()) return it->second;

    Basis all = LINEAR_BASIS;
    all.insert(all.end(), b.begin(), b.end());
    all = canonical_basis(all);
    auto fs = span_values(all);
    set<uint16_t> residues;
    for (size_t i = 1; i < fs.size(); ++i) {
        for (size_t j = 1; j < i; ++j) {
            uint16_t r = STRIP[uint16_t(fs[i] & fs[j])];
            if (r && reduce_by_basis(r, b)) residues.insert(r);
        }
    }
    vector<uint16_t> values(residues.begin(), residues.end());
    auto [inserted, _] = candidate_cache.emplace(k, move(values));
    return inserted->second;
}

set<Basis> first_step_spans() {
    set<Basis> out;
    for (uint16_t r : candidate_residues(Basis{}))
        out.insert(canonical_basis(Basis{r}));
    return out;
}

pair<set<Basis>, set<Basis>> transition_rank5(
    const set<Basis> &frontier, const Basis &target) {
    set<Basis> stay, envelopes;
    for (const Basis &b : frontier) {
        Basis joined = b;
        joined.insert(joined.end(), target.begin(), target.end());
        joined = canonical_basis(joined);
        if (joined.size() != 5) throw runtime_error("unexpected join rank");
        for (uint16_t r : candidate_residues(b)) {
            if (!reduce_by_basis(r, joined)) {
                Basis next = b;
                next.push_back(r);
                stay.insert(canonical_basis(next));
            } else {
                Basis e = joined;
                e.push_back(r);
                e = canonical_basis(e);
                if (e.size() != 6) throw runtime_error("unexpected envelope rank");
                envelopes.insert(e);
            }
        }
    }
    return {move(stay), move(envelopes)};
}

set<Basis> envelopes_for_target(const Basis &target) {
    set<Basis> frontier = first_step_spans();
    set<Basis> all;
    for (int depth = 2; depth <= 6; ++depth) {
        auto [stay, exposed] = transition_rank5(frontier, target);
        all.insert(exposed.begin(), exposed.end());
        frontier = move(stay);
    }
    if (!frontier.empty()) throw runtime_error("rank-five frontier did not exhaust");
    return all;
}

string bits9(int p) {
    string s;
    for (int i = 8; i >= 0; --i) s.push_back(((p >> i) & 1) ? '1' : '0');
    return s;
}

int main() {
    for (int x = 0; x < 65536; ++x) STRIP[x] = strip_affine(uint16_t(x));
    init_targets();
    constexpr uint16_t CARE_NONZERO = 0xFFFE;

    map<Basis, vector<int>> completions_by_space;
    for (int pattern = 0; pattern < 512; ++pattern) {
        Basis residues;
        for (int i = 0; i < 9; ++i) {
            uint16_t t = TARGETS[i] ^ (((pattern >> i) & 1) ? CARE_NONZERO : 0);
            residues.push_back(STRIP[t]);
        }
        completions_by_space[canonical_basis(residues)].push_back(pattern);
    }

    vector<pair<int, Basis>> rank4;
    Basis rank5_space;
    vector<int> rank5_patterns;
    for (auto &kv : completions_by_space) {
        if (kv.first.size() == 4) {
            if (kv.second.size() != 1) throw runtime_error("rank-four multiplicity");
            rank4.push_back({kv.second[0], kv.first});
        } else if (kv.first.size() == 5) {
            if (!rank5_space.empty()) throw runtime_error("multiple rank-five spaces");
            rank5_space = kv.first;
            rank5_patterns = kv.second;
        }
    }
    sort(rank4.begin(), rank4.end());
    cout << "rank4_cases=" << rank4.size()
         << " rank5_patterns=" << rank5_patterns.size() << '\n';
    if (rank4.size() != 16 || rank5_patterns.size() != 496) return 2;

    vector<set<Basis>> envelope_sets;
    map<Basis, int> multiplicity;
    for (auto &pt : rank4) {
        auto es = envelopes_for_target(pt.second);
        cout << bits9(pt.first) << " envelopes=" << es.size() << '\n';
        for (auto &e : es) ++multiplicity[e];
        envelope_sets.push_back(move(es));
    }

    map<int, int> histogram;
    for (auto &kv : multiplicity) ++histogram[kv.second];
    cout << "union=" << multiplicity.size() << " multiplicity:";
    for (auto &kv : histogram) cout << ' ' << kv.first << ':' << kv.second;
    cout << '\n';

    size_t pair_min = size_t(-1), pair_max = 0;
    long long pair_sum = 0;
    int pairs = 0;
    for (int i = 0; i < 16; ++i) {
        for (int j = i + 1; j < 16; ++j) {
            size_t count = 0;
            auto a = envelope_sets[i].begin(), b = envelope_sets[j].begin();
            while (a != envelope_sets[i].end() && b != envelope_sets[j].end()) {
                if (*a < *b) ++a;
                else if (*b < *a) ++b;
                else { ++count; ++a; ++b; }
            }
            pair_min = min(pair_min, count);
            pair_max = max(pair_max, count);
            pair_sum += count;
            ++pairs;
        }
    }
    cout << "pair_intersection_min=" << pair_min
         << " max=" << pair_max
         << " sum=" << pair_sum
         << " pairs=" << pairs << '\n';

    set<Basis> common = envelope_sets[0];
    for (int i = 1; i < 16; ++i) {
        set<Basis> next;
        set_intersection(common.begin(), common.end(),
                         envelope_sets[i].begin(), envelope_sets[i].end(),
                         inserter(next, next.end()));
        common.swap(next);
    }
    cout << "common16=" << common.size() << '\n';

    set<Basis> rank5_first_envelopes;
    map<Basis, vector<uint16_t>> generators;
    for (uint16_t r : candidate_residues(Basis{})) {
        Basis e = rank5_space;
        e.push_back(r);
        e = canonical_basis(e);
        if (e.size() == 6) {
            rank5_first_envelopes.insert(e);
            generators[e].push_back(r);
        }
    }
    cout << "rank5_first_envelopes=" << rank5_first_envelopes.size() << '\n';

    size_t common_in_rank5 = 0, rank5_in_union = 0;
    for (auto &e : common) if (rank5_first_envelopes.count(e)) ++common_in_rank5;
    for (auto &e : rank5_first_envelopes) if (multiplicity.count(e)) ++rank5_in_union;
    cout << "common_in_rank5=" << common_in_rank5
         << " rank5_envs_in_rank4_union=" << rank5_in_union << '\n';

    cout << "rank5_not_common=" << rank5_first_envelopes.size() - common_in_rank5 << '\n';
    for (auto &e : rank5_first_envelopes) {
        if (common.count(e)) continue;
        cout << "not_common first_residues=";
        for (uint16_t r : generators[e]) {
            cout << "0x" << hex << r << dec << ' ';
        }
        cout << '\n';
    }

    // Regression checks for the complete census.
    if (envelope_sets[0].size() != 1545) return 3;
    for (int i = 1; i < 16; ++i) if (envelope_sets[i].size() != 1525) return 3;
    if (multiplicity.size() != 23970) return 3;
    if (histogram != map<int, int>{{1, 23940}, {16, 30}}) return 3;
    if (pair_min != 30 || pair_max != 30 || common.size() != 30) return 3;
    if (rank5_first_envelopes.size() != 35 || common_in_rank5 != 30 || rank5_in_union != 30) return 3;
    return 0;
}
