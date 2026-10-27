// Experimental N=100 probe of the unrestricted second stage in
// Psenicnik et al., arXiv:2409.07222. The paper describes a min-priority
// queue over one-bit neighbors plus bounded cyclic rotations. This file
// follows that mechanism but uses locally chosen Tu/Tr parameters; it is not
// claimed to reproduce the authors' exact implementation or tuning.

#include <array>
#include <algorithm>
#include <chrono>
#include <cstdint>
#include <iostream>
#include <queue>
#include <stdexcept>
#include <string>
#include <unordered_set>
#include <vector>

using Seq = std::array<int8_t, 100>;
using Corr = std::array<int, 100>;

struct Key {
    uint64_t lo = 0, hi = 0;
    bool operator==(const Key& other) const { return lo == other.lo && hi == other.hi; }
};
struct KeyHash {
    size_t operator()(const Key& k) const {
        uint64_t x = k.lo ^ (k.hi + 0x9e3779b97f4a7c15ULL + (k.lo << 6) + (k.lo >> 2));
        x ^= x >> 33;
        x *= 0xff51afd7ed558ccdULL;
        x ^= x >> 33;
        return size_t(x);
    }
};

static Key key_of(const Seq& s) {
    Key k;
    for (int i = 0; i < 64; ++i) if (s[i] > 0) k.lo |= 1ULL << i;
    for (int i = 64; i < 100; ++i) if (s[i] > 0) k.hi |= 1ULL << (i - 64);
    return k;
}

static long long energy(const Seq& s, Corr* out = nullptr) {
    Corr c{};
    long long e = 0;
    for (int k = 1; k < 100; ++k) {
        int x = 0;
        for (int i = 0; i < 100 - k; ++i) x += int(s[i]) * int(s[i + k]);
        c[k] = x;
        e += 1LL * x * x;
    }
    if (out) *out = c;
    return e;
}

static long long energy_if_flipped(const Seq& s, const Corr& c, long long e, int p) {
    long long out = e;
    const int sp = s[p];
    for (int k = 1; k < 100; ++k) {
        int t = 0;
        if (p + k < 100) t += sp * int(s[p + k]);
        if (p - k >= 0) t += int(s[p - k]) * sp;
        if (!t) continue;
        const int d = -2 * t;
        out += 2LL * c[k] * d + 1LL * d * d;
    }
    return out;
}

static Seq parse(const std::string& text) {
    if (text.size() != 100) throw std::runtime_error("sequence must have length 100");
    Seq s{};
    for (int i = 0; i < 100; ++i) {
        if (text[i] == '+') s[i] = 1;
        else if (text[i] == '-') s[i] = -1;
        else throw std::runtime_error("sequence must contain only + and -");
    }
    return s;
}

static std::string format(const Seq& s) {
    std::string out;
    out.reserve(100);
    for (auto x : s) out.push_back(x > 0 ? '+' : '-');
    return out;
}

static Seq rotate_left(const Seq& s, int r) {
    Seq out{};
    for (int i = 0; i < 100; ++i) out[i] = s[(i + r) % 100];
    return out;
}

struct Node {
    long long e;
    uint64_t insertion_id;
    Seq s;
};
struct MinEnergy {
    bool operator()(const Node& a, const Node& b) const {
        return a.e > b.e || (a.e == b.e && a.insertion_id > b.insertion_id);
    }
};

int main(int argc, char** argv) {
    if (argc < 4 || argc > 5) {
        std::cerr << "usage: priority-queue <100-char +/- seed> <Tu> <Tr> [max_seen]\n";
        return 2;
    }
    const Seq seed = parse(argv[1]);
    const int Tu = std::stoi(argv[2]);
    const int Tr = std::stoi(argv[3]);
    const size_t max_seen = argc == 5 ? std::stoull(argv[4]) : 3000000;
    if (Tu <= 0 || Tr < 0 || Tr >= 50 || max_seen < 1000) return 2;

    std::priority_queue<Node, std::vector<Node>, MinEnergy> pq;
    std::unordered_set<Key, KeyHash> seen;
    seen.reserve(max_seen * 2);

    uint64_t insertion_id = 0;
    const long long initial = energy(seed);
    long long best = initial;
    Seq best_seq = seed;
    pq.push({initial, insertion_id++, seed});
    seen.insert(key_of(seed));

    int u = 0;
    unsigned long long popped = 0;
    bool capped = false;
    const auto started = std::chrono::steady_clock::now();

    while (u < Tu && !pq.empty() && !capped) {
        ++u;
        Node pivot = pq.top();
        pq.pop();
        ++popped;

        Corr c{};
        if (energy(pivot.s, &c) != pivot.e) throw std::runtime_error("stored energy mismatch");

        for (int i = 0; i < 100 && !capped; ++i) {
            Seq neighbor = pivot.s;
            neighbor[i] = -neighbor[i];
            const long long neighbor_e = energy_if_flipped(pivot.s, c, pivot.e, i);

            if (seen.insert(key_of(neighbor)).second) {
                pq.push({neighbor_e, insertion_id++, neighbor});
                if (neighbor_e < best) {
                    best = neighbor_e;
                    best_seq = neighbor;
                    u = 0;
                    std::cout << "BEST energy=" << best << " popped=" << popped
                              << " seen=" << seen.size() << "\n";
                    if (best <= 574) {
                        std::cout << "BESTSEQ " << format(best_seq) << "\n";
                        return 0;
                    }
                }
            }

            for (int r = 1; r <= Tr; ++r) {
                for (int direction = 0; direction < 2; ++direction) {
                    Seq rotated = rotate_left(neighbor, direction == 0 ? r : 100 - r);
                    if (!seen.insert(key_of(rotated)).second) continue;
                    const long long rotated_e = energy(rotated);
                    pq.push({rotated_e, insertion_id++, rotated});
                    if (rotated_e < best) {
                        best = rotated_e;
                        best_seq = rotated;
                        u = 0;
                        std::cout << "BEST energy=" << best << " popped=" << popped
                                  << " seen=" << seen.size() << " rotation=1\n";
                        if (best <= 574) {
                            std::cout << "BESTSEQ " << format(best_seq) << "\n";
                            return 0;
                        }
                    }
                    if (seen.size() >= max_seen) {
                        capped = true;
                        break;
                    }
                }
                if (capped) break;
            }
            if (seen.size() >= max_seen) capped = true;
        }
    }

    const double seconds = std::chrono::duration<double>(
        std::chrono::steady_clock::now() - started).count();
    std::cout << "FINAL initial=" << initial << " best=" << best
              << " popped=" << popped << " seen=" << seen.size()
              << " queued=" << pq.size() << " capped=" << int(capped)
              << " seconds=" << seconds << "\n";
    std::cout << "BESTSEQ " << format(best_seq) << "\n";
    return best <= 574 ? 0 : 1;
}
