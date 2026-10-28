#!/usr/bin/env python3
"""Deadline-directed core-guided repair of a ta41 disjunctive graph.

Hypothesis: the 2006 incumbent is protected by interacting, globally
inconsistent precedence decisions. Learn UNSAT cores of the 2005
feasibility model and hit those cores with a small set of relaxed arcs.
An UNSAT core is a sufficient obstruction under the current assumptions,
NOT proof that the entire scheduling instance is infeasible.
"""
import argparse
import json
import random
import time
from pathlib import Path

from search import obtain, setup, evaluate


def graph_analysis(orders, pos, durations):
    n = len(durations)
    succ = [[] for _ in range(n)]
    indeg = [0] * n
    machine_arcs = []
    for j in range(30):
        for k in range(19):
            u, v = j * 20 + k, j * 20 + k + 1
            succ[u].append(v)
            indeg[v] += 1
    for m, order in enumerate(orders):
        for k, (a, b) in enumerate(zip(order, order[1:])):
            u, v = a * 20 + pos[a][m], b * 20 + pos[b][m]
            machine_arcs.append((m, k, u, v))
            succ[u].append(v)
            indeg[v] += 1
    q = [i for i in range(n) if indeg[i] == 0]
    head = [0] * n
    topo = []
    while q:
        u = q.pop()
        topo.append(u)
        for v in succ[u]:
            head[v] = max(head[v], head[u] + durations[u])
            indeg[v] -= 1
            if indeg[v] == 0:
                q.append(v)
    assert len(topo) == n
    tail = durations[:]
    for u in reversed(topo):
        tail[u] = durations[u] + max((tail[v] for v in succ[u]), default=0)
    horizon = max(head[i] + durations[i] for i in range(n))
    slack = [horizon - (head[u] + durations[u] + tail[v])
             for _, _, u, v in machine_arcs]
    assert min(slack) >= 0, min(slack)
    return machine_arcs, head, slack, horizon


def hitting_set(cores, slacks, arcs, rng):
    """Greedy cover of *observed* cores; no optimality claim."""
    uncovered = list(cores)
    chosen = set()
    machines = {}
    while uncovered:
        freq = {}
        for core in uncovered:
            for i in core:
                if i not in chosen:
                    freq[i] = freq.get(i, 0) + 1
        if not freq:
            raise AssertionError("learned a core already hit by current relaxation")
        def key(i):
            mach = arcs[i][0]
            return (freq[i] / (1 + max(0, slacks[i]) / 20),
                    -machines.get(mach, 0), rng.random())
        pick = max(freq, key=key)
        chosen.add(pick)
        machines[arcs[pick][0]] = machines.get(arcs[pick][0], 0) + 1
        uncovered = [core for core in uncovered if pick not in core]
    return chosen


def solve(seconds, seed, output, target, call_seconds):
    from ortools.sat.python import cp_model
    routes, durations_by_job, baseline = obtain()
    pos, durations = setup(routes, durations_by_job)
    arcs, hint, slack, incumbent = graph_analysis(baseline, pos, durations)
    assert incumbent == evaluate(baseline, pos, durations) == 2006
    assert target < incumbent
    total = len(durations)
    model = cp_model.CpModel()
    start = [model.new_int_var(0, target, "s_%d" % i) for i in range(total)]
    end = [model.new_int_var(0, target, "e_%d" % i) for i in range(total)]
    intervals = [model.new_interval_var(start[i], durations[i], end[i], "o_%d" % i)
                 for i in range(total)]
    for j in range(30):
        for k in range(19):
            model.add(start[j * 20 + k + 1] >= end[j * 20 + k])
    for m in range(20):
        model.add_no_overlap([intervals[j * 20 + pos[j][m]] for j in range(30)])
    fixed = []
    for i, (_, _, u, v) in enumerate(arcs):
        bit = model.new_bool_var("keep_%d" % i)
        model.add(start[v] >= end[u]).only_enforce_if(bit)
        fixed.append(bit)
    id_of = {var.index: i for i, var in enumerate(fixed)}
    cores = []
    seen = set()
    rng = random.Random(seed)
    begin = time.monotonic()
    outcomes = []
    best = incumbent
    relaxed = set()
    output.mkdir(parents=True, exist_ok=True)
    all_critical = sum(s == 0 for s in slack)
    while time.monotonic() - begin < seconds:
        relaxed = hitting_set(cores, slack, arcs, rng) if cores else set()
        model.clear_assumptions()
        model.add_assumptions([bit for i, bit in enumerate(fixed) if i not in relaxed])
        # The baseline is an informative hint, but cannot satisfy target=2005.
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = min(call_seconds, max(0.5, seconds - (time.monotonic() - begin)))
        solver.parameters.num_search_workers = 1
        solver.parameters.random_seed = seed + len(cores)
        result = solver.solve(model)
        info = dict(iteration=len(outcomes), status=solver.status_name(result),
                    relaxed=len(relaxed), elapsed=round(time.monotonic() - begin, 3),
                    conflicts=solver.num_conflicts)
        if result in (cp_model.FEASIBLE, cp_model.OPTIMAL):
            orders = []
            for m in range(20):
                orders.append(sorted(range(30), key=lambda j:
                              solver.value(start[j * 20 + pos[j][m]])))
            score = evaluate(orders, pos, durations)
            if score is None or score > target:
                raise AssertionError("solver candidate failed independent DAG evaluation: %s" % score)
            best = score
            (output / "certificate.json").write_text(
                json.dumps({"machines": orders}, separators=(",", ":")) + "\n")
            info["verified_candidate_makespan"] = score
            outcomes.append(info)
            break
        elif result == cp_model.INFEASIBLE:
            core = frozenset(id_of[l] for l in solver.sufficient_assumptions_for_infeasibility()
                             if l in id_of)
            if not core:
                raise RuntimeError("empty assumption core: target globally infeasible, or bad mapping")
            if core in seen:
                raise AssertionError("duplicate core despite core hitting set")
            seen.add(core)
            cores.append(core)
            info["core_size"] = len(core)
            info["core_min_slack"] = min(slack[i] for i in core)
            info["core_machines"] = len(set(arcs[i][0] for i in core))
        else:
            info["note"] = "UNPROVEN: solver returned UNKNOWN; enlarge budget or revise model"
            outcomes.append(info)
            break
        outcomes.append(info)
        print(json.dumps(info, separators=(",", ":")), flush=True)
    summary = {
        "method": "assumption-unsat-core-hitting-set",
        "instance": "ta41",
        "target": target,
        "baseline": incumbent,
        "best_verified_candidate": best if best < incumbent else None,
        "certified_global_infeasibility": False,
        "critical_machine_arcs_in_baseline": all_critical,
        "machine_arcs": len(arcs),
        "observed_unsat_cores": len(cores),
        "min_max_core_size": ([min(map(len, cores)), max(map(len, cores))]
                              if cores else None),
        "last_relaxed_arc_count": len(relaxed),
        "seed": seed,
        "calls": outcomes,
        "core_sets": [sorted(c) for c in cores],
    }
    (output / "core-analysis.json").write_text(json.dumps(summary, indent=2) + "\n")
    print("SUMMARY " + json.dumps({k: v for k, v in summary.items()
                                   if k not in ("calls", "core_sets")}), flush=True)
    return best


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--seconds", type=int, default=600)
    p.add_argument("--seed", type=int, default=41)
    p.add_argument("--call-seconds", type=float, default=20)
    p.add_argument("--target", type=int, default=2005)
    p.add_argument("--output", type=Path,
                   default=Path(__file__).parent / "results" / "core-seed41")
    a = p.parse_args()
    solve(a.seconds, a.seed, a.output, a.target, a.call_seconds)
