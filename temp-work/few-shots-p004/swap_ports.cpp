#include <algorithm>
#include <array>
#include <bitset>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <fstream>
#include <functional>
#include <iomanip>
#include <iostream>
#include <limits>
#include <numeric>
#include <random>
#include <set>
#include <stdexcept>
#include <string>
#include <unordered_set>
#include <utility>
#include <vector>

namespace {
constexpr int Q = 7;
constexpr int D = 5;
constexpr int U = 16807;
constexpr int N = 367;
constexpr int TARGET_PORTS = 9;
constexpr int XWORDS = (N + 63) / 64;
using Dig = std::array<std::uint8_t, D>;
using Foot = std::array<std::uint64_t, XWORDS>;
using Clock = std::chrono::steady_clock;

struct PrivatePair {
    int center;
    int alt;
};
struct PortChoice {
    int center;
    int alt;
    int side; // 0 => H=center,V=alt; 1 => H=alt,V=center
};

int enc(const Dig& d) {
    int v=0;
    for (auto x:d) v=v*Q+x;
    return v;
}
Dig dec(int v) {
    Dig d{};
    for (int i=D-1;i>=0;--i){d[i]=v%Q;v/=Q;}
    return d;
}
bool conflict_digits(const Dig& a,const Dig& b){
    for(int i=0;i<D;++i){int z=(static_cast<int>(a[i])-static_cast<int>(b[i])+Q)%Q;if(z!=0&&z!=1&&z!=Q-1)return false;}
    return true;
}

std::vector<int> load_r(const std::string& path){
    std::ifstream in(path); if(!in) throw std::runtime_error("cannot open R367");
    std::vector<int> r; int a,b,c,d,e;
    while(in>>a>>b>>c>>d>>e) r.push_back(enc(Dig{(uint8_t)a,(uint8_t)b,(uint8_t)c,(uint8_t)d,(uint8_t)e}));
    if(r.size()!=N||std::unordered_set<int>(r.begin(),r.end()).size()!=N) throw std::runtime_error("bad R367");
    return r;
}
std::vector<int> make_x(const std::vector<int>& r,const std::array<Dig,U>& digits){
    std::vector<int>x; x.reserve(N);
    for(int id:r){auto w=digits[id];x.push_back(enc(Dig{(uint8_t)((2-w[1]+Q)%Q),w[3],w[0],(uint8_t)((2-w[2]+Q)%Q),w[4]}));}
    x[267]=enc(Dig{1,5,6,3,5});
    if(std::unordered_set<int>(x.begin(),x.end()).size()!=N) throw std::runtime_error("X duplicates");
    for(int i=0;i<N;++i)for(int j=i+1;j<N;++j)if(conflict_digits(digits[x[i]],digits[x[j]]))throw std::runtime_error("X not independent");
    return x;
}

struct World {
    std::array<Dig,U> digits{};
    std::array<std::array<int,243>,U> nbr{};
    std::array<Foot,U> foot{};
    std::array<std::uint64_t,U> zob{};

    World(const std::vector<int>& x, std::uint64_t seed){
        for(int v=0;v<U;++v) digits[v]=dec(v);
        for(int v=0;v<U;++v){
            int p=0; const auto d=digits[v];
            for(int m=0;m<243;++m){
                int t=m; Dig z=d;
                for(int k=0;k<D;++k){int delta=(t%3)-1;t/=3;z[k]=(z[k]+delta+Q)%Q;}
                nbr[v][p++]=enc(z);
            }
            std::sort(nbr[v].begin(),nbr[v].end());
            if(std::unique(nbr[v].begin(),nbr[v].end())!=nbr[v].end()) throw std::runtime_error("neighborhood duplicates");
        }
        for(int v=0;v<U;++v){
            foot[v].fill(0);
            for(int xi=0;xi<N;++xi) if(conflict_digits(digits[v],digits[x[xi]])) foot[v][xi/64]|=1ull<<(xi%64);
        }
        std::mt19937_64 rng(seed^0x9e3779b97f4a7c15ull);
        for(auto&z:zob)z=rng();
    }
};

bool foot_intersects(const Foot&a,const Foot&b){for(int w=0;w<XWORDS;++w)if(a[w]&b[w])return true;return false;}
void foot_or(Foot&a,const Foot&b){for(int w=0;w<XWORDS;++w)a[w]|=b[w];}

struct State {
    const World* w{};
    std::array<std::uint8_t,U> in{};
    std::array<std::uint16_t,U> cnt{};
    std::set<int> priv;
    std::uint64_t hash=0;

    State()=default;
    State(const World& world,const std::vector<int>& r):w(&world){
        in.fill(0);cnt.fill(0);
        for(int v:r){in[v]=1;hash^=w->zob[v];for(int z:w->nbr[v])++cnt[z];}
        rebuild_private();
    }
    bool is_private(int v)const{return !in[v]&&cnt[v]==1;}
    void rebuild_private(){priv.clear();for(int v=0;v<U;++v)if(is_private(v))priv.insert(v);}
    int unique_private_centers()const{
        std::unordered_set<int>s;s.reserve(priv.size()*2+1);
        for(int q:priv)s.insert(center_of(q));
        return static_cast<int>(s.size());
    }
    int center_of(int q)const{
        int c=-1;
        for(int z:w->nbr[q])if(in[z]){if(c!=-1)throw std::runtime_error("private has multiple centers");c=z;}
        if(c<0)throw std::runtime_error("private has no center");
        return c;
    }
    std::vector<PrivatePair> private_pairs()const{
        std::vector<PrivatePair> out;out.reserve(priv.size());
        for(int q:priv)out.push_back({center_of(q),q});
        return out;
    }
    void swap_points(int center,int alt){
        if(!in[center]||in[alt]||cnt[alt]!=1)throw std::runtime_error("invalid swap");
        std::array<int,486> touched{};int nt=0;
        for(int z:w->nbr[center]){--cnt[z];touched[nt++]=z;}
        in[center]=0;hash^=w->zob[center];
        for(int z:w->nbr[alt]){++cnt[z];touched[nt++]=z;}
        in[alt]=1;hash^=w->zob[alt];
        std::sort(touched.begin(),touched.begin()+nt);
        auto last=std::unique(touched.begin(),touched.begin()+nt);
        for(auto it=touched.begin();it!=last;++it){int v=*it;if(is_private(v))priv.insert(v);else priv.erase(v);}
        // Membership changed for the two endpoints even if one is not reached above due to coding bugs.
        for(int v:{center,alt}){if(is_private(v))priv.insert(v);else priv.erase(v);}
    }
};

bool conflict(const World&w,int a,int b){return conflict_digits(w.digits[a],w.digits[b]);}

bool find_nine_ports(const State& s,std::vector<PortChoice>& sol){
    const auto pairs=s.private_pairs();
    if(pairs.size()<TARGET_PORTS)return false;
    std::unordered_set<int> centers;for(auto&p:pairs)centers.insert(p.center);if(centers.size()<TARGET_PORTS)return false;

    // Order pairs by how constrained their two orientations are against X: smaller footprint first.
    std::vector<int> order(pairs.size());std::iota(order.begin(),order.end(),0);
    auto pc=[](const Foot&f){int c=0;for(auto x:f)c+=std::popcount(x);return c;};
    std::sort(order.begin(),order.end(),[&](int i,int j){
        return pc(s.w->foot[pairs[i].center])+pc(s.w->foot[pairs[i].alt]) < pc(s.w->foot[pairs[j].center])+pc(s.w->foot[pairs[j].alt]);
    });

    std::unordered_set<int> used_centers;
    std::vector<int> hs,vs;
    Foot hu{},vu{};hu.fill(0);vu.fill(0);
    sol.clear();

    std::function<bool(int)> dfs=[&](int pos){
        if(sol.size()==TARGET_PORTS)return true;
        if(pos>=static_cast<int>(order.size()))return false;
        // Upper bound by distinct unused centers remaining.
        std::unordered_set<int> rem;
        for(int k=pos;k<(int)order.size();++k){auto&p=pairs[order[k]];if(!used_centers.count(p.center))rem.insert(p.center);}
        if(sol.size()+rem.size()<TARGET_PORTS)return false;

        for(int kk=pos;kk<(int)order.size();++kk){
            const int oi=order[kk]; const auto p=pairs[oi];
            if(used_centers.count(p.center))continue;
            // Swap current pair into position pos for combination-style recursion.
            std::swap(order[pos],order[kk]);
            const auto pp=pairs[order[pos]];
            for(int side=0;side<2;++side){
                int h=side?pp.alt:pp.center;
                int v=side?pp.center:pp.alt;
                bool ok=true;
                for(int z:hs)if(conflict(*s.w,h,z)){ok=false;break;}
                if(ok)for(int z:vs)if(conflict(*s.w,v,z)){ok=false;break;}
                if(!ok)continue;
                if(foot_intersects(s.w->foot[h],vu)||foot_intersects(s.w->foot[v],hu)||foot_intersects(s.w->foot[h],s.w->foot[v]))continue;
                Foot nhu=hu,nvu=vu;foot_or(nhu,s.w->foot[h]);foot_or(nvu,s.w->foot[v]);
                auto oldhu=hu,oldvu=vu;hu=nhu;vu=nvu;
                used_centers.insert(pp.center);hs.push_back(h);vs.push_back(v);sol.push_back({pp.center,pp.alt,side});
                if(dfs(pos+1))return true;
                sol.pop_back();vs.pop_back();hs.pop_back();used_centers.erase(pp.center);hu=oldhu;vu=oldvu;
            }
            std::swap(order[pos],order[kk]);
        }
        return false;
    };
    return dfs(0);
}

std::vector<int> state_points(const State&s){std::vector<int>v;v.reserve(N);for(int i=0;i<U;++i)if(s.in[i])v.push_back(i);if(v.size()!=N)throw std::runtime_error("state size changed");return v;}

void write_result(const std::string& path,const State&s,const std::vector<PortChoice>&ports,const std::vector<int>&x,long long step,int restart){
    const auto I=state_points(s);
    std::unordered_set<int> pc;for(auto&p:ports)pc.insert(p.center);
    std::vector<int>B;for(int z:I)if(!pc.count(z))B.push_back(z);
    if(B.size()!=N-TARGET_PORTS)throw std::runtime_error("B size mismatch");
    Foot phu{},pvu{};phu.fill(0);pvu.fill(0);
    std::vector<int>ph,pv;
    for(auto&p:ports){int h=p.side?p.alt:p.center,v=p.side?p.center:p.alt;ph.push_back(h);pv.push_back(v);foot_or(phu,s.w->foot[h]);foot_or(pvu,s.w->foot[v]);}
    if(foot_intersects(phu,pvu))throw std::runtime_error("footprint separation failed at emit");
    std::vector<char>A(N,0),Dset(N,0);
    for(int xi=0;xi<N;++xi){if(phu[xi/64]&(1ull<<(xi%64)))Dset[xi]=1;if(pvu[xi/64]&(1ull<<(xi%64)))A[xi]=1;}

    std::ofstream out(path);if(!out)throw std::runtime_error("cannot write result");
    out<<"{\n  \"kind\": \"swap-ports-found\",\n  \"score\": 134770,\n  \"step\": "<<step<<",\n  \"restart\": "<<restart<<",\n  \"private_count\": "<<s.priv.size()<<",\n  \"independent_set\": [";
    for(size_t i=0;i<I.size();++i){if(i)out<<',';out<<I[i];}out<<"],\n  \"ports\": [\n";
    for(size_t i=0;i<ports.size();++i){auto&p=ports[i];out<<"    {\"center\":"<<p.center<<",\"alt\":"<<p.alt<<",\"side\":"<<p.side<<"}"<<(i+1==ports.size()?"\n":",\n");}
    out<<"  ]\n}\n";
}

struct MoveEval{int center,alt,priv,uniq;std::uint64_t hash;};

} // namespace

int main(int argc,char**argv){
    try{
        if(argc<4||argc>7){std::cerr<<"usage: swap_ports R367 OUTPUT_JSON SECONDS [SEED] [RESTART_STEPS] [REPORT_EVERY]\n";return 2;}
        const std::string rpath=argv[1],outpath=argv[2];
        const double seconds=std::stod(argv[3]);
        const std::uint64_t seed=argc>=5?std::stoull(argv[4]):0xC7C7C7ull;
        const int restart_steps=argc>=6?std::stoi(argv[5]):200000;
        const int report_every=argc>=7?std::stoi(argv[6]):100000;
        std::array<Dig,U>digits{};for(int i=0;i<U;++i)digits[i]=dec(i);
        const auto r=load_r(rpath);const auto x=make_x(r,digits);World world(x,seed);State s(world,r);
        std::mt19937_64 rng(seed);
        std::unordered_set<std::uint64_t>visited;visited.reserve(2000000);visited.insert(s.hash);
        const auto t0=Clock::now();
        long long steps=0;int restart=0;int best_priv=s.priv.size(),best_uniq=s.unique_private_centers();
        std::vector<PortChoice>ports;
        if(find_nine_ports(s,ports)){write_result(outpath,s,ports,x,steps,restart);return 0;}
        std::cerr<<"swap start private="<<s.priv.size()<<" unique_centers="<<best_uniq<<"\n";

        int since_restart=0;int last_center=-1;
        while(std::chrono::duration<double>(Clock::now()-t0).count()<seconds){
            auto pp=s.private_pairs();
            if(pp.empty()){s=State(world,r);++restart;since_restart=0;last_center=-1;continue;}
            std::shuffle(pp.begin(),pp.end(),rng);
            const int samples=std::min<int>(pp.size(),32);
            std::vector<MoveEval>evals;evals.reserve(samples);
            for(int i=0;i<samples;++i){auto p=pp[i];if(p.alt==last_center&&pp.size()>1)continue;
                s.swap_points(p.center,p.alt);int pr=s.priv.size(),uq=s.unique_private_centers();auto h=s.hash;s.swap_points(p.alt,p.center);
                evals.push_back({p.center,p.alt,pr,uq,h});
            }
            if(evals.empty()){auto p=pp[0];evals.push_back({p.center,p.alt,(int)s.priv.size(),s.unique_private_centers(),0});}
            int maxscore=std::numeric_limits<int>::min();for(auto&e:evals)maxscore=std::max(maxscore,100*e.uniq+e.priv);
            std::vector<int>choices;
            for(int i=0;i<(int)evals.size();++i){int sc=100*evals[i].uniq+evals[i].priv;if(sc>=maxscore-((rng()%100)<15?105:0))choices.push_back(i);}
            auto e=evals[choices[rng()%choices.size()]];
            // Prefer novel states, but allow revisits to escape local traps.
            if(visited.contains(e.hash)&&evals.size()>1&&(rng()%100)<85){
                bool found=false;
                for(auto&z:evals)if(!visited.contains(z.hash)){e=z;found=true;break;}
                (void)found;
            }
            s.swap_points(e.center,e.alt);visited.insert(s.hash);last_center=e.center;++steps;++since_restart;
            const int uq=s.unique_private_centers();
            if((int)s.priv.size()>best_priv||uq>best_uniq){best_priv=std::max(best_priv,(int)s.priv.size());best_uniq=std::max(best_uniq,uq);std::cerr<<"swap best step="<<steps<<" restart="<<restart<<" private="<<s.priv.size()<<" unique="<<uq<<" visited="<<visited.size()<<"\n";}
            if(uq>=TARGET_PORTS&&find_nine_ports(s,ports)){
                std::cerr<<"swap FOUND step="<<steps<<" restart="<<restart<<" private="<<s.priv.size()<<" unique="<<uq<<"\n";write_result(outpath,s,ports,x,steps,restart);return 0;
            }
            if(report_every>0&&steps%report_every==0)std::cerr<<"swap progress step="<<steps<<" restart="<<restart<<" private="<<s.priv.size()<<" unique="<<uq<<" best_private="<<best_priv<<" best_unique="<<best_uniq<<" visited="<<visited.size()<<" elapsed="<<std::chrono::duration<double>(Clock::now()-t0).count()<<"\n";
            if(since_restart>=restart_steps){s=State(world,r);++restart;since_restart=0;last_center=-1;}
            if(visited.size()>5000000)visited.clear();
        }
        std::ofstream out(outpath);out<<"{\"kind\":\"none\",\"method\":\"5d-private-swap-walk\",\"steps\":"<<steps<<",\"restarts\":"<<restart<<",\"best_private\":"<<best_priv<<",\"best_unique_centers\":"<<best_uniq<<"}\n";
        std::cerr<<"swap NONE steps="<<steps<<" restarts="<<restart<<" best_private="<<best_priv<<" best_unique="<<best_uniq<<"\n";return 0;
    }catch(const std::exception&e){std::cerr<<"error: "<<e.what()<<"\n";return 1;}
}
