// ta41 machine-group longest-path interdiction, exhaustive over all 2^20 subsets.
// Compiles with standard C++17. No external solver or libraries.
// A free machine loses *all* 29 incumbent consecutive arcs. Job arcs remain.
// The resulting longest path is a necessary lower bound for any schedule
// retaining the incumbent order on every fixed machine.
#include <algorithm>
#include <array>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <limits>
#include <queue>
#include <stdexcept>
#include <vector>
using namespace std;
static constexpr int J=30,M=20,N=600;
struct Node {int duration, job_next, mach_next, machine;};
int main(int argc,char**argv) {
  if(argc!=3){cerr<<"usage: program input.txt result.json\n";return 2;}
  ifstream in(argv[1]);
  if(!in)throw runtime_error("missing input");
  int jobs,machines;in>>jobs>>machines;
  if(jobs!=J||machines!=M)throw runtime_error("bad dimensions");
  Node node[N];int pos[J][M];
  for(int j=0;j<J;j++){
    bool seen[M]={};
    for(int k=0;k<M;k++){
      int m,d;in>>m>>d;
      if(!in||m<0||m>=M||seen[m]||d<1)throw runtime_error("bad instance");
      seen[m]=true;pos[j][m]=j*M+k;
      node[j*M+k]={d,k+1<M?j*M+k+1:-1,-1,m};
    }
  }
  for(int m=0;m<M;m++){
    int old=-1;bool seen[J]={};
    for(int k=0;k<J;k++){
      int j;in>>j;
      if(!in||j<0||j>=J||seen[j])throw runtime_error("bad machine orders");
      seen[j]=true;
      int u=pos[j][m];
      if(old>=0)node[old].mach_next=u;
      old=u;
    }
  }
  // Because all subsequent graphs delete edges only, one baseline topological
  // order is valid for every one of the 1,048,576 masks.
  int indegree[N]={};
  for(int i=0;i<N;i++){
    if(node[i].job_next>=0)indegree[node[i].job_next]++;
    if(node[i].mach_next>=0)indegree[node[i].mach_next]++;
  }
  queue<int> q;for(int i=0;i<N;i++)if(!indegree[i])q.push(i);
  vector<int> order;
  while(!q.empty()){
    int u=q.front();q.pop();order.push_back(u);
    for(int v:{node[u].job_next,node[u].mach_next})
      if(v>=0&&--indegree[v]==0)q.push(v);
  }
  if(order.size()!=N)throw runtime_error("baseline cyclic");
  const auto lower_bound=[&](uint32_t freed)->int{
    int start[N]={};
    int total=0;
    for(int u:order){
      const Node& n=node[u];
      int fin=start[u]+n.duration;
      if(fin>total)total=fin;
      if(n.job_next>=0&&start[n.job_next]<fin)start[n.job_next]=fin;
      if(n.mach_next>=0&&!(freed&(1u<<n.machine))
         &&start[n.mach_next]<fin)start[n.mach_next]=fin;
    }
    return total;
  };
  if(lower_bound(0)!=2006)throw runtime_error("baseline != 2006");
  array<long long,21> below={};
  array<int,21> min_lb;
  min_lb.fill(numeric_limits<int>::max());
  array<uint32_t,21> witness={};
  int smallest=21;
  uint32_t first=0;
  for(uint32_t mask=0;mask<(1u<<M);mask++){
    int changed=__builtin_popcount(mask);
    int lb=lower_bound(mask);
    if(lb<min_lb[changed]){min_lb[changed]=lb;witness[changed]=mask;}
    if(lb<=2005){
      below[changed]++;
      if(changed<smallest){smallest=changed;first=mask;}
    }
  }
  ofstream out(argv[2]);
  if(!out)throw runtime_error("cannot write result");
  out<<"{\n\"instance\":\"ta41\",\"baseline\":2006,\"target\":2005,";
  out<<"\n\"complete_exhaustive_masks\":1048576,\n";
  out<<"\"interpretation\":\"Pure precedence longest-path relaxation: frees all machine arcs on selected groups; passing the bound is necessary but not sufficient for a feasible schedule\",\n";
  out<<"\"exact_minimum_free_machines_for_precedence_bound_2005\":"<<smallest<<",\n";
  out<<"\"first_passing_mask_decimal\":"<<first<<",\n";
  out<<"\"first_passing_free_machines\":[";
  bool sep=false;for(int m=0;m<M;m++)if(first&(1u<<m)){if(sep)out<<",";out<<m;sep=true;}
  out<<"],\n\"levels\":[\n";
  for(int i=0;i<=M;i++){
    if(i)out<<",\n";
    out<<"{\"free_machines\":"<<i<<",\"lowest_partial_order_longest_path\":"<<min_lb[i]
       <<",\"machine_subsets_with_bound_at_most_2005\":"<<below[i]
       <<",\"witness_mask_decimal\":"<<witness[i]<<"}";
  }
  out<<"\n]}\n";
  cout<<"FULL 2^20 mask evaluation complete; min groups to relax="
      <<smallest<<" ; first passing mask="<<first<<"\n";
}
