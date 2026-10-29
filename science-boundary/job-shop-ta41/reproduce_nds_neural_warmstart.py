#!/usr/bin/env python3
"""Evaluate upstream pretrained NDS-S on an *officially seeded* ta41=2006.

Crucial fair comparison: the author's standard evaluator begins from a
random activity list. This harness leaves its model, stochastic deconstruction
policy, C++ reconstruction operator, and Search.run() unchanged, but injects
the independently verified 2006 native activity list at initialization.

It evaluates a pre-trained jssp30x20 checkpoint as *improvement* method,
not as a cold-start heuristic. Postprocess solutions.csv separately via
verify_nds_neural_output.py and Few Shots official verifier.
"""
import argparse
import random
import sys
from pathlib import Path
import numpy as np

TOPIC=Path(__file__).resolve().parent
sys.path.insert(0,str(TOPIC))
from search import obtain,setup,evaluate
from structural_cut import disjunctive_dag
from reproduce_nds_cpp import data_validation

def run(a):
    random.seed(a.seed)
    np.random.seed(a.seed)
    import torch
    torch.manual_seed(a.seed)
    torch.set_num_threads(2)
    from omegaconf import OmegaConf
    from ndss.src import create_logger
    from ndss.src.search_lns import Search
    from ndss.src.cpp.jssp import JSSP

    routes,rows,baseline=obtain()
    pos,dur=setup(routes,rows)
    assert evaluate(baseline,pos,dur)==2006
    data_validation(a.nds_repo,routes,rows)
    _,_,topo,_,_,C=disjunctive_dag(baseline,pos,dur,set())
    assert C==2006
    order=[u//20 for u in topo]

    cfg=OmegaConf.load(a.nds_repo/'ndss'/'configs'/'eval'/'jssp.yaml')
    cfg.env_params.num_jobs=30
    cfg.env_params.num_machines=20
    cfg.env_params.num_nodes_to_remove=a.q
    cfg.env_params.recreate_n=a.recreate
    cfg.tester_params.use_cuda=False
    cfg.tester_params.model_load[0].path=str(a.nds_repo/'models'/'jssp30x20')
    cfg.tester_params.model_load[0].epoch=1000
    cfg.tester_params.model_load[0].node_to_remove=a.q
    cfg.tester_params.test_data_load.filename=str(next((a.nds_repo/'data'/'jssp').glob('*__ta41__*.csv')))
    cfg.tester_params.test_episodes=1
    cfg.tester_params.test_batch_size=1
    cfg.tester_params.max_runtime=a.seconds
    cfg.tester_params.rollout_size=a.rollouts
    cfg.tester_params.aug_factor=1
    cfg.logger_params.desc=''
    cfg.logger_params.filepath=str(a.out)
    a.out.mkdir(parents=True,exist_ok=True)
    create_logger(cfg.logger_params)
    search=Search(cfg.env_params,cfg.tester_params)
    original_init=search.env.instanceSet.init_instances

    def inject_official_schedule(problem_data):
        original_init(problem_data)
        assert len(search.env.instanceSet._instances)==1
        native_instance=search.env.instanceSet._instances[0]
        solution=JSSP.Solution(native_instance)
        solution.activityList=order
        solution.schedule(False)
        assert solution.getMakespan()==2006,solution.getMakespan()
        search.env.instanceSet.set_solution(0,solution)
        print('OFFICIAL-2006-SEEDED',solution.getMakespan(),flush=True)

    search.env.instanceSet.init_instances=inject_official_schedule
    search.run()

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--nds-repo',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--seed',type=int,default=4107)
    p.add_argument('--q',type=int,default=10)
    p.add_argument('--recreate',type=int,default=5)
    p.add_argument('--rollouts',type=int,default=8)
    p.add_argument('--seconds',type=int,default=120)
    run(p.parse_args())
