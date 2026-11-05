#!/usr/bin/env python3
"""Minimal AGPLv3-compatible warm-start adaptation to Ming Qi's N7 tabu.

Copyright (C) 2026 project research contributors. Licensed under AGPL-3.0
for compatibility with the upstream Ming Qi C++ implementation.

Pins upstream commit 7e120ebada21cb604c871e0657814bf6e32611f8.
Only ADD a method that maps a complete machine-order permutation into
the existing Graph and resets the incumbent. Do not edit search(), find_move(),
make_move(), is_legal_action(), approximate_evaluation() or tabu tenure.
Re-check the output source diff and original source sha before use.
"""
import argparse
import subprocess
from pathlib import Path

PIN="7e120ebada21cb604c871e0657814bf6e32611f8"
HEADER_INSERT="""    // Added AGPLv3 reproducible initialization hook for public ta41=2006.
    // All original N7 search, tabu, move and score code stays unchanged.
    void load_verified_machine_orders(const std::vector<std::vector<int>>& rows);
"""
CPP_INSERT=r"""
// Added reproducible initialization hook under AGPLv3; not original author code.
// Complete machine sequences; job IDs 0-based; 1 operation per job/machine.
void TabuSearch::load_verified_machine_orders(
    const std::vector<std::vector<int>>& machine_jobs) {
    auto &g=current_schedule.graph;
    const int job_count=g.job_num, machine_count=g.operation_num;
    if(int(machine_jobs.size())!=machine_count)
        throw std::runtime_error("wrong machine count in warmstart");
    std::vector<std::vector<int>> id(machine_count,
            std::vector<int>(job_count,-1));
    for(int op_id=1;op_id<=job_count*machine_count;op_id++){
        const auto &op=current_schedule.operation_list[op_id];
        const int job=op.job_id-1, machine=op.machine_id;
        if(job<0||job>=job_count||machine<0||machine>=machine_count)
            throw std::runtime_error("bad operation mapping");
        if(id[machine][job]>=0)
            throw std::runtime_error("duplicate operation on a machine");
        id[machine][job]=op_id;
    }
    for(int m=0;m<machine_count;m++){
        if(int(machine_jobs[m].size())!=job_count)
            throw std::runtime_error("wrong number of jobs per machine");
        std::vector<bool> seen(job_count,false);
        for(int k=0;k<job_count;k++){
            const int job=machine_jobs[m][k];
            if(job<0||job>=job_count||seen[job])
                throw std::runtime_error("invalid machine job permutation");
            seen[job]=true;
            const int op=id[m][job];
            if(op<0)throw std::runtime_error("missing routed operation");
            g.machine_predecessor[op]=
                (k>0?id[m][machine_jobs[m][k-1]]:-1);
            g.machine_successor[op]=
                (k+1<job_count?id[m][machine_jobs[m][k+1]]:-1);
        }
        g.first_machine_operation[m]=id[m][machine_jobs[m].front()];
        g.last_machine_operation[m]=id[m][machine_jobs[m].back()];
    }
    // Rebuild the exact native longest-path state and initialize best.
    // graph.topological_sort throws on any precedence cycle.
    current_schedule.calculate_time_info();
    best_schedule=current_schedule;
    iteration=0;
    tabu_list=TabuList(machine_count);
}
"""
def main(src):
    result=subprocess.run(["git","-C",str(src),"rev-parse","HEAD"],check=True,
        capture_output=True,text=True).stdout.strip()
    assert result==PIN,(result,PIN)
    h=src/"include"/"tabu_search.h"
    s=src/"src"/"tabu_search.cpp"
    orig=h.read_text()
    marker="    void search(unsigned long long max_iteration, const std::function<bool()> &condition = [] { return false; });"
    assert orig.count(marker)==1
    h.write_text(orig.replace(marker,marker+"\n\n"+HEADER_INSERT))
    srcdata=s.read_text()
    assert "load_verified_machine_orders" not in srcdata
    s.write_text(srcdata+"\n"+CPP_INSERT)
    diff=subprocess.run(["git","-C",str(src),"diff","--stat"],check=True,
        capture_output=True,text=True).stdout.strip()
    assert "include/tabu_search.h" in diff and "src/tabu_search.cpp" in diff
    print("AGPL-WARMSTART-ADAPTER",diff,flush=True)

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("src",type=Path)
    main(p.parse_args().src)
