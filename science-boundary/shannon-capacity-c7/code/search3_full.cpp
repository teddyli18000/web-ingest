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

std::array<std::uint32_t,2> unpack_pair(std::uint64_t key) {
    return {
        static_cast<std::uint32_t>((key >> OWNER_BITS) & OWNER_MASK),
        static_cast<std::uint32_t>(key & OWNER_MASK)
    };
}

std::uint64_t triple_key(std::uint32_t a, std::uint32_t b, std::uint32_t c) {
    std::array<std::uint32_t,3> v{a,b,c};
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

bool find_independent2(const std::vector<std::uint32_t>& v,
                       std::array<std::uint32_t,2>& out) {
    for (std::size_t i = 0; i < v.size(); ++i)
        for (std::size_t j = i + 1; j < v.size(); ++j)
            if (!adjacent(v[i], v[j])) { out = {v[i],v[j]}; return true; }
    return false;
}

bool find_independent3(const std::vector<std::uint32_t>& v,
                       std::array<std::uint32_t,3>& out) {
    for (std::size_t i = 0; i < v.size(); ++i)
        for (std::size_t j = i + 1; j < v.size(); ++j) {
            if (adjacent(v[i],v[j])) continue;
            for (std::size_t k = j + 1; k < v.size(); ++k)
                if (!adjacent(v[i],v[k]) && !adjacent(v[j],v[k])) {
                    out = {v[i],v[j],v[k]}; return true;
                }
        }
    return false;
}

bool find_independent4(const std::vector<std::uint32_t>& v,
                       std::array<std::uint32_t,4>& out) {
    const std::size_t n = v.size();
    if (n < 4) return false;
    const std::size_t words = (n + 63) / 64;
    std::vector<std::uint64_t> ok(n * words, 0);
    auto row = [&](std::size_t i) { return ok.data() + i * words; };
    for (std::size_t i = 0; i < n; ++i)
        for (std::size_t j = i + 1; j < n; ++j)
            if (!adjacent(v[i],v[j])) {
                row(i)[j/64] |= 1ull << (j%64);
                row(j)[i/64] |= 1ull << (i%64);
            }
    for (std::size_t i = 0; i < n; ++i)
        for (std::size_t j = i + 1; j < n; ++j) {
            if ((row(i)[j/64] & (1ull << (j%64))) == 0) continue;
            for (std::size_t w = j/64; w < words; ++w) {
                std::uint64_t common = row(i)[w] & row(j)[w];
                if (w == j/64) {
                    const unsigned cut = static_cast<unsigned>((j%64)+1);
                    common = cut == 64 ? 0 : (common & (~0ull << cut));
                }
                while (common) {
                    const unsigned bit = std::countr_zero(common);
                    const std::size_t k = w*64 + bit;
                    common &= common - 1;
                    if (k >= n) continue;
                    for (std::size_t ww = k/64; ww < words; ++ww) {
                        std::uint64_t fourth = row(i)[ww] & row(j)[ww] & row(k)[ww];
                        if (ww == k/64) {
                            const unsigned cut = static_cast<unsigned>((k%64)+1);
                            fourth = cut == 64 ? 0 : (fourth & (~0ull << cut));
                        }
                        if (!fourth) continue;
                        const std::size_t l = ww*64 + std::countr_zero(fourth);
                        if (l < n) { out = {v[i],v[j],v[k],v[l]}; return true; }
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

void append_cov3(std::vector<std::uint32_t>& out,
                 const std::vector<std::pair<std::uint64_t,std::uint32_t>>& cov3,
                 std::uint64_t key) {
    auto it = std::lower_bound(cov3.begin(), cov3.end(), key,
        [](const auto& p, std::uint64_t k) { return p.first < k; });
    while (it != cov3.end() && it->first == key) { out.push_back(it->second); ++it; }
}

void print_bulk(const char* method, const std::vector<std::uint32_t>& baseline,
                const std::vector<std::uint32_t>& owners,
                const std::vector<std::uint32_t>& add) {
    std::cout << "{\"kind\":\"bulk\",\"method\":\"" << method
              << "\",\"baseline_size\":" << baseline.size() << ",\"remove\":[";
    for (std::size_t i=0;i<owners.size();++i) {
        if (i) std::cout << ',';
        std::cout << baseline[owners[i]];
    }
    std::cout << "],\"add\":[";
    for (std::size_t i=0;i<add.size();++i) {
        if (i) std::cout << ',';
        std::cout << add[i];
    }
    std::cout << "]}\n";
}

} // namespace

int main(int argc, char** argv) {
    try {
        if (argc != 2) { std::cerr << "usage: search3_full BASELINE_IDS\n"; return 2; }
        const auto baseline = load_ids(argv[1]);
        std::unordered_set<std::uint32_t> baseline_set(baseline.begin(),baseline.end());

        std::vector<std::uint16_t> count(N,0), tmp16(N,0);
        for (auto id:baseline) count[id]=1;
        transform<std::uint16_t,Op::Sum>(count,tmp16,"count");
        tmp16.clear(); tmp16.shrink_to_fit();

        for (std::uint32_t id=0; id<N; ++id) {
            if (count[id]==0) { print_bulk("exact-direct",baseline,{}, {id}); return 0; }
        }

        std::vector<std::uint32_t> xo(N,0), tmp32(N,0);
        for (std::uint32_t i=0;i<baseline.size();++i) xo[baseline[i]]=i+1u;
        transform<std::uint32_t,Op::Xor>(xo,tmp32,"xor");
        tmp32.clear(); tmp32.shrink_to_fit();

        std::vector<std::uint32_t> mn(N,INF), tmpmn(N,INF);
        for (std::uint32_t i=0;i<baseline.size();++i) mn[baseline[i]]=i+1u;
        transform<std::uint32_t,Op::Min>(mn,tmpmn,"min");
        tmpmn.clear(); tmpmn.shrink_to_fit();

        std::vector<std::uint32_t> mx(N,0), tmpmx(N,0);
        for (std::uint32_t i=0;i<baseline.size();++i) mx[baseline[i]]=i+1u;
        transform<std::uint32_t,Op::Max>(mx,tmpmx,"max");
        tmpmx.clear(); tmpmx.shrink_to_fit();

        std::vector<std::vector<std::uint32_t>> cov1(baseline.size());
        std::unordered_map<std::uint64_t,std::vector<std::uint32_t>> cov2;
        cov2.reserve(160000);
        std::vector<std::pair<std::uint64_t,std::uint32_t>> cov3;
        cov3.reserve(1100000);
        std::uint64_t n1=0,n2=0,n3=0;
        for (std::uint32_t id=0; id<N; ++id) {
            const auto c=count[id];
            if (c==1) {
                if (baseline_set.contains(id)) continue;
                const auto a=xo[id];
                if (a==0 || a>baseline.size()) throw std::runtime_error("bad cov1 owner");
                cov1[a-1].push_back(id); ++n1;
            } else if (c==2) {
                const auto a=mn[id], b=mx[id];
                if (a==0 || a==INF || b==0 || b==INF || a>=b) throw std::runtime_error("bad cov2 owners");
                cov2[pair_key(a-1,b-1)].push_back(id); ++n2;
            } else if (c==3) {
                const auto lo=mn[id], hi=mx[id];
                if (lo==0 || lo==INF || hi==0 || hi==INF || lo>=hi) throw std::runtime_error("bad cov3 extrema");
                const auto mid=xo[id]^lo^hi;
                if (mid==0 || mid>baseline.size() || mid==lo || mid==hi) throw std::runtime_error("bad cov3 middle");
                cov3.push_back({triple_key(lo-1,mid-1,hi-1),id}); ++n3;
            }
        }
        std::cerr << "low_coverage cov1="<<n1<<" cov2="<<n2<<" cov3="<<n3<<"\n";
        count.clear(); count.shrink_to_fit(); xo.clear(); xo.shrink_to_fit();
        mn.clear(); mn.shrink_to_fit(); mx.clear(); mx.shrink_to_fit();

        // Re-establish the lower-radius facts inside this run.  These facts are
        // what let us prove that a union-of-three replacement either contains
        // a cov3 point or at least two cov2 owner edges.
        for (std::uint32_t a=0;a<cov1.size();++a) {
            std::array<std::uint32_t,2> add{};
            if (find_independent2(cov1[a],add)) {
                print_bulk("exact-1-for-2",baseline,{a},{add[0],add[1]}); return 0;
            }
        }
        for (const auto& [key,g2]:cov2) {
            const auto ab=unpack_pair(key);
            std::vector<std::uint32_t> pool=g2;
            pool.insert(pool.end(),cov1[ab[0]].begin(),cov1[ab[0]].end());
            pool.insert(pool.end(),cov1[ab[1]].begin(),cov1[ab[1]].end());
            std::array<std::uint32_t,3> add{};
            if (find_independent3(pool,add)) {
                print_bulk("exact-2-for-3",baseline,{ab[0],ab[1]},{add[0],add[1],add[2]}); return 0;
            }
        }

        std::sort(cov3.begin(),cov3.end(),[](const auto& a,const auto& b){
            return a.first<b.first || (a.first==b.first && a.second<b.second);
        });

        std::vector<std::vector<std::uint32_t>> owner_adj(baseline.size());
        for (const auto& [key,g2]:cov2) {
            (void)g2;
            const auto ab=unpack_pair(key);
            owner_adj[ab[0]].push_back(ab[1]);
            owner_adj[ab[1]].push_back(ab[0]);
        }

        std::uint64_t wedge_raw=0, cov3_groups=0;
        std::vector<std::uint64_t> keys;
        keys.reserve(2500000);
        for (std::size_t p=0;p<cov3.size();) {
            keys.push_back(cov3[p].first); ++cov3_groups;
            std::size_t q=p+1; while(q<cov3.size() && cov3[q].first==cov3[p].first) ++q; p=q;
        }
        std::size_t max_owner_degree=0;
        for (std::uint32_t a=0;a<owner_adj.size();++a) {
            auto& nb=owner_adj[a];
            std::sort(nb.begin(),nb.end());
            nb.erase(std::unique(nb.begin(),nb.end()),nb.end());
            max_owner_degree=std::max(max_owner_degree,nb.size());
            for (std::size_t i=0;i<nb.size();++i)
                for (std::size_t j=i+1;j<nb.size();++j) {
                    keys.push_back(triple_key(a,nb[i],nb[j])); ++wedge_raw;
                }
        }
        std::cerr << "owner_graph edges="<<cov2.size()<<" wedge_raw="<<wedge_raw
                  <<" max_degree="<<max_owner_degree<<" cov3_groups="<<cov3_groups<<"\n";
        std::sort(keys.begin(),keys.end());
        keys.erase(std::unique(keys.begin(),keys.end()),keys.end());

        std::uint64_t checked=0, eligible=0, wedge_only=0;
        std::size_t max_pool=0;
        for (const auto key:keys) {
            const auto abc=unpack_triple(key);
            const auto a=abc[0],b=abc[1],c=abc[2];
            if (!(a<b && b<c) || c>=baseline.size()) throw std::runtime_error("bad triple key");
            std::vector<std::uint32_t> pool;
            append_cov3(pool,cov3,key);
            const bool has_cov3=!pool.empty();
            append_group(pool,cov2,pair_key(a,b));
            append_group(pool,cov2,pair_key(a,c));
            append_group(pool,cov2,pair_key(b,c));
            pool.insert(pool.end(),cov1[a].begin(),cov1[a].end());
            pool.insert(pool.end(),cov1[b].begin(),cov1[b].end());
            pool.insert(pool.end(),cov1[c].begin(),cov1[c].end());
            std::sort(pool.begin(),pool.end()); pool.erase(std::unique(pool.begin(),pool.end()),pool.end());
            ++checked; if (!has_cov3) ++wedge_only;
            max_pool=std::max(max_pool,pool.size());
            if (pool.size()<4) continue;
            ++eligible;
            std::array<std::uint32_t,4> add{};
            if (find_independent4(pool,add)) {
                std::cerr << "FOUND checked="<<checked<<" pool="<<pool.size()<<" has_cov3="<<has_cov3<<"\n";
                print_bulk("exact-3-for-4-union3",baseline,{a,b,c},{add[0],add[1],add[2],add[3]}); return 0;
            }
        }

        std::cerr << "NONE candidate_triples="<<keys.size()<<" checked="<<checked
                  <<" eligible="<<eligible<<" wedge_only="<<wedge_only<<" max_pool="<<max_pool<<"\n";
        std::cout << "{\"kind\":\"none\",\"method\":\"exact-3-for-4-union3\",\"baseline_size\":"
                  << baseline.size() << ",\"cov1\":"<<n1<<",\"cov2\":"<<n2<<",\"cov3\":"<<n3
                  << ",\"cov3_groups\":"<<cov3_groups<<",\"owner_edges\":"<<cov2.size()
                  << ",\"wedge_raw\":"<<wedge_raw<<",\"candidate_triples\":"<<keys.size()
                  << ",\"wedge_only_triples\":"<<wedge_only<<",\"eligible_triples\":"<<eligible
                  << ",\"max_owner_degree\":"<<max_owner_degree<<",\"max_pool\":"<<max_pool<<"}\n";
        return 0;
    } catch(const std::exception& e) {
        std::cerr << "error: "<<e.what()<<"\n"; return 1;
    }
}
