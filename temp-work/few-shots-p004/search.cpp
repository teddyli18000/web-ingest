#include <algorithm>
#include <array>
#include <chrono>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <unordered_set>
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

using Clock = std::chrono::steady_clock;

double seconds_since(Clock::time_point t0) {
    return std::chrono::duration<double>(Clock::now() - t0).count();
}

template <class T, bool UseXor>
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
                if constexpr (UseXor) {
                    b[base + static_cast<std::uint64_t>(k) * stride] = left ^ mid ^ right;
                } else {
                    b[base + static_cast<std::uint64_t>(k) * stride] =
                        static_cast<T>(left + mid + right);
                }
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

// candidate is known to lie in the closed strong-product neighborhood of owner.
// Return bit masks of coordinates where candidate is owner-1 or owner+1 mod 7.
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

        // Exact number of baseline vertices in every closed neighborhood.
        std::vector<std::uint16_t> count_a(N, 0);
        std::vector<std::uint16_t> count_b(N, 0);
        for (auto id : baseline) count_a[id] = 1;
        neighborhood_transform<std::uint16_t, false>(count_a, count_b, "count");
        count_b.clear();
        count_b.shrink_to_fit();

        std::array<std::uint64_t, 17> hist{};
        std::uint32_t direct = NONE;
        std::uint64_t outside_cov1 = 0;
        std::unordered_set<std::uint32_t> baseline_set;
        baseline_set.reserve(baseline.size() * 2);
        for (auto id : baseline) baseline_set.insert(id);

        const auto scan_t0 = Clock::now();
        for (std::uint32_t id = 0; id < N; ++id) {
            const auto c = count_a[id];
            if (c < 16) ++hist[c]; else ++hist[16];
            if (c == 0) {
                direct = id;
                break;
            }
            if (c == 1 && baseline_set.find(id) == baseline_set.end()) ++outside_cov1;
        }
        std::cerr << "coverage_scan sec=" << seconds_since(scan_t0)
                  << " outside_cov1_prefix=" << outside_cov1 << "\n";

        if (direct != NONE) {
            std::cout << "{\"kind\":\"direct\",\"add\":" << direct
                      << ",\"baseline_size\":" << baseline.size() << "}\n";
            return 0;
        }

        std::cerr << "coverage_hist";
        for (int i = 0; i < 16; ++i) std::cerr << " " << i << ":" << hist[i];
        std::cerr << " 16+:" << hist[16] << "\n";

        // XOR of baseline owner indices over each closed neighborhood. When the
        // coverage count is exactly one this is exactly that unique owner index+1.
        std::vector<std::uint32_t> xor_a(N, 0);
        std::vector<std::uint32_t> xor_b(N, 0);
        for (std::uint32_t i = 0; i < baseline.size(); ++i) {
            xor_a[baseline[i]] = i + 1u;
        }
        neighborhood_transform<std::uint32_t, true>(xor_a, xor_b, "xor");
        xor_b.clear();
        xor_b.shrink_to_fit();

        // For each baseline owner and coordinate, remember one coverage-1 candidate
        // on each side. Opposite sides in any coordinate are automatically
        // non-adjacent, giving a valid remove-1/add-2 improvement.
        std::vector<std::array<std::uint32_t, D>> neg_witness(baseline.size());
        std::vector<std::array<std::uint32_t, D>> pos_witness(baseline.size());
        for (auto& a : neg_witness) a.fill(NONE);
        for (auto& a : pos_witness) a.fill(NONE);

        std::uint64_t outside_cov1_total = 0;
        const auto pair_t0 = Clock::now();
        for (std::uint32_t id = 0; id < N; ++id) {
            if (count_a[id] != 1) continue;
            if (baseline_set.find(id) != baseline_set.end()) continue;
            ++outside_cov1_total;

            const std::uint32_t encoded_owner = xor_a[id];
            if (encoded_owner == 0 || encoded_owner > baseline.size()) {
                throw std::runtime_error("invalid unique-owner XOR");
            }
            const std::uint32_t oi = encoded_owner - 1u;
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

        std::cerr << "replace1_scan sec=" << seconds_since(pair_t0)
                  << " outside_cov1=" << outside_cov1_total
                  << " total_sec=" << seconds_since(all_t0) << "\n";
        std::cout << "{\"kind\":\"none\",\"baseline_size\":" << baseline.size()
                  << ",\"outside_coverage1\":" << outside_cov1_total << "}\n";
        return 0;
    } catch (const std::exception& e) {
        std::cerr << "error: " << e.what() << "\n";
        return 1;
    }
}
