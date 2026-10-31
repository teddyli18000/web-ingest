#include <bits/stdc++.h>
using namespace std;

struct Bits {
    int n=0,W=0; vector<uint64_t>a;
    Bits(){}
    explicit Bits(int n_,bool fill=false):n(n_),W((n_+63)/64),a(W,fill?~0ULL:0ULL){if(fill&&n%64)a.back()&=((1ULL<<(n%64))-1);}
    bool any()const{for(auto x:a)if(x)return true;return false;}
    void reset(int v){a[v>>6]&=~(1ULL<<(v&63));}
    bool test(int v)const{return (a[v>>6]>>(v&63))&1ULL;}
    int first()const{for(int w=0;w<W;w++)if(a[w])return (w<<6)+__builtin_ctzll(a[w]);return -1;}
    void and_with(const Bits&b){for(int i=0;i<W;i++)a[i]&=b.a[i];}
    void andnot_with(const Bits&b){for(int i=0;i<W;i++)a[i]&=~b.a[i];if(n%64)a.back()&=((1ULL<<(n%64))-1);}
};

struct Solver{
    int n,target; vector<Bits>adj; vector<int>new_to_orig,stack,witness; uint64_t nodes=0;
    chrono::steady_clock::time_point start; double limit_sec; bool timed_out=false;
    Solver(int n_,int t_,vector<Bits>A,vector<int>M,double lim):n(n_),target(t_),adj(move(A)),new_to_orig(move(M)),limit_sec(lim){}
    bool timeout_check(){if((nodes&65535ULL)!=0)return false;double s=chrono::duration<double>(chrono::steady_clock::now()-start).count();if(s>=limit_sec){timed_out=true;return true;}return false;}
    void color_sort(const Bits&P,vector<int>&order,vector<int>&colors){
        order.clear();colors.clear();Bits U=P;int color=0;
        while(U.any()){
            ++color;Bits Q=U;
            while(Q.any()){
                int v=Q.first();order.push_back(v);colors.push_back(color);U.reset(v);Q.reset(v);Q.andnot_with(adj[v]);
            }
        }
    }
    bool expand(Bits P){
        ++nodes;if(timeout_check())return false;vector<int>order,colors;color_sort(P,order,colors);
        for(int i=(int)order.size()-1;i>=0;--i){
            if((int)stack.size()+colors[i]<target)return false;
            int v=order[i];if(!P.test(v))continue;stack.push_back(v);
            if((int)stack.size()>=target){witness=stack;return true;}
            Bits P2=P;P2.and_with(adj[v]);if(P2.any()&&expand(P2))return true;
            stack.pop_back();if(timed_out)return false;P.reset(v);
        }
        return false;
    }
    int solve(){start=chrono::steady_clock::now();Bits P(n,true);bool sat=expand(P);if(sat)return 1;if(timed_out)return-1;return 0;}
};

static int brute_alpha(int n,const vector<pair<int,int>>&conflict){
    vector<uint64_t>bad(n,0);for(auto [u,v]:conflict){bad[u]|=1ULL<<v;bad[v]|=1ULL<<u;}int best=0;
    for(uint64_t m=0;m<(1ULL<<n);++m){int c=__builtin_popcountll(m);if(c<=best)continue;bool ok=true;uint64_t t=m;while(t){int v=__builtin_ctzll(t);t&=t-1;if(bad[v]&m){ok=false;break;}}if(ok)best=c;}
    return best;
}
static int selftest(){
    mt19937_64 rng(1234567);
    for(int tc=0;tc<100;tc++){
        int n=5+rng()%8;vector<pair<int,int>>edges;for(int i=0;i<n;i++)for(int j=i+1;j<n;j++)if((rng()%100)<35)edges.push_back({i,j});int a=brute_alpha(n,edges);
        vector<int>M(n);iota(M.begin(),M.end(),0);vector<Bits>comp;for(int i=0;i<n;i++){comp.emplace_back(n,true);comp.back().reset(i);}for(auto [u,v]:edges){comp[u].reset(v);comp[v].reset(u);}
        for(int k=1;k<=n+1;k++){Solver s(n,k,comp,M,10);int r=s.solve();bool exp=a>=k;if((r==1)!=exp||r==-1){cerr<<"selftest fail tc="<<tc<<" alpha="<<a<<" k="<<k<<" r="<<r<<"\n";return 2;}}
    }
    cerr<<"SELFTEST_OK\n";return 0;
}
int main(int argc,char**argv){
    if(argc>=2&&string(argv[1])=="--selftest")return selftest();
    if(argc<6){cerr<<"usage: solver graph.txt target seed seconds out.json\n";return 2;}
    string path=argv[1],out=argv[5];int target=stoi(argv[2]);uint64_t seed=stoull(argv[3]);double seconds=stod(argv[4]);
    ifstream f(path);int n,filetarget;long long m;f>>n>>m>>filetarget;if(!f||filetarget!=target){cerr<<"bad graph header\n";return 2;}
    vector<pair<int,int>>edges;edges.reserve(m);for(long long e=0;e<m;e++){int u,v;f>>u>>v;edges.push_back({u,v});}if((long long)edges.size()!=m){cerr<<"edge read drift\n";return 2;}
    vector<int>perm(n),inv(n);iota(perm.begin(),perm.end(),0);mt19937_64 rng(seed);shuffle(perm.begin(),perm.end(),rng);for(int i=0;i<n;i++)inv[perm[i]]=i;
    vector<Bits>comp;comp.reserve(n);for(int i=0;i<n;i++){comp.emplace_back(n,true);comp.back().reset(i);}for(auto [ou,ov]:edges){int u=inv[ou],v=inv[ov];comp[u].reset(v);comp[v].reset(u);}
    Solver s(n,target,move(comp),perm,seconds);int status=s.solve();double wall=chrono::duration<double>(chrono::steady_clock::now()-s.start).count();vector<int>wit;for(int v:s.witness)wit.push_back(perm[v]);sort(wit.begin(),wit.end());
    ofstream g(out);g<<"{\n  \"method\": \"exact-tomita-greedy-color-target-clique\",\n  \"n\": "<<n<<",\n  \"conflict_edges\": "<<m<<",\n  \"target\": "<<target<<",\n  \"seed\": "<<seed<<",\n  \"status\": \""<<(status==1?"SAT":status==0?"UNSAT":"UNKNOWN")<<"\",\n  \"nodes\": "<<s.nodes<<",\n  \"wall_seconds\": "<<setprecision(12)<<wall<<",\n  \"witness_indices\": [";for(size_t i=0;i<wit.size();i++){if(i)g<<",";g<<wit[i];}g<<"]\n}\n";
    cerr<<"status="<<(status==1?"SAT":status==0?"UNSAT":"UNKNOWN")<<" nodes="<<s.nodes<<" wall="<<wall<<" witness="<<wit.size()<<"\n";return 0;
}
