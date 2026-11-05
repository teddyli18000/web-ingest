#!/usr/bin/env python3
"""Minimal, auditable upstream N7 C++ instrumentation for ta41 seeded comparison.

Upstream authors' N7 neighborhood, approximate evaluation and tabu logic
are not changed. This patch adds ONLY an initialization method accepting
known feasible machine permutations, and exposes it through pybind11.
The resulting 2006-start experiments can be compared with the project's
multi-step predictive search without cold-start confounding.

Upstream SHA: Qiming01/Job-Shop-Scheduling@7e120ebada21...
"""
import argparse
from pathlib import Path

def patch(p,old,new):
    s=p.read_text()
    assert s.count(old)==1,(p,old[:100],s.count(old))
    p.write_text(s.replace(old,new))

def main(root):
    head=root/'include'/'tabu_search.h'
    marker='protected:\n    /**\n     * Find the best available move in neighborhood'
    init="""    /** Seed the EXACT verified machine job orders (jobs zero based).
     *  Only changes initialization; the native search itself is untouched.
     */
    void seed_machine_orders(const std::vector<std::vector<int>>& orders) {
        auto& g=current_schedule.graph;
        const int M=g.operation_num;
        if (orders.size()!=static_cast<size_t>(M))
            throw std::runtime_error("Machine count mismatch");
        std::fill(g.machine_successor.begin(),g.machine_successor.end(),-1);
        std::fill(g.machine_predecessor.begin(),g.machine_predecessor.end(),-1);
        g.first_machine_operation.assign(M,-1);
        g.last_machine_operation.assign(M,-1);
        for(int m=0;m<M;m++) {
            if(orders[m].size()!=static_cast<size_t>(g.job_num))
                throw std::runtime_error("Job count mismatch");
            std::vector<bool> visited(g.job_num,false);
            int previous=-1;
            for(int j:orders[m]) {
                if(j<0 || j>=g.job_num || visited[j])
                    throw std::runtime_error("Invalid machine permutation");
                visited[j]=true;
                int id=-1;
                for(int k=0;k<M;k++) {
                    const int candidate=j*M+k+1;
                    if(current_schedule.operation_list[candidate].machine_id==m) {
                        id=candidate;break;
                    }
                }
                if(id<0)throw std::runtime_error("Machine assignment missing");
                if(previous<0)g.first_machine_operation[m]=id;
                else {
                    g.machine_successor[previous]=id;
                    g.machine_predecessor[id]=previous;
                }
                previous=id;
            }
            g.last_machine_operation[m]=previous;
        }
        if(g.topological_sort().size()!=static_cast<size_t>(g.node_num))
            throw std::runtime_error("Seed machine orders create a cycle");
        current_schedule.calculate_time_info();
        current_schedule.update_critical_blocks();
        best_schedule=current_schedule;
        iteration=0;
        tabu_list=TabuList(M);
    }

protected:
    /**
     * Find the best available move in neighborhood"""
    patch(head,marker,init)
    bind=root/'src'/'python'/'bindings.cpp'
    patch(bind,'#include <pybind11/pybind11.h>','#include <pybind11/pybind11.h>\n#include <pybind11/stl.h>')
    patch(bind,'            .def("makespan", &TabuSearch::makespan)',
        '            .def("seed_machine_orders", &TabuSearch::seed_machine_orders)\n            .def("makespan", &TabuSearch::makespan)')
    print('INSTRUMENTED seed_machine_orders; original N7/tabu search unchanged')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--upstream',type=Path,required=True)
    main(p.parse_args().upstream)
