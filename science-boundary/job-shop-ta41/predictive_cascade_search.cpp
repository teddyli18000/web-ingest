// Predictive critical-path replacement search for Taillard ta41.
// Original experimental algorithm, NOT a faithful reproduction of N7 2026 batch
// evaluation. Comparison controls share THIS exact DAG evaluator and N7-style
// critical-block insertion generator; objective evaluations are counted equally.
// Only final full acyclic schedule score drives best-candidate certification.
#include <bits/stdc++.h>
using namespace std;
constexpr int JOBS=30,MACH=20,OPS=600,ADJ=580;
struct Move {int m,i,j;};
struct Schedule {
    array<int,600> order{};
    inline int at(int m,int i)const{return order[m*30+i];}
};
struct G {
    int score=-1;
    array<int,600> head{},tail{};
    array<uint8_t,580> crit{};
};
struct Inst {
    array<int,600> dur{}, jobnext{};
    array<array<int,20>,30> pos{};
    array<array<int,20>,30> machine{};
};
static Inst I;
static long long evaluations=0, invalids=0,accepted=0,macros=0,replacement_events=0;
static mt19937_64 rng;
static int uni(int n){return int(rng()%uint64_t(n));}
static double u01(){return (rng()>>11)*(1.0/9007199254740992.0);}

static void read_input(const string &file,Schedule &s) {
    ifstream in(file);
    if(!in)throw runtime_error("input missing");
    int j,m;in>>j>>m;
    if(j!=30||m!=20)throw runtime_error("incorrect job/shop shape");
    for(int a=0;a<JOBS;a++){
        array<bool,MACH> used{};
        for(int k=0;k<MACH;k++){
            int machine, duration;in>>machine>>duration;
            if(!in||machine<0||machine>=MACH||used[machine]||duration<=0)
                throw runtime_error("bad instance");
            used[machine]=true;
            I.dur[a*20+k]=duration;
            I.pos[a][machine]=k;
            I.machine[a][k]=machine;
            I.jobnext[a*20+k]=(k<19?a*20+k+1:-1);
        }
    }
    for(int machine=0;machine<MACH;machine++){
        array<bool,30> used{};
        for(int p=0;p<30;p++){
            int a;in>>a;
            if(!in||a<0||a>=30||used[a])throw runtime_error("bad machine orders");
            used[a]=true;
            s.order[machine*30+p]=a;
        }
    }
}
static G evaluate(const Schedule &s, bool detail=false){
    G g;
    array<int,600> mnext{},indeg{},q{},topo{};
    mnext.fill(-1);
    for(int u=0;u<OPS;u++)indeg[u]=(u%20>0?1:0);
    for(int m=0;m<MACH;m++){
        for(int k=0;k<30;k++){
            int job=s.at(m,k),u=job*20+I.pos[job][m];
            if(k>0)indeg[u]++;
            if(k<29){
                int b=s.at(m,k+1);
                mnext[u]=b*20+I.pos[b][m];
            }
        }
    }
    int tailq=0,headq=0,cnt=0;
    for(int u=0;u<OPS;u++)if(!indeg[u])q[tailq++]=u;
    int maxend=0;
    while(headq<tailq){
        int u=q[headq++];topo[cnt++]=u;
        int finish=g.head[u]+I.dur[u];maxend=max(maxend,finish);
        int b=I.jobnext[u],c=mnext[u];
        if(b>=0){g.head[b]=max(g.head[b],finish);if(!--indeg[b])q[tailq++]=b;}
        if(c>=0){g.head[c]=max(g.head[c],finish);if(!--indeg[c])q[tailq++]=c;}
    }
    if(cnt!=OPS){g.score=-1;return g;}
    g.score=maxend;
    if(detail){
        for(int i=cnt-1;i>=0;i--){
            int u=topo[i],finish=0;
            int b=I.jobnext[u],c=mnext[u];
            if(b>=0)finish=max(finish,g.tail[b]);
            if(c>=0)finish=max(finish,g.tail[c]);
            g.tail[u]=I.dur[u]+finish;
        }
        for(int m=0;m<MACH;m++)for(int k=0;k<29;k++){
            int a=s.at(m,k),b=s.at(m,k+1);
            int u=a*20+I.pos[a][m],v=b*20+I.pos[b][m];
            g.crit[m*29+k]=(g.head[u]+I.dur[u]+g.tail[v]==g.score);
        }
    }
    return g;
}
static void insert_move(Schedule &s,Move t){
    int m=t.m,i=t.i,j=t.j,off=m*30;
    if(i==j)return;
    int moved=s.order[off+i];
    if(i<j)for(int p=i;p<j;p++)s.order[off+p]=s.order[off+p+1];
    else for(int p=i;p>j;p--)s.order[off+p]=s.order[off+p-1];
    s.order[off+j]=moved;
}
static int id(const Schedule &s,int m,int k){
    return m*900+s.at(m,k)*30+s.at(m,k+1);
}
static unordered_set<int> critset(const Schedule &s,const G &g){
    unordered_set<int> x;
    for(int m=0;m<MACH;m++)for(int p=0;p<29;p++)
        if(g.crit[m*29+p])x.insert(id(s,m,p));
    return x;
}
static unordered_set<int> delta_critical(const Schedule &s,const G &g,
                                          const unordered_set<int>&old){
    auto now=critset(s,g);
    for(auto it=now.begin();it!=now.end();) {
        if(old.count(*it))it=now.erase(it);else ++it;
    }
    return now;
}
static vector<Move> critical_block_moves(const Schedule&s,const G &g,
                                         const unordered_set<int>&focus={}){
    vector<Move> moves;
    unordered_set<int> used;
    for(int m=0;m<MACH;m++){
        for(int k=0;k<29;){
            if(!g.crit[m*29+k]){k++;continue;}
            int left=k;
            while(k<29&&g.crit[m*29+k])k++;
            int right=k; // inclusive final job position
            bool relevant=focus.empty();
            if(!relevant){
                for(int h=left;h<right;h++)
                    if(focus.count(id(s,m,h))){relevant=true;break;}
            }
            if(!relevant)continue;
            auto add=[&](int i,int j){
                if(i==j)return;
                int code=m*900+i*30+j;
                if(used.insert(code).second)moves.push_back({m,i,j});
            };
            // Critical-block N7-style head/tail insertion, both directions.
            for(int p=left+1;p<=right;p++){add(p,left);add(left,p);}
            for(int p=left;p<right;p++){add(p,right);add(right,p);}
            // Include two short, adjacent changes even in a long block.
            for(int p=left;p<right;p++)add(p,p+1);
        }
    }
    return moves;
}
static vector<Move> focus_moves(const Schedule&s,const G &g,
                                const unordered_set<int>&focus){
    auto moves=critical_block_moves(s,g,focus);
    if(moves.empty())moves=critical_block_moves(s,g);
    return moves;
}
static uint64_t hash_schedule(const Schedule&s){
    uint64_t h=1469598103934665603ULL;
    for(int x:s.order){h^=uint64_t(x+1);h*=1099511628211ULL;}
    return h;
}
static int moveid(Move t){return t.m*900+t.i*30+t.j;}
struct Candidate{
    int score, intermediate, replacement;
    array<Move,3> path{};
    int depth=0;
    bool newstate=false;
};
static void choose_elite(Schedule &cur,const Schedule&best,
                         const vector<Schedule>&elite,int &current){
    if(elite.empty()||uni(4)==0)cur=best;
    else cur=elite[uni(int(elite.size()))];
    current=evaluate(cur).score;
    if(current<0)throw runtime_error("elite infeasible");
}
static void add_elite(const Schedule&s,int score,vector<Schedule>&elites,
                      unordered_set<uint64_t>&seen){
    if(score>2035||elites.size()>=80)return;
    uint64_t h=hash_schedule(s);
    if(seen.insert(h).second)elites.push_back(s);
}
struct Result{
    Schedule best{};
    int score=2006,iterations=0,valid=0;
    long long first_worse=0,intermediate_worse=0,neutral_accepted=0;
    long long visited=0,peak=2006,crit_delta=0;
    int min_accepted=2006;
};
static int score_candidate(const Schedule&s,bool detail,G &g){
    if(evaluations>=LLONG_MAX/2)throw runtime_error("overflow");
    ++evaluations;
    g=evaluate(s,detail);
    if(g.score<0)++invalids;
    return g.score;
}
static void random_cap(vector<Move>&v,int n){
    shuffle(v.begin(),v.end(),rng);
    if(int(v.size())>n)v.resize(n);
}
static Result search(Schedule initial,const string&policy,long long budget,
                     int tabu_cap,int first_cap,int second_cap,int third_cap,
                     int temp_cap,int reset_after){
    Result result;result.best=initial;
    Schedule cur=initial;
    G init=evaluate(cur,true);if(init.score!=2006)throw runtime_error("start !=2006");
    auto starting=critset(cur,init);
    G graph=init;
    int current=2006;
    vector<Schedule>elite{initial};
    unordered_set<uint64_t>seen{hash_schedule(initial)};
    unordered_map<int,int>tabu;
    int stagnation=0;
    auto begin=chrono::steady_clock::now();
    while(evaluations<budget&&result.score>2005){
        result.iterations++;
        if(policy=="tabu"){
            vector<Move> moves=critical_block_moves(cur,graph);
            if(moves.empty())throw runtime_error("no critical block candidates");
            random_cap(moves,tabu_cap);
            int winner=INT_MAX;Move chosen{-1,-1,-1};
            int chosenPenalty=INT_MAX;
            for(Move m:moves){
                if(evaluations>=budget)break;
                insert_move(cur,m);
                G temp;int value=score_candidate(cur,false,temp);
                insert_move(cur,{m.m,m.j,m.i});
                if(value<0||value>result.score+90)continue;
                bool forbidden=tabu.count(moveid(m)) && tabu[moveid(m)]>result.iterations;
                if(forbidden && value>=result.score)continue;
                int penalty=(value==current?0:1);
                if(value<winner||(value==winner&&penalty<chosenPenalty)){
                    winner=value;chosen=m;chosenPenalty=penalty;
                }
            }
            if(chosen.m>=0){
                insert_move(cur,chosen);
                int actual=evaluate(cur).score; if(actual!=winner)throw runtime_error("bad tabu undo");
                current=actual;
                tabu[moveid({chosen.m,chosen.j,chosen.i})]=result.iterations+8+uni(13);
                accepted++;
                if(current==result.score)result.neutral_accepted++;
                if(current<result.score){
                    result.score=current;result.best=cur;stagnation=0;
                    cerr<<"BEST tabu "<<result.score<<" evals="<<evaluations<<"\n";
                }else stagnation++;
                add_elite(cur,current,elite,seen);
            }else stagnation++;
        }else{
            auto moves=critical_block_moves(cur,graph);
            random_cap(moves,first_cap);
            struct First{Move m;int score;G graph;int changed;};
            vector<First>firsts;
            auto oldcrit=critset(cur,graph);
            for(Move m:moves){
                if(evaluations>=budget)break;
                insert_move(cur,m);G g;int val=score_candidate(cur,true,g);
                int change=0;
                if(val>0){
                    auto now=critset(cur,g);
                    for(int x:now)if(!oldcrit.count(x))change++;
                    if(val<=result.score+temp_cap)firsts.push_back({m,val,g,change});
                }
                insert_move(cur,{m.m,m.j,m.i});
            }
            stable_sort(firsts.begin(),firsts.end(),[](const First&a,const First&b){
                if(a.score!=b.score)return a.score<b.score;
                return a.changed>b.changed;
            });
            vector<First>selected;
            unordered_set<int>machines;
            for(auto &f:firsts){
                if(machines.insert(f.m.m).second)selected.push_back(f);
                if(selected.size()==5)break;
            }
            for(auto &f:firsts){
                if(selected.size()==6)break;
                bool already=false;for(auto &x:selected)
                    if(moveid(x.m)==moveid(f.m)){already=true;break;}
                if(!already)selected.push_back(f);
            }
            vector<Candidate>pool;
            for(const First&f:selected){
                if(evaluations>=budget)break;
                insert_move(cur,f.m);
                unordered_set<int>focus=(policy=="dynamic3"
                    ?delta_critical(cur,f.graph,oldcrit):starting);
                auto second=focus_moves(cur,f.graph,focus);
                random_cap(second,second_cap);
                struct Second{Move m;int score;G graph;};
                vector<Second>seconds;
                auto firstcrit=critset(cur,f.graph);
                for(Move m:second){
                    if(evaluations>=budget)break;
                    insert_move(cur,m);
                    G g;int val=score_candidate(cur,true,g);
                    if(val>0&&val<=result.score+temp_cap)seconds.push_back({m,val,g});
                    insert_move(cur,{m.m,m.j,m.i});
                }
                stable_sort(seconds.begin(),seconds.end(),[](auto&a,auto&b){return a.score<b.score;});
                if(seconds.size()>3)seconds.resize(3);
                for(const auto&secondop:seconds){
                    if(evaluations>=budget)break;
                    insert_move(cur,secondop.m);
                    auto focus3=(policy=="dynamic3"
                          ?delta_critical(cur,secondop.graph,firstcrit):starting);
                    auto third=focus_moves(cur,secondop.graph,focus3);
                    random_cap(third,third_cap);
                    for(Move m:third){
                        if(evaluations>=budget)break;
                        insert_move(cur,m);
                        G no;int val=score_candidate(cur,false,no);
                        if(val>0&&val<=result.score+45){
                            Candidate cand;
                            cand.score=val;cand.intermediate=max(f.score,secondop.score);
                            cand.replacement=f.changed;
                            cand.path={f.m,secondop.m,m};cand.depth=3;
                            cand.newstate=!seen.count(hash_schedule(cur));
                            pool.push_back(cand);
                        }
                        if(val>0&&val<result.score){
                            result.score=val;result.best=cur;stagnation=0;
                            cerr<<"BEST "<<policy<<" "<<val<<" evals="<<evaluations<<"\n";
                        }
                        insert_move(cur,{m.m,m.j,m.i});
                        if(result.score<=2005)break;
                    }
                    insert_move(cur,{secondop.m.m,secondop.m.j,secondop.m.i});
                    if(result.score<=2005)break;
                }
                insert_move(cur,{f.m.m,f.m.j,f.m.i});
                if(result.score<=2005)break;
            }
            if(result.score<=2005)break;
            if(!pool.empty()){
                stable_sort(pool.begin(),pool.end(),[](const Candidate&a,const Candidate&b){
                    if(a.score!=b.score)return a.score<b.score;
                    if(a.newstate!=b.newstate)return a.newstate>b.newstate;
                    return a.replacement>b.replacement;
                });
                int idx=(u01()<0.85?0:uni(min(7,int(pool.size()))));
                auto cand=pool[idx];
                for(int k=0;k<cand.depth;k++)insert_move(cur,cand.path[k]);
                current=evaluate(cur).score;
                if(current!=cand.score)throw runtime_error("macro score mismatch");
                accepted++;macros++;
                if(current==result.score)result.neutral_accepted++;
                if(cand.intermediate>current)result.first_worse++;
                if(cand.intermediate>result.score)result.intermediate_worse++;
                if(cand.replacement)replacement_events++;
                if(current<result.score){
                    result.score=current;result.best=cur;stagnation=0;
                }else stagnation++;
                add_elite(cur,current,elite,seen);
            }else stagnation++;
        }
        if(current<result.score){result.score=current;result.best=cur;stagnation=0;}
        graph=evaluate(cur,true);
        if(graph.score!=current)throw runtime_error("critical graph mismatch");
        if(stagnation>=reset_after){
            choose_elite(cur,result.best,elite,current);
            graph=evaluate(cur,true);
            stagnation=0;
        }
        if(result.iterations%150==0){
            cerr<<"PROGRESS "<<policy<<" evals="<<evaluations<<" best="
                <<result.score<<" elites="<<elite.size()<<" score="<<current<<"\n";
        }
    }
    result.visited=seen.size();result.valid=evaluations-invalids;
    if(evaluate(result.best).score!=result.score)throw runtime_error("invalid best");
    return result;
}
#ifndef CASCADE_LIB
int main(int argc,char**argv){
    try{
        if(argc!=10){
            cerr<<"usage: path_search DATA OUT POLICY SEED EVALS TABU FIRST SECOND THIRD\n";
            return 2;
        }
        string data=argv[1],out=argv[2],policy=argv[3];
        long long seed=stoll(argv[4]),budget=stoll(argv[5]);
        int tabu_cap=stoi(argv[6]),first=stoi(argv[7]),second=stoi(argv[8]),third=stoi(argv[9]);
        if(policy!="tabu"&&policy!="static3"&&policy!="dynamic3")
            throw runtime_error("unknown policy");
        rng.seed(seed);
        Schedule root;read_input(data,root);
        if(evaluate(root).score!=2006)throw runtime_error("input must be verified 2006 schedule");
        auto started=chrono::steady_clock::now();
        auto best=search(root,policy,budget,tabu_cap,first,second,third,180,130);
        double elapsed=chrono::duration<double>(chrono::steady_clock::now()-started).count();
        ofstream f(out);
        if(!f)throw runtime_error("cannot open output");
        f<<best.score<<" "<<evaluations<<" "<<invalids<<" "<<accepted<<" "
         <<macros<<" "<<replacement_events<<" "<<best.visited<<" "<<best.iterations<<" "
         <<best.neutral_accepted<<" "<<best.first_worse<<" "<<best.intermediate_worse<<" "
         <<setprecision(10)<<elapsed<<"\n";
        for(int m=0;m<20;m++){
            for(int i=0;i<30;i++)f<<best.best.at(m,i)<<(i==29?"\n":" ");
        }
        cerr<<"FINAL "<<policy<<" best="<<best.score<<" evaluations="<<evaluations
            <<" seconds="<<elapsed<<"\n";
        return 0;
    }catch(const exception&e){
        cerr<<"ERROR "<<e.what()<<"\n";
        return 1;
    }
}

#endif // CASCADE_LIB: permit exact graph evaluator reuse by elite path relinking
