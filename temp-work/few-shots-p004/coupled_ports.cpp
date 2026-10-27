#include <algorithm>
#include <array>
#include <bit>
#include <bitset>
#include <cstdint>
#include <fstream>
#include <functional>
#include <iostream>
#include <limits>
#include <numeric>
#include <queue>
#include <set>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <utility>
#include <vector>

namespace {
constexpr int Q = 7;
constexpr int D = 5;
constexpr int U = 16807;
constexpr int N = 367;
constexpr int K = 9;
constexpr int XWORDS = (N + 63) / 64;
using Dig = std::array<std::uint8_t, D>;
using Foot = std::array<std::uint64_t, XWORDS>;

struct Pair { int center, alt; };
struct Port { int center, alt, side; };

int enc(const Dig& d) {
    int v = 0;
    for (auto x : d) v = v * Q + x;
    return v;
}
Dig dec(int v) {
    Dig d{};
    for (int i = D - 1; i >= 0; --i) { d[i] = v % Q; v /= Q; }
    return d;
}
bool conflict_digits(const Dig& a, const Dig& b) {
    for (int i = 0; i < D; ++i) {
        int z = (static_cast<int>(a[i]) - static_cast<int>(b[i]) + Q) % Q;
        if (z != 0 && z != 1 && z != Q - 1) return false;
    }
    return true;
}

struct World {
    std::array<Dig, U> digits{};
    std::vector<std::array<int,243>> nbr;
    std::array<Foot, U> xfoot{};

    explicit World(const std::vector<int>& x) : nbr(U) {
        for (int v = 0; v < U; ++v) digits[v] = dec(v);
        for (int v = 0; v < U; ++v) {
            int p = 0;
            for (int m = 0; m < 243; ++m) {
                int t = m; Dig z = digits[v];
                for (int d = 0; d < D; ++d) {
                    int delta = (t % 3) - 1; t /= 3;
                    z[d] = static_cast<std::uint8_t>((z[d] + delta + Q) % Q);
                }
                nbr[v][p++] = enc(z);
            }
            std::sort(nbr[v].begin(), nbr[v].end());
        }
        for (int v = 0; v < U; ++v) {
            xfoot[v].fill(0);
            for (int xi = 0; xi < N; ++xi)
                if (conflict_digits(digits[v], digits[x[xi]]))
                    xfoot[v][xi/64] |= 1ull << (xi%64);
        }
    }
};

bool conflict(const World& w, int a, int b) { return conflict_digits(w.digits[a], w.digits[b]); }

std::vector<int> load_r(const std::string& path) {
    std::ifstream in(path); if (!in) throw std::runtime_error("cannot open R367");
    std::vector<int> r; int a,b,c,d,e;
    while (in >> a >> b >> c >> d >> e)
        r.push_back(enc(Dig{(uint8_t)a,(uint8_t)b,(uint8_t)c,(uint8_t)d,(uint8_t)e}));
    if (r.size() != N || std::unordered_set<int>(r.begin(),r.end()).size() != N) throw std::runtime_error("bad R367");
    return r;
}
std::vector<int> make_x(const std::vector<int>& r, const std::array<Dig,U>& digits) {
    std::vector<int> x; x.reserve(N);
    for (int id : r) {
        auto w = digits[id];
        x.push_back(enc(Dig{(uint8_t)((2-w[1]+Q)%Q),w[3],w[0],(uint8_t)((2-w[2]+Q)%Q),w[4]}));
    }
    x[267] = enc(Dig{1,5,6,3,5});
    if (std::unordered_set<int>(x.begin(),x.end()).size() != N) throw std::runtime_error("X duplicate");
    return x;
}

struct StateInfo {
    std::vector<int> points;
    std::vector<Pair> priv;
};

StateInfo analyze_state(const World& w, const std::vector<int>& points) {
    std::array<std::uint16_t,U> cnt{};
    std::array<char,U> in{};
    for (int z : points) { in[z] = 1; for (int q : w.nbr[z]) ++cnt[q]; }
    std::vector<Pair> priv;
    for (int q = 0; q < U; ++q) if (!in[q] && cnt[q] == 1) {
        int center = -1;
        for (int z : w.nbr[q]) if (in[z]) { center = z; break; }
        if (center < 0) throw std::runtime_error("private candidate without center");
        priv.push_back({center,q});
    }
    return {points,priv};
}

std::string state_key(std::vector<int> p) {
    std::sort(p.begin(),p.end());
    std::string s; s.resize(p.size()*2);
    // Collision-free because 0<=v<16807 fits 15 bits.
    for (size_t i=0;i<p.size();++i) { s[2*i]=static_cast<char>(p[i]&255); s[2*i+1]=static_cast<char>((p[i]>>8)&255); }
    return s;
}

int popfoot(const Foot& f) { int c=0; for (auto x:f) c += std::popcount(x); return c; }
bool foot_intersects(const Foot&a,const Foot&b){for(int i=0;i<XWORDS;++i)if(a[i]&b[i])return true;return false;}
void foot_or(Foot&a,const Foot&b){for(int i=0;i<XWORDS;++i)a[i]|=b[i];}

std::vector<int> bad_indices(const Foot& a, const Foot& b) {
    std::vector<int> out;
    for (int w=0;w<XWORDS;++w) {
        std::uint64_t z=a[w]&b[w];
        while(z){int bit=std::countr_zero(z);int i=w*64+bit;if(i<N)out.push_back(i);z&=z-1;}
    }
    return out;
}

bool find_replacements(const World& w, const std::vector<int>& x,
                       const std::vector<int>& bad, const std::vector<Port>& ports,
                       std::vector<int>& repl) {
    if (bad.empty()) { repl.clear(); return true; }
    if (bad.size() > 10) return false;

    Foot retained_mask{}; retained_mask.fill(~0ull);
    // retained_mask should mark retained X positions, not all positions.
    retained_mask.fill(0);
    std::array<char,N> is_bad{};
    for (int i:bad) is_bad[i]=1;
    for (int i=0;i<N;++i) if(!is_bad[i]) retained_mask[i/64]|=1ull<<(i%64);

    std::bitset<U> hu, vu;
    for (const auto& p:ports) {
        int h=p.side?p.alt:p.center, v=p.side?p.center:p.alt;
        for(int q:w.nbr[h]) hu.set(q);
        for(int q:w.nbr[v]) vu.set(q);
    }
    std::bitset<U> forbidden = hu & vu;

    std::vector<int> cand;
    cand.reserve(512);
    std::unordered_set<int> xset(x.begin(),x.end());
    for (int q=0;q<U;++q) {
        if (forbidden.test(q)) continue;
        if (xset.count(q) && !std::any_of(bad.begin(),bad.end(),[&](int i){return x[i]==q;})) continue;
        if (foot_intersects(w.xfoot[q], retained_mask)) continue;
        cand.push_back(q);
    }
    if (cand.size() < bad.size()) return false;

    std::sort(cand.begin(),cand.end(),[&](int a,int b){ return popfoot(w.xfoot[a]) < popfoot(w.xfoot[b]); });
    repl.clear();
    std::function<bool(size_t)> dfs=[&](size_t start){
        if(repl.size()==bad.size())return true;
        if(cand.size()-start < bad.size()-repl.size())return false;
        for(size_t i=start;i<cand.size();++i){
            bool ok=true;for(int z:repl)if(conflict(w,cand[i],z)){ok=false;break;}
            if(!ok)continue;
            repl.push_back(cand[i]);
            if(dfs(i+1))return true;
            repl.pop_back();
        }
        return false;
    };
    return dfs(0);
}

struct SearchBest {
    int bad = std::numeric_limits<int>::max();
    int depth = -1;
    int priv = 0;
    std::vector<int> state;
    std::vector<Port> ports;
};

bool search_ports_and_repair(const World& w, const std::vector<int>& x,
                             const StateInfo& st, int depth,
                             SearchBest& best,
                             std::vector<Port>& solution,
                             std::vector<int>& xprime) {
    if (st.priv.size() < K) return false;
    std::unordered_map<int,int> center_count;
    for(auto&p:st.priv)++center_count[p.center];
    if(center_count.size()<K)return false;

    std::vector<int> order(st.priv.size()); std::iota(order.begin(),order.end(),0);
    std::sort(order.begin(),order.end(),[&](int i,int j){
        const auto&a=st.priv[i];const auto&b=st.priv[j];
        return popfoot(w.xfoot[a.center])+popfoot(w.xfoot[a.alt]) < popfoot(w.xfoot[b.center])+popfoot(w.xfoot[b.alt]);
    });

    std::unordered_set<int> used;
    std::vector<int> hs,vs;
    std::vector<Port> chosen;
    Foot hu{},vu{};hu.fill(0);vu.fill(0);
    long long leaves=0;

    std::function<bool(int)> dfs=[&](int pos){
        if(chosen.size()==K){
            ++leaves;
            auto bad=bad_indices(hu,vu);
            if((int)bad.size()<best.bad){
                best.bad=bad.size();best.depth=depth;best.priv=st.priv.size();best.state=st.points;best.ports=chosen;
                std::cerr<<"coupled best depth="<<depth<<" private="<<st.priv.size()<<" overlap="<<bad.size()<<" leaves="<<leaves<<"\n";
            }
            if(bad.size()>10)return false;
            std::vector<int> repl;
            if(!find_replacements(w,x,bad,chosen,repl))return false;
            xprime=x;
            for(size_t i=0;i<bad.size();++i)xprime[bad[i]]=repl[i];
            if(std::unordered_set<int>(xprime.begin(),xprime.end()).size()!=N)throw std::runtime_error("Xprime duplicates");
            for(int i=0;i<N;++i)for(int j=i+1;j<N;++j)if(conflict(w,xprime[i],xprime[j]))throw std::runtime_error("Xprime repair not independent");
            solution=chosen;
            return true;
        }
        if(pos>=(int)order.size())return false;
        std::unordered_set<int> rem;
        for(int t=pos;t<(int)order.size();++t){auto&p=st.priv[order[t]];if(!used.count(p.center))rem.insert(p.center);}
        if(chosen.size()+rem.size()<K)return false;

        for(int kk=pos;kk<(int)order.size();++kk){
            std::swap(order[pos],order[kk]);
            auto p=st.priv[order[pos]];
            if(!used.count(p.center)){
                for(int side=0;side<2;++side){
                    int h=side?p.alt:p.center,v=side?p.center:p.alt;
                    bool ok=true;for(int z:hs)if(conflict(w,h,z)){ok=false;break;}if(ok)for(int z:vs)if(conflict(w,v,z)){ok=false;break;}if(!ok)continue;
                    auto oldh=hu,oldv=vu;foot_or(hu,w.xfoot[h]);foot_or(vu,w.xfoot[v]);
                    // Branch and bound: current overlap can only grow.
                    int lower=0;for(int ww=0;ww<XWORDS;++ww)lower+=std::popcount(hu[ww]&vu[ww]);
                    if(lower<=std::min(best.bad,10)){
                        used.insert(p.center);hs.push_back(h);vs.push_back(v);chosen.push_back({p.center,p.alt,side});
                        if(dfs(pos+1))return true;
                        chosen.pop_back();vs.pop_back();hs.pop_back();used.erase(p.center);
                    }
                    hu=oldh;vu=oldv;
                }
            }
            std::swap(order[pos],order[kk]);
        }
        return false;
    };
    return dfs(0);
}

void emit(const std::string& path,const std::vector<int>& state,const std::vector<int>& xprime,const std::vector<Port>&ports,int depth,const SearchBest&best){
    std::ofstream out(path);if(!out)throw std::runtime_error("cannot write result");
    out<<"{\n\"kind\":\"coupled-found\",\n\"score\":134770,\n\"depth\":"<<depth<<",\n\"best_overlap_seen\":"<<best.bad<<",\n\"independent_set\":[";
    for(size_t i=0;i<state.size();++i){if(i)out<<',';out<<state[i];}out<<"],\n\"companion_set\":[";
    for(size_t i=0;i<xprime.size();++i){if(i)out<<',';out<<xprime[i];}out<<"],\n\"ports\":[";
    for(size_t i=0;i<ports.size();++i){if(i)out<<',';auto&p=ports[i];out<<"{\"center\":"<<p.center<<",\"alt\":"<<p.alt<<",\"side\":"<<p.side<<"}";}out<<"]\n}\n";
}

} // namespace

int main(int argc,char**argv){
    try{
        if(argc!=4){std::cerr<<"usage: coupled_ports R367 OUTPUT_JSON MAX_DEPTH\n";return 2;}
        int max_depth=std::stoi(argv[3]);if(max_depth<0||max_depth>4)throw std::runtime_error("MAX_DEPTH must be 0..4");
        std::array<Dig,U> d{};for(int i=0;i<U;++i)d[i]=dec(i);
        auto r=load_r(argv[1]);auto x=make_x(r,d);World w(x);
        for(int i=0;i<N;++i)for(int j=i+1;j<N;++j)if(conflict(w,x[i],x[j]))throw std::runtime_error("original X not independent");

        std::vector<std::vector<int>> frontier{r};
        std::unordered_set<std::string> seen;seen.reserve(10000);seen.insert(state_key(r));
        SearchBest best;
        long long states=0;
        for(int depth=0;depth<=max_depth;++depth){
            std::cerr<<"coupled depth="<<depth<<" frontier="<<frontier.size()<<" seen="<<seen.size()<<"\n";
            std::vector<std::vector<int>> next;
            for(const auto& pts:frontier){
                auto st=analyze_state(w,pts);++states;
                if(st.priv.size()>=K){
                    std::vector<Port>ports;std::vector<int>xprime;
                    if(search_ports_and_repair(w,x,st,depth,best,ports,xprime)){
                        std::cerr<<"coupled FOUND depth="<<depth<<" private="<<st.priv.size()<<" overlap_best="<<best.bad<<" states="<<states<<"\n";
                        emit(argv[2],st.points,xprime,ports,depth,best);return 0;
                    }
                }
                if(depth==max_depth)continue;
                for(auto p:st.priv){
                    auto q=pts;auto it=std::find(q.begin(),q.end(),p.center);if(it==q.end())throw std::runtime_error("center absent");*it=p.alt;
                    auto key=state_key(q);if(seen.insert(key).second)next.push_back(std::move(q));
                }
            }
            frontier=std::move(next);
        }
        std::ofstream out(argv[2]);out<<"{\"kind\":\"none\",\"method\":\"coupled-shallow-swap-x-repair\",\"states\":"<<states<<",\"seen\":"<<seen.size()<<",\"best_overlap\":"<<(best.bad==std::numeric_limits<int>::max()?-1:best.bad)<<",\"best_depth\":"<<best.depth<<",\"best_private\":"<<best.priv<<"}\n";
        std::cerr<<"coupled NONE states="<<states<<" seen="<<seen.size()<<" best_overlap="<<(best.bad==std::numeric_limits<int>::max()?-1:best.bad)<<" best_depth="<<best.depth<<" best_private="<<best.priv<<"\n";
        return 0;
    }catch(const std::exception&e){std::cerr<<"error: "<<e.what()<<"\n";return 1;}
}
