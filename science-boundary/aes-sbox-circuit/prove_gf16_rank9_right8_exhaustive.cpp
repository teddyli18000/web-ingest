// Solver-free exact exclusion of eight distinct right forms in a 9-product
// GF(16) bilinear multiplier over GF(2).
//
// `prove_gf16_right8_semilinear_orbits.py` proves that every weighted support
// surviving the necessary rank-sum inequalities lies in one of the 16 exact
// semilinear autotopism orbits represented below.
//
// For one representative, group the 9 rank-one terms by right form.  Eight
// distinct forms force multiplicities (2,1,1,1,1,1,1,1).  Since bilinear rank
// of GF(16) multiplication is 9, the doubled group must have matrix rank 2;
// otherwise all eight grouped contributions would themselves be rank one and
// give an 8-product multiplier.  The other seven grouped matrices have rank 1.
//
// Each representative has a nonzero y for which the active group-rank sum is
// exactly 4.  Their XOR is the invertible multiplication-by-y matrix, so equality
// in rank subadditivity makes the four rank-one units a basis/dual-basis
// decomposition.  Enumerating all ordered output bases therefore enumerates all
// 20,160 possibilities for that equality (splitting the rank-2 heavy group into
// its two actual rank-one terms when it is active).  Singleton equations then
// propagate grouped matrices.  For all 16 representatives one additional
// unknown rank-one matrix is enough structurally to determine the rest, so the
// only remaining finite branch is over the 225 nonzero rank-one 4x4 matrices.
//
// Every derived grouped matrix is rank-checked and every one of the 15 nonzero
// multiplication-by-y equations is checked.  A witness, if found, is expanded
// back to nine rank-one tensor terms and verified on all 256 input pairs.

#include <bits/stdc++.h>
using namespace std;

struct Rep { array<int,8> S; int heavy; };
static const Rep reps[] = {
{{2,3,4,5,11,12,13,14},4},
{{2,3,5,10,11,12,13,15},11},
{{2,4,5,10,11,12,13,15},12},
{{2,3,4,5,6,10,12,13},13},
{{1,3,7,9,11,13,14,15},11},
{{5,6,7,8,12,13,14,15},12},
{{2,3,7,10,11,13,14,15},11},
{{1,3,4,6,9,11,12,14},14},
{{1,2,5,6,9,10,12,13},2},
{{1,3,5,7,8,10,12,14},8},
{{2,5,6,7,8,9,12,13},6},
{{2,8,9,10,12,13,14,15},9},
{{1,4,6,8,10,11,13,15},8},
{{1,2,3,5,6,10,13,14},10},
{{1,2,4,6,7,9,10,12},9},
{{1,5,6,9,10,12,13,14},14},
};

int gf16mul(int a,int b){
    int p=0; for(int i=0;i<4;i++) if((b>>i)&1) p ^= a<<i;
    for(int d=6;d>=4;--d) if((p>>d)&1){ p ^= 1<<d; p ^= 1<<(d-3); p ^= 1<<(d-4); }
    return p&15;
}
int dot4(int a,int b){ return __builtin_parity((unsigned)(a&b)); }
int rank_vecs(const vector<int>& vs){
    int b[4]={},r=0;
    for(int x:vs){ int y=x; for(int p=3;p>=0;--p) if((y>>p)&1){
        if(b[p]) y^=b[p]; else {b[p]=y;++r;break;}
    }} return r;
}
int mat_rank(uint16_t M){
    vector<int> rows; for(int k=0;k<4;k++) rows.push_back((M>>(4*k))&15);
    return rank_vecs(rows);
}
uint16_t outer(int c,int l){
    uint16_t M=0; for(int k=0;k<4;k++) if((c>>k)&1) M |= (uint16_t)l << (4*k); return M;
}
uint16_t mult_matrix(int y){
    uint16_t M=0;
    for(int i=0;i<4;i++){
        int col=gf16mul(1<<i,y);
        for(int k=0;k<4;k++) if((col>>k)&1) M |= (uint16_t)1 << (4*k+i);
    }
    return M;
}
array<uint16_t,16> MM;

vector<int> active(const Rep& R,int y){
    vector<int>a; for(int i=0;i<8;i++) if(dot4(R.S[i],y)) a.push_back(i); return a;
}
int rho(const Rep&R,int i){return R.S[i]==R.heavy?2:1;}

bool propagate(const Rep&R,array<uint16_t,8>&A,array<char,8>&known){
    bool changed=true;
    while(changed){
        changed=false;
        for(int y=1;y<16;y++){
            auto ac=active(R,y); int ui=-1,uc=0; uint16_t rhs=MM[y];
            for(int i:ac){ if(known[i]) rhs ^= A[i]; else {ui=i;++uc;} }
            if(uc==0){ if(rhs) return false; }
            else if(uc==1){
                int rr=mat_rank(rhs); if(rr!=rho(R,ui)) return false;
                A[ui]=rhs; known[ui]=1; changed=true;
            }
        }
    }
    return true;
}
int closure_count(const Rep&R,array<char,8> known){
    bool ch=true; while(ch){ ch=false; for(int y=1;y<16;y++){
        int ui=-1,uc=0; for(int i:active(R,y)) if(!known[i]){ui=i;++uc;}
        if(uc==1){known[ui]=1;ch=true;}
    }} int n=0;for(char x:known)n+=x;return n;
}

vector<uint16_t> rank1m;
unordered_map<uint16_t,pair<int,int>> rank1factor;

bool verify_all(const Rep&R,const array<uint16_t,8>&A){
    for(int i=0;i<8;i++) if(mat_rank(A[i])!=rho(R,i)) return false;
    for(int y=1;y<16;y++){ uint16_t z=0; for(int i:active(R,y)) z^=A[i]; if(z!=MM[y]) return false; }
    return true;
}

bool extract_terms(const Rep&R,const array<uint16_t,8>&A, vector<tuple<int,int,int>>&terms){
    terms.clear();
    for(int i=0;i<8;i++){
        int r=R.S[i]; uint16_t m=A[i];
        if(rho(R,i)==1){
            auto it=rank1factor.find(m); if(it==rank1factor.end()) return false;
            terms.emplace_back(it->second.second,r,it->second.first);
        } else {
            bool ok=false;
            for(uint16_t p:rank1m){
                uint16_t q=m^p;
                auto itp=rank1factor.find(p),itq=rank1factor.find(q);
                if(itq!=rank1factor.end() && p!=q){
                    // factor map stores (c,l); tensor term is (l,r,c)
                    terms.emplace_back(itp->second.second,r,itp->second.first);
                    terms.emplace_back(itq->second.second,r,itq->second.first);
                    ok=true; break;
                }
            }
            if(!ok) return false;
        }
    }
    if(terms.size()!=9) return false;
    for(int x=0;x<16;x++) for(int y=0;y<16;y++){
        int out=0; for(auto [l,r,c]:terms) if(dot4(l,x)&&dot4(r,y)) out^=c;
        if(out!=gf16mul(x,y)) return false;
    }
    return true;
}

int main(){
    for(int y=0;y<16;y++) MM[y]=mult_matrix(y);
    for(int c=1;c<16;c++) for(int l=1;l<16;l++){
        uint16_t m=outer(c,l); rank1m.push_back(m); rank1factor[m]={c,l};
    }
    sort(rank1m.begin(),rank1m.end());
    rank1m.erase(unique(rank1m.begin(),rank1m.end()),rank1m.end());
    if(rank1m.size()!=225) return 90;

    long long total_basis=0,total_guesses=0,total_full=0;
    auto started=chrono::steady_clock::now();
    for(int ri=0;ri<16;ri++){
        const Rep&R=reps[ri];
        int bestY=-1,bestGuess=-1,bestScore=-1;
        for(int y=1;y<16;y++){
            auto ac=active(R,y); int w=0; for(int i:ac)w+=rho(R,i); if(w!=4)continue;
            array<char,8> known{}; for(int i:ac)known[i]=1;
            bool ch=true;
            while(ch){
                ch=false;
                for(int z=1;z<16;z++){
                    int u=-1,n=0;
                    for(int i:active(R,z))if(!known[i]){u=i;n++;}
                    if(n==1){known[u]=1;ch=true;}
                }
            }
            for(int g=0;g<8;g++) if(!known[g]&&rho(R,g)==1){
                auto k=known; k[g]=1; int sc=closure_count(R,k);
                if(sc>bestScore){bestScore=sc;bestY=y;bestGuess=g;}
            }
        }
        if(bestScore!=8){cerr<<"bad structural rep "<<ri<<" score "<<bestScore<<"\n";return 91;}

        auto ac0=active(R,bestY);
        bool heavyActive=false; int heavyIdx=-1; vector<int> singles;
        for(int i:ac0){ if(rho(R,i)==2){heavyActive=true;heavyIdx=i;} else singles.push_back(i); }
        if((heavyActive&&singles.size()!=2)||(!heavyActive&&singles.size()!=4)) return 92;

        long long bases=0,guesses=0,full=0;
        bool found=false; array<uint16_t,8> foundA{};
        for(int c0=1;c0<16&&!found;c0++)
        for(int c1=1;c1<16&&!found;c1++) if(rank_vecs({c0,c1})==2)
        for(int c2=1;c2<16&&!found;c2++) if(rank_vecs({c0,c1,c2})==3)
        for(int c3=1;c3<16&&!found;c3++) if(rank_vecs({c0,c1,c2,c3})==4){
            ++bases;
            int cs[4]={c0,c1,c2,c3}; int coord[16]; fill(begin(coord),end(coord),-1);
            for(int m=0;m<16;m++){
                int v=0; for(int j=0;j<4;j++)if((m>>j)&1)v^=cs[j]; coord[v]=m;
            }
            int ls[4]={};
            for(int ib=0;ib<4;ib++){
                int col=gf16mul(1<<ib,bestY); int mask=coord[col]; if(mask<0)return 93;
                for(int j=0;j<4;j++) if((mask>>j)&1) ls[j]|=1<<ib;
            }
            uint16_t unit[4];
            for(int j=0;j<4;j++){unit[j]=outer(cs[j],ls[j]);if(mat_rank(unit[j])!=1)return 94;}

            array<uint16_t,8>A{}; array<char,8>known{};
            if(heavyActive){
                A[heavyIdx]=unit[0]^unit[1]; known[heavyIdx]=1;
                A[singles[0]]=unit[2]; known[singles[0]]=1;
                A[singles[1]]=unit[3]; known[singles[1]]=1;
            } else {
                for(int j=0;j<4;j++){A[singles[j]]=unit[j];known[singles[j]]=1;}
            }
            if(!propagate(R,A,known)) continue;

            if(known[bestGuess]){
                if(closure_count(R,known)!=8) continue;
                auto AA=A; auto KK=known;
                if(!propagate(R,AA,KK))continue;
                int kc=0; for(char z:KK)kc+=z;
                if(kc==8&&verify_all(R,AA)){found=true;foundA=AA;break;}
                continue;
            }
            for(uint16_t G:rank1m){
                ++guesses;
                auto AA=A; auto KK=known; AA[bestGuess]=G; KK[bestGuess]=1;
                if(!propagate(R,AA,KK))continue;
                int kc=0;for(char z:KK)kc+=z;
                if(kc!=8)continue;
                ++full;
                if(verify_all(R,AA)){found=true;foundA=AA;break;}
            }
        }
        total_basis+=bases; total_guesses+=guesses; total_full+=full;
        cout<<"rep="<<ri<<" y0="<<bestY<<" guess="<<bestGuess
            <<" bases="<<bases<<" guesses="<<guesses<<" full="<<full
            <<" found="<<found<<"\n"<<flush;
        if(found){
            vector<tuple<int,int,int>> terms;
            if(!extract_terms(R,foundA,terms))return 95;
            cout<<"WITNESS";
            for(auto [l,r,c]:terms)cout<<" ("<<l<<","<<r<<","<<c<<")";
            cout<<"\n";
            return 0;
        }
    }
    auto sec=chrono::duration<double>(chrono::steady_clock::now()-started).count();
    cout<<"NO_WITNESS reps=16 total_basis="<<total_basis
        <<" total_guesses="<<total_guesses<<" total_full="<<total_full
        <<" seconds="<<sec<<"\n";
    // Exit zero because complete exclusion is the expected verified result.
    return 0;
}
