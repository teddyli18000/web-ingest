// Thin standalone driver around the ORIGINAL AGPLv3 author's N7 tabu code.
// Original copyright (C) 2025 Ming Qi; implementation is fetched verbatim
// from https://github.com/Qiming01/Job-Shop-Scheduling at pinned commit.
// This driver is authored for benchmarking and does NOT change original
// algorithm, neighborhood, tenure or schedule generation.
#include "RandomGenerator.h"
#include "instance.h"
#include "tabu_search.h"
#include <chrono>
#include <fstream>
#include <vector>
#include <iostream>
#include <stdexcept>
#include <string>
using namespace std;

int main(int argc,char**argv){
    try{
        if(argc!=5&&argc!=6)throw runtime_error("usage: original_n7_driver INSTANCE OUT.csv SECONDS SEED [verified-machine-orders-file]");
        string file=argv[1],result=argv[2];
        int secs=stoi(argv[3]),seed=stoi(argv[4]);
        if(secs<=0)throw runtime_error("positive budget required");
        Instance inst=load_instance(file);
        if(inst.job_num!=30 || inst.operation_num!=20)
            throw runtime_error("shape mismatch");
        RandomGenerator::instance().setSeed(seed);
        TabuSearch solver(inst);
        if(argc==6){
            ifstream in(argv[5]);
            if(!in)throw runtime_error("missing verified machine orders");
            vector<vector<int>> machine_jobs(20,vector<int>(30));
            for(auto &row:machine_jobs)for(int &job:row){
                in>>job;
                if(!in)throw runtime_error("truncated machine orders");
            }
            solver.load_verified_machine_orders(machine_jobs);
            if(solver.makespan()!=2006)
                throw runtime_error("native warmstart did not reproduce 2006");
            cerr<<"BOOTSTRAP original N7 search from verified 2006 C++ DAG\n";
        }
        auto begin=chrono::steady_clock::now();
        auto stop=begin+chrono::seconds(secs);
        solver.search(100000000ULL,[&]{
            return solver.makespan()<=2005 || chrono::steady_clock::now()>=stop;
        });
        auto elapsed=chrono::duration<double>(
            chrono::steady_clock::now()-begin).count();
        solver.export_result(result.c_str());
        cout<<"RESULT "<<solver.makespan()<<" "<<solver.get_iter()
            <<" "<<elapsed<<"\n";
        return 0;
    }catch(const exception&e){cerr<<"ERROR "<<e.what()<<"\n";return 1;}
}
