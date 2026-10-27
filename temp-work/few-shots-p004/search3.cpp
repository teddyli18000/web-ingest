#include <algorithm>
#include <array>
#include <bit>
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
constexpr unsigned OWNER_BITS = 18;
constexpr std::uint64_t OWNER_MASK = (1ull << OWNER_BITS) - 1;

enum class Op { Sum, Xor, Min, Max };

template <class T, Op operation>
void transform(std::vector<T>& a, std::vector<T>& b, const char* label) {
    for (int dim = 0; dim < D; ++dim) {
        const std::uint32_t stride = POW7[dim];
        const std::uint64_t block = static_cast<std::uint64_t>(stride) * 7u;
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
        std::cerr << label << " dim=" << dim << "\n";
    }
}

std::vector<std::uint32_t> load_ids(const std::string& path) {
    std::ifstream in(path);
    if (!in) throw std::runtime_error("cannot open baseline IDs");
    std::vector<std::uint32_t> ids;
    std::uint64_t x;
    while (in >> x) {
        if (x >= N) throw std::runtime_error("baseline ID out of range");
        ids.push_back(static_cast<std::uint32_t>(x));
    }
    if (ids.size() != 134753u) throw std::runtime_error("unexpected baseline size");
    return ids;
}

bool adjacent(std::uint32_t a, std::uint32_t b) {
    if (a == b) return true;
    for (int d = 0; d < D; ++d) {
        const int x = a % 7u, y = b % 7u;
        a /= 7u; b /= 7u;
        const int delta = (x - y + 7) % 7;
        if (delta != 0 && delta != 1 && delta != 6) return false;
    }
    return true;
}

std::uint64_t pair_key(std::uint32_t a, std::uint32_t b) {
    if (a > b) std::swap(a, b);
    return (static_cast<std::uint64_t>(a) << OWNER_BITS) | b;
}

std::uint64_t triple_key(std::uint32_t a, std::uint32_t b, std::uint32_t c) {
    std::array<std::uint32_t, 3> v{a,b,c};
    std::sort(v.begin(), v.end());
    return (static_cast<std::uint64_t>(v[0]) << (2 * OWNER_BITS)) |
           (static_cast<std::uint64_t>(v[1]) << OWNER_BITS) | v[2];
}

std::array<std::uint32_t,3> unpack_triple(std::uint64_t key) {
    return {
        static_cast<std::uint32_t>((key >> (2 * OWNER_BITS)) & OWNER_MASK),
        static_cast<std::uint32_t>((key >> OWNER_BITS) & OWNER_MASK),
        static_cast<std::uint32_t>(key & OWNER_MASK)
    };
}

bool find_independent4(const std::vector<std::uint32_t>& v,
                       std::array<std::uint32_t,4>& out) {
    const std::size_t n = v.size();
    if (n < 4) return false;
    const std::size_t words = (n + 63) / 64;
    std::vector<std::uint64_t> ok(n * words, 0);
    auto row = [&](std::size_t i) { return ok.data() + i * words; };

    for (std::size_t i = 0; i < n; ++i) {
        for (std::size_t j = i + 1; j < n; ++j) {
            if (adjacent(v[i], v[j])) continue;
            row(i)[j / 64] |= 1ull << (j % 64);
            row(j)[i / 64] |= 1ull << (i % 64);
        }
    }

    for (std::size_t i = 0; i < n; ++i) {
        for (std::size_t j = i + 1; j < n; ++j) {
            if ((row(i)[j / 64] & (1ull << (j % 64))) == 0) continue;
            for (std::size_t w = j / 64; w < words; ++w) {
                std::uint64_t common = row(i)[w] & row(j)[w];
                if (w == j / 64) {
                    const unsigned cut = static_cast<unsigned>((j % 64) + 1);
                    if (cut == 64) common = 0;
                    else common &= (~0ull << cut);
                }
                while (common) {
                    const unsigned bit = std::countr_zero(common);
                    const std::size_t k = w * 64 + bit;
                    common &= common - 1;
                    if (k >= n) continue;
                    for (std::size_t ww = k / 64; ww < words; ++ww) {
                        std::uint64_t fourth = row(i)[ww] & row(j)[ww] & row(k)[ww];
                        if (ww == k / 64) {
                            const unsigned cut2 = static_cast<unsigned>((k % 64) + 1);
                            if (cut2 == 64) fourth = 0;
                            else fourth &= (~0ull << cut2);
                        }
                        if (!fourth) continue;
                        const std::size_t l = ww * 64 + std::countr_zero(fourth);
                        if (l < n) {
                            out = {v[i], v[j], v[k], v[l]};
                            return true;
                        }
                    }
                }
            }
        }
    }
    return false;
}

void append_group(std::vector<std::uint32_t>& out,
                  const std::unordered_map<std::uint64_t,std::vector<std::uint32_t>>& groups,
                  std::uint64_t key) {
    auto it = groups.find(key);
    if (it != groups.end()) out.insert(out.end(), it->second.begin(), it->second.end());
}

} // namespace

int main(int argc, char** argv) {
    try {
        if (argc != 2) {
            std::cerr << "usage: search3 BASELINE_IDS\n";
            return 2;
        }
        const auto baseline = load_ids(argv[1]);
        std::unordered_set<std::uint32_t> baseline_set(baseline.begin(), baseline.end());

        std::vector<std::uint16_t> count(N, 0), tmp16(N, 0);
        for (auto id : baseline) count[id] = 1;
        transform<std::uint16_t,Op::Sum>(count, tmp16, "count");
        tmp16.clear(); tmp16.shrink_to_fit();

        std::vector<std::uint32_t> xo(N, 0), tmp32(N, 0);
        for (std::uint32_t i = 0; i < baseline.size(); ++i) xo[baseline[i]] = i + 1u;
        transform<std::uint32_t,Op::Xor>(xo, tmp32, "xor");
        tmp32.clear(); tmp32.shrink_to_fit();

        std::vector<std::uint32_t> mn(N, INF), tmpmn(N, INF);
        for (std::uint32_t i = 0; i < baseline.size(); ++i) mn[baseline[i]] = i + 1u;
        transform<std::uint32_t,Op::Min>(mn, tmpmn, "min");
        tmpmn.clear(); tmpmn.shrink_to_fit();

        std::vector<std::uint32_t> mx(N, 0), tmpmx(N, 0);
        for (std::uint32_t i = 0; i < baseline.size(); ++i) mx[baseline[i]] = i + 1u;
        transform<std::uint32_t,Op::Max>(mx, tmpmx, "max");
        tmpmx.clear(); tmpmx.shrink_to_fit();

        std::vector<std::vector<std::uint32_t>> cov1(baseline.size());
        std::unordered_map<std::uint64_t,std::vector<std::uint32_t>> cov2;
        cov2.reserve(160000);
        std::vector<std::pair<std::uint64_t,std::uint32_t>> cov3;
        cov3.reserve(1100000);

        std::uint64_t n1=0,n2=0,n3=0;
        for (std::uint32_t id = 0; id < N; ++id) {
            const auto c = count[id];
            if (c == 1) {
                if (baseline_set.contains(id)) continue;
                const auto a = xo[id];
                if (a == 0 || a > baseline.size()) throw std::runtime_error("bad cov1 owner");
                cov1[a-1].push_back(id); ++n1;
            } else if (c == 2) {
                const auto a = mn[id], b = mx[id];
                if (a == 0 || a == INF || b == 0 || b == INF || a >= b) throw std::runtime_error("bad cov2 owners");
                cov2[pair_key(a-1,b-1)].push_back(id); ++n2;
            } else if (c == 3) {
                const auto lo = mn[id], hi = mx[id];
                if (lo == 0 || lo == INF || hi == 0 || hi == INF || lo >= hi) throw std::runtime_error("bad cov3 extrema");
                const auto mid = xo[id] ^ lo ^ hi;
                if (mid == 0 || mid > baseline.size() || mid == lo || mid == hi) throw std::runtime_error("bad cov3 middle");
                const auto key = triple_key(lo-1, mid-1, hi-1);
                cov3.push_back({key,id}); ++n3;
            }
        }
        std::cerr << "low_coverage cov1=" << n1 << " cov2=" << n2 << " cov3=" << n3 << "\n";

        count.clear(); count.shrink_to_fit();
        xo.clear(); xo.shrink_to_fit();
        mn.clear(); mn.shrink_to_fit();
        mx.clear(); mx.shrink_to_fit();

        std::sort(cov3.begin(), cov3.end(), [](const auto& a, const auto& b) {
            return a.first < b.first || (a.first == b.first && a.second < b.second);
        });

        std::uint64_t triple_groups = 0;
        std::size_t max_pool = 0;
        std::size_t pos = 0;
        while (pos < cov3.size()) {
            const std::uint64_t key = cov3[pos].first;
            std::size_t end = pos + 1;
            while (end < cov3.size() && cov3[end].first == key) ++end;
            ++triple_groups;

            const auto owners = unpack_triple(key);
            const auto a = owners[0], b = owners[1], c = owners[2];
            if (!(a < b && b < c) || c >= baseline.size()) throw std::runtime_error("bad unpacked triple");

            std::vector<std::uint32_t> pool;
            pool.reserve((end-pos) + cov1[a].size()+cov1[b].size()+cov1[c].size()+12);
            for (std::size_t i = pos; i < end; ++i) pool.push_back(cov3[i].second);
            append_group(pool,cov2,pair_key(a,b));
            append_group(pool,cov2,pair_key(a,c));
            append_group(pool,cov2,pair_key(b,c));
            pool.insert(pool.end(),cov1[a].begin(),cov1[a].end());
            pool.insert(pool.end(),cov1[b].begin(),cov1[b].end());
            pool.insert(pool.end(),cov1[c].begin(),cov1[c].end());
            std::sort(pool.begin(),pool.end());
            pool.erase(std::unique(pool.begin(),pool.end()),pool.end());
            max_pool = std::max(max_pool,pool.size());

            std::array<std::uint32_t,4> add{};
            if (find_independent4(pool,add)) {
                std::cerr << "FOUND triple_groups_checked=" << triple_groups << " pool=" << pool.size() << "\n";
                std::cout << "{\"kind\":\"bulk\",\"method\":\"exact-3-for-4-cov3\",\"baseline_size\":"
                          << baseline.size() << ",\"remove\":[" << baseline[a] << ',' << baseline[b] << ',' << baseline[c]
                          << "],\"add\":[" << add[0] << ',' << add[1] << ',' << add[2] << ',' << add[3]
                          << "],\"owner_indices\":[" << a << ',' << b << ',' << c << "]}\n";
                return 0;
            }
            pos = end;
        }

        std::cerr << "NONE triple_groups=" << triple_groups << " max_pool=" << max_pool << "\n";
        std::cout << "{\"kind\":\"none\",\"method\":\"exact-3-for-4-cov3\",\"baseline_size\":"
                  << baseline.size() << ",\"cov1\":" << n1 << ",\"cov2\":" << n2 << ",\"cov3\":" << n3
                  << ",\"triple_groups\":" << triple_groups << ",\"max_pool\":" << max_pool << "}\n";
        return 0;
    } catch (const std::exception& e) {
        std::cerr << "error: " << e.what() << "\n";
        return 1;
    }
}
