#include <algorithm>
#include <array>
#include <bit>
#include <chrono>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <utility>
#include <vector>

#ifdef _OPENMP
#include <omp.h>
#endif

namespace {
constexpr int D = 10;
constexpr std::uint32_t POW7[D + 1] = {
    1u, 7u, 49u, 343u, 2401u, 16807u,
    117649u, 823543u, 5764801u, 40353607u, 282475249u
};
constexpr std::uint32_t N = POW7[D];
constexpr std::uint32_t GROUPS = N / 7u;
constexpr std::uint32_t INF = std::numeric_limits<std::uint32_t>::max();

using Clock = std::chrono::steady_clock;
enum class Op { Sum, Xor, Min, Max };

double elapsed(Clock::time_point t0) {
    return std::chrono::duration<double>(Clock::now() - t0).count();
}

template <class T, Op operation>
void transform(std::vector<T>& a, std::vector<T>& b, const char* label) {
    for (int dim = 0; dim < D; ++dim) {
        const std::uint32_t stride = POW7[dim];
        const std::uint64_t block = static_cast<std::uint64_t>(stride) * 7u;
        const auto t0 = Clock::now();
        #pragma omp parallel for schedule(static)
        for (std::int64_t gg = 0; gg < static_cast<std::int64_t>(GROUPS); ++gg) {
            const std::uint64_t g = static_cast<std::uint64_t>(gg);
            const std::uint64_t block_no = g / stride;
            const std::uint32_t off = static_cast<std::uint32_t>(g % stride);
            const std::uint64_t base = block_no * block + off;
            T v[7];
            for (int k = 0; k < 7; ++k) v[k] = a[base + static_cast<std::uint64_t>(k) * stride];
            for (int k = 0; k < 7; ++k) {
                const T l = v[(k + 6) % 7], m = v[k], r = v[(k + 1) % 7];
                T out{};
                if constexpr (operation == Op::Sum) out = static_cast<T>(l + m + r);
                else if constexpr (operation == Op::Xor) out = l ^ m ^ r;
                else if constexpr (operation == Op::Min) out = std::min(l, std::min(m, r));
                else out = std::max(l, std::max(m, r));
                b[base + static_cast<std::uint64_t>(k) * stride] = out;
            }
        }
        a.swap(b);
        std::cerr << label << " dim=" << dim << " sec=" << elapsed(t0) << "\n";
    }
}

std::vector<std::uint32_t> load_ids(const std::string& path) {
    std::ifstream in(path);
    if (!in) throw std::runtime_error("cannot open baseline ids");
    std::vector<std::uint32_t> ids;
    std::uint64_t x;
    while (in >> x) {
        if (x >= N) throw std::runtime_error("baseline id out of range");
        ids.push_back(static_cast<std::uint32_t>(x));
    }
    if (ids.empty()) throw std::runtime_error("empty baseline");
    std::unordered_set<std::uint32_t> seen;
    seen.reserve(ids.size() * 2);
    for (auto id : ids) if (!seen.insert(id).second) throw std::runtime_error("duplicate baseline id");
    return ids;
}

bool adjacent(std::uint32_t a, std::uint32_t b) {
    if (a == b) return true;
    for (int d = 0; d < D; ++d) {
        const int da = a % 7u, db = b % 7u;
        a /= 7u; b /= 7u;
        const int delta = (da - db + 7) % 7;
        if (delta != 0 && delta != 1 && delta != 6) return false;
    }
    return true;
}

bool compatible(std::uint32_t a, std::uint32_t b) {
    return a != b && !adjacent(a, b);
}

bool independent_triple(const std::vector<std::uint32_t>& v,
                        std::array<std::uint32_t, 3>& out) {
    const std::size_t n = v.size();
    if (n < 3) return false;
    const std::size_t words = (n + 63) / 64;
    std::vector<std::uint64_t> ok(n * words, 0);
    auto row = [&](std::size_t i) { return ok.data() + i * words; };

    for (std::size_t i = 0; i < n; ++i) {
        for (std::size_t j = i + 1; j < n; ++j) {
            if (!compatible(v[i], v[j])) continue;
            row(i)[j / 64] |= 1ull << (j % 64);
            row(j)[i / 64] |= 1ull << (i % 64);
        }
    }

    for (std::size_t i = 0; i < n; ++i) {
        for (std::size_t j = i + 1; j < n; ++j) {
            if ((row(i)[j / 64] & (1ull << (j % 64))) == 0) continue;
            for (std::size_t w = j / 64; w < words; ++w) {
                std::uint64_t bits = row(i)[w] & row(j)[w];
                if (w == j / 64) {
                    const unsigned cut = static_cast<unsigned>((j % 64) + 1);
                    if (cut == 64) bits = 0;
                    else bits &= (~0ull << cut);
                }
                if (!bits) continue;
                const std::size_t k = w * 64 + std::countr_zero(bits);
                if (k < n) {
                    out = {v[i], v[j], v[k]};
                    return true;
                }
            }
        }
    }
    return false;
}

}  // namespace

int main(int argc, char** argv) {
    try {
        if (argc != 2) {
            std::cerr << "usage: search_exact BASELINE_IDS\n";
            return 2;
        }
        const auto t_all = Clock::now();
        const auto baseline = load_ids(argv[1]);
        std::cerr << "vertices=" << N << " baseline=" << baseline.size();
#ifdef _OPENMP
        std::cerr << " omp_threads=" << omp_get_max_threads();
#endif
        std::cerr << "\n";

        std::unordered_set<std::uint32_t> baseline_set;
        baseline_set.reserve(baseline.size() * 2);
        for (auto x : baseline) baseline_set.insert(x);

        std::vector<std::uint16_t> count(N, 0), scratch16(N, 0);
        for (auto x : baseline) count[x] = 1;
        transform<std::uint16_t, Op::Sum>(count, scratch16, "count");
        scratch16.clear(); scratch16.shrink_to_fit();

        std::array<std::uint64_t, 17> hist{};
        for (std::uint32_t id = 0; id < N; ++id) {
            const auto c = count[id];
            if (c < 16) ++hist[c]; else ++hist[16];
            if (c == 0) {
                std::cout << "{\"kind\":\"direct\",\"add\":" << id
                          << ",\"baseline_size\":" << baseline.size() << "}\n";
                return 0;
            }
        }
        std::cerr << "coverage_hist";
        for (int i = 0; i < 16; ++i) std::cerr << " " << i << ":" << hist[i];
        std::cerr << " 16+:" << hist[16] << "\n";

        std::vector<std::uint32_t> xors(N, 0), scratch32(N, 0);
        for (std::uint32_t i = 0; i < baseline.size(); ++i) xors[baseline[i]] = i + 1u;
        transform<std::uint32_t, Op::Xor>(xors, scratch32, "xor");
        scratch32.clear(); scratch32.shrink_to_fit();

        std::vector<std::vector<std::uint32_t>> cov1(baseline.size());
        std::uint64_t cov1_total = 0;
        std::size_t max_cov1_group = 0;
        for (std::uint32_t id = 0; id < N; ++id) {
            if (count[id] != 1 || baseline_set.contains(id)) continue;
            const std::uint32_t owner = xors[id];
            if (owner == 0 || owner > baseline.size()) throw std::runtime_error("bad coverage-1 owner");
            auto& g = cov1[owner - 1u];
            g.push_back(id);
            ++cov1_total;
            max_cov1_group = std::max(max_cov1_group, g.size());
        }
        xors.clear(); xors.shrink_to_fit();

        std::uint64_t cov1_pairs = 0;
        for (std::uint32_t oi = 0; oi < cov1.size(); ++oi) {
            const auto& g = cov1[oi];
            for (std::size_t i = 0; i < g.size(); ++i) {
                for (std::size_t j = i + 1; j < g.size(); ++j) {
                    ++cov1_pairs;
                    if (!compatible(g[i], g[j])) continue;
                    std::cout << "{\"kind\":\"replace1\",\"remove_index\":" << oi
                              << ",\"remove\":" << baseline[oi]
                              << ",\"add\":[" << g[i] << "," << g[j] << "]"
                              << ",\"baseline_size\":" << baseline.size() << "}\n";
                    return 0;
                }
            }
        }
        std::cerr << "replace1_exact_none cov1=" << cov1_total
                  << " max_group=" << max_cov1_group
                  << " pairs=" << cov1_pairs << "\n";

        std::vector<std::uint32_t> min_owner(N, INF), tmp_min(N, INF);
        for (std::uint32_t i = 0; i < baseline.size(); ++i) min_owner[baseline[i]] = i + 1u;
        transform<std::uint32_t, Op::Min>(min_owner, tmp_min, "min-owner");
        tmp_min.clear(); tmp_min.shrink_to_fit();

        std::vector<std::uint32_t> max_owner(N, 0), tmp_max(N, 0);
        for (std::uint32_t i = 0; i < baseline.size(); ++i) max_owner[baseline[i]] = i + 1u;
        transform<std::uint32_t, Op::Max>(max_owner, tmp_max, "max-owner");
        tmp_max.clear(); tmp_max.shrink_to_fit();

        std::unordered_map<std::uint64_t, std::vector<std::uint32_t>> cov2;
        cov2.reserve(180000);
        std::uint64_t cov2_total = 0;
        std::size_t max_cov2_group = 0;
        for (std::uint32_t id = 0; id < N; ++id) {
            if (count[id] != 2) continue;
            const auto lo = min_owner[id], hi = max_owner[id];
            if (lo == INF || lo == 0 || hi == 0 || hi == INF || lo >= hi || hi > baseline.size())
                throw std::runtime_error("bad coverage-2 owners");
            const std::uint32_t a = lo - 1u, b = hi - 1u;
            const std::uint64_t key = (static_cast<std::uint64_t>(a) << 32) | b;
            auto& g = cov2[key];
            g.push_back(id);
            max_cov2_group = std::max(max_cov2_group, g.size());
            ++cov2_total;
        }
        count.clear(); count.shrink_to_fit();
        min_owner.clear(); min_owner.shrink_to_fit();
        max_owner.clear(); max_owner.shrink_to_fit();

        std::vector<std::pair<std::uint64_t, std::size_t>> keys;
        keys.reserve(cov2.size());
        for (const auto& [key, g] : cov2) {
            const std::uint32_t a = static_cast<std::uint32_t>(key >> 32);
            const std::uint32_t b = static_cast<std::uint32_t>(key);
            keys.push_back({key, g.size() + cov1[a].size() + cov1[b].size()});
        }
        std::sort(keys.begin(), keys.end(), [](auto x, auto y) { return x.second > y.second; });

        std::size_t max_union = 0;
        std::uint64_t union_vertices_scanned = 0;
        const auto t_r2 = Clock::now();
        for (const auto& [key, union_size] : keys) {
            max_union = std::max(max_union, union_size);
            const std::uint32_t a = static_cast<std::uint32_t>(key >> 32);
            const std::uint32_t b = static_cast<std::uint32_t>(key);
            std::vector<std::uint32_t> candidates;
            candidates.reserve(union_size);
            candidates.insert(candidates.end(), cov2.at(key).begin(), cov2.at(key).end());
            candidates.insert(candidates.end(), cov1[a].begin(), cov1[a].end());
            candidates.insert(candidates.end(), cov1[b].begin(), cov1[b].end());
            union_vertices_scanned += candidates.size();

            std::array<std::uint32_t, 3> add{};
            if (!independent_triple(candidates, add)) continue;
            std::cout << "{\"kind\":\"replace2\",\"remove_indices\":[" << a << "," << b << "]"
                      << ",\"remove\":[" << baseline[a] << "," << baseline[b] << "]"
                      << ",\"add\":[" << add[0] << "," << add[1] << "," << add[2] << "]"
                      << ",\"baseline_size\":" << baseline.size() << "}\n";
            return 0;
        }

        std::cerr << "replace2_exact_none owner_pairs=" << cov2.size()
                  << " cov2=" << cov2_total
                  << " max_cov2_group=" << max_cov2_group
                  << " max_union=" << max_union
                  << " union_vertices_scanned=" << union_vertices_scanned
                  << " sec=" << elapsed(t_r2)
                  << " total_sec=" << elapsed(t_all) << "\n";

        std::cout << "{\"kind\":\"none\",\"baseline_size\":" << baseline.size()
                  << ",\"outside_coverage1\":" << cov1_total
                  << ",\"max_coverage1_group\":" << max_cov1_group
                  << ",\"coverage1_pairs_checked\":" << cov1_pairs
                  << ",\"coverage2\":" << cov2_total
                  << ",\"owner_pairs\":" << cov2.size()
                  << ",\"max_coverage2_group\":" << max_cov2_group
                  << ",\"max_union\":" << max_union << "}\n";
        return 0;
    } catch (const std::exception& e) {
        std::cerr << "error: " << e.what() << "\n";
        return 1;
    }
}
