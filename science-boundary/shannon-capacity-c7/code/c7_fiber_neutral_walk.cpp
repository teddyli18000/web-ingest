#include <algorithm>
#include <array>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <random>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {
constexpr int Q=7, D=5, U=16807, N=367, NB=243;
using Nb = std::array<std::uint16_t,NB>;

std::array<int,D> dec(int v){std::array<int,D>a{};for(int i=0;i<D;++i){a[i]=v%Q;v/=Q;}return a;}
int enc(const std::array<int,D>&a){int p=1,v=0;for(int i=0;i<D;++i){v+=a[i]*p;p*=Q;}return v;}
std::vector<Nb> make_nb(){
    std::vector<Nb> out(U);
    for(int v=0;v<U;++v){auto a=dec(v);int k=0;
        for(int d0=-1;d0<=1;++d0)for(int d1=-1;d1<=1;++d1)for(int d2=-1;d2<=1;++d2)
        for(int d3=-1;d3<=1;++d3)for(int d4=-1;d4<=1;++d4){
            std::array<int,D>b{(a[0]+d0+Q)%Q,(a[1]+d1+Q)%Q,(a[2]+d2+Q)%Q,(a[3]+d3+Q)%Q,(a[4]+d4+Q)%Q};
            out[v][k++]=static_cast<std::uint16_t>(enc(b));
        }
        if(k!=NB)throw std::runtime_error("neighborhood drift");
    }
    return out;
}
std::vector<int> parse_ids(const std::string&s){std::istringstream in(s);std::vector<int>a;int x;while(in>>x)a.push_back(x);return a;}
struct Input{int bad=-1;std::vector<int> selected,Dset;};
Input load(const std::string&path){
    std::ifstream in(path);if(!in)throw std::runtime_error("cannot open input");Input z;std::string line;
    while(std::getline(in,line)){
        if(line.rfind("bad ",0)==0)z.bad=std::stoi(line.substr(4));
        else if(line.rfind("selected ",0)==0)z.selected=parse_ids(line.substr(9));
        else if(line.rfind("obstruction ",0)==0)z.Dset=parse_ids(line.substr(12));
    }
    if(z.bad<0||z.bad>=U||z.selected.size()!=N||z.Dset.empty())throw std::runtime_error("bad input");return z;
}
void json_array(std::ostream&os,const std::vector<int>&a){os<<'[';for(size_t i=0;i<a.size();++i){if(i)os<<',';os<<a[i];}os<<']';}
}

int main(int argc,char**argv){
    try{
        if(argc<5){std::cerr<<"usage: neutral_walk INPUT STEPS SEED CHECK_EVERY\n";return 2;}
        auto inp=load(argv[1]);const std::uint64_t max_steps=std::stoull(argv[2]);const std::uint64_t seed=std::stoull(argv[3]);const std::uint64_t check_every=std::stoull(argv[4]);
        auto nb=make_nb();
        std::array<std::uint8_t,U> sel{},ind{},adjbad{};
        for(int v:inp.selected){if(v<0||v>=U||sel[v])throw std::runtime_error("selected drift");sel[v]=1;}
        for(int v:inp.Dset){if(v<0||v>=U)throw std::runtime_error("D range");ind[v]=1;}
        for(auto v:nb[inp.bad])adjbad[v]=1;
        if(!sel[inp.bad]||!ind[inp.bad])throw std::runtime_error("bad point not selected obstruction");
        int hits=0;for(int v=0;v<U;++v)if(sel[v]&&ind[v])++hits;if(hits!=1)throw std::runtime_error("start not one-hit");

        std::array<std::uint16_t,U> cnt{},xo{};
        for(int x=0;x<U;++x)if(sel[x])for(auto u:nb[x]){++cnt[u];xo[u]^=static_cast<std::uint16_t>(x+1);}
        for(int x=0;x<U;++x)if(sel[x]&&cnt[x]!=1)throw std::runtime_error("start not independent");
        auto valid_replacement=[&](int y){
            if(y<0||y>=U||sel[y]||ind[y])return false;
            if(cnt[y]==0)return true;
            return cnt[y]==1&&xo[y]==static_cast<std::uint16_t>(inp.bad+1);
        };
        auto global_replacement=[&](){for(int y=0;y<U;++y)if(valid_replacement(y))return y;return -1;};
        auto local_replacement=[&](int a,int b){for(auto y:nb[a])if(valid_replacement(y))return int(y);for(auto y:nb[b])if(valid_replacement(y))return int(y);return -1;};
        auto emit_found=[&](std::uint64_t step,std::uint64_t accepted,std::uint64_t proposals,int z,int x,int y){
            std::vector<int> out;out.reserve(N);for(int v=0;v<U;++v)if(sel[v]&&v!=inp.bad)out.push_back(v);out.push_back(z);std::sort(out.begin(),out.end());
            std::cout<<"{\"found\":true,\"steps\":"<<step<<",\"accepted\":"<<accepted<<",\"proposals\":"<<proposals<<",\"replacement\":"<<z
                     <<",\"last_swap_remove\":"<<x<<",\"last_swap_add\":"<<y<<",\"selected\":";json_array(std::cout,out);std::cout<<"}\n";
        };
        if(int z=global_replacement();z>=0){emit_found(0,0,0,z,-1,-1);return 0;}

        std::mt19937_64 rng(seed);std::uniform_int_distribution<int> pick(0,U-1);
        int last_removed=-1;std::uint64_t accepted=0,proposals=0,dead_fallbacks=0;int best_blockers=999;
        auto scan_best=[&](){int b=999;for(int y=0;y<U;++y){if(sel[y]||ind[y])continue;int q=int(cnt[y])-(adjbad[y]?1:0);if(q<b)b=q;}return b;};

        for(std::uint64_t step=1;step<=max_steps;++step){
            int y=-1,x=-1;
            for(int tries=0;tries<4096;++tries){++proposals;int q=pick(rng);if(q==last_removed||sel[q]||ind[q]||cnt[q]!=1)continue;int owner=int(xo[q])-1;if(owner<0||owner>=U||!sel[owner]||owner==inp.bad||ind[owner])continue;y=q;x=owner;break;}
            if(y<0){
                ++dead_fallbacks;std::vector<int> cand;
                for(int q=0;q<U;++q){if(q==last_removed||sel[q]||ind[q]||cnt[q]!=1)continue;int owner=int(xo[q])-1;if(owner>=0&&owner<U&&sel[owner]&&owner!=inp.bad&&!ind[owner])cand.push_back(q);}
                if(cand.empty())break;y=cand[rng()%cand.size()];x=int(xo[y])-1;
            }
            sel[x]=0;for(auto u:nb[x]){--cnt[u];xo[u]^=static_cast<std::uint16_t>(x+1);}
            sel[y]=1;for(auto u:nb[y]){++cnt[u];xo[u]^=static_cast<std::uint16_t>(y+1);}
            if(cnt[y]!=1)throw std::runtime_error("swap broke independence");last_removed=x;++accepted;
            if(int z=local_replacement(x,y);z>=0){emit_found(step,accepted,proposals,z,x,y);return 0;}
            if(check_every&&step%check_every==0)best_blockers=std::min(best_blockers,scan_best());
        }
        std::cout<<"{\"found\":false,\"steps\":"<<max_steps<<",\"accepted\":"<<accepted<<",\"proposals\":"<<proposals<<",\"dead_fallbacks\":"<<dead_fallbacks<<",\"best_blockers_diagnostic\":"<<best_blockers<<"}\n";
        return 0;
    }catch(const std::exception&e){std::cerr<<"error: "<<e.what()<<"\n";return 1;}
}
