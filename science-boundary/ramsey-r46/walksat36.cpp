#include <algorithm>
#include <array>
#include <bit>
#include <cctype>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <limits>
#include <random>
#include <sstream>
#include <string>
#include <tuple>
#include <vector>

using U = uint64_t;
static constexpr int N = 36;
static constexpr U FULL = (U(1) << N) - 1;

struct Graph {
    std::array<U,N> a{};
    bool edge(int u,int v) const { return (a[u]>>v)&1ULL; }
    void flip(int u,int v) { a[u]^=U(1)<<v; a[v]^=U(1)<<u; }
};

static long long count_cliques_mask(const std::array<U,N>& adj, U cand, int k) {
    if (k==0) return 1;
    if (std::popcount(cand)<k) return 0;
    long long out=0;
    while (std::popcount(cand)>=k) {
        U b=cand&-cand; int v=std::countr_zero(b); cand^=b;
        out += count_cliques_mask(adj, cand & adj[v], k-1);
    }
    return out;
}

static std::array<U,N> complement_adj(const Graph& g) {
    std::array<U,N> h{};
    for(int i=0;i<N;i++) h[i]=FULL & ~g.a[i] & ~(U(1)<<i);
    return h;
}

static long long total_k4(const Graph& g) { return count_cliques_mask(g.a,FULL,4); }
static long long total_i6(const Graph& g) { auto h=complement_adj(g); return count_cliques_mask(h,FULL,6); }

// Number of K4s containing uv if uv were/are present.
static int k4_through_edge(const Graph& g,int u,int v) {
    U c=g.a[u]&g.a[v] & ~(U(1)<<u) & ~(U(1)<<v);
    int out=0;
    U x=c;
    while(x){ U b=x&-x; int w=std::countr_zero(b); x^=b; out += std::popcount(g.a[w] & x); }
    return out;
}

// Number of independent 6-sets containing uv if uv were/are absent.
static int i6_through_nonedge(const Graph& g,int u,int v) {
    U c=FULL & ~g.a[u] & ~g.a[v] & ~(U(1)<<u) & ~(U(1)<<v);
    auto h=complement_adj(g);
    return (int)count_cliques_mask(h,c,4);
}

struct Delta { int dk4; int di6; };
static Delta flip_delta(const Graph& g,int u,int v) {
    int x=k4_through_edge(g,u,v);
    int y=i6_through_nonedge(g,u,v);
    if(g.edge(u,v)) return {-x,+y};
    return {+x,-y};
}

static bool find_clique_rec(const std::array<U,N>& adj,U cand,int k,std::array<int,6>& out,int depth,std::mt19937_64& rng){
    if(k==0) return true;
    if(std::popcount(cand)<k) return false;
    int cnt=std::popcount(cand); int skip=(int)(rng()%cnt);
    U tmp=cand, chosen=0;
    for(int i=0;i<=skip;i++){ chosen=tmp&-tmp; tmp^=chosen; }
    int first=std::countr_zero(chosen);
    auto tryv=[&](int v,U& rest)->bool{
        rest &= ~(U(1)<<v);
        out[depth]=v;
        return find_clique_rec(adj, rest & adj[v], k-1,out,depth+1,rng);
    };
    U rest=cand;
    if(tryv(first,rest)) return true;
    while(std::popcount(rest)>=k){ U b=rest&-rest; int v=std::countr_zero(b); if(tryv(v,rest)) return true; }
    return false;
}

static bool find_conflict(const Graph& g,bool independent,std::array<int,6>& out,int& sz,std::mt19937_64& rng){
    if(independent){ auto h=complement_adj(g); sz=6; return find_clique_rec(h,FULL,6,out,0,rng); }
    sz=4; return find_clique_rec(g.a,FULL,4,out,0,rng);
}

static Graph parse_baseline(const std::string& path, bool do_complement){
    std::ifstream f(path); if(!f) throw std::runtime_error("cannot open baseline");
    std::stringstream ss; ss<<f.rdbuf(); std::string s=ss.str();
    std::vector<std::string> rows;
    for(size_t i=0;i<s.size();){
        if(s[i]=='\"'){
            size_t j=s.find('\"',i+1); if(j==std::string::npos) break;
            std::string t=s.substr(i+1,j-i-1);
            if(t.size()==35 && t.find_first_not_of("01")==std::string::npos) rows.push_back(t);
            i=j+1;
        }else i++;
    }
    if(rows.empty()) {
        std::istringstream ls(s); std::string line;
        while(std::getline(ls,line)){
            line.erase(std::remove_if(line.begin(),line.end(),[](unsigned char c){return std::isspace(c);}),line.end());
            if(line.size()==35 && line.find_first_not_of("01")==std::string::npos) rows.push_back(line);
        }
    }
    if(rows.size()!=35) throw std::runtime_error("baseline must contain 35 binary rows");
    Graph g;
    for(int i=0;i<35;i++) for(int j=0;j<35;j++) if(rows[i][j]=='1') g.a[i]|=U(1)<<j;
    for(int i=0;i<35;i++){
        if((g.a[i]>>i)&1ULL) throw std::runtime_error("loop in baseline");
        for(int j=i+1;j<35;j++) if(g.edge(i,j)!=g.edge(j,i)) throw std::runtime_error("asymmetric baseline");
    }
    if(do_complement){
        U mask=(U(1)<<35)-1;
        for(int i=0;i<35;i++) g.a[i]=mask & ~g.a[i] & ~(U(1)<<i);
    }
    return g;
}

static void write_cert(const Graph& g,const std::string& path){
    std::ofstream o(path); if(!o) throw std::runtime_error("cannot write certificate");
    o<<"{\"adjacency\":[\n";
    for(int i=0;i<N;i++){
        o<<"\""; for(int j=0;j<N;j++) o<<(g.edge(i,j)?'1':'0'); o<<"\""<<(i+1==N?"\n":",\n");
    }
    o<<"]}\n";
}

static void self_test(){
    std::mt19937_64 rng(1234567);
    for(int t=0;t<60;t++){
        Graph g;
        for(int i=0;i<N;i++) for(int j=i+1;j<N;j++) if((rng()%100)<42){ g.a[i]|=U(1)<<j; g.a[j]|=U(1)<<i; }
        long long a=total_k4(g), b=total_i6(g);
        for(int z=0;z<12;z++){
            int u=rng()%N,v=rng()%N; if(u==v){z--;continue;} if(u>v) std::swap(u,v);
            Delta d=flip_delta(g,u,v); Graph h=g; h.flip(u,v);
            long long aa=total_k4(h), bb=total_i6(h);
            if(aa-a!=d.dk4 || bb-b!=d.di6){
                std::cerr<<"delta mismatch t="<<t<<" uv="<<u<<","<<v<<" got "<<d.dk4<<","<<d.di6<<" actual "<<(aa-a)<<","<<(bb-b)<<"\n";
                std::exit(2);
            }
        }
    }
    std::cout<<"self-test ok\n";
}

static Graph optimize_extension(Graph g, std::mt19937_64& rng, int steps, long long& best4, long long& best6){
    long long c4=total_k4(g), c6=total_i6(g), obj=c4+c6;
    Graph bestg=g; long long best=obj; best4=c4; best6=c6;
    std::array<long long,35> tabu{};
    for(int it=0;it<steps;it++){
        int deg=std::popcount(g.a[35]);
        struct C{long long no;int v;Delta d;uint64_t noise;};
        C bc{std::numeric_limits<long long>::max(),0,{0,0},0}; bool have=false;
        for(int v=0;v<35;v++){
            bool e=g.edge(35,v);
            if((e && deg<=11)||(!e && deg>=17)) continue;
            Delta d=flip_delta(g,35,v); long long no=obj+d.dk4+d.di6;
            if(tabu[v]>it && no>=best) continue;
            C c{no,v,d,rng()};
            if(!have||std::tie(c.no,c.noise)<std::tie(bc.no,bc.noise)){bc=c;have=true;}
        }
        if(!have){ for(int v=0;v<35;v++) tabu[v]=0; continue; }
        g.flip(35,bc.v); c4+=bc.d.dk4; c6+=bc.d.di6; obj=c4+c6;
        tabu[bc.v]=it+5+(rng()%11);
        if(obj<best){best=obj;bestg=g;best4=c4;best6=c6; if(best==0) break;}
        if(it%2000==1999 && obj>best+8){g=bestg;c4=best4;c6=best6;obj=best; for(auto&x:tabu)x=0;}
    }
    return bestg;
}

struct Options{
    std::string baseline, out="best-certificate.json", summary="summary.json";
    uint64_t seed=1;
    long long steps=5000000;
    int restarts=50;
    bool complement_core=false;
};
static Options options(int argc,char**argv){
    Options o;
    for(int i=1;i<argc;i++){
        std::string a=argv[i];
        auto val=[&](){ if(++i>=argc) throw std::runtime_error("missing argument"); return std::string(argv[i]); };
        if(a=="--baseline") o.baseline=val();
        else if(a=="--out") o.out=val();
        else if(a=="--seed") o.seed=std::stoull(val());
        else if(a=="--summary") o.summary=val();
        else if(a=="--complement-core") o.complement_core=true;
        else if(a=="--steps") o.steps=std::stoll(val());
        else if(a=="--restarts") o.restarts=std::stoi(val());
        else if(a=="--self-test"){ self_test(); std::exit(0); }
        else throw std::runtime_error("unknown arg: "+a);
    }
    if(o.baseline.empty()) throw std::runtime_error("--baseline required");
    return o;
}

int main(int argc,char**argv){
    try{
        auto opt=options(argc,argv);
        std::mt19937_64 rng(opt.seed);
        Graph core=parse_baseline(opt.baseline,opt.complement_core);
        U core_mask=(U(1)<<35)-1;
        long long core4=count_cliques_mask(core.a,core_mask,4);
        auto core_comp=complement_adj(core);
        long long core6=count_cliques_mask(core_comp,core_mask,6);
        if(core4||core6) throw std::runtime_error("baseline is not (4,6)");
        Graph global_best; long long global_obj=std::numeric_limits<long long>::max(), global4=0,global6=0;
        std::array<long long,630> tabu{};
        std::vector<std::pair<int,int>> edges;
        for(int i=0;i<N;i++) for(int j=i+1;j<N;j++) edges.push_back({i,j});
        auto edge_id=[&](int u,int v){ if(u>v) std::swap(u,v); int id=0; for(int a=0;a<u;a++) id+=N-a-1; return id+(v-u-1); };
        long long per=std::max<long long>(1,opt.steps/std::max(1,opt.restarts));
        bool found=false;
        for(int r=0;r<opt.restarts;r++){
            Graph g=core;
            int deg=11+(rng()%7);
            std::vector<int> vs(35); for(int i=0;i<35;i++) vs[i]=i;
            std::shuffle(vs.begin(),vs.end(),rng);
            for(int k=0;k<deg;k++){ int v=vs[k]; g.a[35]|=U(1)<<v; g.a[v]|=U(1)<<35; }
            long long ec4=0,ec6=0; g=optimize_extension(g,rng,8000,ec4,ec6);
            std::cout<<"extension seed="<<opt.seed<<" restart="<<r<<" obj="<<(ec4+ec6)<<" k4="<<ec4<<" i6="<<ec6<<"\n"<<std::flush;
            int destroy=(r==0?0:2+(rng()%8));
            for(int k=0;k<destroy;k++){ auto [u,v]=edges[rng()%edges.size()]; if(u==35||v==35){k--;continue;} g.flip(u,v); }
            long long c4=total_k4(g), c6=total_i6(g), obj=c4+c6;
            std::fill(tabu.begin(),tabu.end(),0);
            long long stagnant=0;
            for(long long it=0;it<per;it++){
                long long global_it=(long long)r*per+it;
                if(obj<global_obj){
                    global_obj=obj; global4=c4; global6=c6; global_best=g; write_cert(g,opt.out);
                    std::cout<<"best seed="<<opt.seed<<" restart="<<r<<" step="<<it<<" obj="<<obj<<" k4="<<c4<<" i6="<<c6<<"\n"<<std::flush;
                    stagnant=0;
                    if(obj==0){ std::cout<<"FOUND\n"; found=true; break; }
                } else stagnant++;
                if(found) break;
                bool pick_ind = (c4==0) ? true : (c6==0 ? false : (rng()%(c4+c6) >= (uint64_t)c4));
                std::array<int,6> conflict{}; int sz=0;
                if(!find_conflict(g,pick_ind,conflict,sz,rng)){
                    pick_ind=!pick_ind;
                    if(!find_conflict(g,pick_ind,conflict,sz,rng)){
                        if(obj==0){write_cert(g,opt.out); found=true; break;}
                        throw std::runtime_error("conflict counts disagree with witness search");
                    }
                }
                struct Cand{ long long score; int u,v,id; Delta d; uint64_t noise;};
                Cand best{std::numeric_limits<long long>::max(),0,0,0,{0,0},0}; bool have=false;
                for(int x=0;x<sz;x++) for(int y=x+1;y<sz;y++){
                    int u=conflict[x],v=conflict[y];
                    if(pick_ind ? g.edge(u,v) : !g.edge(u,v)) continue;
                    int id=edge_id(u,v); Delta d=flip_delta(g,u,v); long long no=obj+d.dk4+d.di6;
                    bool aspiration=no<global_obj;
                    if(tabu[id]>global_it && !aspiration) continue;
                    Cand c{no,u,v,id,d,rng()};
                    if(!have || std::tie(c.score,c.noise)<std::tie(best.score,best.noise)){best=c;have=true;}
                }
                if(!have){
                    for(int x=0;x<sz;x++) for(int y=x+1;y<sz;y++){
                        int u=conflict[x],v=conflict[y]; if(pick_ind ? g.edge(u,v) : !g.edge(u,v)) continue;
                        int id=edge_id(u,v); Delta d=flip_delta(g,u,v); long long no=obj+d.dk4+d.di6;
                        Cand c{no,u,v,id,d,rng()}; if(!have || std::tie(c.score,c.noise)<std::tie(best.score,best.noise)){best=c;have=true;}
                    }
                }
                if((rng()%100)<22){
                    std::vector<Cand> rw;
                    for(int x=0;x<sz;x++) for(int y=x+1;y<sz;y++){
                        int u=conflict[x],v=conflict[y]; if(pick_ind ? g.edge(u,v) : !g.edge(u,v)) continue;
                        int id=edge_id(u,v); Delta d=flip_delta(g,u,v); long long no=obj+d.dk4+d.di6;
                        rw.push_back(Cand{no,u,v,id,d,rng()});
                    }
                    if(!rw.empty()) best=rw[rng()%rw.size()];
                }
                g.flip(best.u,best.v); c4+=best.d.dk4; c6+=best.d.di6; obj=c4+c6;
                tabu[best.id]=global_it+7+(rng()%19);
                if(stagnant>50000){ std::fill(tabu.begin(),tabu.end(),0); stagnant=0; for(int k=0;k<3;k++){ auto [u,v]=edges[rng()%edges.size()]; Delta d=flip_delta(g,u,v); g.flip(u,v); c4+=d.dk4; c6+=d.di6; obj=c4+c6; } }
            }
            if(found) break;
        }
        std::ofstream js(opt.summary);
        js<<"{\n  \"seed\": "<<opt.seed<<",\n  \"steps_requested\": "<<opt.steps<<",\n  \"restarts\": "<<opt.restarts
          <<",\n  \"best\": "<<global_obj<<",\n  \"k4\": "<<global4<<",\n  \"independent6\": "<<global6
          <<",\n  \"found\": "<<(global_obj==0?"true":"false")<<"\n}\n";
        std::cout<<"DONE best="<<global_obj<<" k4="<<global4<<" i6="<<global6<<" out="<<opt.out<<"\n";
        return 0;
    }catch(const std::exception& e){ std::cerr<<"error: "<<e.what()<<"\n"; return 2; }
}
