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
constexpr std::uint32_t NONE = std::numeric_limits<std::uint32_t>::max();
constexpr std::uint32_t INF = std::numeric_limits<std::uint32_t>::max();

using Clock = std::chrono::steady_clock;

enum class Op { Sum, Xor, Min, Max };

double seconds_since(Clock::time_point t0) {
    return std::chrono::duration<double>(Clock::now() - t0).count();
}

template <class T, Op operation>
void neighborhood_transform(std::vector<T>& a, std::vector<T>& b, const char* label) {
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
            for (int k = 0; k < 7; ++k) {
                v[k] = a[base + static_cast<std::uint64_t>(k) * stride];
            }
            for (int k = 0; k < 7; ++k) {
                const T left = v[(k + 6) % 7];
                const T mid = v[k];
                const T right = v[(k + 1) % 7];
                T out{};
                if constexpr (operation == Op::Sum) {
                    out = static_cast<T>(left + mid + right);
                } else if constexpr (operation == Op::Xor) {
                    out = left ^ mid ^ right;
                } else if constexpr (operation == Op::Min) {
                    out = std::min(left, std::min(mid, right));
                } else {
                    out = std::max(left, std::max(mid, right));
                }
                b[base + static_cast<std::uint64_t>(k) * stride] = out;
            }
        }
        a.swap(b);
        std::cerr << label << " dim=" << dim
                  << " stride=" << stride
                  << " sec=" << seconds_since(t0) << "\n";
    }
}

std::vector<std::uint32_t> load_ids(const std::string& path) {
    std::ifstream in(path);
    if (!in) throw std::runtime_error("cannot open baseline id file");

    std::vector<std::uint32_t> ids;
    std::uint64_t x;
    while (in >> x) {
        if (x >= N) throw std::runtime_error("baseline id out of range");
        ids.push_back(static_cast<std::uint32_t>(x));
    }
    if (ids.empty()) throw std::runtime_error("baseline id file is empty");

    std::unordered_set<std::uint32_t> seen;
    seen.reserve(ids.size() * 2);
    for (auto id : ids) {
        if (!seen.insert(id).second) throw std::runtime_error("duplicate baseline id");
    }
    return ids;
}

bool strong_adjacent(std::uint32_t a, std::uint32_t b) {
    if (a == b) return true;
    for (int d = 0; d < D; ++d) {
        const int x = a % 7u;
        const int y = b % 7u;
        a /= 7u;
        b /= 7u;
        const int delta = (x - y + 7) % 7;
        if (delta != 0 && delta != 1 && delta != 6) return false;
    }
    return true;
}

bool compatible(std::uint32_t a, std::uint32_t b) {
    return a != b && !strong_adjacent(a, b);
}

std::pair<std::uint16_t, std::uint16_t> relative_masks(std::uint32_t candidate,
                                                       std::uint32_t owner) {
    std::uint16_t neg = 0;
    std::uint16_t pos = 0;
    for (int d = 0; d < D; ++d) {
        const int a = candidate % 7u;
        const int b = owner % 7u;
        candidate /= 7u;
        owner /= 7u;
        const int delta = (a - b + 7) % 7;
        if (delta == 6) neg |= static_cast<std::uint16_t>(1u << d);
        else if (delta == 1) pos |= static_cast<std::uint16_t>(1u << d);
        else if (delta != 0) throw std::runtime_error("coverage owner is not adjacent");
    }
    return {neg, pos};
}

void emit_replace2(const std::vector<std::uint32_t>& baseline,
                   std::uint32_t i, std::uint32_t j,
                   const std::array<std::uint32_t, 3>& add) {
    std::cout << "{\"kind\":\"replace2\",\"remove_indices\":[" << i << "," << j
              << "],\"remove\":[" << baseline[i] << "," << baseline[j]
              << "],\"add\":[" << add[0] << "," << add[1] << "," << add[2]
              << "],\"baseline_size\":" << baseline.size() << "}\n";
}

bool try_replace2_group(std::uint32_t oi, std::uint32_t oj,
                        const std::vector<std::uint32_t>& c2,
                        const std::vector<std::vector<std::uint32_t>>& cov1,
                        std::array<std::uint32_t, 3>& answer) {
    const auto& a1 = cov1[oi];
    const auto& b1 = cov1[oj];

    // One exact-two-conflict candidate plus one unique candidate from each owner.
    for (auto x : c2) {
        for (auto a : a1) {
            if (!compatible(x, a)) continue;
            for (auto b : b1) {
                if (compatible(x, b) && compatible(a, b)) {
                    answer = {x, a, b};
                    return true;
                }
            }
        }
    }

    const std::size_t k = c2.size();
    if (k < 2) return false;

    // Build the non-adjacency graph inside the exact-two-conflict candidates.
    // A triangle is three mutually compatible additions. While building it, also
    // test every compatible pair against the coverage-1 candidates at either owner.
    const std::size_t words = (k + 63) / 64;
    std::vector<std::uint64_t> nonadj(k * words, 0);
    auto row = [&](std::size_t i) { return nonadj.data() + i * words; };

    for (std::size_t i = 0; i < k; ++i) {
        for (std::size_t j = i + 1; j < k; ++j) {
            if (!compatible(c2[i], c2[j])) continue;
            row(i)[j / 64] |= 1ull << (j % 64);
            row(j)[i / 64] |= 1ull << (i % 64);

            for (auto a : a1) {
                if (compatible(c2[i], a) && compatible(c2[j], a)) {
                    answer = {c2[i], c2[j], a};
                    return true;
                }
            }
            for (auto b : b1) {
                if (compatible(c2[i], b) && compatible(c2[j], b)) {
                    answer = {c2[i], c2[j], b};
                    return true;
                }
            }
        }
    }

    for (std::size_t i = 0; i < k; ++i) {
        for (std::size_t j = i + 1; j < k; ++j) {
            if ((row(i)[j / 64] & (1ull << (j % 64))) == 0) continue;
            const std::size_t first_word = j / 64;
            for (std::size_t w = first_word; w < words; ++w) {
                std::uint64_t bits = row(i)[w] & row(j)[w];
                if (w == first_word) {
                    const unsigned shift = static_cast<unsigned>((j + 1) % 64);
                    if (shift != 0) bits &= (~0ull << shift);
                    else if (j + 1 >= (w + 1) * 64) bits = 0;
                }
                if (bits == 0) continue;
                const unsigned bit = std::countr_zero(bits);
                const std::size_t l = w * 64 + bit;
                if (l < k) {
                    answer = {c2[i], c2[j], c2[l]};
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
            std::cerr << "usage: search BASELINE_IDS\n";
            return 2;
        }

        const auto all_t0 = Clock::now();
        const auto baseline = load_ids(argv[1]);
        std::cerr << "vertices=" << N << " baseline=" << baseline.size();
#ifdef _OPENMP
        std::cerr << " omp_threads=" << omp_get_max_threads();
#endif
        std::cerr << "\n";

        std::vector<std::uint16_t> count_a(N, 0);
        std::vector<std::uint16_t> count_b(N, 0);
        for (auto id : baseline) count_a[id] = 1;
        neighborhood_transform<std::uint16_t, Op::Sum>(count_a, count_b, "count");
        count_b.clear();
        count_b.shrink_to_fit();

        std::array<std::uint64_t, 17> hist{};
        std::uint32_t direct = NONE;
        std::unordered_set<std::uint32_t> baseline_set;
        baseline_set.reserve(baseline.size() * 2);
        for (auto id : baseline) baseline_set.insert(id);

        for (std::uint32_t id = 0; id < N; ++id) {
            const auto c = count_a[id];
            if (c < 16) ++hist[c]; else ++hist[16];
            if (c == 0) {
                direct = id;
                break;
            }
        }
        if (direct != NONE) {
            std::cout << "{\"kind\":\"direct\",\"add\":" << direct
                      << ",\"baseline_size\":" << baseline.size() << "}\n";
            return 0;
        }
        std::cerr << "coverage_hist";
        for (int i = 0; i < 16; ++i) std::cerr << " " << i << ":" << hist[i];
        std::cerr << " 16+:" << hist[16] << "\n";

        std::vector<std::uint32_t> xor_a(N, 0);
        std::vector<std::uint32_t> xor_b(N, 0);
        for (std::uint32_t i = 0; i < baseline.size(); ++i) xor_a[baseline[i]] = i + 1u;
        neighborhood_transform<std::uint32_t, Op::Xor>(xor_a, xor_b, "xor");
        xor_b.clear();
        xor_b.shrink_to_fit();

        std::vector<std::vector<std::uint32_t>> cov1(baseline.size());
        std::vector<std::array<std::uint32_t, D>> neg_witness(baseline.size());
        std::vector<std::array<std::uint32_t, D>> pos_witness(baseline.size());
        for (auto& a : neg_witness) a.fill(NONE);
        for (auto& a : pos_witness) a.fill(NONE);

        std::uint64_t outside_cov1 = 0;
        for (std::uint32_t id = 0; id < N; ++id) {
            if (count_a[id] != 1 || baseline_set.find(id) != baseline_set.end()) continue;
            ++outside_cov1;
            const std::uint32_t encoded_owner = xor_a[id];
            if (encoded_owner == 0 || encoded_owner > baseline.size()) {
                throw std::runtime_error("invalid unique-owner XOR");
            }
            const std::uint32_t oi = encoded_owner - 1u;
            cov1[oi].push_back(id);
            const auto [neg, pos] = relative_masks(id, baseline[oi]);
            for (int d = 0; d < D; ++d) {
                const std::uint16_t bit = static_cast<std::uint16_t>(1u << d);
                if ((neg & bit) && pos_witness[oi][d] != NONE) {
                    std::cout << "{\"kind\":\"replace1\",\"remove_index\":" << oi
                              << ",\"remove\":" << baseline[oi]
                              << ",\"add\":[" << pos_witness[oi][d] << "," << id << "]"
                              << ",\"baseline_size\":" << baseline.size() << "}\n";
                    return 0;
                }
                if ((pos & bit) && neg_witness[oi][d] != NONE) {
                    std::cout << "{\"kind\":\"replace1\",\"remove_index\":" << oi
                              << ",\"remove\":" << baseline[oi]
                              << ",\"add\":[" << neg_witness[oi][d] << "," << id << "]"
                              << ",\"baseline_size\":" << baseline.size() << "}\n";
                    return 0;
                }
            }
            for (int d = 0; d < D; ++d) {
                const std::uint16_t bit = static_cast<std::uint16_t>(1u << d);
                if ((neg & bit) && neg_witness[oi][d] == NONE) neg_witness[oi][d] = id;
                if ((pos & bit) && pos_witness[oi][d] == NONE) pos_witness[oi][d] = id;
            }
        }
        std::cerr << "replace1_none outside_cov1=" << outside_cov1 << "\n";
        xor_a.clear();
        xor_a.shrink_to_fit();

        // Recover the exact pair of baseline conflicts for every coverage-2 vertex.
        std::vector<std::uint32_t> min_a(N, INF), min_b(N, INF);
        for (std::uint32_t i = 0; i < baseline.size(); ++i) min_a[baseline[i]] = i + 1u;
        neighborhood_transform<std::uint32_t, Op::Min>(min_a, min_b, "min-owner");
        min_b.clear();
        min_b.shrink_to_fit();

        std::vector<std::uint32_t> max_a(N, 0), max_b(N, 0);
        for (std::uint32_t i = 0; i < baseline.size(); ++i) max_a[baseline[i]] = i + 1u;
        neighborhood_transform<std::uint32_t, Op::Max>(max_a, max_b, "max-owner");
        max_b.clear();
        max_b.shrink_to_fit();

        std::unordered_map<std::uint64_t, std::vector<std::uint32_t>> pair_groups;
        pair_groups.reserve(180000);
        std::uint64_t cov2_total = 0;
        for (std::uint32_t id = 0; id < N; ++id) {
            if (count_a[id] != 2) continue;
            ++cov2_total;
            const std::uint32_t lo = min_a[id];
            const std::uint32_t hi = max_a[id];
            if (lo == 0 || lo == INF || hi == 0 || hi == INF || lo >= hi || hi > baseline.size()) {
                throw std::runtime_error("invalid coverage-2 owners");
            }
            const std::uint32_t oi = lo - 1u;
            const std::uint32_t oj = hi - 1u;
            const std::uint64_t key = (static_cast<std::uint64_t>(oi) << 32) | oj;
            pair_groups[key].push_back(id);
        }
        count_a.clear();
        count_a.shrink_to_fit();
        min_a.clear();
        min_a.shrink_to_fit();
        max_a.clear();
        max_a.shrink_to_fit();

        std::vector<std::pair<std::uint64_t, std::size_t>> order;
        order.reserve(pair_groups.size());
        std::size_t max_group = 0;
        for (const auto& [key, vals] : pair_groups) {
            order.push_back({key, vals.size()});
            max_group = std::max(max_group, vals.size());
        }
        std::sort(order.begin(), order.end(), [](const auto& a, const auto& b) {
            return a.second > b.second;
        });
        std::cerr << "coverage2=" << cov2_total
                  << " owner_pairs=" << pair_groups.size()
                  << " max_pair_group=" << max_group << "\n";

        const auto r2_t0 = Clock::now();
        for (const auto& [key, ignored_size] : order) {
            (void)ignored_size;
            const std::uint32_t oi = static_cast<std::uint32_t>(key >> 32);
            const std::uint32_t oj = static_cast<std::uint32_t>(key & 0xffffffffu);
            std::array<std::uint32_t, 3> answer{};
            if (try_replace2_group(oi, oj, pair_groups.at(key), cov1, answer)) {
                std::cerr << "replace2_found pair_group=" << pair_groups.at(key).size()
                          << " sec=" << seconds_since(r2_t0)
                          << " total_sec=" << seconds_since(all_t0) << "\n";
                emit_replace2(baseline, oi, oj, answer);
                return 0;
            }
        }

        std::cerr << "replace2_none sec=" << seconds_since(r2_t0)
                  << " total_sec=" << seconds_since(all_t0) << "\n";
        std::cout << "{\"kind\":\"none\",\"baseline_size\":" << baseline.size()
                  << ",\"outside_coverage1\":" << outside_cov1
                  << ",\"coverage2\":" << cov2_total
                  << ",\"owner_pairs\":" << pair_groups.size()
                  << ",\"max_pair_group\":" << max_group << "}\n";
        return 0;
    } catch (const std::exception& e) {
        std::cerr << "error: " << e.what() << "\n";
        return 1;
    }
}
