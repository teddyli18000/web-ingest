#include <algorithm>
#include <array>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <limits>
#include <numeric>
#include <random>
#include <stdexcept>
#include <string>
#include <vector>

namespace {
constexpr int DIM = 8;
constexpr int U = 6561;
constexpr std::array<int, DIM> POW3 = {1,3,9,27,81,243,729,2187};

struct State {
    std::vector<uint8_t> in;
    std::vector<uint16_t> conf;
    std::vector<int> pts;
};

struct Searcher {
    std::vector<uint16_t> third;
    std::mt19937_64 rng;
    std::uniform_real_distribution<double> uni{0.0, 1.0};

    explicit Searcher(uint64_t seed) : third(static_cast<size_t>(U) * U), rng(seed) {
        build_third();
    }

    void build_third() {
        std::array<std::array<uint8_t, DIM>, U> digits{};
        for (int x = 0; x < U; ++x) {
            int t = x;
            for (int k = 0; k < DIM; ++k) {
                digits[x][k] = static_cast<uint8_t>(t % 3);
                t /= 3;
            }
        }
        for (int x = 0; x < U; ++x) {
            size_t base = static_cast<size_t>(x) * U;
            for (int y = 0; y < U; ++y) {
                int z = 0;
                for (int k = 0; k < DIM; ++k) {
                    int d = (3 - ((digits[x][k] + digits[y][k]) % 3)) % 3;
                    z += d * POW3[k];
                }
                third[base + y] = static_cast<uint16_t>(z);
            }
        }
    }

    inline int t3(int x, int y) const {
        return third[static_cast<size_t>(x) * U + y];
    }

    State make_state(const std::vector<int>& pts) const {
        State s{std::vector<uint8_t>(U, 0), std::vector<uint16_t>(U, 0), pts};
        for (int x : pts) {
            if (x < 0 || x >= U || s.in[x]) throw std::runtime_error("bad input point");
            s.in[x] = 1;
        }
        for (size_t i = 0; i < pts.size(); ++i) {
            for (size_t j = i + 1; j < pts.size(); ++j) {
                int z = t3(pts[i], pts[j]);
                if (s.conf[z] == std::numeric_limits<uint16_t>::max()) throw std::runtime_error("conf overflow");
                ++s.conf[z];
            }
        }
        for (int x : pts) {
            if (s.conf[x] != 0) throw std::runtime_error("input is not a cap set");
        }
        return s;
    }

    void add(State& s, int x) const {
        if (s.in[x] || s.conf[x] != 0) throw std::runtime_error("invalid add");
        for (int y : s.pts) {
            int z = t3(x, y);
            ++s.conf[z];
        }
        s.in[x] = 1;
        s.pts.push_back(x);
    }

    void remove(State& s, int x) const {
        if (!s.in[x]) throw std::runtime_error("invalid remove");
        s.in[x] = 0;
        auto it = std::find(s.pts.begin(), s.pts.end(), x);
        if (it == s.pts.end()) throw std::runtime_error("state mismatch");
        *it = s.pts.back();
        s.pts.pop_back();
        for (int y : s.pts) {
            int z = t3(x, y);
            if (s.conf[z] == 0) throw std::runtime_error("conf underflow");
            --s.conf[z];
        }
    }

    int unlock_score(const State& s, int x) const {
        int score = 0;
        for (int y : s.pts) {
            if (y == x) continue;
            int z = t3(x, y);
            if (!s.in[z] && s.conf[z] == 1) ++score;
        }
        return score;
    }

    std::vector<std::pair<int,int>> conflicts_for(const State& s, int x) const {
        std::vector<std::pair<int,int>> pairs;
        pairs.reserve(s.conf[x]);
        for (int y : s.pts) {
            int z = t3(x, y);
            if (s.in[z] && y < z) pairs.emplace_back(y, z);
        }
        return pairs;
    }

    int block_score_sample(const State& s, int x) const {
        int score = 0;
        for (int y : s.pts) {
            int z = t3(x, y);
            if (!s.in[z] && s.conf[z] == 0) ++score;
        }
        return score;
    }

    void greedy_repair(State& s) {
        while (true) {
            std::array<int, 40> sample{};
            int got = 0;
            int seen = 0;
            for (int x = 0; x < U; ++x) {
                if (s.in[x] || s.conf[x] != 0) continue;
                ++seen;
                if (got < static_cast<int>(sample.size())) {
                    sample[got++] = x;
                } else {
                    std::uniform_int_distribution<int> pick(0, seen - 1);
                    int r = pick(rng);
                    if (r < static_cast<int>(sample.size())) sample[r] = x;
                }
            }
            if (got == 0) break;
            int best_x = sample[0];
            int best_score = block_score_sample(s, best_x);
            for (int i = 1; i < got; ++i) {
                int sc = block_score_sample(s, sample[i]);
                if (sc < best_score || (sc == best_score && (rng() & 1))) {
                    best_score = sc;
                    best_x = sample[i];
                }
            }
            add(s, best_x);
        }
    }

    int choose_eject_candidate(const State& s) {
        int best_x = -1;
        int best_conf = std::numeric_limits<int>::max();
        for (int k = 0; k < 128; ++k) {
            int x = static_cast<int>(rng() % U);
            if (s.in[x]) continue;
            int c = s.conf[x];
            if (c == 0) return x;
            if (c < best_conf) {
                best_conf = c;
                best_x = x;
            }
        }
        if (best_x >= 0) return best_x;
        for (int x = 0; x < U; ++x) if (!s.in[x]) return x;
        return -1;
    }

    void shake(State& s, int removals) {
        removals = std::min(removals, static_cast<int>(s.pts.size()));
        for (int i = 0; i < removals; ++i) {
            int idx = static_cast<int>(rng() % s.pts.size());
            remove(s, s.pts[idx]);
        }
        greedy_repair(s);
    }

    std::vector<int> search(const std::vector<int>& initial, double seconds, int target, uint64_t seed) {
        State cur = make_state(initial);
        State best = cur;
        auto start = std::chrono::steady_clock::now();
        auto deadline = start + std::chrono::duration<double>(seconds);
        uint64_t iter = 0;
        uint64_t last_best_iter = 0;
        double temp = 1.35;

        while (std::chrono::steady_clock::now() < deadline && static_cast<int>(best.pts.size()) < target) {
            ++iter;
            if (iter - last_best_iter > 25000) {
                shake(cur, 2 + static_cast<int>(rng() % 7));
                last_best_iter = iter - 10000;
                temp = 1.6;
            }

            State before = cur;
            int x = choose_eject_candidate(cur);
            if (x < 0) break;

            if (cur.conf[x] == 0) {
                add(cur, x);
                greedy_repair(cur);
            } else {
                auto pairs = conflicts_for(cur, x);
                if (pairs.size() != cur.conf[x]) throw std::runtime_error("conflict accounting mismatch");
                if (pairs.size() > 14 && (rng() % 8 != 0)) {
                    cur = std::move(before);
                    continue;
                }
                std::vector<int> to_remove;
                to_remove.reserve(pairs.size());
                for (auto [a,b] : pairs) {
                    int sa = unlock_score(cur, a);
                    int sb = unlock_score(cur, b);
                    int chosen;
                    if (sa > sb) chosen = a;
                    else if (sb > sa) chosen = b;
                    else chosen = (rng() & 1) ? a : b;
                    to_remove.push_back(chosen);
                }
                std::sort(to_remove.begin(), to_remove.end());
                to_remove.erase(std::unique(to_remove.begin(), to_remove.end()), to_remove.end());
                for (int r : to_remove) if (cur.in[r]) remove(cur, r);
                if (cur.conf[x] != 0) {
                    cur = std::move(before);
                    continue;
                }
                add(cur, x);
                greedy_repair(cur);
            }

            int delta = static_cast<int>(cur.pts.size()) - static_cast<int>(before.pts.size());
            bool accept = delta >= 0 || uni(rng) < std::exp(static_cast<double>(delta) / temp);
            if (!accept) cur = std::move(before);

            if (cur.pts.size() > best.pts.size()) {
                best = cur;
                last_best_iter = iter;
                std::cerr << "seed=" << seed << " iter=" << iter << " best=" << best.pts.size() << "\n";
                if (static_cast<int>(best.pts.size()) >= target) break;
            }

            temp *= 0.999985;
            if (temp < 0.35) temp = 0.35;
        }
        std::cerr << "seed=" << seed << " iterations=" << iter << " final_best=" << best.pts.size() << "\n";
        std::sort(best.pts.begin(), best.pts.end());
        return best.pts;
    }
};

std::vector<int> read_ids(const std::string& path) {
    std::ifstream f(path);
    if (!f) throw std::runtime_error("cannot open input");
    std::vector<int> pts;
    int x;
    while (f >> x) pts.push_back(x);
    return pts;
}

void write_ids(const std::string& path, const std::vector<int>& pts) {
    std::ofstream f(path);
    if (!f) throw std::runtime_error("cannot open output");
    for (int x : pts) f << x << '\n';
}
}

int main(int argc, char** argv) {
    if (argc != 6) {
        std::cerr << "usage: search <baseline.ids> <output.ids> <seconds> <seed> <target>\n";
        return 2;
    }
    try {
        auto initial = read_ids(argv[1]);
        double seconds = std::stod(argv[3]);
        uint64_t seed = std::stoull(argv[4]);
        int target = std::stoi(argv[5]);
        Searcher s(seed);
        auto best = s.search(initial, seconds, target, seed);
        write_ids(argv[2], best);
        std::cout << best.size() << "\n";
        return 0;
    } catch (const std::exception& e) {
        std::cerr << "error: " << e.what() << "\n";
        return 1;
    }
}
