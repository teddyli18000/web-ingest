#include <algorithm>
#include <array>
#include <bit>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <map>
#include <sstream>
#include <string>
#include <vector>

using U = uint64_t;
static constexpr int N = 36;
static constexpr U FULL = (U(1) << N) - 1;

struct Graph { std::array<U,N> a{}; };

static long long count_cliques(const std::array<U,N>& a, U cand, int k) {
    if (k == 0) return 1;
    if (std::popcount(cand) < k) return 0;
    long long out = 0;
    while (std::popcount(cand) >= k) {
        U b = cand & -cand;
        int v = std::countr_zero(b);
        cand ^= b;
        out += count_cliques(a, cand & a[v], k - 1);
    }
    return out;
}

static std::pair<int,int> defect_counts(const Graph& g) {
    std::array<U,N> comp{};
    for (int i=0;i<N;i++) comp[i] = FULL & ~g.a[i] & ~(U(1)<<i);
    return {(int)count_cliques(g.a, FULL, 4), (int)count_cliques(comp, FULL, 6)};
}

static Graph read_graph(const std::string& path) {
    std::ifstream f(path);
    if (!f) throw std::runtime_error("cannot open seed");
    std::stringstream ss; ss << f.rdbuf(); std::string s = ss.str();
    std::vector<std::string> rows;
    for (size_t i=0;i<s.size();) {
        if (s[i]=='\"') {
            size_t j=s.find('\"',i+1); if(j==std::string::npos) break;
            std::string t=s.substr(i+1,j-i-1);
            if(t.size()==36 && t.find_first_not_of("01")==std::string::npos) rows.push_back(t);
            i=j+1;
        } else i++;
    }
    if(rows.size()!=36) throw std::runtime_error("seed must have 36 binary rows");
    Graph g;
    for(int i=0;i<N;i++) for(int j=0;j<N;j++) if(rows[i][j]=='1') g.a[i]|=U(1)<<j;
    return g;
}

static int edge_id(int u,int v) {
    if(u>v) std::swap(u,v);
    int id=0;
    for(int a=0;a<u;a++) id += N-a-1;
    return id + (v-u-1);
}

static std::pair<int,int> edge_uv(int id) {
    for(int u=0;u<N;u++) {
        int block=N-u-1;
        if(id<block) return {u,u+1+id};
        id-=block;
    }
    throw std::runtime_error("bad edge id");
}

int main(int argc,char**argv) {
    if(argc!=2) { std::cerr << "usage: nearmiss_radius6 <seed.json>\n"; return 2; }
    Graph base=read_graph(argv[1]);
    auto [seed_k4, seed_i6]=defect_counts(base);
    if(seed_k4!=10 || seed_i6!=4) throw std::runtime_error("expected the frozen 10+4 near-miss");

    std::vector<std::vector<int>> defects;
    for(int a=0;a<N;a++) for(int b=a+1;b<N;b++) for(int c=b+1;c<N;c++) for(int d=c+1;d<N;d++) {
        int v[4]={a,b,c,d}; bool ok=true;
        for(int i=0;i<4;i++) for(int j=i+1;j<4;j++) if(!((base.a[v[i]]>>v[j])&1)) ok=false;
        if(ok) {
            std::vector<int> es;
            for(int i=0;i<4;i++) for(int j=i+1;j<4;j++) es.push_back(edge_id(v[i],v[j]));
            defects.push_back(es);
        }
    }
    std::array<U,N> comp{};
    for(int i=0;i<N;i++) comp[i]=FULL&~base.a[i]&~(U(1)<<i);
    std::vector<std::array<int,6>> i6sets;
    std::array<int,6> stack{};
    auto rec_i6=[&](auto&& self,U cand,int depth)->void {
        if(depth==6) { i6sets.push_back(stack); return; }
        int need=6-depth;
        while(std::popcount(cand)>=need) {
            U b=cand&-cand; int v=std::countr_zero(b); cand^=b;
            stack[depth]=v; self(self,cand&comp[v],depth+1);
        }
    };
    rec_i6(rec_i6,FULL,0);
    for(auto vs:i6sets) {
        std::vector<int> es;
        for(int i=0;i<6;i++) for(int j=i+1;j<6;j++) es.push_back(edge_id(vs[i],vs[j]));
        defects.push_back(es);
    }
    if(defects.size()!=14) throw std::runtime_error("unexpected defect count");

    U target=(U(1)<<defects.size())-1;
    std::map<int,U> coverage;
    for(int i=0;i<(int)defects.size();i++) for(int e:defects[i]) coverage[e]|=U(1)<<i;
    std::vector<int> repair, external;
    for(int e=0;e<630;e++) (coverage.count(e)?repair:external).push_back(e);
    if(repair.size()!=68 || external.size()!=562) throw std::runtime_error("unexpected repair universe");

    long long tested=0;
    int best=1000000000,best_k4=0,best_i6=0;
    std::vector<int> best_edges;
    bool found=false;
    auto test=[&](const std::vector<int>& es) {
        Graph g=base;
        for(int id:es) {
            auto [u,v]=edge_uv(id);
            g.a[u]^=U(1)<<v; g.a[v]^=U(1)<<u;
        }
        auto [k4,i6]=defect_counts(g); tested++;
        if(k4+i6<best) { best=k4+i6; best_k4=k4; best_i6=i6; best_edges=es; }
        if(k4+i6==0) found=true;
    };

    std::vector<int> chosen;
    for(int repair_count=4; repair_count<=6 && !found; repair_count++) {
        auto generate=[&](auto&& self,int pos,int need,U mask)->void {
            if(found) return;
            if(need==0) {
                if(mask!=target) return;
                if(repair_count==4) {
                    for(size_t i=0;i<external.size();i++) for(size_t j=i+1;j<external.size();j++) {
                        auto es=chosen; es.push_back(external[i]); es.push_back(external[j]); test(es);
                        if(found) return;
                    }
                } else if(repair_count==5) {
                    for(int e:external) { auto es=chosen; es.push_back(e); test(es); if(found) return; }
                } else test(chosen);
                return;
            }
            if((int)repair.size()-pos<need) return;
            for(int p=pos;p<=(int)repair.size()-need;p++) {
                chosen.push_back(repair[p]);
                self(self,p+1,need-1,mask|coverage[repair[p]]);
                chosen.pop_back();
                if(found) return;
            }
        };
        generate(generate,0,repair_count,0);
    }

    std::cout << "{\"radius\":6,\"tested\":" << tested
              << ",\"found\":" << (found?"true":"false")
              << ",\"best_total\":" << best
              << ",\"best_k4\":" << best_k4
              << ",\"best_independent6\":" << best_i6
              << ",\"best_edges\":[";
    for(size_t i=0;i<best_edges.size();i++) {
        auto [u,v]=edge_uv(best_edges[i]);
        if(i) std::cout << ',';
        std::cout << '[' << u << ',' << v << ']';
    }
    std::cout << "]}\n";
    return 0;
}
