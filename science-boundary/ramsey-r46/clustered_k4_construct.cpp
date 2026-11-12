// Constructive p003 search: guide edge changes toward *overlapping* K4 witnesses.
// Score is exact K4+I6, exploration uses score-lambda*K4_edge_overlap.
// Every accepted move updates all affected 4-cliques and incident edge supports.
// Does not claim a Ramsey breakthrough without an independent exact recount.
#include <algorithm>
#include <array>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <random>
#include <string>
#include <tuple>
#include <vector>
using namespace std;
static constexpr int N=36;
static constexpr uint64_t FULL=(1ULL<<N)-1ULL;
using Adj=array<uint64_t,N>;
struct Graph {
    Adj a{};
    void flip(int u,int v){a[u]^=1ULL<<v;a[v]^=1ULL<<u;}
    Adj complement()const{
        Adj c{};
        for(int i=0;i<N;i++)c[i]=FULL&~a[i]&~(1ULL<<i);
        return c;
    }
    static int cliques(const Adj& g,uint64_t c,int k){
        if(!k)return 1;
        int z=0;
        while(__builtin_popcountll(c)>=k){
            int v=__builtin_ctzll(c);
            c&=c-1;
            z+=cliques(g,c&g[v],k-1);
        }
        return z;
    }
    pair<int,int> recount()const{
        return {cliques(a,FULL,4),cliques(complement(),FULL,6)};
    }
    int blue_around(int u,int v)const{
        auto c=complement();
        return cliques(c,c[u]&c[v],4);
    }
    void save(const string& p)const{
        ofstream f(p);
        f<<"{\"adjacency\":[";
        for(int i=0;i<N;i++){
            if(i)f<<',';
            f<<'"';
            for(int j=0;j<N;j++)f<<((a[i]>>j)&1);
            f<<'"';
        }
        f<<"]}\n";
    }
};
struct Impact {
    int k4=0,i6=0,overlap=0;
    vector<tuple<int,int,int>> changes;
};
struct State {
    Graph g;
    int k4=0,i6=0,overlap=0;
    array<array<int,N>,N> support{};
    int score()const{return k4+i6;}
};
static int bonus(int x){return max(0,x-1);}
static State initial_state(const Graph& g){
    State s;
    s.g=g;
    auto counts=g.recount();
    s.k4=counts.first;s.i6=counts.second;
    auto dfs=[&](auto&&self,uint64_t c,vector<int>&v)->void{
        if(v.size()==4){
            for(int i=0;i<4;i++)for(int j=i+1;j<4;j++){
                int u=v[i],w=v[j];
                s.support[u][w]++;
            }
            return;
        }
        while(__builtin_popcountll(c)>=4-(int)v.size()){
            int u=__builtin_ctzll(c);
            c&=c-1;
            v.push_back(u);
            self(self,c&g.a[u],v);
            v.pop_back();
        }
    };
    vector<int>v;
    dfs(dfs,FULL,v);
    for(int u=0;u<N;u++)for(int w=u+1;w<N;w++)
        s.overlap+=bonus(s.support[u][w]);
    return s;
}
static Impact delta(const State&s,int u,int v){
    Impact out;
    bool present=(s.g.a[u]>>v)&1;
    auto common=s.g.a[u]&s.g.a[v];
    array<array<int,N>,N> involved{};
    int copies=0;
    while(common){
        int x=__builtin_ctzll(common);
        common&=common-1;
        uint64_t neighbors=s.g.a[x]&common;
        while(neighbors){
            int y=__builtin_ctzll(neighbors);
            neighbors&=neighbors-1;
            copies++;
            int e[6][2]={{u,v},{u,x},{u,y},{v,x},{v,y},{x,y}};
            for(auto &pair:e){
                int a=min(pair[0],pair[1]),b=max(pair[0],pair[1]);
                involved[a][b]++;
            }
        }
    }
    out.k4=present?-copies:copies;
    int blue=s.g.blue_around(u,v);
    out.i6=present?blue:-blue;
    for(int a=0;a<N;a++)for(int b=a+1;b<N;b++)if(involved[a][b]){
        int d=present?-involved[a][b]:involved[a][b];
        out.overlap+=bonus(s.support[a][b]+d)-bonus(s.support[a][b]);
        out.changes.emplace_back(a,b,d);
    }
    return out;
}
static void apply(State &s,int u,int v,const Impact&d){
    s.g.flip(u,v);
    s.k4+=d.k4;s.i6+=d.i6;s.overlap+=d.overlap;
    for(auto [a,b,z]:d.changes)s.support[a][b]+=z;
}
int main(int argc,char**argv){
    if(argc!=8){
        cerr<<"usage: construct <parents.txt> <seconds> <seed> <lambda> <best.json> <cluster.json> <summary.txt>\n";
        return 2;
    }
    ifstream input(argv[1]);
    int num;input>>num;
    vector<State> parents;
    for(int i=0;i<num;i++){
        Graph g;
        string row;
        for(int j=0;j<N;j++){
            input>>row;
            if(row.size()!=N)throw runtime_error("malformed input row");
            for(int v=0;v<N;v++)if(row[v]=='1')g.a[j]|=1ULL<<v;
        }
        parents.push_back(initial_state(g));
    }
    mt19937_64 rng(stoul(argv[3]));
    double seconds=stod(argv[2]),lambda=stod(argv[4]);
    auto started=chrono::steady_clock::now();
    auto elapsed=[&](){return chrono::duration<double>(chrono::steady_clock::now()-started).count();};
    State best=parents.front(),cluster=parents.front();
    int best_score=best.score(),best_overlap=-1;
    for(const auto &p:parents){
        if(p.score()<best_score)best=p,best_score=p.score();
        if(p.score()<=14&&p.overlap>best_overlap)
            cluster=p,best_overlap=p.overlap;
    }
    // An archive of different parents and low-score constructed states.
    vector<State> archive=parents;
    State cur=archive[rng()%archive.size()];
    uint64_t moves=0,accepted=0;
    while(elapsed()<seconds && best_score>0){
        if(moves && moves%12000==0){
            cur=(rng()%3==0)?cluster:archive[rng()%archive.size()];
        }
        double weight=lambda*(0.35+0.95*((moves/12000)%5)/4.0);
        double temperature=0.33+1.95*(1-(moves%12000)/12000.0);
        moves++;
        struct Option {double energy;int u,v;Impact d;};
        vector<Option> options;
        for(int trial=0;trial<8;trial++){
            int u=rng()%N,v=rng()%(N-1);
            if(v>=u)v++;
            if(u>v)swap(u,v);
            Impact d=delta(cur,u,v);
            options.push_back({d.k4+d.i6-weight*d.overlap,u,v,std::move(d)});
        }
        sort(options.begin(),options.end(),[](const Option&a,const Option&b){
            return a.energy<b.energy;
        });
        auto &o=options[rng()%min(4,(int)options.size())];
        if(o.energy<=0 || uniform_real_distribution<double>(0,1)(rng)<exp(-o.energy/temperature)){
            apply(cur,o.u,o.v,o.d);
            accepted++;
            if(cur.score()<best_score){
                best=cur;best_score=cur.score();
                best.g.save(argv[5]);
                cout<<"IMPROVED score="<<best_score<<" K4="<<best.k4
                    <<" I6="<<best.i6<<" time="<<elapsed()<<"\n";
            }
            if(cur.score()<=14 && cur.overlap>best_overlap){
                cluster=cur;
                best_overlap=cur.overlap;
                cluster.g.save(argv[6]);
                cout<<"CLUSTER score="<<cur.score()<<" K4="<<cur.k4
                    <<" I6="<<cur.i6<<" overlap="<<cur.overlap
                    <<" time="<<elapsed()<<"\n";
            }
            if(cur.score()<=16 && rng()%340==0){
                if(archive.size()<120)archive.push_back(cur);
                else archive[rng()%archive.size()]=cur;
            }
            if(cur.score()>85)cur=archive[rng()%archive.size()];
        }
        if(moves%40000==0){
            State verify=initial_state(cur.g);
            if(verify.k4!=cur.k4 || verify.i6!=cur.i6 ||
               verify.overlap!=cur.overlap)throw runtime_error("incremental count error");
        }
    }
    auto c=best.g.recount();
    if(c.first+c.second!=best_score)throw runtime_error("best recount error");
    auto k=cluster.g.recount();
    if(k.first+k.second>14)throw runtime_error("cluster recount error");
    ofstream summary(argv[7]);
    summary<<"best="<<best_score<<" best_K4="<<c.first<<" best_I6="<<c.second
           <<" best_cluster_overlap="<<best_overlap
           <<" cluster_K4="<<k.first<<" cluster_I6="<<k.second
           <<" moves="<<moves<<" accepted="<<accepted<<" seconds="<<elapsed()<<"\n";
    cout<<"SUMMARY best="<<best_score<<" overlap="<<best_overlap
        <<" moves="<<moves<<" accepted="<<accepted<<"\n";
    return 0;
}
