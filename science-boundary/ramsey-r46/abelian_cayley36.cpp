#include <bits/stdc++.h>
using namespace std;
using U=uint64_t;

struct Group {
    vector<int> mod;
    int n=1;
    vector<vector<int>> coord;
    Group(vector<int> m):mod(move(m)){
        for(int x:mod)n*=x;
        coord.resize(n);
        for(int id=0;id<n;id++){
            int q=id; coord[id].resize(mod.size());
            for(int i=(int)mod.size()-1;i>=0;i--){ coord[id][i]=q%mod[i]; q/=mod[i]; }
        }
    }
    int id(const vector<int>& c) const { int x=0; for(size_t i=0;i<mod.size();i++) x=x*mod[i]+c[i]; return x; }
    int add(int a,int b) const { vector<int> c(mod.size()); for(size_t i=0;i<mod.size();i++) c[i]=(coord[a][i]+coord[b][i])%mod[i]; return id(c); }
    int neg(int a) const { vector<int> c(mod.size()); for(size_t i=0;i<mod.size();i++) c[i]=(mod[i]-coord[a][i])%mod[i]; return id(c); }
};

static inline bool clique_k(const array<U,36>& adj, U cand, int need){
    if(need==0) return true;
    while(__builtin_popcountll(cand)>=need){
        U b=cand&-cand; int v=__builtin_ctzll(b); cand^=b;
        if(clique_k(adj,cand & adj[v],need-1)) return true;
    }
    return false;
}
static inline bool hasK4(const array<U,36>& a){ return clique_k(a,(1ULL<<36)-1,4); }
static inline bool hasI6(const array<U,36>& a){
    array<U,36> c{}; U full=(1ULL<<36)-1;
    for(int i=0;i<36;i++) c[i]=full & ~a[i] & ~(1ULL<<i);
    return clique_k(c,full,6);
}

int main(){
    // The four abelian group types of order 36 = 2^2 * 3^2.
    vector<vector<int>> types={{36},{4,3,3},{2,2,9},{2,2,3,3}};
    for(auto mods:types){
        Group G(mods); if(G.n!=36) return 2;
        vector<char> seen(36); vector<vector<int>> orbits;
        seen[0]=1;
        for(int d=1;d<36;d++) if(!seen[d]){
            int e=G.neg(d); seen[d]=seen[e]=1;
            if(e==d) orbits.push_back({d}); else orbits.push_back({d,e});
        }
        int m=orbits.size();
        vector<array<U,36>> oa(m);
        for(int o=0;o<m;o++){
            oa[o].fill(0);
            for(int x=0;x<36;x++) for(int d:orbits[o]){
                int y=G.add(x,d); oa[o][x]|=1ULL<<y;
            }
        }
        array<U,36> adj{}; adj.fill(0);
        uint64_t total=1ULL<<m, prev=0, k4free=0, valid=0;
        auto start=chrono::steady_clock::now();
        for(uint64_t t=0;t<total;t++){
            uint64_t gray=t^(t>>1);
            if(t){
                uint64_t diff=gray^prev; int o=__builtin_ctzll(diff);
                for(int v=0;v<36;v++) adj[v]^=oa[o][v];
            }
            prev=gray;
            if(!hasK4(adj)){
                k4free++;
                if(!hasI6(adj)){
                    valid++;
                    cout<<"FOUND mods="; for(int z:mods)cout<<z<<',';
                    cout<<" mask="<<gray<<" orbits="<<m<<"\n";
                    cout<<"{\"adjacency\":[";
                    for(int i=0;i<36;i++){
                        if(i)cout<<','; cout<<'\"';
                        for(int j=0;j<36;j++) cout<<((adj[i]>>j)&1ULL);
                        cout<<'\"';
                    }
                    cout<<"]}\n";
                    return 0;
                }
            }
        }
        double sec=chrono::duration<double>(chrono::steady_clock::now()-start).count();
        cout<<"DONE mods="; for(int z:mods)cout<<z<<',';
        cout<<" orbits="<<m<<" total="<<total<<" k4free="<<k4free
            <<" valid="<<valid<<" sec="<<fixed<<setprecision(3)<<sec<<"\n";
    }
}
