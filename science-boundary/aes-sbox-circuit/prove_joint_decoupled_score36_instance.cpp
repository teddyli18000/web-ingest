// Exact final checker for a generic transported p008 joint-decoupled score-36 frontier.
//
// Input 1 is an instance emitted by emit_joint_decoupled_instance.py.
// Input 2 is the <=36 CSV emitted by screen_joint_decoupled_instance.cpp and must
// contain only score-36 rows. For each row this checker:
//   * decides whether the output linear lower bound is exactly achievable with the
//     relevant 0/1/2 helper-only XOR/XNOR gates;
//   * enumerates every minimum-support middle correction system and rejects any
//     unexpected rank-deficient minimum support;
//   * adds the exact correction values to the prelinear target set; and
//   * decides the remaining <=2 helper-only prelinear budget exactly.
//
// Exit status 0 means no <=36 variable-cost witness survives and there is no
// unresolved rank/helper-budget case. A printed CANDIDATE is only a component
// witness and still requires full circuit materialization and AES verification.

#include <array>
#include <algorithm>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <map>
#include <sstream>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>
using namespace std;

struct Bits { array<uint64_t,4> w{}; };
static inline void setb(Bits& b,int x){ b.w[x>>6]|=1ULL<<(x&63); }
static inline bool getb(const Bits& b,int x){ return (b.w[x>>6]>>(x&63))&1ULL; }
static inline int pc(const Bits& b){ return __builtin_popcountll(b.w[0])+__builtin_popcountll(b.w[1])+__builtin_popcountll(b.w[2])+__builtin_popcountll(b.w[3]); }

static bool is_input[256];
static array<pair<int,int>,9> planes, outpairs;
static array<int,9> corrections;
static const array<int,9> middle_cols={4,1,2,14,10,8,3,5,13};

struct Row { int front, final, support, pre_lb, out_lb, distance, score; };

static array<uint8_t,256> closure(const Bits& targets){
    array<uint8_t,256> available{};
    for(int i=0;i<8;++i) available[1<<i]=1;
    bool changed=true;
    while(changed){
        changed=false;
        for(int t=1;t<256;++t){
            if(!getb(targets,t)||available[t]) continue;
            for(int a=1;a<256;++a) if(available[a]){
                int b=a^t;
                if(b&&available[b]){ available[t]=1; changed=true; break; }
            }
        }
    }
    return available;
}

static bool closed(const Bits& targets,const array<uint8_t,256>& available){
    for(int t=1;t<256;++t) if(getb(targets,t)&&!available[t]) return false;
    return true;
}

static bool feasible2(const Bits& targets,int helpers){
    auto a0=closure(targets);
    if(closed(targets,a0)) return true;
    if(helpers<=0) return false;
    vector<int> v0;
    for(int x=1;x<256;++x) if(a0[x]) v0.push_back(x);
    bool seen1[256]{};
    for(size_t i=0;i<v0.size();++i) for(size_t j=i+1;j<v0.size();++j){
        int h1=v0[i]^v0[j];
        if(!h1||a0[h1]||getb(targets,h1)||is_input[h1]||seen1[h1]) continue;
        seen1[h1]=true;
        Bits t1=targets; setb(t1,h1); auto a1=closure(t1);
        if(closed(targets,a1)) return true;
        if(helpers==1) continue;
        vector<int> v1;
        for(int x=1;x<256;++x) if(a1[x]) v1.push_back(x);
        bool seen2[256]{};
        for(size_t p=0;p<v1.size();++p) for(size_t q=p+1;q<v1.size();++q){
            int h2=v1[p]^v1[q];
            if(!h2||a1[h2]||getb(targets,h2)||is_input[h2]||seen2[h2]) continue;
            seen2[h2]=true;
            Bits t2=t1; setb(t2,h2);
            if(closed(targets,closure(t2))) return true;
        }
    }
    return false;
}

static pair<int,int> orient(pair<int,int> p,int c){
    int a=p.first,b=p.second;
    if(c==0) return {a,b};
    if(c==1) return {a,a^b};
    return {a^b,b};
}
static pair<int,int> dual(pair<int,int> p,int c){
    int a=p.first,b=p.second;
    if(c==0) return {a,b};
    if(c==1) return {a^b,b};
    return {a,a^b};
}
static array<int,9> decode(int id){
    array<int,9> out{};
    for(int i=8;i>=0;--i){ out[i]=id%3; id/=3; }
    return out;
}

static int rank4(const vector<int>& values){
    int basis[4]{}, rank=0;
    for(int x:values){
        int y=x;
        for(int p=3;p>=0;--p) if((y>>p)&1){
            if(basis[p]) y^=basis[p];
            else { basis[p]=y; ++rank; break; }
        }
    }
    return rank;
}
static int xor_columns(const vector<int>& cols,int selector){
    int out=0;
    for(int i=0;i<(int)cols.size();++i) if((selector>>i)&1) out^=cols[i];
    return out;
}

static array<int,4> wanted_for(const array<int,9>& choices){
    array<int,4> want{};
    for(int i=0;i<9;++i) if(corrections[i])
        for(int j=0;j<4;++j) if((middle_cols[i]>>j)&1) want[j]^=corrections[i];
    for(int i=0;i<9;++i){
        auto [a,b]=planes[i];
        int off=choices[i]==0?0:(choices[i]==1?a:b);
        if(off) for(int j=0;j<4;++j) if((middle_cols[i]>>j)&1) want[j]^=off;
    }
    return want;
}

static bool support_consistent(int mask,const array<int,4>& want,int& nullity){
    vector<int> cols;
    for(int i=0;i<9;++i) if((mask>>i)&1) cols.push_back(middle_cols[i]);
    int s=cols.size(); nullity=s-rank4(cols);
    for(int bit=0;bit<8;++bit){
        int rhs=0;
        for(int j=0;j<4;++j) if((want[j]>>bit)&1) rhs|=1<<j;
        bool hit=false;
        for(int m=0;m<(1<<s);++m) if(xor_columns(cols,m)==rhs){ hit=true; break; }
        if(!hit) return false;
    }
    return true;
}

static bool unique_corrections(int mask,const array<int,4>& want,vector<int>& values){
    vector<int> cols;
    for(int i=0;i<9;++i) if((mask>>i)&1) cols.push_back(middle_cols[i]);
    int s=cols.size();
    if(rank4(cols)!=s) return false;
    values.assign(s,0);
    for(int bit=0;bit<8;++bit){
        int rhs=0;
        for(int j=0;j<4;++j) if((want[j]>>bit)&1) rhs|=1<<j;
        int solution=-1,count=0;
        for(int m=0;m<(1<<s);++m) if(xor_columns(cols,m)==rhs){ solution=m; ++count; }
        if(count!=1) return false;
        for(int i=0;i<s;++i) if((solution>>i)&1) values[i]|=1<<bit;
    }
    return all_of(values.begin(),values.end(),[](int v){ return v!=0; });
}

static Bits prelinear_targets(const array<int,9>& front,const array<int,9>& final){
    Bits targets;
    for(int i=0;i<9;++i) for(int choice:{front[i],final[i]}){
        auto p=orient(planes[i],choice);
        for(int v:{p.first,p.second}) if(v&&!is_input[v]) setb(targets,v);
    }
    return targets;
}
static Bits output_targets(const array<int,9>& final){
    Bits targets;
    for(int i=0;i<9;++i){
        auto p=dual(outpairs[i],final[i]);
        for(int v:{p.first,p.second}) if(v&&!is_input[v]) setb(targets,v);
    }
    return targets;
}

int main(int argc,char** argv){
    if(argc!=3) return 64;
    for(int i=0;i<8;++i) is_input[1<<i]=true;

    ifstream instance(argv[1]);
    if(!instance) return 65;
    for(int i=0;i<9;++i) instance>>planes[i].first>>planes[i].second;
    for(int i=0;i<9;++i) instance>>outpairs[i].first>>outpairs[i].second;
    for(int i=0;i<9;++i) instance>>corrections[i];

    ifstream csv(argv[2]);
    if(!csv) return 66;
    string line; getline(csv,line);
    vector<Row> rows;
    while(getline(csv,line)){
        if(line.empty()) continue;
        replace(line.begin(),line.end(),',',' ');
        stringstream ss(line); Row row;
        if(!(ss>>row.front>>row.final>>row.support>>row.pre_lb>>row.out_lb>>row.distance>>row.score)) return 67;
        if(row.score!=36) return 68;
        rows.push_back(row);
    }

    unordered_map<int,int> exact_output_cost;
    auto output_cost=[&](const Row& row){
        auto it=exact_output_cost.find(row.final);
        if(it!=exact_output_cost.end()) return it->second;
        Bits targets=output_targets(decode(row.final));
        int n=pc(targets), helpers=row.out_lb-n;
        bool exact=helpers>=0&&helpers<=2&&feasible2(targets,helpers);
        int cost=exact?row.out_lb:row.out_lb+1;
        exact_output_cost[row.final]=cost;
        return cost;
    };

    long long systems=0;
    int output_killed=0,target_killed=0,pre_killed=0,rankdef=0,unresolved=0,candidates=0;
    map<int,int> output_hist,support_hist,prehelper_hist;

    for(const Row& row:rows){
        int outcost=output_cost(row);
        ++output_hist[outcost]; ++support_hist[row.support];
        if(row.pre_lb+row.support+outcost>36){ ++output_killed; continue; }

        auto front=decode(row.front), final=decode(row.final);
        auto want=wanted_for(front);
        Bits base=prelinear_targets(front,final);

        for(int mask=0;mask<(1<<9);++mask){
            if(__builtin_popcount((unsigned)mask)!=row.support) continue;
            int nullity=0;
            bool consistent=support_consistent(mask,want,nullity);
            if(consistent&&nullity!=0){ ++rankdef; continue; }

            vector<int> values;
            if(!unique_corrections(mask,want,values)) continue;
            ++systems;
            Bits targets=base;
            for(int v:values) if(v&&!is_input[v]) setb(targets,v);

            int cap=36-row.support-outcost;
            int n=pc(targets);
            if(n>cap){ ++target_killed; continue; }
            int helpers=cap-n;
            ++prehelper_hist[helpers];
            if(helpers<0){ ++target_killed; continue; }
            if(helpers>2){ ++unresolved; continue; }
            if(!feasible2(targets,helpers)){ ++pre_killed; continue; }

            ++candidates;
            cout<<"CANDIDATE front="<<row.front<<" final="<<row.final
                <<" support="<<row.support<<" mask="<<mask
                <<" targets="<<n<<" cap="<<cap<<" helpers="<<helpers<<" values";
            for(int v:values) cout<<' '<<v;
            cout<<'\n';
        }
    }

    cout<<"rows="<<rows.size()<<" systems="<<systems
        <<" output_killed="<<output_killed
        <<" target_killed="<<target_killed
        <<" pre_killed="<<pre_killed
        <<" rankdef="<<rankdef
        <<" unresolved_helpers="<<unresolved
        <<" candidates="<<candidates<<'\n';
    cout<<"output_cost"; for(auto [k,v]:output_hist) cout<<' '<<k<<':'<<v;
    cout<<" support"; for(auto [k,v]:support_hist) cout<<' '<<k<<':'<<v;
    cout<<" prehelper"; for(auto [k,v]:prehelper_hist) cout<<' '<<k<<':'<<v;
    cout<<'\n';

    return (candidates||rankdef||unresolved)?2:0;
}
