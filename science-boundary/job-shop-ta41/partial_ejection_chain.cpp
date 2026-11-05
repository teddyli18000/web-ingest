// Partial-schedule ejection-chain solver for 30x20 Taillard instances.
// Contrast: dynamic NEW critical-path ejections, static INITIAL path focus,
// random. All complete schedules are independently rescored in Python.
// This is a new experimental implementation inspired by Nagata/Ono IEBO,
// not a reproduction of their dynamic programming enumerator.
#include <algorithm>
#include <array>
#include <cassert>
#include <chrono>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <limits>
#include <numeric>
#include <random>
#include <set>
#include <stdexcept>
#include <string>
#include <unordered_set>
#include <vector>
using namespace std;
constexpr int J=30,M=20,N=600;
struct Problem{
    int pos[J][M]{};
    int dur[N]{};
    int opMachine[N]{};
    array<vector<int>,M> initial;
};
struct State{
    array<vector<int>,M> machines;
    vector<int> pool;
};
struct Evaluation{
    int cmax=-1;
    vector<int> path;
    int machineLinks=0;
};
struct Candidate{
    State state;
    int lb=-1;
    int replaced=0;
    int extra_ejections=0;
    uint64_t hash=0;
};
struct Stats {
    long long evaluated=0,acyclic=0,overlimit=0,unacceptable=0;
    long long accepted=0,ejections=0,complete=0;
    long long newly_critical_ejection_candidates=0;
    int best=-1,restarts=0,maxpool=0;
};
static mt19937_64 rng;
Problem read(const string &path){
    ifstream in(path);
    if(!in)throw runtime_error("bad input "+path);
    int n,m;in>>n>>m;
    if(n!=J||m!=M)throw runtime_error("must be 30x20");
    Problem p;
    for(int j=0;j<J;j++){
        array<int,M> seen{};
        for(int k=0;k<M;k++){
            int machine,duration;in>>machine>>duration;
            if(!in||machine<0||machine>=M||seen[machine]++||duration<1)
                throw runtime_error("bad route");
            int op=j*M+k;
            p.pos[j][machine]=op;
            p.dur[op]=duration;
            p.opMachine[op]=machine;
        }
    }
    for(int m=0;m<M;m++){
        array<int,J> seen{};
        for(int k=0;k<J;k++){
            int j;in>>j;
            if(!in||j<0||j>=J||seen[j]++)
                throw runtime_error("bad start permutation");
            p.initial[m].push_back(j);
        }
    }
    int garbage;
    if(in>>garbage)throw runtime_error("extra input");
    return p;
}
uint64_t stateHash(const State& s,const Problem&p) {
    uint64_t h=1469598103934665603ULL;
    for(int m=0;m<M;m++){
        h=(h^static_cast<uint64_t>(m+2048))*1099511628211ULL;
        for(int job:s.machines[m])
            h=(h^static_cast<uint64_t>(job+1))*1099511628211ULL;
    }
    return h;
}
int partialCount(const State&s){
    int result=0;
    for(const auto &seq:s.machines)result+=int(seq.size());
    return N-result;
}
Evaluation evaluate(const State& state,const Problem& prob,Stats*stats=nullptr){
    if(stats) stats->evaluated++;
    array<int,N> indegree{},head{},pred{},machinePred{},machineSucc{};
    pred.fill(-1);machinePred.fill(-1);machineSucc.fill(-1);
    for(int i=0;i<N;i++) indegree[i]=(i%M!=0);
    int assigned=0;
    for(int m=0;m<M;m++){
        int last=-1;
        for(int job:state.machines[m]){
            int op=prob.pos[job][m];
            assigned++;
            if(last>=0){
                if(machinePred[op]>=0||machineSucc[last]>=0)
                    throw runtime_error("invalid machine order");
                machinePred[op]=last;machineSucc[last]=op;indegree[op]++;
            }
            last=op;
        }
    }
    if(assigned+int(state.pool.size())!=N)
        throw runtime_error("partial schedule lost operation");
    array<int,N> ready{};
    int qhead=0,qtail=0;
    for(int i=0;i<N;i++)if(indegree[i]==0)ready[qtail++]=i;
    int processed=0,maximum=0,last=-1;
    while(qhead<qtail){
        int u=ready[qhead++];processed++;
        int finish=head[u]+prob.dur[u];
        if(finish>maximum){maximum=finish;last=u;}
        int successors[2]={u%M==M-1?-1:u+1,machineSucc[u]};
        for(int v:successors){
            if(v<0)continue;
            if(finish>head[v]){head[v]=finish;pred[v]=u;}
            if(--indegree[v]==0)ready[qtail++]=v;
        }
    }
    if(processed!=N) return Evaluation{};
    if(stats)stats->acyclic++;
    Evaluation out;out.cmax=maximum;
    for(int u=last;u>=0;u=pred[u])out.path.push_back(u);
    reverse(out.path.begin(),out.path.end());
    for(size_t i=1;i<out.path.size();i++)
        out.machineLinks+=(machinePred[out.path[i]]==out.path[i-1]);
    return out;
}
bool ejected(const State&s,int op,const Problem&p) {
    return find(s.pool.begin(),s.pool.end(),op)!=s.pool.end();
}
bool removeOperation(State &s,int op,const Problem&p) {
    int m=p.opMachine[op];int job=op/M;
    auto&seq=s.machines[m];
    auto it=find(seq.begin(),seq.end(),job);
    if(it==seq.end())return false;
    seq.erase(it);s.pool.push_back(op);
    return true;
}
bool insertOperation(State&s,int op,int k,const Problem&p){
    int m=p.opMachine[op];int job=op/M;
    auto it=find(s.pool.begin(),s.pool.end(),op);
    if(it==s.pool.end())return false;
    s.pool.erase(it);
    auto&seq=s.machines[m];
    if(k<0||k>int(seq.size()))throw runtime_error("invalid insert index");
    seq.insert(seq.begin()+k,job);
    return true;
}
vector<int> ejectionCandidates(const State&s,const Evaluation& eval,
    const Problem& p,const vector<int>& initialPath, int inserted,
    const string& policy,int limit) {
    // Candidate pool combines actual new critical machine-link endpoints
    // and original critical path endpoints. Only the policy chooses priority.
    set<int> newCritical;
    if(eval.path.size()>1){
        array<int,N> prevMachine{};prevMachine.fill(-1);
        for(int m=0;m<M;m++){
            int prev=-1;
            for(int j:s.machines[m]){
                int op=p.pos[j][m];prevMachine[op]=prev;prev=op;
            }
        }
        for(size_t k=1;k<eval.path.size();k++){
            int u=eval.path[k-1],v=eval.path[k];
            if(prevMachine[v]==u){newCritical.insert(u);newCritical.insert(v);}
        }
    }
    set<int> pool=newCritical;
    set<int> staticCritical(initialPath.begin(),initialPath.end());
    for(int u:initialPath)pool.insert(u);
    // Also use target insertion's machine neighbors: replacement conflicts
    // may be induced by a new edge with a noncritical endpoint.
    int im=p.opMachine[inserted];const auto&seq=s.machines[im];
    for(int k=0;k<int(seq.size());k++)
        if(p.pos[seq[k]][im]==inserted) {
            if(k>0)pool.insert(p.pos[seq[k-1]][im]);
            if(k+1<int(seq.size()))pool.insert(p.pos[seq[k+1]][im]);
        }
    vector<pair<double,int>> ranking;
    for(int op:pool){
        if(op==inserted||ejected(s,op,p))continue;
        bool onNew=newCritical.count(op)>0;
        bool onOld=staticCritical.count(op)>0;
        double bias=0;
        if(policy=="dynamic") bias=onNew*10.0+(onOld?1.0:0.0);
        if(policy=="static")bias=onOld*10.0+onNew*0.01;
        // random policy ignores structural priorities
        double noise=uniform_real_distribution<double>(0,1)(rng);
        ranking.push_back({bias+noise,op});
    }
    sort(ranking.begin(),ranking.end(),[](auto a,auto b){return a.first>b.first;});
    vector<int> chosen;
    for(auto [score,op]:ranking){
        if(int(chosen.size())>=limit)break;
        chosen.push_back(op);
    }
    // Ensure enough choices even for small critical paths without
    // invoking any target schedule or hidden oracle.
    for(int attempt=0;chosen.size()<size_t(limit)&&attempt<80;attempt++){
        int op=int(rng()%N);
        if(op==inserted||ejected(s,op,p)||
           find(chosen.begin(),chosen.end(),op)!=chosen.end())continue;
        chosen.push_back(op);
    }
    return chosen;
}
bool samePool(const State &a,const State &b) {
    return a.pool.size()==b.pool.size();
}
int main(int argc,char**argv){
    try{
        if(argc!=8) throw runtime_error(
          "usage: ejection INPUT OUTPUT POLICY SEED DAG_BUDGET MAX_POOL RESTART_EVALS");
        string policy=argv[3];
        if(policy!="dynamic"&&policy!="static"&&policy!="random")
            throw runtime_error("invalid policy");
        uint64_t seed=stoull(argv[4]);rng.seed(seed);
        long long budget=stoll(argv[5]);
        int maxPool=stoi(argv[6]);long long restartEvals=stoll(argv[7]);
        Problem p=read(argv[1]);
        State baseline;baseline.machines=p.initial;
        Stats stats;
        Evaluation v=evaluate(baseline,p,&stats);
        if(v.cmax<=0)throw runtime_error("input cyclic");
        int initial=v.cmax;
        int target=initial-1;
        int best=initial;
        State bestState=baseline;
        vector<int> initialPath=v.path;
        bool found=false;
        auto start=chrono::steady_clock::now();
        auto seedState=[&]()->State{
            State s=baseline;
            // Deliberately visit 1..4 simultaneous unscheduled operations.
            // A strict one-in/one-out state graph never escaped pool=1.
            int seedTarget=min(maxPool,1+(stats.restarts%4));
            for(int step=0;step<maxPool;step++){
                Evaluation ev=evaluate(s,p,&stats);
                if(ev.cmax<=target&&step>=seedTarget)break;
                vector<int> pool;
                for(int u:ev.path){
                    if(!ejected(s,u,p))pool.push_back(u);
                }
                if(pool.empty())break;
                // Greedy one-operation destructive ejection minimizing the
                // precompletion DAG critical lower bound.
                vector<pair<int,int>> scored;
                shuffle(pool.begin(),pool.end(),rng);
                for(int u:pool){
                    if(stats.evaluated>=budget)break;
                    State candidate=s;
                    if(!removeOperation(candidate,u,p))continue;
                    Evaluation after=evaluate(candidate,p,&stats);
                    if(after.cmax>=0)scored.push_back({after.cmax,u});
                }
                if(scored.empty())break;
                sort(scored.begin(),scored.end());
                int n=min(6,int(scored.size()));
                int choice=int(rng()%n);
                // Prefer strong reduction in deadline violation.
                if(step>1||rng()%4!=0)choice=0;
                removeOperation(s,scored[choice].second,p);
            }
            return s;
        };
        State state=seedState();
        Evaluation now=evaluate(state,p,&stats);
        int initialReleased=partialCount(state);
        if(now.cmax>target)throw runtime_error("initial partial lower bound cannot be reduced within pool cap");
        unordered_set<uint64_t> visited;
        visited.insert(stateHash(state,p));
        long long restartAt=stats.evaluated+restartEvals;
        int poolReductionStall=0;
        while(stats.evaluated<budget){
            if(state.pool.empty()){
                Evaluation full=evaluate(state,p,&stats);
                if(full.cmax>=0&&full.cmax<best){
                    best=full.cmax;bestState=state;found=true;break;
                }
                stats.complete++;
                state=seedState();now=evaluate(state,p,&stats);
                visited.clear();visited.insert(stateHash(state,p));
                stats.restarts++;poolReductionStall=0;restartAt=stats.evaluated+restartEvals;
                continue;
            }
            if(stats.evaluated>restartAt){
                state=seedState();now=evaluate(state,p,&stats);
                visited.clear();visited.insert(stateHash(state,p));
                stats.restarts++;restartAt=stats.evaluated+restartEvals;
                continue;
            }
            stats.maxpool=max(stats.maxpool,partialCount(state));
            int x=state.pool[rng()%state.pool.size()];
            int m=p.opMachine[x];
            vector<Candidate> proposals;
            int choices=int(state.machines[m].size())+1;
            for(int position=0;position<choices&&stats.evaluated<budget;position++){
                State inserted=state;
                if(!insertOperation(inserted,x,position,p))throw runtime_error("not in pool");
                Evaluation after=evaluate(inserted,p,&stats);
                if(after.cmax<0)continue;
                if(after.cmax<=target){
                    Candidate cand{move(inserted),after.cmax,0,0,0};
                    cand.hash=stateHash(cand.state,p);
                    if(!visited.count(cand.hash))proposals.push_back(move(cand));
                    continue;
                }
                stats.overlimit++;
                // Analyze NEW deadline-breaking path created by insertion,
                // then consider ejection of one conflicting scheduled op.
                vector<int> eligible=ejectionCandidates(inserted,after,p,
                    initialPath,x,policy,8);
                for(int y:eligible){
                    if(stats.evaluated>=budget)break;
                    State repaired=inserted;
                    if(!removeOperation(repaired,y,p))continue;
                    Evaluation er=evaluate(repaired,p,&stats);
                    if(er.cmax<0)continue;
                    if(er.cmax<=target){
                        Candidate cand{repaired,er.cmax,
                            int(find(initialPath.begin(),initialPath.end(),y)==initialPath.end()),
                            1,0};
                        cand.hash=stateHash(cand.state,p);
                        if(!visited.count(cand.hash))proposals.push_back(move(cand));
                    }
                    // Allow TWO jointly coordinated ejections before
                    // completing another insertion. This qualitatively
                    // extends the original pool=1 lateral move graph.
                    if(int(repaired.pool.size())>=maxPool)continue;
                    vector<int> additional=ejectionCandidates(repaired,er,p,
                        initialPath,x,policy,6);
                    for(int z:additional){
                        if(stats.evaluated>=budget)break;
                        State twice=repaired;
                        if(!removeOperation(twice,z,p))continue;
                        Evaluation ez=evaluate(twice,p,&stats);
                        if(ez.cmax<0||ez.cmax>target)continue;
                        Candidate cand{move(twice),ez.cmax,
                            int(find(initialPath.begin(),initialPath.end(),z)==initialPath.end()),
                            2,0};
                        cand.hash=stateHash(cand.state,p);
                        if(!visited.count(cand.hash))proposals.push_back(move(cand));
                    }
                }
            }
            if(proposals.empty()){
                stats.unacceptable++;
                // Changing pool operation changes which coordinated
                // insertion is attempted on the next step; stalled states
                // are periodically restarted, not silently marked UNSAT.
                if(stats.unacceptable%11==0){
                    state=seedState();now=evaluate(state,p,&stats);
                    visited.clear();visited.insert(stateHash(state,p));
                    stats.restarts++;restartAt=stats.evaluated+restartEvals;
                }
                continue;
            }
            // Prefer a strictly smaller unscheduled pool; for lateral
            // transitions, choose extra slack and novel critical paths.
            sort(proposals.begin(),proposals.end(),[](const Candidate&a,const Candidate&b){
                if(a.state.pool.size()!=b.state.pool.size())
                    return a.state.pool.size()<b.state.pool.size();
                if(a.lb!=b.lb)return a.lb<b.lb;
                return a.replaced>b.replaced;
            });
            int pick=0;
            int oldPool=int(state.pool.size());
            // When lateral ejections stall, occasionally enlarge the
            // unscheduled set instead of accepting another one-for-one
            // operation replacement. Otherwise prefer shrinking it.
            vector<int> growth;
            for(int i=0;i<int(proposals.size());i++)
                if(int(proposals[i].state.pool.size())>oldPool)
                    growth.push_back(i);
            if(!growth.empty()&&poolReductionStall>=8&&rng()%5!=0)
                pick=growth[rng()%min(size_t(5),growth.size())];
            else if(proposals.size()>1&&rng()%7==0)
                pick=int(rng()%min(size_t(4),proposals.size()));
            int nextPool=int(proposals[pick].state.pool.size());
            if(nextPool<oldPool)poolReductionStall=0;
            else poolReductionStall++;
            State next=move(proposals[pick].state);
            stats.ejections+=proposals[pick].extra_ejections;
            if(proposals[pick].replaced)
                stats.newly_critical_ejection_candidates++;
            state=move(next);
            now=evaluate(state,p,&stats);
            if(now.cmax<0||now.cmax>target)
                throw runtime_error("accepted an infeasible partial state");
            visited.insert(stateHash(state,p));
            stats.accepted++;
            if(state.pool.empty()){
                if(now.cmax<best){best=now.cmax;bestState=state;found=true;break;}
                stats.complete++;
            }
        }
        Evaluation finalEval=evaluate(bestState,p,&stats);
        if(finalEval.cmax!=best||partialCount(bestState)!=0)
            throw runtime_error("invalid best schedule");
        ofstream out(argv[2]);
        if(!out)throw runtime_error("cannot write result");
        out<<best<<" "<<stats.evaluated<<" "<<stats.accepted<<" "<<stats.ejections
           <<" "<<stats.complete<<" "<<stats.restarts<<" "<<stats.maxpool
           <<" "<<stats.newly_critical_ejection_candidates<<" "<<initialReleased
           <<" "<<chrono::duration<double>(chrono::steady_clock::now()-start).count()
           <<" "<<(found?1:0)<<"\n";
        for(int m=0;m<M;m++){
            if(bestState.machines[m].size()!=30)
                throw runtime_error("incomplete output");
            for(int j:bestState.machines[m])out<<j<<" ";
            out<<"\n";
        }
        cout<<"RESULT "<<policy<<" "<<initial<<" "<<best<<" "
            <<stats.evaluated<<" "<<stats.accepted<<" "<<stats.restarts
            <<" "<<stats.maxpool<<" "<<(found?1:0)<<"\n";
        return 0;
    }catch(const exception&e){
        cerr<<"ERROR "<<e.what()<<"\n";return 1;
    }
}
