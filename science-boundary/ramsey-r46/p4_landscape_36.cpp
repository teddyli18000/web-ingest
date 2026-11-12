// Four-vertex P4-biased constructive Ramsey(4,6,36) search.
// Exoo's 2012 Method B deliberately optimized the induced P4 count and
// discovered a genuinely new 34-point family leading to the R(4,6) record.
// Here an exploration stage changes this structural objective, and a
// subsequent quench returns to the exact K4 + independent-six objective.
#include <bits/stdc++.h>
#include <filesystem>
using namespace std;
using ull=uint64_t;
constexpr int N=36;
constexpr ull FULL=(1ull<<N)-1;
bool p4_lut[64];

struct Graph {
    ull a[N]{};
    inline int edge(int u,int v) const {return (a[u]>>v)&1;}
    void flip(int u,int v){a[u]^=1ull<<v;a[v]^=1ull<<u;}
    int edge_count() const {int s=0;for(int i=0;i<N;i++)s+=__builtin_popcountll(a[i]);return s/2;}
    int bad(int* out4=nullptr,int* out6=nullptr)const {
        int k4=0;
        ull c[N];
        for(int i=0;i<N;i++)c[i]=FULL&~a[i]&~(1ull<<i);
        for(int i=0;i<N;i++){
            ull js=a[i]&~((1ull<<(i+1))-1);
            while(js){
                int j=__builtin_ctzll(js);js&=js-1;
                ull common=a[i]&a[j]&~((1ull<<(j+1))-1);
                while(common){
                    int k=__builtin_ctzll(common);common&=common-1;
                    k4+=__builtin_popcountll(common&a[k]);
                }
            }
        }
        auto dfs=[&](auto&& self,ull cand,int depth)->int{
            if(depth==0)return 1;
            int total=0;
            while(__builtin_popcountll(cand)>=depth){
                int v=__builtin_ctzll(cand);cand&=cand-1;
                total+=self(self,cand&c[v],depth-1);
            }
            return total;
        };
        int i6=dfs(dfs,FULL,6);
        if(out4)*out4=k4;
        if(out6)*out6=i6;
        return k4+i6;
    }
};
void initP4(){
    const int pairs[6][2]={{0,1},{0,2},{0,3},{1,2},{1,3},{2,3}};
    for(int bits=0;bits<64;bits++){
        if(__builtin_popcount(unsigned(bits))!=3)continue;
        int deg[4]{};
        for(int k=0;k<6;k++)if((bits>>k)&1){
            deg[pairs[k][0]]++;deg[pairs[k][1]]++;
        }
        sort(deg,deg+4);
        p4_lut[bits]=deg[0]==1&&deg[1]==1&&deg[2]==2&&deg[3]==2;
    }
}
int p4total(const Graph& g){
    int total=0;
    for(int a=0;a<N;a++)for(int b=a+1;b<N;b++)
    for(int c=b+1;c<N;c++)for(int d=c+1;d<N;d++){
        int bits=g.edge(a,b)|(g.edge(a,c)<<1)|(g.edge(a,d)<<2)|
                 (g.edge(b,c)<<3)|(g.edge(b,d)<<4)|(g.edge(c,d)<<5);
        total+=p4_lut[bits];
    }
    return total;
}
int deltaP4(const Graph& g,int u,int v){
    int delta=0,uv=g.edge(u,v);
    for(int a=0;a<N;a++)if(a!=u&&a!=v)
    for(int b=a+1;b<N;b++)if(b!=u&&b!=v){
        int bits=uv|(g.edge(u,a)<<1)|(g.edge(u,b)<<2)|
                 (g.edge(v,a)<<3)|(g.edge(v,b)<<4)|(g.edge(a,b)<<5);
        delta+=int(p4_lut[bits^1])-int(p4_lut[bits]);
    }
    return delta;
}
string toJson(const Graph& g){
    string s="{\"adjacency\":[";
    for(int i=0;i<N;i++){
        if(i)s+=",";
        s+='"';
        for(int j=0;j<N;j++)s+=char('0'+g.edge(i,j));
        s+='"';
    }
    return s+"]}\n";
}
void save(const filesystem::path& p,const Graph& g){
    ofstream f(p);f<<toJson(g);
}
int hamming(const Graph&a,const Graph&b){
    int n=0;for(int i=0;i<N;i++)n+=__builtin_popcountll(a.a[i]^b.a[i]);
    return n/2;
}
struct Search {
    mt19937_64 rng;
    Graph initial,best,high;
    int bestBad,highP4,highBad,bestP4;
    Search(Graph init,uint64_t seed):rng(seed),initial(init),best(init),high(init){
        bestBad=init.bad();bestP4=highP4=p4total(init);highBad=bestBad;
    }
    void run(Graph& current,double lambda,long long steps,int phase){
        int bad=current.bad(),p4=p4total(current),edges=current.edge_count();
        for(long long it=0;it<steps;it++){
            if(it && it%100000==0 && rng()%7==0){
                current=phase==1?high:best;
                bad=current.bad();p4=p4total(current);edges=current.edge_count();
            }
            int u=rng()%N,v=rng()%N;
            if(u==v)continue;
            int dp=deltaP4(current,u,v);
            bool edge=current.edge(u,v);
            current.flip(u,v);
            int newBad=current.bad(),newEdges=edges+(edge?-1:1);
            double entropy=(newEdges-260)*(newEdges-260)-(edges-260)*(edges-260);
            double objective=(newBad-bad)-lambda*dp+0.018*entropy;
            double temp=0.35+2.9*(1.0-(it%100000)/100000.0);
            if(objective>0 && double(rng())/rng.max()>=exp(-objective/temp)){
                current.flip(u,v);
                continue;
            }
            bad=newBad;p4+=dp;edges=newEdges;
            if(bad<bestBad){
                best=current;bestBad=bad;bestP4=p4;
                cout<<"IMPROVED phase="<<phase<<" it="<<it<<" bad="<<bestBad
                    <<" P4="<<p4<<" edges="<<edges
                    <<" edit="<<hamming(initial,best)<<'\n'<<flush;
                if(bad==0)break;
            }
            if(bad<=24 && p4>highP4){
                high=current;highP4=p4;highBad=bad;
            }
            if(it%100000==0){
                assert(p4==p4total(current));
                assert(bad==current.bad());
            }
        }
    }
};

int main(int argc,char**argv){
    assert(argc==7);
    initP4();
    ifstream f(argv[1]);string row;Graph initial;
    for(int i=0;i<N;i++){
        f>>row;assert(row.size()==N);
        for(int j=0;j<N;j++)if(row[j]=='1')initial.a[i]|=1ull<<j;
    }
    double lambda=stod(argv[2]);
    long long explore=stoll(argv[3]),quench=stoll(argv[4]);
    uint64_t seed=stoull(argv[5]);
    filesystem::path out=argv[6];
    filesystem::create_directories(out);
    Search search(initial,seed);
    Graph current=initial;
    int originalP4=search.bestP4,originalBad=search.bestBad;
    cout<<"BASE bad="<<originalBad<<" P4="<<originalP4
        <<" edges="<<initial.edge_count()<<" lambda="<<lambda<<'\n'<<flush;
    search.run(current,lambda,explore,1);
    cout<<"EXPLORE best="<<search.bestBad<<" highP4="<<search.highP4
        <<" highScore="<<search.highBad
        <<" distance="<<hamming(initial,search.high)<<'\n'<<flush;
    current=search.high;
    search.run(current,0.0,quench,2);
    cout<<"QUENCH best="<<search.bestBad<<" bestP4="<<search.bestP4
        <<" highP4="<<search.highP4<<" highScore="<<search.highBad<<'\n'<<flush;
    int k4=0,i6=0;
    assert(search.best.bad(&k4,&i6)==search.bestBad);
    assert(search.high.bad()==search.highBad);
    assert(p4total(search.high)==search.highP4);
    save(out/"best36.json",search.best);
    save(out/"p4-high36.json",search.high);
    ofstream summary(out/"summary.json");
    summary<<"{\"campaign\":\"induced-P4-guided-R46-construction\","
           <<"\"seed\":"<<seed<<",\"lambda\":"<<lambda
           <<",\"initial_bad\":"<<originalBad<<",\"initial_P4\":"<<originalP4
           <<",\"best_bad\":"<<search.bestBad<<",\"best_K4\":"<<k4
           <<",\"best_I6\":"<<i6<<",\"best_P4\":"<<search.bestP4
           <<",\"best_edges\":"<<search.best.edge_count()
           <<",\"best_edit_distance\":"<<hamming(initial,search.best)
           <<",\"high_P4\":"<<search.highP4
           <<",\"high_bad\":"<<search.highBad
           <<",\"high_edges\":"<<search.high.edge_count()
           <<",\"high_edit_distance\":"<<hamming(initial,search.high)
           <<"}\n";
}
