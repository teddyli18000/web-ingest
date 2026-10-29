// Exact final screen for the helper-aware score-35/36 frontier of the live-field
// independently oriented front/final product-plane family.
//
// Inputs are the CSVs emitted by enumerate_joint_decoupled_frontier.cpp for scores
// 35 and 36.  A retained-core 101 circuit has variable budget 36.
//
// The checker restores the actual middle correction bytes.  It also decides the
// only relevant linear-network helper budgets (0,1,2 helpers) exactly.  It exits
// nonzero if any <=36 variable-cost witness survives.

#include <array>
#include <algorithm>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <map>
#include <sstream>
#include <string>
#include <tuple>
#include <unordered_map>
#include <utility>
#include <vector>

using namespace std;

struct Bits { array<uint64_t,4> w{}; };
static inline void set_bit(Bits& b,int x){ b.w[x>>6]|=1ULL<<(x&63); }
static inline bool get_bit(const Bits& b,int x){ return (b.w[x>>6]>>(x&63))&1ULL; }
static inline int popcount(const Bits& b){ return __builtin_popcountll(b.w[0])+__builtin_popcountll(b.w[1])+__builtin_popcountll(b.w[2])+__builtin_popcountll(b.w[3]); }

static bool is_input[256];
static array<pair<int,int>,9> planes;
static array<pair<int,int>,9> outpairs;
static const array<int,9> middle_cols={4,1,2,14,10,8,3,5,13};
static const int base_correction[9]={8,0,0,202,4,0,34,234,0};

struct Row { int f,g,s,pre_lb,out_lb,distance; };

static vector<Row> read_rows(const string& path){
    ifstream in(path); if(!in) throw runtime_error("cannot open "+path);
    string line; getline(in,line); vector<Row> rows;
    while(getline(in,line)){
        replace(line.begin(),line.end(),',',' '); stringstream ss(line); Row r;
        if(!(ss>>r.f>>r.g>>r.s>>r.pre_lb>>r.out_lb>>r.distance)) throw runtime_error("bad csv row");
        rows.push_back(r);
    }
    return rows;
}

static array<uint8_t,256> closure(const Bits& targets){
    array<uint8_t,256> available{}; for(int i=0;i<8;++i) available[1<<i]=1;
    bool changed=true;
    while(changed){
        changed=false;
        for(int t=1;t<256;++t){
            if(!get_bit(targets,t)||available[t]) continue;
            for(int a=1;a<256;++a){
                if(!available[a]) continue; int b=a^t;
                if(b&&available[b]){ available[t]=1; changed=true; break; }
            }
        }
    }
    return available;
}
static bool closed(const Bits& targets,const array<uint8_t,256>& available){
    for(int t=1;t<256;++t) if(get_bit(targets,t)&&!available[t]) return false;
    return true;
}

// Exact feasibility with at most two helper-only XOR/XNOR gates.  Target wires are
// already charged one gate each and are therefore not counted as helpers.
static bool feasible2(const Bits& targets,int helpers){
    auto a0=closure(targets); if(closed(targets,a0)) return true;
    if(helpers<=0) return false;
    vector<int> v0; for(int x=1;x<256;++x) if(a0[x]) v0.push_back(x);
    bool seen1[256]{};
    for(size_t i=0;i<v0.size();++i) for(size_t j=i+1;j<v0.size();++j){
        int h1=v0[i]^v0[j];
        if(!h1||a0[h1]||get_bit(targets,h1)||is_input[h1]||seen1[h1]) continue;
        seen1[h1]=true; Bits t1=targets; set_bit(t1,h1); auto a1=closure(t1);
        if(closed(targets,a1)) return true;
        if(helpers==1) continue;
        vector<int> v1; for(int x=1;x<256;++x) if(a1[x]) v1.push_back(x);
        bool seen2[256]{};
        for(size_t p=0;p<v1.size();++p) for(size_t q=p+1;q<v1.size();++q){
            int h2=v1[p]^v1[q];
            if(!h2||a1[h2]||get_bit(targets,h2)||is_input[h2]||seen2[h2]) continue;
            seen2[h2]=true; Bits t2=t1; set_bit(t2,h2);
            if(closed(targets,closure(t2))) return true;
        }
    }
    return false;
}

static pair<int,int> orient(pair<int,int> p,int c){
    int a=p.first,b=p.second; if(c==0)return{a,b}; if(c==1)return{a,a^b}; return{a^b,b};
}
static pair<int,int> dual_columns(pair<int,int> p,int c){
    int a=p.first,b=p.second; if(c==0)return{a,b}; if(c==1)return{a^b,b}; return{a,a^b};
}
static array<int,9> decode(int id){
    array<int,9> out{}; for(int i=8;i>=0;--i){out[i]=id%3;id/=3;} return out;
}
static int rank4(const vector<int>& v){
    int basis[4]{},rank=0;
    for(int x:v){ int y=x; for(int p=3;p>=0;--p) if((y>>p)&1){
        if(basis[p]) y^=basis[p]; else {basis[p]=y;++rank;break;}
    }}
    return rank;
}
static int xor_cols(const vector<int>& cols,int selector){
    int out=0; for(int i=0;i<(int)cols.size();++i) if((selector>>i)&1) out^=cols[i]; return out;
}

static Bits pre_union(const array<int,9>& f,const array<int,9>& g){
    Bits t;
    for(int i=0;i<9;++i) for(int c:{f[i],g[i]}){
        auto p=orient(planes[i],c); for(int v:{p.first,p.second}) if(v&&!is_input[v]) set_bit(t,v);
    }
    return t;
}
static Bits output_targets(const array<int,9>& g){
    Bits t;
    for(int i=0;i<9;++i){ auto p=dual_columns(outpairs[i],g[i]);
        for(int v:{p.first,p.second}) if(v&&!is_input[v]) set_bit(t,v); }
    return t;
}
static array<int,4> wanted_for(const array<int,9>& f){
    array<int,4> w{};
    for(int i=0;i<9;++i) if(base_correction[i])
        for(int j=0;j<4;++j) if((middle_cols[i]>>j)&1) w[j]^=base_correction[i];
    for(int i=0;i<9;++i){ auto [a,b]=planes[i]; int off=f[i]==0?0:(f[i]==1?a:b);
        if(off) for(int j=0;j<4;++j) if((middle_cols[i]>>j)&1) w[j]^=off; }
    return w;
}
static bool support_consistent(int mask,const array<int,4>& w,int& nullity){
    vector<int> cols; for(int i=0;i<9;++i) if((mask>>i)&1) cols.push_back(middle_cols[i]);
    int s=cols.size(); nullity=s-rank4(cols);
    for(int bit=0;bit<8;++bit){
        int rhs=0; for(int j=0;j<4;++j) if((w[j]>>bit)&1) rhs|=1<<j;
        bool hit=false; for(int m=0;m<(1<<s);++m) if(xor_cols(cols,m)==rhs){hit=true;break;}
        if(!hit) return false;
    }
    return true;
}

struct Param1 { bool ok=false; int nullity=0; vector<int> base; int kernel=0; };
static Param1 parameterize_le1(int mask,const array<int,4>& w){
    vector<int> cols; for(int i=0;i<9;++i) if((mask>>i)&1) cols.push_back(middle_cols[i]);
    int s=cols.size(); Param1 P; P.nullity=s-rank4(cols); if(P.nullity>1) return P;
    vector<int> kernel; for(int m=1;m<(1<<s);++m) if(xor_cols(cols,m)==0) kernel.push_back(m);
    P.base.assign(s,0);
    for(int bit=0;bit<8;++bit){
        int rhs=0; for(int j=0;j<4;++j) if((w[j]>>bit)&1) rhs|=1<<j;
        vector<int> sols; for(int m=0;m<(1<<s);++m) if(xor_cols(cols,m)==rhs) sols.push_back(m);
        if(sols.empty() || (int)sols.size()!=(1<<P.nullity)) return P;
        int chosen=*min_element(sols.begin(),sols.end());
        for(int i=0;i<s;++i) if((chosen>>i)&1) P.base[i]|=1<<bit;
    }
    if(P.nullity==1){ if(kernel.size()!=1) return P; P.kernel=kernel[0]; }
    else if(!kernel.empty()) return P;
    P.ok=true; return P;
}

static bool unique_corrections(int mask,const array<int,4>& w,vector<int>& vals){
    vector<int> cols; for(int i=0;i<9;++i) if((mask>>i)&1) cols.push_back(middle_cols[i]);
    int s=cols.size(); if(rank4(cols)!=s) return false;
    vals.assign(s,0);
    for(int bit=0;bit<8;++bit){
        int rhs=0; for(int j=0;j<4;++j) if((w[j]>>bit)&1) rhs|=1<<j;
        int sol=-1,cnt=0; for(int m=0;m<(1<<s);++m) if(xor_cols(cols,m)==rhs){sol=m;++cnt;}
        if(cnt!=1) return false;
        for(int i=0;i<s;++i) if((sol>>i)&1) vals[i]|=1<<bit;
    }
    return all_of(vals.begin(),vals.end(),[](int v){return v!=0;});
}

static void init_data(){
    for(int i=0;i<8;++i) is_input[1<<i]=true;
    int x[8]; for(int i=0;i<8;++i) x[i]=1<<i; vector<int> q;
    q.push_back(x[5]^x[0]); q.push_back(x[1]^x[5]); q.push_back(q[1]^x[2]);
    q.push_back(q[2]^x[0]); q.push_back(q[2]^x[6]); q.push_back(x[0]^x[1]);
    q.push_back(q[5]^x[4]); q.push_back(q[6]^q[4]); q.push_back(q[7]^x[3]);
    q.push_back(q[8]^x[7]); q.push_back(q[9]^q[3]); q.push_back(q[9]^q[5]);
    q.push_back(q[10]^x[4]); q.push_back(q[11]^x[6]); q.push_back(q[12]^x[5]);
    q.push_back(q[12]^q[0]); q.push_back(q[14]^q[8]); q.push_back(q[16]^q[10]);
    planes={{{q[11],q[10]},{q[3],q[12]},{q[15],q[2]},{q[8],q[7]},
             {x[6],q[17]},{q[4],x[7]},{q[13],q[16]},{q[9],q[6]},{q[0],q[14]}}};
    const int out[18]={200,230,68,227,185,8,113,183,241,17,64,245,128,16,84,1,136,19};
    for(int i=0;i<9;++i) outpairs[i]={out[i],out[i+9]};
}

int main(int argc,char** argv){
    if(argc!=3) return 64;
    init_data(); auto rows35=read_rows(argv[1]), rows36=read_rows(argv[2]);
    if(rows35.size()!=136 || rows36.size()!=9625) return 2;

    unordered_map<int,int> out_cost;
    auto get_out_cost=[&](const Row& r){
        auto it=out_cost.find(r.g); if(it!=out_cost.end()) return it->second;
        Bits t=output_targets(decode(r.g)); int n=popcount(t), helpers=r.out_lb-n;
        bool ok=helpers>=0&&helpers<=2&&feasible2(t,helpers);
        int cost=ok?r.out_lb:r.out_lb+1; out_cost[r.g]=cost; return cost;
    };

    // Score 35: minimum support and minimum+1 are the only possible sizes.  The
    // exact correction values alone push every pair above 36, so no prelinear
    // helper search is even needed.
    long long assignments35=0, highnull_consistent=0; int survivors35=0; map<int,int> best35;
    map<int,int> out35;
    for(const Row& r:rows35){
        int ocost=get_out_cost(r); ++out35[ocost]; auto f=decode(r.f), g=decode(r.g);
        auto want=wanted_for(f); Bits base=pre_union(f,g); int best=99;
        for(int s=r.s;s<=r.s+1;++s){
            if(r.pre_lb+s+r.out_lb>36) continue;
            for(int mask=0;mask<(1<<9);++mask){
                if(__builtin_popcount((unsigned)mask)!=s) continue;
                int nul=0; bool consistent=support_consistent(mask,want,nul);
                if(consistent&&nul>1){++highnull_consistent;continue;}
                auto P=parameterize_le1(mask,want); if(!P.ok) continue;
                int zmax=P.nullity?256:1;
                for(int z=0;z<zmax;++z){
                    ++assignments35; Bits t=base; bool exact=true;
                    for(int i=0;i<(int)P.base.size();++i){
                        int v=P.base[i]^((P.nullity&&((P.kernel>>i)&1))?z:0);
                        if(!v){exact=false;break;} if(!is_input[v]) set_bit(t,v);
                    }
                    if(exact) best=min(best,popcount(t)+s+ocost);
                }
            }
        }
        ++best35[best]; if(best<=36) ++survivors35;
    }
    // out35 counts rows, not unique outputs; the structural regressions below are
    // the stronger all-row result.
    if(highnull_consistent!=0 || assignments35!=1898065 || survivors35!=0 ||
       best35!=map<int,int>{{37,21},{38,48},{39,66},{40,1}}) return 3;

    // Score 36: any extra support gate is impossible.  If the output lower bound
    // is not achievable exactly, the row dies immediately.  Otherwise enumerate
    // every minimum-size correction support.  Such a support must have full rank;
    // a consistent rank-deficient set would contain a smaller spanning basis and
    // contradict the already verified minimum support.
    int output_killed=0,target_killed=0,pre_killed=0,candidates=0; long long systems36=0;
    map<int,int> out36; unordered_map<int,bool> counted_g;
    for(const Row& r:rows36){
        int ocost=get_out_cost(r); if(!counted_g[r.g]){++out36[ocost];counted_g[r.g]=true;}
        if(r.pre_lb+r.s+ocost>36){++output_killed;continue;}
        auto f=decode(r.f), g=decode(r.g); auto want=wanted_for(f); Bits base=pre_union(f,g);
        for(int mask=0;mask<(1<<9);++mask){
            if(__builtin_popcount((unsigned)mask)!=r.s) continue;
            int nul=0; bool consistent=support_consistent(mask,want,nul);
            if(consistent&&nul!=0) return 4;
            vector<int> vals; if(!unique_corrections(mask,want,vals)) continue;
            ++systems36; Bits t=base; for(int v:vals) if(!is_input[v]) set_bit(t,v);
            int cap=36-r.s-ocost, n=popcount(t);
            if(n>cap){++target_killed;continue;}
            int helpers=cap-n;
            if(helpers<0||helpers>2||!feasible2(t,helpers)){++pre_killed;continue;}
            ++candidates;
            cerr<<"CANDIDATE front="<<r.f<<" final="<<r.g<<" support="<<r.s<<"\n";
        }
    }
    if(candidates!=0 || systems36!=48076 || output_killed!=8829 ||
       target_killed!=48012 || pre_killed!=64 ||
       out36!=map<int,int>{{14,1},{15,79},{16,1557},{17,107}}) return 5;

    cout<<"score35_rows=136 assignments="<<assignments35<<" survivors=0 best_lb";
    for(auto [k,v]:best35) cout<<" "<<k<<":"<<v; cout<<"\n";
    cout<<"score36_rows=9625 systems="<<systems36<<" output_killed="<<output_killed
        <<" target_killed="<<target_killed<<" pre_killed="<<pre_killed<<" candidates=0\n";
    cout<<"conclusion=all_helper_frontier_pairs_excluded_from_101\n";
    return 0;
}
