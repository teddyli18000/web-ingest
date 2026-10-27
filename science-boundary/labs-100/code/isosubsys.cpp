// Experimental N=100 implementation of the n=4 kicked-descent idea from
// Lau & Gangat, arXiv:2610.14361v2 (2026). This is a research probe, not the
// authors' code and not a claim of exact implementation equivalence.

#include <algorithm>
#include <array>
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

static long long exact(const Seq& s, Corr* out = nullptr) {
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

static Seq random_sequence(std::mt19937_64& rng) {
    Seq s{};
    for (auto& x : s) x = (rng() & 1) ? 1 : -1;
    return s;
}

struct Proposal {
    std::array<int, 4> pos{};
    std::array<int8_t, 4> value{};
};

// Assignment-dependent part of the exact isolated-subsystem Hamiltonian.
// Expanding E=sum_k C_k^2 gives two-body terms when two same-k edges share a
// vertex and four-body terms when two disjoint same-k edges are both internal
// to the selected subsystem. Terms touching an environment variable vanish
// when the subsystem is disconnected; additive constants are irrelevant.
static int isolated_objective(const std::array<int, 4>& p,
                              const std::array<int8_t, 4>& v) {
    int h = 0;
    for (int i = 0; i < 4; ++i) {
        for (int j = i + 1; j < 4; ++j) {
            if (((p[j] - p[i]) & 1) == 0) h += 2 * int(v[i]) * int(v[j]);
        }
    }
    const int pairings[3][4] = {{0, 1, 2, 3}, {0, 2, 1, 3}, {0, 3, 1, 2}};
    for (const auto& q : pairings) {
        if (p[q[1]] - p[q[0]] == p[q[3]] - p[q[2]]) {
            h += 2 * int(v[0]) * int(v[1]) * int(v[2]) * int(v[3]);
        }
    }
    return h;
}

static Proposal random_isolated_optimum(std::mt19937_64& rng) {
    std::array<int, 100> index{};
    for (int i = 0; i < 100; ++i) index[i] = i;
    for (int i = 0; i < 4; ++i) {
        std::uniform_int_distribution<int> choose(i, 99);
        std::swap(index[i], index[choose(rng)]);
    }

    std::array<int, 4> p = {index[0], index[1], index[2], index[3]};
    std::sort(p.begin(), p.end());

    int best = INT_MAX;
    std::array<std::array<int8_t, 4>, 16> ties{};
    int tie_count = 0;
    for (int mask = 0; mask < 16; ++mask) {
        std::array<int8_t, 4> v{};
        for (int i = 0; i < 4; ++i) v[i] = (mask >> i & 1) ? 1 : -1;
        const int h = isolated_objective(p, v);
        if (h < best) {
            best = h;
            tie_count = 0;
            ties[tie_count++] = v;
        } else if (h == best) {
            ties[tie_count++] = v;
        }
    }
    std::uniform_int_distribution<int> choose_tie(0, tie_count - 1);
    return {p, ties[choose_tie(rng)]};
}

static long long evaluate_assignment(const Seq& s, const Corr& c, long long e,
                                     const Proposal& p, bool complement) {
    Seq trial = s;
    Corr trial_corr = c;
    long long trial_e = e;
    for (int j = 0; j < 4; ++j) {
        const int8_t wanted = complement ? -p.value[j] : p.value[j];
        if (trial[p.pos[j]] != wanted) flip(trial, trial_corr, trial_e, p.pos[j]);
    }
    return trial_e;
}

static void apply_assignment(Seq& s, Corr& c, long long& e,
                             const Proposal& p, bool complement) {
    for (int j = 0; j < 4; ++j) {
        const int8_t wanted = complement ? -p.value[j] : p.value[j];
        if (s[p.pos[j]] != wanted) flip(s, c, e, p.pos[j]);
    }
}

struct Result { long long energy; Seq seq; long long evaluations; };

static Result run_kicked_descent(Seq s, std::mt19937_64& rng,
                                 long long max_evaluations, int failure_threshold,
                                 long long target) {
    Corr c{};
    long long e = exact(s, &c);
    long long best = e;
    Seq best_seq = s;
    long long evaluations = 0;
    int failures = 0;

    while (evaluations < max_evaluations && best > target) {
        const Proposal p = random_isolated_optimum(rng);
        if (failures < failure_threshold) {
            const long long direct = evaluate_assignment(s, c, e, p, false);
            const long long complement = evaluate_assignment(s, c, e, p, true);
            evaluations += 2;
            const long long proposed = std::min(direct, complement);
            if (proposed < e) {
                apply_assignment(s, c, e, p, complement < direct);
                if (e != proposed) throw std::runtime_error("incremental application mismatch");
                failures = 0;
                if (e < best) { best = e; best_seq = s; }
            } else {
                ++failures;
            }
        } else {
            // One Base step: accept the isolated-subsystem optimum regardless
            // of the resulting global energy, providing the kick.
            apply_assignment(s, c, e, p, false);
            ++evaluations;
            failures = 0;
            if (e < best) { best = e; best_seq = s; }
        }
#ifndef NDEBUG
        if ((evaluations & 0x3fff) == 0 && exact(s, nullptr) != e) {
            throw std::runtime_error("incremental score mismatch");
        }
#endif
    }
    return {best, best_seq, evaluations};
}

int main(int argc, char** argv) {
    const std::string incumbent_text =
        "++++++--+++++-----++-++--+--++++++++++---+-++--++++-+--++----+--+-+-+-+-++---++---++-+-++-+-++--+-+-";
    int runs = 16;
    int threads = 0;
    int failure_threshold = 80;
    long long evaluations = 1000000;
    long long target = 574;
    uint64_t seed = 1;
    std::string mode = "random";

    for (int i = 1; i < argc; ++i) {
        const std::string arg = argv[i];
        auto need = [&]() {
            if (++i >= argc) throw std::runtime_error("missing argument value");
            return std::string(argv[i]);
        };
        if (arg == "--runs") runs = std::stoi(need());
        else if (arg == "--threads") threads = std::stoi(need());
        else if (arg == "--evals") evaluations = std::stoll(need());
        else if (arg == "--seed") seed = std::stoull(need());
        else if (arg == "--X") failure_threshold = std::stoi(need());
        else if (arg == "--target") target = std::stoll(need());
        else if (arg == "--mode") mode = need();
        else throw std::runtime_error("unknown argument: " + arg);
    }

#ifdef _OPENMP
    if (threads <= 0) threads = omp_get_max_threads();
    omp_set_num_threads(threads);
#else
    threads = 1;
#endif

    const Seq incumbent = parse(incumbent_text);
    std::vector<long long> run_best(runs, LLONG_MAX);
    long long global_best = LLONG_MAX;
    Seq global_seq = incumbent;
    const auto started = std::chrono::steady_clock::now();

#pragma omp parallel for schedule(dynamic, 1) if(runs > 1)
    for (int run = 0; run < runs; ++run) {
        std::mt19937_64 rng(seed + 0x9e3779b97f4a7c15ULL * uint64_t(run + 1));
        Seq start;
        if (mode == "random") start = random_sequence(rng);
        else if (mode == "incumbent") start = incumbent;
        else throw std::runtime_error("mode must be random or incumbent");

        const Result result = run_kicked_descent(
            start, rng, evaluations, failure_threshold, target);
        run_best[run] = result.energy;
#pragma omp critical
        {
            if (result.energy < global_best) {
                global_best = result.energy;
                global_seq = result.seq;
                std::cout << "BEST energy=" << global_best << " run=" << run
                          << " evals=" << result.evaluations
                          << " seq=" << format(global_seq) << "\n" << std::flush;
            }
        }
    }

    std::sort(run_best.begin(), run_best.end());
    auto quantile = [&](double fraction) {
        return run_best[size_t(fraction * (run_best.size() - 1))];
    };
    const double seconds = std::chrono::duration<double>(
        std::chrono::steady_clock::now() - started).count();
    std::cout << "SUMMARY runs=" << runs
              << " min=" << run_best.front()
              << " p10=" << quantile(0.10)
              << " median=" << quantile(0.50)
              << " p90=" << quantile(0.90)
              << " max=" << run_best.back() << "\n";
    std::cout << "FINAL energy=" << global_best << " seconds=" << seconds
              << " seq=" << format(global_seq) << "\n";
    return global_best <= target ? 0 : 1;
}
