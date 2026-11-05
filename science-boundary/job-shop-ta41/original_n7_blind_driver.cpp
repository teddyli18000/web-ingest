// Published N7 search kernel (Ming Qi, 2025, AGPLv3), original source pinned.
// This driver only generalizes the prior ta41-specific warmstart checks.
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
        if(argc!=6)throw runtime_error("usage: native-n7 INSTANCE OUTPUT.csv SECONDS SEED MACHINE_ORDERS");
        string file=argv[1],output=argv[2];int secs=stoi(argv[3]),seed=stoi(argv[4]);
        if(secs<=0)throw runtime_error("must set seconds");
        Instance inst=load_instance(file);
        if(inst.job_num!=30||inst.operation_num!=20)throw runtime_error("wrong problem shape");
        RandomGenerator::instance().setSeed(seed);
        TabuSearch solver(inst);
        ifstream in(argv[5]);
        if(!in)throw runtime_error("initial machine sequence not found");
        vector<vector<int>> machine_jobs(20,vector<int>(30));
        for(auto&line:machine_jobs)for(int&j:line){in>>j;if(!in)throw runtime_error("incomplete order");}
        solver.load_verified_machine_orders(machine_jobs);
        if(solver.makespan()<=0)throw runtime_error("invalid initial schedule");
        cerr<<"N7 START "<<solver.makespan()<<"\n";
        auto start=chrono::steady_clock::now();
        auto stop=start+chrono::seconds(secs);
        solver.search(100000000ULL,[&]{return chrono::steady_clock::now()>=stop;});
        double duration=chrono::duration<double>(chrono::steady_clock::now()-start).count();
        solver.export_result(output.c_str());
        cout<<"RESULT "<<solver.makespan()<<" "<<solver.get_iter()<<" "<<duration<<"\n";
        return 0;
    }catch(const exception&e){cerr<<"ERROR "<<e.what()<<"\n";return 1;}
}
