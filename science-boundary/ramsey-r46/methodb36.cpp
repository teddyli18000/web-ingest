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
#include <stdexcept>
#include <string>
#include <tuple>
#include <vector>

using U = uint64_t;
static constexpr int N = 36;
static constexpr int M = N*(N-1)/2;
static constexpr U FULL = (U(1)<<N)-1;
static constexpr std::array<long long,11> G1_PROFILE = {
    0,1886,1640,4880,2167,9553,3204,11268,2558,7634,1586
};
static constexpr long long PROFILE_DEN = 46376; // C(34,4)
static constexpr long long PROFILE_NUM = 58905; // C(36,4)

struct Graph {
    std::array<U,N> a{};
    bool edge(int u,int v) const { return ((a[u]>>v)&1ULL)!=0; }
    void flip(int u,int v){ a[u]^=U(1)<<v; a[v]^=U(1)<<u; }
    int deg(int u) const { return std::popcount(a[u]); }
};

static long long count_cliques_mask(const std::array<U,N>& adj,U cand,int k){
    if(k==0) return 1;
    if(std::popcount(cand)<k) return 0;
    long long out=0;
    while(std::popcount(cand)>=k){
        U b=cand&-cand; int v=std::countr_zero(b); cand^=b;
        out += count_cliques_mask(adj,cand&adj[v],k-1);
    }
    return out;
}
static std::array<U,N> complement_adj(const Graph& g){
    std::array<U,N> h{};
    for(int i=0;i<N;i++) h[i]=FULL & ~g.a[i] & ~(U(1)<<i);
    return h;
}
static long long total_k4(const Graph& g){ return count_cliques_mask(g.a,FULL,4); }
static long long total_i6(const Graph& g){ auto h=complement_adj(g); return count_cliques_mask(h,FULL,6); }

static int k4_through_edge(const Graph& g,int u,int v){
    U c=g.a[u]&g.a[v] & ~(U(1)<<u) & ~(U(1)<<v);
    int out=0; U x=c;
    while(x){ U b=x&-x; int w=std::countr_zero(b); x^=b; out += std::popcount(g.a[w]&x); }
    return out;
}
static int i6_through_nonedge(const Graph& g,int u,int v){
    U c=FULL & ~g.a[u] & ~g.a[v] & ~(U(1)<<u) & ~(U(1)<<v);
    auto h=complement_adj(g);
    return (int)count_cliques_mask(h,c,4);
}
struct DefDelta { int dk4,di6; };
static DefDelta defect_delta(const Graph& g,int u,int v){
    int x=k4_through_edge(g,u,v), y=i6_through_nonedge(g,u,v);
    return g.edge(u,v) ? DefDelta{-x,+y} : DefDelta{+x,-y};
}

// 11 unlabeled four-vertex graph classes in Exoo table order:
// E4,K2,2K2,P3,K1,3,P4,K3,K3+e,C4,K4-e,K4.
static int class4_bits(int bits){
    int e=std::popcount((unsigned)bits);
    if(e==0) return 0;
    if(e==1) return 1;
    int deg[4]={0,0,0,0};
    int p=0;
    for(int i=0;i<4;i++) for(int j=i+1;j<4;j++,p++) if((bits>>p)&1){deg[i]++;deg[j]++;}
    std::sort(deg,deg+4);
    if(e==2) return deg[3]==1 ? 2 : 3;
    if(e==3){
        if(deg[3]==3) return 4;
        if(deg[0]==0) return 6;
        return 5;
    }
    if(e==4) return deg[0]==2 ? 8 : 7;
    if(e==5) return 9;
    return 10;
}
static int induced4_bits(const Graph& g,const std::array<int,4>& q,bool complement){
    int bits=0,p=0;
    for(int i=0;i<4;i++) for(int j=i+1;j<4;j++,p++){
        bool e=g.edge(q[i],q[j]);
        if(complement) e=!e;
        if(e) bits|=1<<p;
    }
    return bits;
}
using Profile = std::array<long long,11>;
static Profile profile4(const Graph& g,bool complement=true){
    Profile pr{};
    for(int a=0;a<N;a++) for(int b=a+1;b<N;b++) for(int c=b+1;c<N;c++) for(int d=c+1;d<N;d++){
        std::array<int,4> q{a,b,c,d};
        pr[class4_bits(induced4_bits(g,q,complement))]++;
    }
    return pr;
}
static long long profile_distance(const Profile& pr){
    long long out=0;
    for(int i=0;i<11;i++) out += std::llabs(pr[i]*PROFILE_DEN - G1_PROFILE[i]*PROFILE_NUM);
    return out;
}
struct ShapeDelta {
    long long dp4=0;
    Profile dprofile{};
};
static ShapeDelta shape_delta(const Graph& g,int u,int v){
    ShapeDelta d;
    std::array<int,N-2> rest{}; int nr=0;
    for(int x=0;x<N;x++) if(x!=u && x!=v) rest[nr++]=x;
    for(int ii=0;ii<nr;ii++) for(int jj=ii+1;jj<nr;jj++){
        std::array<int,4> q{u,v,rest[ii],rest[jj]};
        int before=induced4_bits(g,q,true);
        int after=before^1;
        int cb=class4_bits(before), ca=class4_bits(after);
        d.dprofile[cb]--; d.dprofile[ca]++;
        if(cb==5) d.dp4--;
        if(ca==5) d.dp4++;
    }
    return d;
}
static Profile add_profile(const Profile& a,const Profile& b){
    Profile c{}; for(int i=0;i<11;i++) c[i]=a[i]+b[i]; return c;
}

static bool find_clique_rec(const std::array<U,N>& adj,U cand,int k,std::array<int,6>& out,int depth,std::mt19937_64& rng){
    if(k==0) return true;
    if(std::popcount(cand)<k) return false;
    int cnt=std::popcount(cand), skip=(int)(rng()%cnt);
    U tmp=cand,chosen=0;
    for(int i=0;i<=skip;i++){chosen=tmp&-tmp;tmp^=chosen;}
    int first=std::countr_zero(chosen);
    auto tryv=[&](int x,U& rest)->bool{
        rest &= ~(U(1)<<x); out[depth]=x;
        return find_clique_rec(adj,rest&adj[x],k-1,out,depth+1,rng);
    };
    U rest=cand;
    if(tryv(first,rest)) return true;
    while(std::popcount(rest)>=k){U b=rest&-rest;int x=std::countr_zero(b);if(tryv(x,rest)) return true;}
    return false;
}
static bool find_conflict(const Graph& g,bool independent,std::array<int,6>& out,int& sz,std::mt19937_64& rng){
    if(independent){auto h=complement_adj(g);sz=6;return find_clique_rec(h,FULL,6,out,0,rng);}
    sz=4;return find_clique_rec(g.a,FULL,4,out,0,rng);
}

static std::vector<std::pair<int,int>> all_edges(){
    std::vector<std::pair<int,int>> e; e.reserve(M);
    for(int i=0;i<N;i++) for(int j=i+1;j<N;j++) e.push_back({i,j});
    return e;
}
static int edge_id(int u,int v){
    if(u>v) std::swap(u,v);
    return u*(2*N-u-1)/2 + (v-u-1);
}
static bool degree_safe_after_flip(const Graph& g,int u,int v){
    int du=g.deg(u), dv=g.deg(v), step=g.edge(u,v)?-1:+1;
    du+=step; dv+=step;
    return 11<=du && du<=17 && 11<=dv && dv<=17;
}

static Graph parse_json_graph(const std::string& path){
    std::ifstream f(path); if(!f) throw std::runtime_error("cannot open graph");
    std::stringstream ss;ss<<f.rdbuf();std::string s=ss.str();
    std::vector<std::string> rows;
    for(size_t i=0;i<s.size();){
        if(s[i]=='\"'){
            size_t j=s.find('\"',i+1);if(j==std::string::npos)break;
            std::string t=s.substr(i+1,j-i-1);
            if(t.size()==N && t.find_first_not_of("01")==std::string::npos) rows.push_back(t);
            i=j+1;
        }else i++;
    }
    if(rows.size()!=N) throw std::runtime_error("expected 36 adjacency rows");
    Graph g;
    for(int i=0;i<N;i++) for(int j=0;j<N;j++) if(rows[i][j]=='1')g.a[i]|=U(1)<<j;
    for(int i=0;i<N;i++){
        if(g.edge(i,i)) throw std::runtime_error("loop");
        for(int j=i+1;j<N;j++) if(g.edge(i,j)!=g.edge(j,i)) throw std::runtime_error("asymmetric");
    }
    return g;
}
static void write_cert(const Graph& g,const std::string& path){
    std::ofstream o(path);if(!o)throw std::runtime_error("cannot write cert");
    o<<"{\"adjacency\":[\n";
    for(int i=0;i<N;i++){
        o<<"\"";for(int j=0;j<N;j++)o<<(g.edge(i,j)?'1':'0');o<<"\""<<(i+1==N?"\n":",\n");
    }o<<"]}\n";
}

static void self_test(){
    std::mt19937_64 rng(20261028);
    auto edges=all_edges();
    for(int t=0;t<20;t++){
        Graph g;
        for(auto [u,v]:edges) if(rng()%100<42){g.a[u]|=U(1)<<v;g.a[v]|=U(1)<<u;}
        long long k4=total_k4(g),i6=total_i6(g);Profile p=profile4(g,true);
        long long sum=0;for(auto x:p)sum+=x;if(sum!=PROFILE_NUM)throw std::runtime_error("profile sum");
        Profile pg=profile4(g,false);
        if(pg[5]!=p[5])throw std::runtime_error("P4 complement invariance");
        for(int z=0;z<8;z++){
            auto [u,v]=edges[rng()%edges.size()];
            auto dd=defect_delta(g,u,v);auto sd=shape_delta(g,u,v);
            Graph h=g;h.flip(u,v);
            if(total_k4(h)-k4!=dd.dk4 || total_i6(h)-i6!=dd.di6) throw std::runtime_error("defect delta");
            Profile q=profile4(h,true);
            for(int c=0;c<11;c++) if(q[c]-p[c]!=sd.dprofile[c]) throw std::runtime_error("profile delta");
            if(q[5]-p[5]!=sd.dp4) throw std::runtime_error("p4 delta");
        }
    }
    std::cout<<"self-test ok\n";
}

struct Options{
    std::string seed_graph,out="methodb-best.json",summary="methodb-summary.json",mode="profile";
    uint64_t seed=1;
    long long steps=1000000;
    int restarts=8;
    int slack=1;
    int shape_threshold=40;
    int kick_percent=25;
    int tradeoff=256;
};
static Options options(int argc,char**argv){
    Options o;
    for(int i=1;i<argc;i++){
        std::string a=argv[i];auto val=[&](){if(++i>=argc)throw std::runtime_error("missing arg");return std::string(argv[i]);};
        if(a=="--seed-graph")o.seed_graph=val();
        else if(a=="--out")o.out=val();
        else if(a=="--summary")o.summary=val();
        else if(a=="--mode")o.mode=val();
        else if(a=="--seed")o.seed=std::stoull(val());
        else if(a=="--steps")o.steps=std::stoll(val());
        else if(a=="--restarts")o.restarts=std::stoi(val());
        else if(a=="--slack")o.slack=std::stoi(val());
        else if(a=="--shape-threshold")o.shape_threshold=std::stoi(val());
        else if(a=="--kick-percent")o.kick_percent=std::stoi(val());
        else if(a=="--tradeoff")o.tradeoff=std::stoi(val());
        else if(a=="--self-test"){self_test();std::exit(0);} else throw std::runtime_error("unknown arg "+a);
    }
    if(o.seed_graph.empty())throw std::runtime_error("--seed-graph required");
    if(o.mode!="p4" && o.mode!="profile" && o.mode!="defect")throw std::runtime_error("mode defect|p4|profile");
    return o;
}

static void kick(Graph& g,std::mt19937_64& rng,int percent){
    auto edges=all_edges();std::shuffle(edges.begin(),edges.end(),rng);
    int target=M*percent/100,done=0;
    for(auto [u,v]:edges){if(done>=target)break;if(!degree_safe_after_flip(g,u,v))continue;g.flip(u,v);done++;}
}

int main(int argc,char**argv){
    try{
        auto opt=options(argc,argv);auto edges=all_edges();std::mt19937_64 rng(opt.seed);
        Graph seed=parse_json_graph(opt.seed_graph);
        Graph global=seed; long long g4=total_k4(seed),g6=total_i6(seed),gobj=g4+g6;Profile gp=profile4(seed,true);
        long long gdist=profile_distance(gp),gp4=gp[5];write_cert(global,opt.out);
        std::cout<<"initial obj="<<gobj<<" k4="<<g4<<" i6="<<g6<<" p4="<<gp4<<" pdist="<<(double)gdist/PROFILE_DEN<<"\n";
        bool found=false; long long per=std::max<long long>(1,opt.steps/std::max(1,opt.restarts));
        for(int r=0;r<opt.restarts && !found;r++){
            Graph g=global;
            if(r>0) kick(g,rng,opt.kick_percent);
            long long c4=total_k4(g),c6=total_i6(g),obj=c4+c6;Profile pr=profile4(g,true);long long pd=profile_distance(pr);long long p4=pr[5];
            std::array<long long,M> tabu{};long long best_since=0;
            for(long long it=0;it<per;it++){
                if(obj<gobj || (obj==gobj && (opt.mode=="p4" ? p4>gp4 : (opt.mode=="profile" ? pd<gdist : false)))){
                    global=g;g4=c4;g6=c6;gobj=obj;gp=pr;gdist=pd;gp4=p4;write_cert(global,opt.out);best_since=0;
                    std::cout<<"best restart="<<r<<" step="<<it<<" obj="<<obj<<" k4="<<c4<<" i6="<<c6<<" p4="<<p4<<" pdist="<<(double)pd/PROFILE_DEN<<"\n"<<std::flush;
                    if(obj==0){found=true;break;}
                } else best_since++;
                if(best_since>=4LL*N*N){
                    g=global;kick(g,rng,opt.kick_percent);c4=total_k4(g);c6=total_i6(g);obj=c4+c6;pr=profile4(g,true);pd=profile_distance(pr);p4=pr[5];tabu.fill(0);best_since=0;continue;
                }
                bool indep = c4==0 ? true : (c6==0 ? false : (rng()%(c4+c6)>=(uint64_t)c4));
                std::array<int,6> conflict{};int sz=0;
                if(!find_conflict(g,indep,conflict,sz,rng)){indep=!indep;if(!find_conflict(g,indep,conflict,sz,rng))throw std::runtime_error("conflict witness mismatch");}
                struct Cand{int u,v,id;DefDelta d;long long no;uint64_t noise;};
                std::vector<Cand> cs;long long minno=std::numeric_limits<long long>::max();
                for(int x=0;x<sz;x++)for(int y=x+1;y<sz;y++){
                    int u=conflict[x],v=conflict[y];if(indep ? g.edge(u,v) : !g.edge(u,v))continue;
                    if(!degree_safe_after_flip(g,u,v))continue;
                    int id=edge_id(u,v);auto d=defect_delta(g,u,v);long long no=obj+d.dk4+d.di6;
                    bool aspiration=no<gobj;
                    if(tabu[id]>r*per+it && !aspiration)continue;
                    cs.push_back({u,v,id,d,no,rng()});minno=std::min(minno,no);
                }
                if(cs.empty()){tabu.fill(0);continue;}
                int chosen=-1;long long bestShape=std::numeric_limits<long long>::max();uint64_t bestNoise=0;
                ShapeDelta chosenSd{};bool chosenHasShape=false;
                for(int ci=0;ci<(int)cs.size();ci++){
                    auto &c=cs[ci];
                    int allow=(obj<=opt.shape_threshold && opt.mode!="defect")?opt.slack:0;
                    if(c.no>minno+allow)continue;
                    long long shape=0;ShapeDelta sd{};bool has=false;
                    if(opt.mode!="defect"){
                        sd=shape_delta(g,c.u,c.v);has=true;
                        if(opt.mode=="p4"){
                            shape=(c.no-minno)*(long long)opt.tradeoff - sd.dp4;
                        }else{
                            Profile q=add_profile(pr,sd.dprofile);long long qd=profile_distance(q);
                            shape=(c.no-minno)*(long long)opt.tradeoff*PROFILE_DEN + qd;
                        }
                    }else shape=(c.no-minno);
                    if(chosen<0 || shape<bestShape || (shape==bestShape && c.no<cs[chosen].no) || (shape==bestShape && c.no==cs[chosen].no && c.noise<bestNoise)){
                        chosen=ci;bestShape=shape;bestNoise=c.noise;chosenSd=sd;chosenHasShape=has;
                    }
                }
                if(chosen<0) continue;
                auto c=cs[chosen];
                if(!chosenHasShape) chosenSd=shape_delta(g,c.u,c.v);
                g.flip(c.u,c.v); c4+=c.d.dk4; c6+=c.d.di6; obj=c.no;
                pr=add_profile(pr,chosenSd.dprofile);p4+=chosenSd.dp4;pd=profile_distance(pr);
                tabu[c.id]=r*per+it+24+(rng()%25);
            }
        }
        long long v4=total_k4(global),v6=total_i6(global);Profile vp=profile4(global,true);
        if(v4!=g4||v6!=g6||vp!=gp)throw std::runtime_error("final incremental recount mismatch");
        std::ofstream s(opt.summary);s<<"{\n"
          <<"  \"seed\": "<<opt.seed<<",\n  \"mode\": \""<<opt.mode<<"\",\n"
          <<"  \"steps\": "<<opt.steps<<",\n  \"restarts\": "<<opt.restarts<<",\n  \"tradeoff\": "<<opt.tradeoff<<",\n"
          <<"  \"best_defects\": "<<gobj<<",\n  \"k4\": "<<g4<<",\n  \"independent6\": "<<g6<<",\n"
          <<"  \"p4\": "<<gp4<<",\n  \"profile_distance_scaled\": "<<(double)gdist/PROFILE_DEN<<",\n"
          <<"  \"found\": "<<(gobj==0?"true":"false")<<"\n}\n";
        std::cout<<"RESULT obj="<<gobj<<" k4="<<g4<<" i6="<<g6<<" p4="<<gp4<<" pdist="<<(double)gdist/PROFILE_DEN<<" found="<<(gobj==0)<<"\n";
        return gobj==0?0:1;
    }catch(const std::exception& e){std::cerr<<"error: "<<e.what()<<"\n";return 2;}
}
