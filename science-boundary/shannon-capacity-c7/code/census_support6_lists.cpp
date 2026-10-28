// Exact support-list transform for C7^10 around a supplied independent set.
//
// Each ambient vertex carries either the sorted distinct owner labels in its
// current partial strong-product neighborhood (when there are <=6), or an
// overflow marker. Expanding one coordinate replaces a support by the union
// of the three cyclic neighboring supports. Support size is monotone under
// coordinate expansion, so any final vertex with coverage <=6 can never have
// overflowed at an intermediate stage. Consequently this single-array
// in-place transform recovers every final blocker support of sizes 1..6 exactly.
//
// Memory: 7^10 * 6 * 4 bytes ~= 6.78 GB. No full-size double buffer is used:
// for each disjoint 7-cycle group we first copy all seven old support records to
// stack storage, then write the seven new records back in place.
#include <algorithm>
#include <array>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <unordered_set>
#include <vector>
#ifdef _OPENMP
#include <omp.h>
#endif

namespace {
constexpr int D = 10;
constexpr std::uint32_t P7[D+1] = {1u,7u,49u,343u,2401u,16807u,117649u,823543u,5764801u,40353607u,282475249u};
constexpr std::uint32_t N = P7[D];
constexpr std::uint32_t GROUPS = N / 7u;
constexpr unsigned K = 6;
constexpr std::uint32_t OVER = 0xffffffffu;

struct Rec { std::uint32_t x[K]; };

std::vector<std::uint32_t> load_ids(const char* p) {
    std::ifstream in(p); if(!in) throw std::runtime_error("cannot open ids");
    std::vector<std::uint32_t> a; std::uint64_t z;
    while(in >> z) { if(z >= N) throw std::runtime_error("id range"); a.push_back((std::uint32_t)z); }
    if(a.empty()) throw std::runtime_error("empty baseline");
    std::sort(a.begin(), a.end());
    if(std::adjacent_find(a.begin(), a.end()) != a.end()) throw std::runtime_error("duplicate baseline");
    return a;
}

inline bool overflow(const Rec& r) { return r.x[0] == OVER; }
inline unsigned size_of(const Rec& r) {
    if(overflow(r)) return K+1;
    unsigned n=0; while(n<K && r.x[n]) ++n; return n;
}

// Merge three already-sorted, zero-terminated support lists.  This is on the
// hot path (~2.8e9 calls across ten dimensions), so avoid a per-call sort.
inline Rec unite3(const Rec& a, const Rec& b, const Rec& c) {
    if(overflow(a) || overflow(b) || overflow(c)) { Rec r{}; r.x[0]=OVER; return r; }
    unsigned ia=0, ib=0, ic=0, m=0;
    std::uint32_t last=0;
    Rec out{};
    for(;;) {
        const std::uint32_t va = ia<K ? a.x[ia] : 0;
        const std::uint32_t vb = ib<K ? b.x[ib] : 0;
        const std::uint32_t vc = ic<K ? c.x[ic] : 0;
        std::uint32_t v=0;
        if(va) v=va;
        if(vb && (!v || vb<v)) v=vb;
        if(vc && (!v || vc<v)) v=vc;
        if(!v) break;
        if(va==v) ++ia;
        if(vb==v) ++ib;
        if(vc==v) ++ic;
        if(v==last) continue;
        if(m==K) { Rec r{}; r.x[0]=OVER; return r; }
        out.x[m++]=v; last=v;
    }
    return out;
}

struct SixKey {
    std::array<std::uint32_t,K> a;
    bool operator==(const SixKey& o) const { return a==o.a; }
};
struct SixHash {
    std::size_t operator()(const SixKey& q) const noexcept {
        std::size_t h=0;
        for(auto x:q.a) h ^= std::size_t(x) + 0x9e3779b97f4a7c15ULL + (h<<6) + (h>>2);
        return h;
    }
};
}

int main(int argc,char**argv) try {
    if(argc!=2){ std::cerr << "usage: census_support6_lists BASELINE_IDS\n"; return 2; }
    auto base=load_ids(argv[1]);
    std::vector<Rec> a(N);
    for(std::uint32_t i=0;i<base.size();++i) a[base[i]].x[0]=i+1;

    for(int dim=0;dim<D;++dim){
        const std::uint32_t s=P7[dim]; const std::uint64_t block=std::uint64_t(s)*7u;
        #pragma omp parallel for schedule(static)
        for(std::int64_t gg=0; gg<(std::int64_t)GROUPS; ++gg){
            const std::uint64_t g=(std::uint64_t)gg, bn=g/s; const std::uint32_t off=g%s;
            const std::uint64_t base0=bn*block+off;
            Rec old[7];
            for(int k=0;k<7;++k) old[k]=a[base0+std::uint64_t(k)*s];
            Rec nw[7];
            for(int k=0;k<7;++k) nw[k]=unite3(old[(k+6)%7],old[k],old[(k+1)%7]);
            for(int k=0;k<7;++k) a[base0+std::uint64_t(k)*s]=nw[k];
        }
        std::cerr << "support-list dim=" << dim << "\n";
    }

    std::array<std::uint64_t,K+2> hist{}; // 0..6 plus overflow index 7
    std::unordered_set<SixKey,SixHash> g6; g6.reserve(5000000);
    for(std::uint32_t v=0;v<N;++v){
        unsigned n=size_of(a[v]);
        if(n>K){ ++hist[K+1]; continue; }
        ++hist[n];
        if(n==K){ SixKey q{}; for(unsigned j=0;j<K;++j) q.a[j]=a[v].x[j]-1; g6.insert(q); }
    }
    std::cout << "{\"kind\":\"census\",\"method\":\"exact-inplace-support-list-up-to6\",\"baseline_size\":" << base.size()
              << ",\"coverage0\":" << hist[0] << ",\"coverage1\":" << hist[1] << ",\"coverage2\":" << hist[2]
              << ",\"coverage3\":" << hist[3] << ",\"coverage4\":" << hist[4] << ",\"coverage5\":" << hist[5]
              << ",\"coverage6\":" << hist[6] << ",\"coverage_gt6\":" << hist[7]
              << ",\"coverage6_groups\":" << g6.size() << "}\n";
    return 0;
} catch(const std::exception& e) { std::cerr << "error: " << e.what() << "\n"; return 1; }
