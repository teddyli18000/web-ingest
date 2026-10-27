// Unrestricted N=100 memetic-tabu search following the public lMAts source in
// borkob/git_labs (Gallardo/Cotta/Fernandez algorithm as instrumented by
// Boskovic et al.). This is an independent clean-room reimplementation of the
// public algorithmic details, not copied build output or third-party binaries.
//
// Core historical parameters reproduced here:
//   population size 100
//   uniform crossover probability 0.9
//   per-bit mutation probability 1/N
//   binary tournament parent selection
//   nonduplicate child replaces a random population member
//   child tabu search maxIter = N/2 + U{0,...,N-1}
//   tabu tenure = floor(maxIter/10) + U{0,...,floor(maxIter/50)-1}

#include <algorithm>
#include <array>
#include <atomic>
#include <chrono>
#include <climits>
#include <cstdint>
#include <iostream>
#include <random>
#include <stdexcept>
#include <string>
#include <vector>
#ifdef _OPENMP
#include <omp.h>
#endif

using Seq = std::array<int8_t, 100>;
using Corr = std::array<int, 100>;

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

static void flip(Seq& s, Corr& c, long long& e, int p) {
    const int sp = s[p];
    for (int k = 1; k < 100; ++k) {
        int t = 0;
        if (p + k < 100) t += sp * int(s[p + k]);
        if (p - k >= 0) t += int(s[p - k]) * sp;
        if (!t) continue;
        const int d = -2 * t;
        e += 2LL * c[k] * d + 1LL * d * d;
        c[k] += d;
    }
    s[p] = -s[p];
}

static Seq random_sequence(std::mt19937_64& rng) {
    Seq s{};
    for (auto& x : s) x = (rng() & 1) ? 1 : -1;
    return s;
}

static std::string format(const Seq& s) {
    std::string out;
    out.reserve(100);
    for (auto x : s) out.push_back(x > 0 ? '+' : '-');
    return out;
}

struct Individual {
    Seq s{};
    long long e = LLONG_MAX;
};

static Individual tabu_polish(Seq s, std::mt19937_64& rng) {
    Corr c{};
    long long current_e = energy(s, &c);
    Individual best{s, current_e};

    const int max_iter = 50 + int(rng() % 100);  // N/2 + U[0,N)
    const int min_tabu = max_iter / 10;
    const int random_tabu_span = max_iter / 50;
    std::array<int, 100> tabu_until{};
    std::array<int, 100> tied_moves{};

    for (int iter = 1; iter <= max_iter; ++iter) {
        long long best_move_e = LLONG_MAX;
        int tie_count = 0;

        for (int bit = 0; bit < 100; ++bit) {
            const long long candidate_e = energy_if_flipped(s, c, current_e, bit);
            const bool allowed = tabu_until[bit] < iter || candidate_e < best.e;
            if (!allowed) continue;

            if (candidate_e < best_move_e) {
                best_move_e = candidate_e;
                tied_moves[0] = bit;
                tie_count = 1;
            } else if (candidate_e == best_move_e) {
                tied_moves[tie_count++] = bit;
            }
        }

        if (tie_count == 0) continue;
        const int bit = tied_moves[rng() % tie_count];
        flip(s, c, current_e, bit);
        tabu_until[bit] = iter + min_tabu +
            (random_tabu_span ? int(rng() % random_tabu_span) : 0);

        if (current_e < best.e) best = {s, current_e};
    }

#ifndef NDEBUG
    if (energy(best.s) != best.e) throw std::runtime_error("tabu score mismatch");
#endif
    return best;
}

struct RunResult {
    Individual best;
    unsigned long long generations = 0;
};

static RunResult run_replica(uint64_t seed, double seconds, long long target,
                             std::atomic<bool>& target_found, int replica_id) {
    std::mt19937_64 rng(seed);
    std::array<Individual, 100> population{};
    Individual global_best;

    for (auto& ind : population) {
        ind.s = random_sequence(rng);
        ind.e = energy(ind.s);
        if (ind.e < global_best.e) global_best = ind;
    }

    auto tournament = [&]() {
        const int a = int(rng() % 100);
        const int b = int(rng() % 100);
        return population[a].e < population[b].e ? a : b;
    };

    const auto started = std::chrono::steady_clock::now();
    unsigned long long generation = 0;

    while (!target_found.load(std::memory_order_relaxed)) {
        if ((generation & 0xff) == 0) {
            const double elapsed = std::chrono::duration<double>(
                std::chrono::steady_clock::now() - started).count();
            if (elapsed >= seconds) break;
        }
        ++generation;

        Seq child{};
        if ((rng() % 1000) < 900) {
            const int a = tournament();
            const int b = tournament();
            for (int i = 0; i < 100; ++i)
                child[i] = (rng() & 1) ? population[a].s[i] : population[b].s[i];
        } else {
            child = population[rng() % 100].s;
        }

        for (int i = 0; i < 100; ++i)
            if ((rng() % 100) == 0) child[i] = -child[i];

        Individual polished = tabu_polish(child, rng);

        bool duplicate = false;
        for (const auto& ind : population) {
            if (ind.e == polished.e && ind.s == polished.s) {
                duplicate = true;
                break;
            }
        }
        if (!duplicate) population[rng() % 100] = polished;

        if (polished.e < global_best.e) {
            global_best = polished;
#pragma omp critical
            {
                std::cout << "BEST replica=" << replica_id
                          << " generation=" << generation
                          << " energy=" << global_best.e
                          << " seq=" << format(global_best.s) << "\n" << std::flush;
            }
            if (global_best.e <= target) {
                target_found.store(true, std::memory_order_relaxed);
                break;
            }
        }
    }

    if (energy(global_best.s) != global_best.e)
        throw std::runtime_error("final independent score mismatch");
    return {global_best, generation};
}

int main(int argc, char** argv) {
    int replicas = 4;
    int threads = 0;
    double seconds = 60.0;
    uint64_t seed = 1;
    long long target = 574;

    for (int i = 1; i < argc; ++i) {
        const std::string arg = argv[i];
        auto need = [&]() {
            if (++i >= argc) throw std::runtime_error("missing argument value");
            return std::string(argv[i]);
        };
        if (arg == "--replicas") replicas = std::stoi(need());
        else if (arg == "--threads") threads = std::stoi(need());
        else if (arg == "--seconds") seconds = std::stod(need());
        else if (arg == "--seed") seed = std::stoull(need());
        else if (arg == "--target") target = std::stoll(need());
        else throw std::runtime_error("unknown argument: " + arg);
    }
    if (replicas <= 0 || seconds <= 0) return 2;

#ifdef _OPENMP
    if (threads <= 0) threads = omp_get_max_threads();
    omp_set_num_threads(threads);
#else
    threads = 1;
#endif

    std::atomic<bool> target_found{false};
    std::vector<RunResult> results(replicas);
    const auto started = std::chrono::steady_clock::now();

#pragma omp parallel for schedule(dynamic, 1) if(replicas > 1)
    for (int r = 0; r < replicas; ++r) {
        results[r] = run_replica(
            seed + 0x9e3779b97f4a7c15ULL * uint64_t(r + 1),
            seconds, target, target_found, r);
    }

    int best_index = 0;
    for (int r = 1; r < replicas; ++r)
        if (results[r].best.e < results[best_index].best.e) best_index = r;

    std::vector<long long> scores;
    scores.reserve(replicas);
    unsigned long long total_generations = 0;
    for (const auto& result : results) {
        scores.push_back(result.best.e);
        total_generations += result.generations;
    }
    std::sort(scores.begin(), scores.end());
    auto q = [&](double f) { return scores[size_t(f * (scores.size() - 1))]; };

    const auto& best = results[best_index].best;
    const double wall = std::chrono::duration<double>(
        std::chrono::steady_clock::now() - started).count();
    std::cout << "SUMMARY replicas=" << replicas
              << " total_generations=" << total_generations
              << " min=" << scores.front()
              << " p10=" << q(0.10)
              << " median=" << q(0.50)
              << " p90=" << q(0.90)
              << " max=" << scores.back()
              << " wall_seconds=" << wall << "\n";
    std::cout << "FINAL energy=" << best.e << " seq=" << format(best.s) << "\n";
    return best.e <= target ? 0 : 1;
}
