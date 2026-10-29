// Exact grouped-matrix classification of possible right-factor supports in a
// 9-product GF(16) bilinear multiplier over GF(2).
//
// `classify_gf16_rank9_right_supports.py` first proves that the necessary
// rank-subadditivity condition leaves 385 nine-element supports, partitioned by
// the exact 60-element semilinear tensor-autotopism group into the 11 orbit
// representatives below.
//
// For a fixed support every grouped contribution A_r must have matrix rank one:
// there is exactly one rank-one tensor term using each of the nine distinct right
// forms.  If a nonzero y activates exactly four support forms, their four A_r sum
// to the invertible multiplication-by-y matrix.  Equality in rank subadditivity
// means the four rank-one matrices form a basis/dual-basis decomposition, so all
// 20,160 possibilities are enumerated by ordered output bases.  Singleton matrix
// equations are propagated.  For every representative, at most two additional
// rank-one grouped matrices must be guessed; each has only 225 possibilities.
//
// All remaining matrix ranks and all 15 nonzero multiplication equations are
// checked exactly.  Any positive support is expanded to nine tensor terms and
// independently verified on all 256 GF(16) input pairs.

#include <bits/stdc++.h>
using namespace std;

struct Rep{array<int,9>S;int orbit;};
static const Rep reps[]={
{{1,2,3,4,5,8,9,14,15},30},
{{1,2,3,4,5,8,10,12,15},15},
{{1,2,3,4,5,8,10,13,14},60},
{{1,2,3,4,5,8,11,12,14},15},
{{1,2,3,4,5,8,11,13,15},60},
{{1,2,3,4,5,9,10,12,14},30},
{{1,2,3,4,5,9,10,13,15},60},
{{1,2,3,4,5,10,11,12,13},60},
{{1,2,3,4,6,8,10,13,15},15},
{{1,2,3,4,6,8,11,14,15},30},
{{1,2,3,5,7,9,10,12,13},10},
};

int gf16mul(int a,int b){
    int p=0;for(int i=0;i<4;i++)if((b>>i)&1)p^=a<<i;
    for(int d=6;d>=4;--d)if((p>>d)&1){p^=1<<d;p^=1<<(d-3);p^=1<<(d-4);}
    return p&15;
}
int dot4(int a,int b){return __builtin_parity((unsigned)(a&b));}
int rank_vecs(initializer_list<int> vs){
    int b[4]={},r=0;
    for(int x:vs){int y=x;for(int p=3;p>=0;--p)if((y>>p)&1){
        if(b[p])y^=b[p];else{b[p]=y;r++;break;}
    }}return r;
}
int rank_vec(const vector<int>&vs){
    int b[4]={},r=0;
    for(int x:vs){int y=x;for(int p=3;p>=0;--p)if((y>>p)&1){
        if(b[p])y^=b[p];else{b[p]=y;r++;break;}
    }}return r;
}
uint16_t outer(int c,int l){
    uint16_t M=0;for(int k=0;k<4;k++)if((c>>k)&1)M|=(uint16_t)l<<(4*k);return M;
}
int mat_rank(uint16_t M){
    vector<int>v;for(int k=0;k<4;k++)v.push_back((M>>(4*k))&15);return rank_vec(v);
}
uint16_t multM(int y){
    uint16_t M=0;
    for(int i=0;i<4;i++){
        int col=gf16mul(1<<i,y);
        for(int k=0;k<4;k++)if((col>>k)&1)M|=(uint16_t)1<<(4*k+i);
    }
    return M;
}
array<uint16_t,16> MM;
vector<uint16_t> R1;
unordered_map<uint16_t,pair<int,int>> fac;

vector<int> active(const Rep&R,int y){
    vector<int>a;for(int i=0;i<9;i++)if(dot4(R.S[i],y))a.push_back(i);return a;
}
bool propagate(const Rep&R,array<uint16_t,9>&A,array<char,9>&K){
    bool ch=true;
    while(ch){
        ch=false;
        for(int y=1;y<16;y++){
            int ui=-1,uc=0;uint16_t rhs=MM[y];
            for(int i:active(R,y)){if(K[i])rhs^=A[i];else{ui=i;uc++;}}
            if(uc==0){if(rhs)return false;}
            else if(uc==1){
                if(mat_rank(rhs)!=1)return false;
                A[ui]=rhs;K[ui]=1;ch=true;
            }
        }
    }
    return true;
}
int struct_closure(const Rep&R,array<char,9>K){
    bool ch=true;
    while(ch){
        ch=false;
        for(int y=1;y<16;y++){
            int u=-1,n=0;for(int i:active(R,y))if(!K[i]){u=i;n++;}
            if(n==1){K[u]=1;ch=true;}
        }
    }
    int n=0;for(char x:K)n+=x;return n;
}
bool verify(const Rep&R,const array<uint16_t,9>&A){
    for(int i=0;i<9;i++)if(mat_rank(A[i])!=1)return false;
    for(int y=1;y<16;y++){
        uint16_t z=0;for(int i:active(R,y))z^=A[i];if(z!=MM[y])return false;
    }
    return true;
}
struct Cnt{long long guess1=0,guess2=0,leaves=0;};
bool dfs(const Rep&R,array<uint16_t,9>A,array<char,9>K,int depth,Cnt&cnt,array<uint16_t,9>&out){
    if(!propagate(R,A,K))return false;
    int kc=0;for(char z:K)kc+=z;
    if(kc==9){
        cnt.leaves++;
        if(verify(R,A)){out=A;return true;}
        return false;
    }
    if(depth==2)return false;

    int best=-1,bs=-1;
    for(int g=0;g<9;g++)if(!K[g]){
        auto T=K;T[g]=1;int sc=struct_closure(R,T);
        if(sc>bs){bs=sc;best=g;}
    }
    if(best<0)return false;
    for(uint16_t G:R1){
        if(depth==0)cnt.guess1++;else cnt.guess2++;
        auto AA=A;auto KK=K;AA[best]=G;KK[best]=1;
        if(dfs(R,AA,KK,depth+1,cnt,out))return true;
    }
    return false;
}
vector<tuple<int,int,int>> extract(const Rep&R,const array<uint16_t,9>&A){
    vector<tuple<int,int,int>>t;
    for(int i=0;i<9;i++){
        auto [c,l]=fac[A[i]];
        t.emplace_back(l,R.S[i],c);
    }
    return t;
}

int main(){
    for(int y=0;y<16;y++)MM[y]=multM(y);
    for(int c=1;c<16;c++)for(int l=1;l<16;l++){
        auto m=outer(c,l);R1.push_back(m);fac[m]={c,l};
    }
    sort(R1.begin(),R1.end());R1.erase(unique(R1.begin(),R1.end()),R1.end());
    if(R1.size()!=225)return 90;

    vector<int> found_indices;
    long long total_bases=0,total_g1=0,total_g2=0,total_leaves=0;
    auto whole=chrono::steady_clock::now();
    for(int ri=0;ri<11;ri++){
        const Rep&R=reps[ri];
        int y0=-1;
        for(int y=1;y<16;y++)if(active(R,y).size()==4){y0=y;break;}
        if(y0<0)return 91;
        auto ac=active(R,y0);
        long long bases=0;Cnt cnt;bool found=false;array<uint16_t,9>foundA{};
        auto st=chrono::steady_clock::now();

        for(int c0=1;c0<16&&!found;c0++)
        for(int c1=1;c1<16&&!found;c1++)if(rank_vecs({c0,c1})==2)
        for(int c2=1;c2<16&&!found;c2++)if(rank_vecs({c0,c1,c2})==3)
        for(int c3=1;c3<16&&!found;c3++)if(rank_vecs({c0,c1,c2,c3})==4){
            bases++;
            int cs[4]={c0,c1,c2,c3},coord[16];fill(begin(coord),end(coord),-1);
            for(int m=0;m<16;m++){
                int v=0;for(int j=0;j<4;j++)if((m>>j)&1)v^=cs[j];coord[v]=m;
            }
            int ls[4]={};
            for(int ib=0;ib<4;ib++){
                int mask=coord[gf16mul(1<<ib,y0)];
                if(mask<0)return 92;
                for(int j=0;j<4;j++)if((mask>>j)&1)ls[j]|=1<<ib;
            }
            array<uint16_t,9>A{};array<char,9>K{};
            for(int j=0;j<4;j++){A[ac[j]]=outer(cs[j],ls[j]);K[ac[j]]=1;}
            if(dfs(R,A,K,0,cnt,foundA)){found=true;break;}
        }

        double sec=chrono::duration<double>(chrono::steady_clock::now()-st).count();
        total_bases+=bases;total_g1+=cnt.guess1;total_g2+=cnt.guess2;total_leaves+=cnt.leaves;
        cout<<"rep="<<ri<<" orbit="<<R.orbit<<" y0="<<y0
            <<" bases="<<bases<<" g1="<<cnt.guess1<<" g2="<<cnt.guess2
            <<" leaves="<<cnt.leaves<<" found="<<found<<" sec="<<sec<<"\n"<<flush;
        if(found){
            found_indices.push_back(ri);
            auto terms=extract(R,foundA);
            cout<<"WITNESS";
            for(auto [l,r,c]:terms)cout<<" ("<<l<<","<<r<<","<<c<<")";
            cout<<"\n";
            for(int x=0;x<16;x++)for(int y=0;y<16;y++){
                int z=0;for(auto [l,r,c]:terms)if(dot4(l,x)&&dot4(r,y))z^=c;
                if(z!=gf16mul(x,y))return 93;
            }
        }
    }

    const vector<int> expected={1,8,10};
    if(found_indices!=expected)return 94;
    double sec=chrono::duration<double>(chrono::steady_clock::now()-whole).count();
    cout<<"CLASSIFICATION realizable_orbits=1,8,10 realizable_supports=40"
        <<" total_bases="<<total_bases<<" total_g1="<<total_g1
        <<" total_g2="<<total_g2<<" total_leaves="<<total_leaves
        <<" seconds="<<sec<<"\n";
    return 0;
}
