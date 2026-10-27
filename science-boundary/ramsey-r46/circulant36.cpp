#include <array>
#include <bit>
#include <chrono>
#include <cstdint>
#include <functional>
#include <iostream>
#include <limits>

namespace {
constexpr int N = 36;
constexpr int CLASSES = 18;
constexpr std::uint64_t FULL = (std::uint64_t{1} << N) - 1;
using Adj = std::array<std::uint64_t, N>;

bool has_clique(const Adj& adj, int size) {
    std::function<bool(std::uint64_t, int)> extend = [&](std::uint64_t cand, int need) {
        if (need == 0) return true;
        while (cand && std::popcount(cand) >= need) {
            unsigned v = std::countr_zero(cand);
            cand &= cand - 1;
            if (extend(cand & adj[v], need - 1)) return true;
        }
        return false;
    };
    return extend(FULL, size);
}

long long count_cliques(const Adj& adj, int size) {
    long long total = 0;
    std::function<void(std::uint64_t, int)> extend = [&](std::uint64_t cand, int need) {
        if (need == 0) {
            ++total;
            return;
        }
        while (cand && std::popcount(cand) >= need) {
            unsigned v = std::countr_zero(cand);
            cand &= cand - 1;
            extend(cand & adj[v], need - 1);
        }
    };
    extend(FULL, size);
    return total;
}

Adj make_circulant(std::uint32_t mask) {
    Adj adj{};
    for (int i = 0; i < N; ++i) {
        for (int j = i + 1; j < N; ++j) {
            int d = j - i;
            if (d > N - d) d = N - d;
            if ((mask >> (d - 1)) & 1U) {
                adj[i] |= std::uint64_t{1} << j;
                adj[j] |= std::uint64_t{1} << i;
            }
        }
    }
    return adj;
}

Adj complement(const Adj& adj) {
    Adj out{};
    for (int i = 0; i < N; ++i) {
        out[i] = FULL & ~adj[i] & ~(std::uint64_t{1} << i);
    }
    return out;
}
}  // namespace

int main() {
    const auto started = std::chrono::steady_clock::now();
    std::uint64_t k4_free = 0;
    std::uint64_t valid = 0;
    long long best_objective = std::numeric_limits<long long>::max();
    long long best_k4 = -1;
    long long best_i6 = -1;
    std::uint32_t best_mask = 0;

    for (std::uint32_t mask = 0; mask < (1U << CLASSES); ++mask) {
        const Adj adj = make_circulant(mask);
        const bool k4 = has_clique(adj, 4);
        if (!k4) ++k4_free;
        const Adj comp = complement(adj);
        const bool i6 = has_clique(comp, 6);
        if (!k4 && !i6) {
            ++valid;
            std::cout << "FOUND valid mask=" << mask << "\n";
        }

        // The score scan is separate from the fast validity tests. It gives a useful
        // seed for unrestricted local search but is not itself a Ramsey certificate.
        const long long k4_count = count_cliques(adj, 4);
        if (k4_count <= best_objective) {
            const long long i6_count = count_cliques(comp, 6);
            const long long objective = k4_count + i6_count;
            if (objective < best_objective) {
                best_objective = objective;
                best_k4 = k4_count;
                best_i6 = i6_count;
                best_mask = mask;
            }
        }
    }

    const double seconds = std::chrono::duration<double>(
        std::chrono::steady_clock::now() - started).count();
    std::cout << "checked=" << (1U << CLASSES) << "\n";
    std::cout << "k4_free=" << k4_free << "\n";
    std::cout << "valid=" << valid << "\n";
    std::cout << "best_objective=" << best_objective << "\n";
    std::cout << "best_k4=" << best_k4 << "\n";
    std::cout << "best_independent6=" << best_i6 << "\n";
    std::cout << "best_mask=" << best_mask << "\n";
    std::cout << "seconds=" << seconds << "\n";
    return valid == 0 ? 0 : 10;
}
