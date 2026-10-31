// Sound compressed exhaustion for odd-perfect (18,0), K=19, kp=15,kc=4.
// This file intentionally contains no fibre quotient.  It enumerates all
// signed c orbits under AGL(1,Z25) and c->-c, solves periodic cross exactly
// through GF(3) RREF plus integer regression, and checks the exact K19 spectra.
#include <bits/stdc++.h>
#include <omp.h>
using namespace std;static constexpr int N=25;using A=array<int,N>;
vector<int> units(){vector<int>u;for(int a=0;a<N;a++)if(gcd(a,N)==1)u.push_back(a);return u;}
A aff(const A&x,int a,int b){A y{};for(int i=0;i<N;i++)y[(a*i+b)%N]=x[i];return y;}string key(const A&x){string s(N,' ');for(int i=0;i<N;i++)s[i]=char(x[i]+1);return s;}
bool crossok(const A&p,const A&c){for(int r=0;r<N;r++){int h=0;for(int i=0;i<N;i++)h+=p[i]*c[(i-r+N)%N]+c[i]*p[(i-r+N)%N];if(h)return false;}return true;}int paf(const A&x,int r){int s=0;for(int i=0;i<N;i++)s+=x[i]*x[(i+r)%N];return s;}
struct RREF{int rank;vector<int>piv,fr;vector<A>row;};
RREF rref3(const A&c){vector<A>a(14);for(auto&r:a)r.fill(0);for(int r=0;r<13;r++)for(int j=0;j<N;j++){int v=(c[(j-r+N)%N]+c[(j+r)%N])%3;if(v<0)v+=3;a[r][j]=v;}for(int j=0;j<N;j++)a[13][j]=1;int rr=0;vector<int>piv;for(int col=0;col<N&&rr<14;col++){int q=-1;for(int i=rr;i<14;i++)if(a[i][col]){q=i;break;}if(q<0)continue;swap(a[rr],a[q]);if(a[rr][col]==2)for(int j=0;j<N;j++)a[rr][j]=(2*a[rr][j])%3;for(int i=0;i<14;i++)if(i!=rr&&a[i][col]){int z=a[i][col];for(int j=0;j<N;j++){a[i][j]=(a[i][j]-z*a[rr][j])%3;if(a[i][j]<0)a[i][j]+=3;}}piv.push_back(col);rr++;}vector<char>isp(N);for(int x:piv)isp[x]=1;vector<int>fr;for(int j=0;j<N;j++)if(!isp[j])fr.push_back(j);return{rr,piv,fr,a};}
int tern(int z){return z==2?-1:z;}
vector<A> c_orbits(){vector<A>reps;unordered_set<string>seen;auto U=units();for(int a0=0;a0<N;a0++)for(int a1=a0+1;a1<N;a1++)for(int a2=a1+1;a2<N;a2++)for(int a3=a2+1;a3<N;a3++){int s[4]={a0,a1,a2,a3};for(int m=0;m<16;m++)if(__builtin_popcount((unsigned)m)==2){A c{};for(int k=0;k<4;k++)c[s[k]]=(m>>k&1)?1:-1;if(seen.count(key(c)))continue;A best=c;string bk=key(c);for(int u:U)for(int b=0;b<N;b++){A y=aff(c,u,b),z=y;for(int&i:z)i=-i;for(auto&w:{y,z}){string kk=key(w);seen.insert(kk);if(kk<bk){bk=kk;best=w;}}}reps.push_back(best);}}return reps;}
const set<vector<int>> BASE={{2,2,2,2,2,2,2,2,3,4,4,4},{2,2,2,2,2,2,2,3,3,3,4,4},{2,2,2,2,2,2,3,3,3,3,3,4},{2,2,2,2,2,3,3,3,3,3,3,3}};
const set<vector<int>> ALT={{1,2,2,2,2,2,2,2,4,4,4,4},{1,2,2,2,2,2,2,3,3,4,4,4},{1,2,2,2,2,2,3,3,3,3,4,4},{1,2,2,2,2,3,3,3,3,3,3,4},{1,2,2,2,3,3,3,3,3,3,3,3},{2,2,2,2,2,2,2,2,2,4,4,5},{2,2,2,2,2,2,2,2,3,3,4,5},{2,2,2,2,2,2,2,2,3,4,4,4},{2,2,2,2,2,2,2,3,3,3,3,5},{2,2,2,2,2,2,2,3,3,3,4,4},{2,2,2,2,2,2,3,3,3,3,3,4},{2,2,2,2,2,3,3,3,3,3,3,3}};
struct Hit{A p,c;bool base,alt;};
int main(){auto reps=c_orbits();if(reps.size()!=88)return 2;atomic<long long>tested{0},valid{0},spectral{0},bh{0},ah{0};atomic<int>r11{0},r13{0};vector<Hit>hits;mutex hm;
#pragma omp parallel for schedule(dynamic,1)
for(int ri=0;ri<(int)reps.size();ri++){A c=reps[ri];auto R=rref3(c);if(R.rank==11)r11++;else if(R.rank==13)r13++;else abort();int d=R.fr.size();uint64_t tot=1;for(int i=0;i<d;i++)tot*=3;tested+=tot;long long lv=0,ls=0;vector<Hit>lh;for(uint64_t code=0;code<tot;code++){uint64_t q=code;array<int,N>z{};for(int k=0;k<d;k++){z[R.fr[k]]=q%3;q/=3;}for(int rr=R.rank-1;rr>=0;rr--){int s=0;for(int fc:R.fr)s=(s+R.row[rr][fc]*z[fc])%3;z[R.piv[rr]]=(3-s)%3;}A p{};int sm=0,nm=0;for(int i=0;i<N;i++){p[i]=tern(z[i]);sm+=p[i];nm+=p[i]*p[i];}if(sm!=9||nm!=15||!crossok(p,c))continue;lv++;vector<int>g;for(int r=1;r<=12;r++)g.push_back(paf(p,r)+paf(c,r));sort(g.begin(),g.end());bool b=BASE.count(g),a=ALT.count(g);if(b||a){ls++;lh.push_back({p,c,b,a});bh+=b;ah+=a;}}valid+=lv;spectral+=ls;if(!lh.empty()){lock_guard<mutex>g(hm);hits.insert(hits.end(),lh.begin(),lh.end());}}
cout<<"K19_KP15_COMPRESSED orbits="<<reps.size()<<" rank11="<<r11<<" rank13="<<r13<<" tested="<<tested<<" exactvalid="<<valid<<" spectral="<<spectral<<" base="<<bh<<" alt="<<ah<<"\n";for(auto&H:hits){cout<<"HIT p=";for(int i=0;i<N;i++)cout<<H.p[i]<<(i==N-1?'|':',');cout<<"c=";for(int i=0;i<N;i++)cout<<H.c[i]<<(i==N-1?'\n':',');}
if(tested!=80779032||valid!=92501||spectral!=1||bh!=0||ah!=1||hits.size()!=1)return 3;
}
