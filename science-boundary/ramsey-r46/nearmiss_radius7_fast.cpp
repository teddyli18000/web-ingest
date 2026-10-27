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

static bool has_clique(const std::array<U,N>& a, U cand, int k) {
    if (k == 0) return true;
    if (std::popcount(cand) < k) return false;
    while (std::popcount(cand) >= k) {
        U b = cand & -cand;
        int v = std::countr_zero(b);
        cand ^= b;
        if (has_clique(a, cand & a[v], k - 1)) return true;
    }
    return false;
}

static Graph read_graph(const std::string& path) {
    std::ifstream f(path); if(!f) throw std::runtime_error("cannot open seed");
    std::stringstream ss; ss << f.rdbuf(); std::string s=ss.str();
    std::vector<std::string> rows;
    for(size_t i=0;i<s.size();) {
        if(s[i]=='\"') {
            auto j=s.find('\"',i+1); if(j==std::string::npos) break;
            auto t=s.substr(i+1,j-i-1);
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
    int id=0; for(int a=0;a<u;a++) id += N-a-1;
    return id+v-u-1;
}
static std::pair<int,int> edge_uv(int id) {
    for(int u=0;u<N;u++) {
        int z=N-u-1;
        if(id<z) return {u,u+1+id};
        id-=z;
    }
    throw std::runtime_error("bad edge id");
}

int main(int argc,char**argv) {
    if(argc!=3) { std::cerr << "usage: nearmiss_radius7_fast <seed.json> <repair-count>\n"; return 2; }
    int repair_count=std::stoi(argv[2]);
    if(repair_count<4 || repair_count>7) throw std::runtime_error("repair-count must be 4..7");
    Graph base=read_graph(argv[1]);

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
    std::array<int,6> stack{};
    std::vector<std::array<int,6>> sixes;
    auto rec6=[&](auto&& self,U cand,int depth)->void {
        if(depth==6) { sixes.push_back(stack); return; }
        int need=6-depth;
        while(std::popcount(cand)>=need) {
            U b=cand&-cand; int v=std::countr_zero(b); cand^=b;
            stack[depth]=v; self(self,cand&comp[v],depth+1);
        }
    };
    rec6(rec6,FULL,0);
    for(auto vs:sixes) {
        std::vector<int> es;
        for(int i=0;i<6;i++) for(int j=i+1;j<6;j++) es.push_back(edge_id(vs[i],vs[j]));
        defects.push_back(es);
    }
    if(defects.size()!=14 || sixes.size()!=4) throw std::runtime_error("expected frozen 10+4 defect seed");

    U target=(U(1)<<14)-1;
    std::map<int,U> coverage;
    for(int i=0;i<14;i++) for(int e:defects[i]) coverage[e]|=U(1)<<i;
    std::vector<int> repair, external;
    for(int e=0;e<630;e++) (coverage.count(e)?repair:external).push_back(e);
    if(repair.size()!=68 || external.size()!=562) throw std::runtime_error("unexpected repair universe");
    int external_count=7-repair_count;

    uint64_t tested=0, k4free=0;
    bool found=false;
    std::vector<int> hit;
    auto test=[&](const std::vector<int>& edges) {
        Graph g=base;
        for(int id:edges) {
            auto [u,v]=edge_uv(id);
            g.a[u]^=U(1)<<v; g.a[v]^=U(1)<<u;
        }
        tested++;
        if(has_clique(g.a,FULL,4)) return;
        k4free++;
        std::array<U,N> c{};
        for(int i=0;i<N;i++) c[i]=FULL&~g.a[i]&~(U(1)<<i);
        if(!has_clique(c,FULL,6)) { found=true; hit=edges; }
    };

    std::vector<int> chosen;
    auto emit_with_external=[&]() {
        if(external_count==0) { test(chosen); return; }
        std::vector<int> edges=chosen;
        auto add_external=[&](auto&& self,int pos,int need)->void {
            if(found) return;
            if(need==0) { test(edges); return; }
            for(int p=pos;p<=(int)external.size()-need;p++) {
                edges.push_back(external[p]);
                self(self,p+1,need-1);
                edges.pop_back();
                if(found) return;
            }
        };
        add_external(add_external,0,external_count);
    };
    auto gen_repair=[&](auto&& self,int pos,int need,U mask)->void {
        if(found) return;
        if(need==0) { if(mask==target) emit_with_external(); return; }
        for(int p=pos;p<=(int)repair.size()-need;p++) {
            chosen.push_back(repair[p]);
            self(self,p+1,need-1,mask|coverage[repair[p]]);
            chosen.pop_back();
            if(found) return;
        }
    };
    gen_repair(gen_repair,0,repair_count,0);

    std::cout << "{\"radius\":7,\"repair_count\":" << repair_count
              << ",\"external_count\":" << external_count
              << ",\"tested\":" << tested << ",\"k4free\":" << k4free
              << ",\"found\":" << (found?"true":"false") << ",\"hit\":[";
    for(size_t i=0;i<hit.size();i++) {
        auto [u,v]=edge_uv(hit[i]); if(i) std::cout << ',';
        std::cout << '[' << u << ',' << v << ']';
    }
    std::cout << "]}\n";
    return 0;
}
