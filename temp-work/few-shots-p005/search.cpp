#include <algorithm>
#include <array>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <limits>
#include <random>
#include <stdexcept>
#include <string>
#include <vector>

namespace {
constexpr int Q = 3;
constexpr int D = 8;
constexpr int HALF = 81;          // 3^4
constexpr int U = 6561;           // 3^8
constexpr int BASE = 512;
constexpr int TARGET = 513;

struct Search {
    std::array<std::array<std::uint8_t, HALF>, HALF> negsum{};
    std::array<int, U> conf{};
    std::array<int, U> pos{};
    std::array<int, U> tabu_until{};
    std::array<unsigned char, U> in{};
    std::vector<int> sel;
    std::vector<int> baseline;
    std::mt19937_64 rng;
    long long moves = 0;
    int violations = 0;
    int best_v = std::numeric_limits<int>::max();
    std::vector<int> best_set;

    explicit Search(std::uint64_t seed) : rng(seed) {
        pos.fill(-1);
        for (int a = 0; a < HALF; ++a) {
            for (int b = 0; b < HALF; ++b) {
                int x = a, y = b, out = 0, place = 1;
                for (int k = 0; k < 4; ++k) {
                    int d = (-(x % 3 + y % 3)) % 3;
                    if (d < 0) d += 3;
                    out += d * place;
                    place *= 3;
                    x /= 3;
                    y /= 3;
                }
                negsum[a][b] = static_cast<std::uint8_t>(out);
            }
        }
    }

    int third(int a, int b) const {
        return int(negsum[a / HALF][b / HALF]) * HALF + int(negsum[a % HALF][b % HALF]);
    }

    void load(const std::string& path) {
        std::ifstream f(path);
        int x;
        while (f >> x) baseline.push_back(x);
        if (baseline.size() != BASE) throw std::runtime_error("expected 512 baseline ids");
        auto z = baseline;
        std::sort(z.begin(), z.end());
        if (std::adjacent_find(z.begin(), z.end()) != z.end()) throw std::runtime_error("duplicate baseline id");
        for (int v : baseline) if (v < 0 || v >= U) throw std::runtime_error("baseline id out of range");
    }

    void add_pair(int a, int b, int delta) {
        int w = third(a, b);
        conf[w] += delta;
        if (conf[w] < 0) throw std::runtime_error("negative conflict count");
    }

    void init_restart() {
        conf.fill(0);
        in.fill(0);
        pos.fill(-1);
        tabu_until.fill(0);
        sel = baseline;
        for (int i = 0; i < BASE; ++i) {
            in[sel[i]] = 1;
            pos[sel[i]] = i;
        }
        for (int i = 0; i < BASE; ++i)
            for (int j = i + 1; j < BASE; ++j)
                add_pair(sel[i], sel[j], +1);

        // Start one point above the known cap.
        std::uniform_int_distribution<int> du(0, U - 1);
        int u;
        do { u = du(rng); } while (in[u]);
        violations = conf[u];
        for (int x : sel) add_pair(u, x, +1);
        pos[u] = int(sel.size());
        sel.push_back(u);
        in[u] = 1;
        if (violations < best_v) {
            best_v = violations;
            best_set = sel;
        }
    }

    void swap_points(int r, int u, int new_v, int tenure) {
        int idx = pos[r];
        if (idx < 0 || in[u]) throw std::runtime_error("bad swap");
        for (int x : sel) if (x != r) add_pair(r, x, -1);
        in[r] = 0;
        pos[r] = -1;
        sel[idx] = u;
        pos[u] = idx;
        for (int x : sel) if (x != u) add_pair(u, x, +1);
        in[u] = 1;
        violations = new_v;
        tabu_until[r] = int(std::min<long long>(moves + tenure, std::numeric_limits<int>::max()));
    }

    bool step() {
        std::vector<int> bad;
        bad.reserve(64);
        int maxc = 0;
        for (int r : sel) {
            if (conf[r] > 0) {
                bad.push_back(r);
                maxc = std::max(maxc, conf[r]);
            }
        }
        if (bad.empty()) return violations == 0;

        // Usually attack a maximally guilty selected point; sometimes pick any
        // violating point to move across plateaus.
        int r = -1;
        if ((rng() % 10) < 8) {
            std::vector<int> top;
            for (int x : bad) if (conf[x] == maxc && tabu_until[x] <= moves) top.push_back(x);
            if (top.empty()) for (int x : bad) if (conf[x] == maxc) top.push_back(x);
            r = top[rng() % top.size()];
        } else {
            r = bad[rng() % bad.size()];
        }

        int best_nv = std::numeric_limits<int>::max();
        int best_u = -1;
        std::uint64_t ties = 0;
        for (int u = 0; u < U; ++u) {
            if (in[u]) continue;
            int after_remove = conf[u] - (in[third(r, u)] ? 1 : 0);
            int nv = violations - conf[r] + after_remove;
            bool tabu = tabu_until[u] > moves;
            if (tabu && nv != 0 && nv >= best_v) continue;
            if (nv < best_nv) {
                best_nv = nv;
                best_u = u;
                ties = 1;
            } else if (nv == best_nv) {
                ++ties;
                if ((rng() % ties) == 0) best_u = u;
            }
        }
        if (best_u < 0) return false;

        // Permit small uphill moves; repeated kicks/restarts provide larger escapes.
        bool accept = best_nv <= violations;
        if (!accept) {
            int d = best_nv - violations;
            std::uint64_t threshold = d == 1 ? 70 : (d == 2 ? 8 : 1); // per 1000
            accept = (rng() % 1000) < threshold;
        }
        if (!accept) {
            // Force a random non-tabu move occasionally rather than freezing.
            if ((rng() % 20) != 0) return false;
            std::vector<int> outside;
            outside.reserve(U - TARGET);
            for (int u = 0; u < U; ++u) if (!in[u] && tabu_until[u] <= moves) outside.push_back(u);
            if (outside.empty()) return false;
            best_u = outside[rng() % outside.size()];
            best_nv = violations - conf[r] + conf[best_u] - (in[third(r, best_u)] ? 1 : 0);
        }

        int tenure = 7 + int(rng() % 19) + std::min(25, violations / 4);
        swap_points(r, best_u, best_nv, tenure);
        ++moves;
        if (violations < best_v) {
            best_v = violations;
            best_set = sel;
            std::cerr << "best violations=" << best_v << " moves=" << moves << "\n";
        }
        return violations == 0;
    }

    void kick(int count) {
        for (int t = 0; t < count; ++t) {
            int idx = rng() % sel.size();
            int r = sel[idx];
            int u;
            do { u = rng() % U; } while (in[u]);
            int nv = violations - conf[r] + conf[u] - (in[third(r, u)] ? 1 : 0);
            swap_points(r, u, nv, 3);
            ++moves;
        }
    }
};

void emit(const std::string& out, const char* kind, const Search& s, int restart, std::uint64_t seed) {
    std::ofstream f(out);
    f << "{\"kind\":\"" << kind << "\",\"violations\":" << s.best_v
      << ",\"moves\":" << s.moves << ",\"restart\":" << restart
      << ",\"seed\":" << seed << ",\"points\":[";
    const auto& v = (std::string(kind) == "found") ? s.sel : s.best_set;
    for (std::size_t i = 0; i < v.size(); ++i) {
        if (i) f << ',';
        f << v[i];
    }
    f << "]}\n";
}

} // namespace

int main(int argc, char** argv) {
    try {
        if (argc < 4 || argc > 5) {
            std::cerr << "usage: search BASELINE_IDS OUT_JSON SECONDS [SEED]\n";
            return 2;
        }
        const std::string in = argv[1], out = argv[2];
        const double seconds = std::stod(argv[3]);
        const std::uint64_t seed = argc == 5 ? std::stoull(argv[4])
            : std::chrono::high_resolution_clock::now().time_since_epoch().count();
        Search s(seed);
        s.load(in);
        const auto start = std::chrono::steady_clock::now();
        int restart = 0;
        while (std::chrono::duration<double>(std::chrono::steady_clock::now() - start).count() < seconds) {
            ++restart;
            s.init_restart();
            int stagnant = 0;
            int local_best = s.violations;
            while (std::chrono::duration<double>(std::chrono::steady_clock::now() - start).count() < seconds) {
                if (s.violations == 0 || s.step()) {
                    std::cerr << "FOUND restart=" << restart << " moves=" << s.moves << "\n";
                    emit(out, "found", s, restart, seed);
                    return 0;
                }
                if (s.violations < local_best) {
                    local_best = s.violations;
                    stagnant = 0;
                } else {
                    ++stagnant;
                }
                if (stagnant > 6000) {
                    if ((restart % 4) != 0) {
                        s.kick(12 + int(s.rng() % 20));
                        stagnant = 0;
                    } else {
                        break;
                    }
                }
            }
            if ((restart % 10) == 0)
                std::cerr << "restart=" << restart << " global_best=" << s.best_v << " moves=" << s.moves << "\n";
        }
        emit(out, "none", s, restart, seed);
        std::cerr << "DONE best=" << s.best_v << " moves=" << s.moves << " restarts=" << restart << "\n";
        return 0;
    } catch (const std::exception& e) {
        std::cerr << "error: " << e.what() << "\n";
        return 1;
    }
}
