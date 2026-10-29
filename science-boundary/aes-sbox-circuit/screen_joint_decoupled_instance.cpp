// Helper-aware joint front/final plane frontier for an arbitrary transported
// retained-core p008 instance emitted by emit_joint_decoupled_instance.py.
//
// Usage: ./screen_joint_decoupled_instance instance.txt
// stdout is the complete <=36 frontier as CSV; stderr contains summary counts.

#include <array>
#include <algorithm>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <map>
#include <unordered_set>
#include <utility>
#include <vector>
using namespace std;

struct Bits { array<uint64_t,4> w{}; };
static inline void set_bit(Bits& b,int x){ b.w[x>>6]|=1ULL<<(x&63); }
static inline bool get_bit(const Bits& b,int x){ return (b.w[x>>6]>>(x&63))&1ULL; }
static inline int popcount(const Bits& b){ return __builtin_popcountll(b.w[0])+__builtin_popcountll(b.w[1])+__builtin_popcountll(b.w[2])+__builtin_popcountll(b.w[3]); }

static bool is_input[256];
static array<pair<int,int>,9> planes,outpairs;
static array<int,9> corrections;
static const array<int,9> middle_cols={4,1,2,14,10,8,3,5,13};

static array<uint8_t,256> closure(const Bits& targets){
    array<uint8_t,256> a{}; for(int i=0;i<8;++i)a[1<<i]=1; bool changed=true;
    while(changed){ changed=false; for(int t=1;t<256;++t){
        if(!get_bit(targets,t)||a[t])continue;
        for(int x=1;x<256;++x)if(a[x]){int y=x^t;if(y&&a[y]){a[t]=1;changed=true;break;}}
    }} return a;
}
static bool closed(const Bits& t,const array<uint8_t,256>& a){for(int x=1;x<256;++x)if(get_bit(t,x)&&!a[x])return false;return true;}
static int helper_lb0(const Bits& t){int n=popcount(t);return closed(t,closure(t))?n:n+1;}
static int helper_lb1(const Bits& t){
    int n=popcount(t);auto a=closure(t);if(closed(t,a))return n;
    vector<int>v;for(int x=1;x<256;++x)if(a[x])v.push_back(x);bool seen[256]{};
    for(size_t i=0;i<v.size();++i)for(size_t j=i+1;j<v.size();++j){int h=v[i]^v[j];
        if(!h||a[h]||get_bit(t,h)||is_input[h]||seen[h])continue;seen[h]=1;Bits e=t;set_bit(e,h);if(closed(t,closure(e)))return n+1;}
    return n+2;
}
static pair<int,int> orient(pair<int,int>p,int c){int a=p.first,b=p.second;if(c==0)return{a,b};if(c==1)return{a,a^b};return{a^b,b};}
static pair<int,int> dual(pair<int,int>p,int c){int a=p.first,b=p.second;if(c==0)return{a,b};if(c==1)return{a^b,b};return{a,a^b};}
static int rank4(vector<int> v){int basis[4]{},r=0;for(int x:v){int y=x;for(int p=3;p>=0;--p)if((y>>p)&1){if(basis[p])y^=basis[p];else{basis[p]=y;++r;break;}}}return r;}
static array<int,4> wanted(const array<int,9>& ch){
    array<int,4>w{};for(int i=0;i<9;++i)if(corrections[i])for(int j=0;j<4;++j)if((middle_cols[i]>>j)&1)w[j]^=corrections[i];
    for(int i=0;i<9;++i){auto[a,b]=planes[i];int off=ch[i]==0?0:(ch[i]==1?a:b);if(off)for(int j=0;j<4;++j)if((middle_cols[i]>>j)&1)w[j]^=off;}return w;
}
static int middle_lb(const array<int,9>& ch){
    auto w=wanted(ch);vector<int>rhs;for(int bit=0;bit<8;++bit){int v=0;for(int j=0;j<4;++j)if((w[j]>>bit)&1)v|=1<<j;if(v)rhs.push_back(v);}int rr=rank4(rhs);
    for(int s=0;s<=9;++s)for(int m=0;m<(1<<9);++m){if(__builtin_popcount((unsigned)m)!=s)continue;vector<int>cols;for(int i=0;i<9;++i)if((m>>i)&1)cols.push_back(middle_cols[i]);int r=rank4(cols);if(r<rr)continue;bool ok=true;for(int v:rhs){auto z=cols;z.push_back(v);if(rank4(z)>r){ok=false;break;}}if(ok)return s;}return 99;
}

int main(int argc,char**argv){
    if(argc!=2)return 64;for(int i=0;i<8;++i)is_input[1<<i]=true;
    ifstream in(argv[1]);if(!in)return 65;
    for(int i=0;i<9;++i)in>>planes[i].first>>planes[i].second;
    for(int i=0;i<9;++i)in>>outpairs[i].first>>outpairs[i].second;
    for(int i=0;i<9;++i)in>>corrections[i];

    constexpr int N=19683,U=262144;vector<array<int,9>>choices(N);vector<int>mid(N),outlb(N);vector<Bits>outbits(N);
    for(int id=0;id<N;++id){int z=id;for(int i=8;i>=0;--i){choices[id][i]=z%3;z/=3;}mid[id]=middle_lb(choices[id]);Bits t;for(int i=0;i<9;++i){auto p=dual(outpairs[i],choices[id][i]);for(int v:{p.first,p.second})if(v&&!is_input[v])set_bit(t,v);}outbits[id]=t;outlb[id]=helper_lb0(t);}
    vector<int>prelb(U);vector<Bits>prebits(U);
    for(int id=0;id<U;++id){int z=id;Bits t;for(int i=8;i>=0;--i){int s=z&3;z>>=2;if(s<3){auto p=orient(planes[i],s);for(int v:{p.first,p.second})if(v&&!is_input[v])set_bit(t,v);}else{auto[a,b]=planes[i];for(int v:{a,b,a^b})if(v&&!is_input[v])set_bit(t,v);}}prebits[id]=t;prelb[id]=helper_lb0(t);}
    auto uid=[&](const array<int,9>&f,const array<int,9>&g){int id=0;for(int i=0;i<9;++i)id=(id<<2)|(f[i]==g[i]?f[i]:3);return id;};

    unordered_set<int>us,fs,gs;long long pass0=0;
    for(int f=0;f<N;++f)for(int g=0;g<N;++g){int u=uid(choices[f],choices[g]);if(prelb[u]+mid[f]+outlb[g]<=36){++pass0;us.insert(u);fs.insert(f);gs.insert(g);}}
    for(int u:us)prelb[u]=helper_lb1(prebits[u]);for(int g:gs)outlb[g]=helper_lb1(outbits[g]);
    map<int,long long>scores,dist,mids;long long pass1=0;
    cout<<"front_id,final_id,middle_support,pre_lb,output_lb,distance,score\n";
    for(int f:fs)for(int g:gs){int u=uid(choices[f],choices[g]);if(!us.count(u))continue;int score=prelb[u]+mid[f]+outlb[g];if(score>36)continue;++pass1;++scores[score];++mids[mid[f]];int d=0;for(int i=0;i<9;++i)d+=choices[f][i]!=choices[g][i];++dist[d];cout<<f<<','<<g<<','<<mid[f]<<','<<prelb[u]<<','<<outlb[g]<<','<<d<<','<<score<<'\n';}
    cerr<<"pass0="<<pass0<<" helper_frontier="<<pass1<<" scores";for(auto[k,v]:scores)cerr<<' '<<k<<':'<<v;cerr<<" middle";for(auto[k,v]:mids)cerr<<' '<<k<<':'<<v;cerr<<" distance";for(auto[k,v]:dist)cerr<<' '<<k<<':'<<v;cerr<<'\n';
    return 0;
}
