// Exact deletion transfer into length 100 for source lengths 101..104.
// Uses a 128-bit packed candidate and popcount-based LABS scoring.

#include <array>
#include <bit>
#include <cstdint>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>

using U128 = unsigned __int128;

static int popcount128(U128 x) {
    return std::popcount(uint64_t(x)) + std::popcount(uint64_t(x >> 64));
}

static long long energy100(U128 x) {
    long long e = 0;
    for (int k = 1; k < 100; ++k) {
        const int length = 100 - k;
        const U128 mask = (U128(1) << length) - 1;
        const int different = popcount128((x ^ (x >> k)) & mask);
        const int c = length - 2 * different;
        e += 1LL * c * c;
    }
    return e;
}

static std::string format(U128 x) {
    std::string out;
    out.reserve(100);
    for (int i = 0; i < 100; ++i) out.push_back(((x >> i) & 1) ? '-' : '+');
    return out;
}

struct Search {
    std::vector<int> source;
    int remove_count = 0;
    std::vector<int> chosen;
    unsigned long long tested = 0;
    long long best_energy = std::numeric_limits<long long>::max();
    std::vector<int> best_deleted;
    U128 best_candidate = 0;

    void evaluate() {
        U128 x = 0;
        int out = 0;
        int j = 0;
        for (int i = 0; i < int(source.size()); ++i) {
            if (j < remove_count && chosen[j] == i) {
                ++j;
                continue;
            }
            if (source[i]) x |= U128(1) << out;
            ++out;
        }
        if (out != 100) throw std::runtime_error("internal length mismatch");
        const long long e = energy100(x);
        ++tested;
        if (e < best_energy) {
            best_energy = e;
            best_deleted = chosen;
            best_candidate = x;
            std::cout << "BEST energy=" << best_energy << " tested=" << tested << " deleted=";
            for (int i = 0; i < remove_count; ++i) {
                if (i) std::cout << ',';
                std::cout << chosen[i];
            }
            std::cout << "\n";
        }
    }

    void dfs(int next) {
        if (int(chosen.size()) == remove_count) {
            evaluate();
            return;
        }
        const int still = remove_count - int(chosen.size());
        for (int p = next; p <= int(source.size()) - still; ++p) {
            chosen.push_back(p);
            dfs(p + 1);
            chosen.pop_back();
        }
    }
};

int main(int argc, char** argv) {
    if (argc != 2) {
        std::cerr << "usage: delete-to-100 <101..104-character +/- sequence>\n";
        return 2;
    }
    const std::string text = argv[1];
    if (text.size() < 101 || text.size() > 104) return 2;

    Search search;
    search.remove_count = int(text.size()) - 100;
    search.source.reserve(text.size());
    for (char ch : text) {
        if (ch == '+') search.source.push_back(0);
        else if (ch == '-') search.source.push_back(1);
        else return 2;
    }
    search.dfs(0);

    std::cout << "FINAL tested=" << search.tested << " best=" << search.best_energy << " deleted=";
    for (int i = 0; i < search.remove_count; ++i) {
        if (i) std::cout << ',';
        std::cout << search.best_deleted[i];
    }
    std::cout << "\nBESTSEQ " << format(search.best_candidate) << "\n";
    return 0;
}
