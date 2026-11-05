// Exact bounded-radius exchange search on an arbitrary 367-word C7^5 code.
//
// For selected source S and new outside vertex v define owner support
// S(v)={a in S : v is confusable with a}. A replacement adds an independent
// set T outside S and removes union_{v in T} S(v). Its exact prize is
// |T|-|union S(v)|.
//
// An improving replacement with minimal owner count has a connected support
// hypergraph: disconnected components have additive prizes, so at least one
// component is independently improving. Enumerate ALL connected owner-set
// unions of observed supports up to radius R, and search the COMPLETE
// candidate pool P(U)={v: nonempty S(v) subset U} for |U|+1 independent
// outside vertices. No SAT timeout or approximate subset is used.
#include <algorithm>
#include <array>
#include <cstdint>
#include <fstream>
#include <functional>
#include <iostream>
#include <queue>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>
using namespace std;
constexpr int Q=7,D=5,U=16807,N=367;
constexpr array<int,5> POW{1,7,49,343,2401};
using Code=vector<int>;
struct Key{
    array<uint16_t,6> a{};
    bool operator==(const Key&o)const{return a==o.a;}
};
struct KeyHash{
    size_t operator()(const Key&k)const noexcept{
        size_t h=1469598103934665603ull;
        for(auto x:k.a)h=(h^x)*1099511628211ull;
        return h;
    }
};
int sizeKey(const Key&k){int n=0;while(n<6&&k.a[n])++n;return n;}
Key makeKey(vector<uint16_t> u){
    sort(u.begin(),u.end());
    u.erase(unique(u.begin(),u.end()),u.end());
    if(u.size()>5)throw runtime_error("too many owners");
    Key k{};
    for(int i=0;i<(int)u.size();i++)k.a[i]=u[i];
    return k;
}
Code readCode(const string&path){
    ifstream in(path);if(!in)throw runtime_error("missing seed "+path);
    Code a;int v;
    while(in>>v)a.push_back(v);
    if(a.size()!=N)throw runtime_error("seed must have 367 words");
    sort(a.begin(),a.end());
    if(unique(a.begin(),a.end())!=a.end()||a.front()<0||a.back()>=U)
        throw runtime_error("invalid seed ids");
    return a;
}
array<int,D> dec(int x){
    array<int,D>a{};
    for(int k=0;k<D;k++)a[k]=(x/POW[k])%Q;
    return a;
}
bool conf(int x,int y,const vector<array<int,D>>&dig){
    for(int k=0;k<D;k++){
        int d=(dig[x][k]-dig[y][k]+Q)%Q;
        if(d!=0&&d!=1&&d!=6)return false;
    }
    return true;
}
bool independent(const Code& S,const vector<array<int,D>>&dig){
    auto a=S;sort(a.begin(),a.end());
    if(adjacent_find(a.begin(),a.end())!=a.end())return false;
    for(int i=0;i<(int)a.size();i++)
        for(int j=i+1;j<(int)a.size();j++)
            if(conf(a[i],a[j],dig))return false;
    return true;
}
bool findK(Code&pool,int target,const vector<array<int,D>>&dig,Code&out){
    if((int)pool.size()<target)return false;
    Code chosen;
    function<bool(int)> search=[&](int st){
        if((int)chosen.size()==target){out=chosen;return true;}
        if((int)chosen.size()+(int)pool.size()-st<target)return false;
        for(int i=st;i<(int)pool.size();i++){
            bool legal=true;
            for(int x:chosen)if(conf(x,pool[i],dig)){legal=false;break;}
            if(!legal)continue;
            chosen.push_back(pool[i]);
            if(search(i+1))return true;
            chosen.pop_back();
        }
        return false;
    };
    return search(0);
}
void dump(const string&path,const Code&S){
    ofstream o(path);if(!o)throw runtime_error("output witness");
    for(int v:S)o<<v<<'\n';
}
int main(int argc,char**argv)try{
    if(argc!=5)throw runtime_error("usage: connected R=4|5 seed.ids status.json witness.ids");
    int R=stoi(argv[1]);
    if(R<1||R>5)throw runtime_error("radius must be 1..5");
    auto S=readCode(argv[2]);
    vector<array<int,D>>dig(U);
    for(int v=0;v<U;v++)dig[v]=dec(v);
    if(!independent(S,dig))throw runtime_error("source code not independent");

    vector<char> inS(U,0);
    for(int v:S)inS[v]=1;
    vector<vector<uint16_t>> sup(U);
    for(int i=0;i<N;i++){
        auto d=dig[S[i]];
        for(int offset=0;offset<243;offset++){
            int q=offset,v=0;
            for(int j=0;j<D;j++){
                int step=q%3-1;q/=3;
                v+=((d[j]+step+Q)%Q)*POW[j];
            }
            if(!inS[v])sup[v].push_back(i+1);
        }
    }

    unordered_map<Key,Code,KeyHash> groups;
    array<int,12> hist{};
    for(int v=0;v<U;v++){
        if(inS[v])continue;
        int count=sup[v].size();
        if(count==0){
            Code out=S;out.push_back(v);
            if(!independent(out,dig))throw runtime_error("direct witness failed");
            dump(argv[4],out);
            cout<<"FOUND zero-support direct-add "<<v<<"\n";
            return 0;
        }
        hist[count]++;
        if(count>R)continue;
        Key k=makeKey(sup[v]);
        groups[k].push_back(v);
    }
    if(hist[1]!=6||hist[2]!=224||hist[3]!=1499||hist[4]!=3118||hist[5]!=3694)
        throw runtime_error("pinned circular support histogram drift");

    vector<Key> anchors,edges;
    vector<vector<int>> incident(N);
    for(auto&kv:groups){
        anchors.push_back(kv.first);
        if(sizeKey(kv.first)>=2){
            int id=edges.size();edges.push_back(kv.first);
            for(auto a:kv.first.a)if(a)incident[a-1].push_back(id);
        }
    }
    sort(anchors.begin(),anchors.end(),[](const Key&a,const Key&b){
        int x=sizeKey(a),y=sizeKey(b);
        return x==y?a.a<b.a:x>y;
    });

    unordered_set<Key,KeyHash> visited;
    unsigned long long tested=0,pool_count=0,max_pool=0,expansions=0;
    bool found=false;Code witness,added;Key removed{};
    auto poolFor=[&](const Key&u){
        int n=sizeKey(u);
        Code pool;
        for(int mask=1;mask<(1<<n);mask++){
            Key k{};int j=0;
            for(int i=0;i<n;i++)if(mask&(1<<i))k.a[j++]=u.a[i];
            auto it=groups.find(k);
            if(it!=groups.end())pool.insert(pool.end(),it->second.begin(),it->second.end());
        }
        return pool;
    };
    function<void(const Key&)> dfs=[&](const Key&u){
        if(found||!visited.insert(u).second)return;
        int n=sizeKey(u);
        auto pool=poolFor(u);
        max_pool=max<unsigned long long>(max_pool,pool.size());
        if((int)pool.size()>=n+1){
            pool_count++;Code add;
            if(findK(pool,n+1,dig,add)){
                Code out;
                for(int i=0;i<N;i++){
                    if(!binary_search(u.a.begin(),u.a.begin()+n,(uint16_t)(i+1)))
                        out.push_back(S[i]);
                }
                out.insert(out.end(),add.begin(),add.end());
                sort(out.begin(),out.end());
                if(out.size()!=N+1||!independent(out,dig))
                    throw runtime_error("witness independent replay failed");
                witness=out;added=add;removed=u;found=true;return;
            }
        }
        tested++;
        if(n==R)return;
        vector<int> ids;
        for(int i=0;i<n;i++){
            const auto&x=incident[u.a[i]-1];
            ids.insert(ids.end(),x.begin(),x.end());
        }
        sort(ids.begin(),ids.end());ids.erase(unique(ids.begin(),ids.end()),ids.end());
        for(int id:ids){
            vector<uint16_t> merged;
            for(int i=0;i<n;i++)merged.push_back(u.a[i]);
            for(auto x:edges[id].a)if(x)merged.push_back(x);
            sort(merged.begin(),merged.end());
            merged.erase(unique(merged.begin(),merged.end()),merged.end());
            if((int)merged.size()<=n||(int)merged.size()>R)continue;
            Key v=makeKey(merged);
            ++expansions;
            dfs(v);
            if(found)return;
        }
    };
    for(const Key&anchor:anchors){
        dfs(anchor);
        if(found)break;
    }

    if(found)dump(argv[4],witness);
    ofstream o(argv[3]);if(!o)throw runtime_error("status output");
    o<<"{\n\"method\":\"exact-connected-support-exchanges\",\n"
     <<"\"radius\":"<<R<<",\n\"checked_all_connected_owner_states\":"
     <<(found?"false":"true")<<",\n"
     <<"\"states_visited\":"<<visited.size()<<",\n"
     <<"\"pool_tests\":"<<pool_count<<",\n"
     <<"\"max_candidate_pool\":"<<max_pool<<",\n"
     <<"\"expansions\":"<<expansions<<",\n"
     <<"\"improved\":"<<(found?"true":"false")<<",\n"
     <<"\"witness_size\":"<<(found?witness.size():0)<<",\n"
     <<"\"added_vertices\":[";
    for(int i=0;i<(int)added.size();i++)o<<(i?",":"")<<added[i];
    o<<"],\n\"removed_vertices\":[";
    for(int i=0;i<sizeKey(removed);i++)o<<(i?",":"")<<S[removed.a[i]-1];
    o<<"]\n}\n";
    cout<<(found?"FOUND":"NONE")
        <<" radius="<<R<<" connected_states="<<visited.size()
        <<" pool_tests="<<pool_count<<" max_pool="<<max_pool
        <<" witness="<<(found?witness.size():0)<<"\n";
}catch(const exception&e){
    cerr<<"ERROR "<<e.what()<<'\n';return 1;
}
