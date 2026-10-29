// Exact recombination of two independently verified Cmax=2006 schedules.
// Every machine takes its entire permutation from parent A or parent B.
// All 30x20 job precedence arcs remain fixed. This enumerates the
// complete 2^d machine-level crossover cube, where d differing machine
// sequences; invalid cyclic graphs are rejected. Standard C++17 only.
#include <algorithm>
#include <array>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
using namespace std;
static constexpr int J=30, M=20, N=600;
int p[J][M],dur[N],parents[2][M][J];
int changed[M],d;
uint64_t checked,valid,cyclic,eq2006,better;
int best=100000000,first=100000000;
uint64_t bestmask=0;
int indeg[N],starttime[N],machine_succ[N],q[N];
int score(uint64_t mask) {
    for(int i=0;i<N;i++) {
        indeg[i]=(i%M!=0);
        starttime[i]=0;
        machine_succ[i]=-1;
    }
    int selected[M]={};
    for(int k=0;k<d;k++)selected[changed[k]]=(mask>>k)&1ULL;
    for(int m=0;m<M;m++){
        const int* order=parents[selected[m]][m];
        int prior=p[order[0]][m];
        for(int k=1;k<J;k++){
            int curr=p[order[k]][m];
            machine_succ[prior]=curr;
            ++indeg[curr];
            prior=curr;
        }
    }
    int head=0,tail=0;
    for(int i=0;i<N;i++)if(indeg[i]==0)q[tail++]=i;
    int done=0,C=0;
    while(head<tail){
        int u=q[head++];done++;
        int finish=starttime[u]+dur[u];
        if(finish>C)C=finish;
        int v=(u%M==M-1)?-1:u+1;
        if(v>=0){
            if(starttime[v]<finish)starttime[v]=finish;
            if(--indeg[v]==0)q[tail++]=v;
        }
        v=machine_succ[u];
        if(v>=0){
            if(starttime[v]<finish)starttime[v]=finish;
            if(--indeg[v]==0)q[tail++]=v;
        }
    }
    return done==N ? C : -1;
}
void write_certificate(const string& path,uint64_t mask) {
    ofstream f(path);
    if(!f)throw runtime_error("cannot open certificate");
    int choice[M]={};
    for(int k=0;k<d;k++)choice[changed[k]]=(mask>>k)&1ULL;
    f<<"{\"machines\":[";
    for(int m=0;m<M;m++){
        if(m)f<<",";
        f<<"[";
        for(int k=0;k<J;k++){
            if(k)f<<",";
            f<<parents[choice[m]][m][k];
        }
        f<<"]";
    }
    f<<"]}\n";
}
int main(int argc,char**argv){
    if(argc!=6)throw runtime_error("usage: crossover <input> <out_dir> <left> <right> <forced_machine>");
    string dir=argv[2],left=argv[3],right=argv[4]; int forcedmachine=std::stoi(argv[5]); if(forcedmachine<0||forcedmachine>=M)throw runtime_error("bad forced machine");
    ifstream f(argv[1]);
    if(!f)throw runtime_error("cannot read input");
    int n,m;f>>n>>m;
    if(n!=J||m!=M)throw runtime_error("instance dimensions differ");
    for(int j=0;j<J;j++){
        bool visited[M]={};
        for(int k=0;k<M;k++){
            int mach,t;f>>mach>>t;
            if(!f||mach<0||mach>=M||visited[mach]||t<1)throw runtime_error("bad instance");
            visited[mach]=true;
            p[j][mach]=j*M+k;dur[j*M+k]=t;
        }
    }
    for(int parent=0;parent<2;parent++){
        for(int mach=0;mach<M;mach++){
            bool seen[J]={};
            for(int k=0;k<J;k++){
                int j;f>>j;
                if(!f||j<0||j>=J||seen[j])throw runtime_error("bad machine order");
                seen[j]=true;parents[parent][mach][k]=j;
            }
        }
    }
    for(int m=0;m<M;m++){
        bool same=true;
        for(int k=0;k<J;k++)same&=(parents[0][m][k]==parents[1][m][k]);
        if(!same)changed[d++]=m;
    }
    if(score(0)<=2006 || score(0)>2500 || score((1ULL<<d)-1)!=2006)
        throw runtime_error("parent score mismatch vs independent baseline");
    const uint64_t total=1ULL<<d;
    for(uint64_t mask=0;mask<total;mask++){
        bool inherits=false;
        for(int x=0;x<d;x++)if(changed[x]==forcedmachine){inherits=((mask>>x)&1ULL)==0;break;}
        if(!inherits)continue;
        int C=score(mask);checked++;
        if(C<0){cyclic++;continue;}
        valid++;
        if(C==2006)eq2006++;
        if(C<2006)better++;
        if(C<best){best=C;bestmask=mask;}
        if(C<first)first=C;
    }
    if(checked*2!=total || valid+cyclic!=checked)
        throw runtime_error("enumeration incomplete");
    if(best<=2005)write_certificate(dir+"/certificate.json",bestmask);
    write_certificate(dir+"/best-machine-order-certificate.json",bestmask);
    ofstream out(dir+"/crossover-analysis.json");
    if(!out)throw runtime_error("cannot write report");
    out<<"{\n\"instance\":\"ta41\",\"left_parent\":\""<<left
       <<"\",\"right_parent\":\""<<right<<"\",\n";
    out<<"\"machine_groups_differing_between_parents\":"<<d<<",\n";
    out<<"\"forced_machine_from_reversal_parent\":"<<forcedmachine<<",\n";
    out<<"\"all_possible_machine_choices\":"<<total<<",\n";
    out<<"\"candidate_crossover_masks_exhaustively_evaluated\":"<<checked<<",\n";
    out<<"\"feasible_acyclic_permutations\":"<<valid<<",\n";
    out<<"\"cyclic_permutations\":"<<cyclic<<",\n";
    out<<"\"makespan_equal_2006\":"<<eq2006<<",\n";
    out<<"\"makespan_below_2006\":"<<better<<",\n";
    out<<"\"best_makespan\":"<<best<<",\n";
    out<<"\"best_crossover_mask\":"<<bestmask<<",\n";
    out<<"\"scope\":\"All 2^(d-1) crossover masks inheriting the forced reverse machine from a verified 2024-plus schedule and all other machines from one of two parents; complete only for this finite restricted crossover\"\n}\n";
    cout<<"RESULT parents="<<left<<","<<right<<" groups="<<d
        <<" masks="<<checked<<" valid="<<valid<<" cycles="<<cyclic
        <<" equal2006="<<eq2006<<" better="<<better
        <<" BEST="<<best<<" mask="<<bestmask<<"\n";
    return 0;
}
