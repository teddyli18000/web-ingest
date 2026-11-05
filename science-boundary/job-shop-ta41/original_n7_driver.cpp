// Thin standalone driver around the ORIGINAL AGPLv3 author's N7 tabu code.
// Original copyright (C) 2025 Ming Qi; implementation is fetched verbatim
// from https://github.com/Qiming01/Job-Shop-Scheduling at pinned commit.
// This driver is authored for benchmarking and does NOT change original
// algorithm, neighborhood, tenure or schedule generation.
#include "RandomGenerator.h"
#include "instance.h"
#include "tabu_search.h"
#include <chrono>
#include <iostream>
#include <stdexcept>
#include <string>
using namespace std;

int main(int argc,char**argv){
    try{
        if(argc!=5)throw runtime_error("usage: original_n7_driver INSTANCE OUT.csv SECONDS SEED");
        string file=argv[1],result=argv[2];
        int secs=stoi(argv[3]),seed=stoi(argv[4]);
        if(secs<=0)throw runtime_error("positive budget required");
        Instance inst=load_instance(file);
        if(inst.job_num!=30 || inst.operation_num!=20)
            throw runtime_error("shape mismatch");
        RandomGenerator::instance().setSeed(seed);
        TabuSearch solver(inst);
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
