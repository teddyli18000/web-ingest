// Elite path relinking with conditional replacement-critical-path prediction.
// 2026 Diaz-style elite path relinking motivates the comparison, but this is
// original code, not an exact reproduction of Diaz's proprietary implementation.
//
// Two constructive policies with the SAME full DAG evaluator and 2006 parents:
// greedy: target-directed adjacent swaps, choose the best feasible next swap.
// dynamic2: shortlist target-directed swaps, inspect newly critical resource
// arcs, and evaluate coordinated second target-directed swaps that attack them.
// Both can cross temporary uphill states; every output is an acyclic full
// disjunctive graph and must pass independent Python/Few Shots verification.
#define CASCADE_LIB
#include "predictive_cascade_search.cpp"

static long long pair_evals=0, paired_steps=0, relink_runs=0, completed_paths=0;
static long long cyclic_deadends=0, focus_hits=0, neutral_states=0;
static double max_peak=2006;
static constexpr int MAX_POOL=64;
static unordered_set<uint64_t> visited;
static vector<Schedule> parents;

static int dist_to(const Schedule&a,const Schedule&target){
    int ans=0;
    for(int m=0;m<MACH;m++){
        array<int,30> rank{};
        for(int k=0;k<30;k++)rank[target.at(m,k)]=k;
        for(int i=0;i<30;i++)for(int j=i+1;j<30;j++)
            if(rank[a.at(m,i)]>rank[a.at(m,j)])ans++;
    }
    return ans;
}
static vector<Move> towards(const Schedule&s,const Schedule&target){
    vector<Move>out;
    for(int m=0;m<MACH;m++){
        array<int,30> rank{};
        for(int k=0;k<30;k++)rank[target.at(m,k)]=k;
        for(int k=0;k<29;k++)
            if(rank[s.at(m,k)]>rank[s.at(m,k+1)])out.push_back({m,k,k+1});
    }
    return out;
}
static void read_pool(const string&file){
    Schedule first;
    read_input(file,first);
    parents.push_back(first);
    ifstream f(file);
    int n,m;f>>n>>m;
    if(n!=30||m!=20)throw runtime_error("bad pool dimensions");
    int trash=0;
    for(int i=0;i<1200+600;i++){f>>trash;if(!f)throw runtime_error("truncated seed pool");}
    int additional=0;f>>additional;
    if(additional<=0||additional>30)throw runtime_error("need 1-30 additional verified seeds");
    for(int p=0;p<additional;p++){
        Schedule s;
        for(int i=0;i<600;i++){f>>s.order[i];if(!f)throw runtime_error("bad seed schedule");}
        parents.push_back(s);
    }
    for(auto&s:parents){
        if(evaluate(s).score!=2006)throw runtime_error("seed is not feasible 2006");
        visited.insert(hash_schedule(s));
    }
}
static void note_solution(const Schedule&s,int score,Schedule&best,int&best_score){
    if(score<0)return;
    if(score<best_score){
        best=s;best_score=score;
        cerr<<"BEST path relink "<<score<<" evaluations="<<evaluations<<"\n";
    }
    if(score==2006){
        auto hash=hash_schedule(s);
        if(visited.insert(hash).second){
            neutral_states++;
            if(parents.size()<MAX_POOL)parents.push_back(s);
            else if(u01()<0.08)
                parents[8+uni(int(parents.size())-8)]=s;
        }
    }
}
static int overlapping_focus(Move m,const Schedule&s,const unordered_set<int>&focus){
    int quality=0,jobA=s.at(m.m,m.i),jobB=s.at(m.m,m.j);
    for(int x:focus){
        if(x/900!=m.m)continue;
        quality++;
        int a=(x%900)/30,b=x%30;
        if(a==jobA||b==jobA||a==jobB||b==jobB)quality+=3;
    }
    return quality;
}
struct RelinkResult {
    Schedule best{};
    int score=2006;
    long long total_relinked_kendall=0;
    int maximum_elite_distance=0;
};
static RelinkResult relink(long long budget,const string&policy){
    RelinkResult R;R.best=parents[0];
    int consecutive_bad=0;
    while(evaluations<budget && R.score>2005){
        if(parents.size()<2)break;
        // Repeated elite relinking, preserving original verified parents.
        int i=uni(int(parents.size())),j=uni(int(parents.size()));
        for(int attempts=0;attempts<20 && (j==i || dist_to(parents[i],parents[j])<12);attempts++)
            j=uni(int(parents.size()));
        if(j==i)continue;
        Schedule cur=parents[i],target=parents[j];
        int distance=dist_to(cur,target);
        if(distance<1)continue;
        R.maximum_elite_distance=max(R.maximum_elite_distance,distance);
        R.total_relinked_kendall+=distance;
        relink_runs++;
        bool dead=false;
        int steps=0;
        while(distance>0 && evaluations<budget && R.score>2005){
            G current=evaluate(cur,true);
            auto moves=towards(cur,target);
            if(moves.empty())throw runtime_error("target moves empty at positive distance");
            Move chosen{-1,-1,-1},chosen2{-1,-1,-1};
            int bestMoveScore=INT_MAX,bestStageScore=INT_MAX,bestFocus=-1;
            if(policy=="greedy"){
                random_cap(moves,200);
                for(Move m:moves){
                    if(evaluations>=budget)break;
                    insert_move(cur,m);G g;
                    int score=score_candidate(cur,false,g);
                    note_solution(cur,score,R.best,R.score);
                    insert_move(cur,{m.m,m.j,m.i});
                    if(score<0)continue;
                    if(score<bestMoveScore || (score==bestMoveScore&&u01()<0.25)){
                        bestMoveScore=score;chosen=m;
                    }
                    if(R.score<=2005)break;
                }
            }else{
                random_cap(moves,12);
                auto oldcrit=critset(cur,current);
                for(Move first:moves){
                    if(evaluations>=budget)break;
                    insert_move(cur,first);
                    G intermediate;int mid=score_candidate(cur,true,intermediate);
                    note_solution(cur,mid,R.best,R.score);
                    if(mid>0){
                        auto fresh=delta_critical(cur,intermediate,oldcrit);
                        auto second=towards(cur,target);
                        if(!fresh.empty()){
                            stable_sort(second.begin(),second.end(),[&](Move&a,Move&b){
                                return overlapping_focus(a,cur,fresh)>overlapping_focus(b,cur,fresh);
                            });
                        }
                        // 12 prioritized newly critical/resource-conflicting
                        // moves, with exploration among the remaining pool.
                        if(second.size()>18){
                            vector<Move> chosenSecond(second.begin(),second.begin()+12);
                            vector<Move> rest(second.begin()+12,second.end());
                            random_cap(rest,6);
                            chosenSecond.insert(chosenSecond.end(),rest.begin(),rest.end());
                            second.swap(chosenSecond);
                        }
                        // A one-inversion remainder has no eligible second
                        // target-directed swap. Do not label a legal final
                        // step as a blocked path merely because the macro
                        // cannot have depth two.
                        if(second.empty() && mid<bestMoveScore){
                            bestMoveScore=mid;bestStageScore=mid;
                            bestFocus=0;chosen=first;chosen2={-1,-1,-1};
                        }
                        for(Move secondMove:second){
                            if(evaluations>=budget)break;
                            int hit=overlapping_focus(secondMove,cur,fresh);
                            insert_move(cur,secondMove);
                            G g;int val=score_candidate(cur,false,g);
                            note_solution(cur,val,R.best,R.score);
                            insert_move(cur,{secondMove.m,secondMove.j,secondMove.i});
                            if(val<0)continue;
                            // Makespan first, predicted resource-replacement
                            // overlap as a tie breaker, never as a fake score.
                            if(val<bestMoveScore || (val==bestMoveScore&&hit>bestFocus) ||
                               (val==bestMoveScore&&hit==bestFocus&&u01()<0.10)){
                                bestMoveScore=val;bestStageScore=mid;
                                bestFocus=hit;chosen=first;chosen2=secondMove;
                            }
                            if(R.score<=2005)break;
                        }
                    }
                    insert_move(cur,{first.m,first.j,first.i});
                    if(R.score<=2005)break;
                }
            }
            if(R.score<=2005)break;
            if(chosen.m<0){dead=true;cyclic_deadends++;break;}
            int oldDist=distance;
            insert_move(cur,chosen);
            if(chosen2.m>=0)insert_move(cur,chosen2);
            distance=dist_to(cur,target);
            if(distance!=oldDist-(chosen2.m>=0?2:1))
                throw runtime_error("relink did not monotonically reduce Kendall distance");
            int score=evaluate(cur).score;
            if(score!=bestMoveScore)throw runtime_error("relink accepted score mismatch");
            max_peak=max(max_peak,double(score));
            if(bestFocus>0)focus_hits++;
            if(chosen2.m>=0)paired_steps++;
            steps++;
            if(score==2006)note_solution(cur,score,R.best,R.score);
            if(steps>600)throw runtime_error("path too long");
        }
        if(distance==0){completed_paths++;if(cur.order!=target.order)throw runtime_error("wrong target");}
        if(relink_runs%20==0)
            cerr<<"RELINK "<<policy<<" traversals="<<relink_runs
                <<" completed="<<completed_paths
                <<" elite="<<parents.size()
                <<" visited="<<visited.size()
                <<" best="<<R.score<<" evals="<<evaluations<<"\n";
        if(dead)consecutive_bad++;else consecutive_bad=0;
        if(consecutive_bad>100)break;
    }
    if(evaluate(R.best).score!=R.score)throw runtime_error("unverified relink result");
    return R;
}
int main(int argc,char**argv){
    try{
        if(argc!=7)throw runtime_error("usage: relink POOL OUT greedy|dynamic2 SEED EVALS CHECK");
        string data=argv[1],out=argv[2],policy=argv[3];
        if(policy!="greedy"&&policy!="dynamic2")throw runtime_error("unknown relink policy");
        rng.seed(stoull(argv[4]));long long budget=stoll(argv[5]);
        if(budget<100)throw runtime_error("budget too small");
        read_pool(data);
        int originalCount=int(parents.size());
        auto t=chrono::steady_clock::now();
        auto result=relink(budget,policy);
        double seconds=chrono::duration<double>(chrono::steady_clock::now()-t).count();
        ofstream f(out);
        f<<result.score<<" "<<evaluations<<" "<<invalids<<" "<<relink_runs<<" "
          <<completed_paths<<" "<<cyclic_deadends<<" "<<paired_steps<<" "
          <<focus_hits<<" "<<neutral_states<<" "<<visited.size()<<" "
          <<result.maximum_elite_distance<<" "<<originalCount<<" "
          <<parents.size()<<" "<<setprecision(10)<<seconds<<"\n";
        for(int m=0;m<20;m++)for(int k=0;k<30;k++)
            f<<result.best.at(m,k)<<(k==29?"\n":" ");
        cerr<<"FINAL "<<policy<<" best="<<result.score<<" evals="<<evaluations
            <<" paths="<<completed_paths<<" seconds="<<seconds<<"\n";
        return 0;
    }catch(const exception&e){cerr<<"ERROR "<<e.what()<<"\n";return 1;}
}
