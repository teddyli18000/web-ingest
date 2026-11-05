// Source-faithful published Ming Qi (2025) N7 tabu, random active constructor.
// Only the external driver prints a complete schedule after a fixed time cap;
// no ta41-specific score / early exit / incumbent is injected.
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
        if(argc!=5)throw runtime_error("usage: n7_cold instance output.csv SECONDS seed");
        int secs=stoi(argv[3]),seed=stoi(argv[4]);
        if(secs<1)throw runtime_error("positive seconds");
        Instance inst=load_instance(argv[1]);
        if(inst.job_num!=30 || inst.operation_num!=20)throw runtime_error("shape mismatch");
        RandomGenerator::instance().setSeed(seed);
        TabuSearch solver(inst);
        auto begin=chrono::steady_clock::now();
        auto stop=begin+chrono::seconds(secs);
        solver.search(100000000ULL,[&]{return chrono::steady_clock::now()>=stop;});
        solver.export_result(argv[2]);
        cout<<"RESULT "<<solver.makespan()<<" "<<solver.get_iter()
            <<" "<<chrono::duration<double>(chrono::steady_clock::now()-begin).count()<<"\n";
        return 0;
    }catch(const exception&e){cerr<<"ERROR "<<e.what()<<"\n";return 1;}
}
