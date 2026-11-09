// Reproducible FIXED-ITERATION reference driver for original author N7 tabu.
//
// Source pin: Qiming01/Job-Shop-Scheduling@7e120ebada21cb604c871e0657814bf6e32611f8.
// The source find_move/make_move/tabu/approximate_evaluation is unchanged.
// Only the external driver uses fixed search iterations rather than a
// timing-dependent condition; warmstart method is the audited AGPLv3
// source-compatible adapter.
#include "RandomGenerator.h"
#include "instance.h"
#include "tabu_search.h"
#include <chrono>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>
using namespace std;
int main(int argc,char**argv){
 try{
  if(argc!=6)throw runtime_error("usage: native-n7 INSTANCE OUTPUT.csv ITERATIONS SEED MACHINE_ORDERS");
  string instance_file=argv[1],out=argv[2];
  unsigned long long iteration_limit=stoull(argv[3]);
  int seed=stoi(argv[4]);
  if(iteration_limit<1||iteration_limit>100000000ULL)throw runtime_error("iterations out of range");
  Instance instance=load_instance(instance_file);
  if(instance.job_num!=30||instance.operation_num!=20)throw runtime_error("requires 30x20");
  RandomGenerator::instance().setSeed(seed);
  TabuSearch solver(instance);
  ifstream in(argv[5]);
  if(!in)throw runtime_error("missing initial full machine order");
  vector<vector<int>> machine_jobs(20,vector<int>(30));
  for(auto &line:machine_jobs)for(int &job:line){
   in>>job;if(!in)throw runtime_error("invalid machine permutation file");
  }
  solver.load_verified_machine_orders(machine_jobs);
  int oldscore=solver.makespan();
  if(oldscore<=0)throw runtime_error("invalid starting schedule");
  auto began=chrono::steady_clock::now();
  solver.search(iteration_limit);
  double secs=chrono::duration<double>(chrono::steady_clock::now()-began).count();
  solver.export_result(out.c_str());
  cout<<"RESULT "<<solver.makespan()<<" "<<solver.get_iter()<<" "<<secs
      <<" "<<oldscore<<" "<<iteration_limit<<"\n";
  return 0;
 }catch(const exception&e){
  cerr<<"ERROR "<<e.what()<<"\n";return 1;
 }
}
