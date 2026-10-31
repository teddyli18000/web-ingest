// Exact alternative compressed solver for odd-perfect (18,0): enumerate
// balanced c signs first, solve every p sign vector from the periodic cross
// equations over GF(3), then check the original integer equations and qmin.
// This is especially useful for high-kp splits with small kc.
#include <bits/stdc++.h>
#include <omp.h>
using namespace std;using U=uint32_t;static const U ALL=(1u<<25)-1;static const int N=25;using A=array<int8_t,25>;
U rot(U x,int k){k%=25;return((x<<k)|(x>>(25-k)))&ALL;}U star(U x){U y=0;for(int i=0;i<25;i++)if(x>>i&1)y|=1u<<((25-i)%25);return y;}U mul(U a,U b){U y=0;for(int i=0;i<25;i++)if(a>>i&1)y^=rot(b,i);return y;}
vector<int> units(){vector<int>u;for(int a=1;a<25;a++)if(gcd(a,25)==1)u.push_back(a);return u;}U aff(U x,int a,int b){U y=0;for(int i=0;i<25;i++)if(x>>i&1)y|=1u<<((a*i+b)%25);return y;}
vector<U> orbit_reps(int w){vector<U>reps;unordered_set<U>seen;auto us=units();seen.reserve(5000000);U x=(1u<<w)-1;while(x<(1u<<25)){if(!seen.count(x)){reps.push_back(x);for(int a:us)for(int b=0;b<25;b++)seen.insert(aff(x,a,b));}U c=x&-x,r=x+c;if(!r||r>=(1u<<25))break;x=(((r^x)>>2)/c)|r;}return reps;}
struct Ker{vector<U>b;};Ker kernel(U D){U rows[25]{};U Ds=star(D);for(int j=0;j<25;j++){U col=mul(1u<<j,Ds)^mul(D,star(1u<<j));for(int r=0;r<25;r++)if(col>>r&1)rows[r]|=1u<<j;}int pr=0;vector<int>pc;for(int c=0;c<25&&pr<25;c++){int q=-1;for(int r=pr;r<25;r++)if(rows[r]>>c&1){q=r;break;}if(q<0)continue;swap(rows[pr],rows[q]);for(int r=0;r<25;r++)if(r!=pr&&(rows[r]>>c&1))rows[r]^=rows[pr];pc.push_back(c);pr++;}bool isp[25]{};for(int c:pc)isp[c]=1;Ker K;for(int f=0;f<25;f++)if(!isp[f]){U v=1u<<f;for(int r=0;r<pr;r++)if(rows[r]>>f&1)v|=1u<<pc[r];K.b.push_back(v);}return K;}
vector<pair<int,int>> stabilizer(U E){vector<pair<int,int>>s;auto us=units();for(int a:us)for(int b=0;b<25;b++)if(aff(E,a,b)==E)s.push_back({a,b});return s;}U canon_stab(U P,const vector<pair<int,int>>&st){U z=P;for(auto[a,b]:st)z=min(z,aff(P,a,b));return z;}
static bool crossok(const A&p,const A&c){for(int r=0;r<25;r++){int h=0;for(int i=0;i<25;i++)h+=p[i]*c[(i-r+25)%25]+c[i]*p[(i-r+25)%25];if(h)return false;}return true;}
static int qminG(const A&p,const A&c){int q=0;for(int r=1;r<=12;r++){int g=0;for(int i=0;i<25;i++)g+=p[i]*p[(i+r)%25]+c[i]*c[(i+r)%25];q+=(g*g+(abs(g)&1))/2;}return q;}

// On a fixed p support, solve H_r=0 mod3 (r=0..12) and sum p=0 mod3.
// Free variables are restricted to +/-1 mod3, pivots are derived and also
// required +/-1. Every survivor is then checked with exact integer sum p=9
// and all original periodic cross equations.
static vector<A> solve_p(const vector<int>&pi,const A&c){int np=pi.size();vector<vector<uint8_t>>a(14,vector<uint8_t>(np));for(int j=0;j<np;j++){int pos=pi[j];for(int r=0;r<=12;r++){int z=c[(pos-r+25)%25]+c[(pos+r)%25];z%=3;if(z<0)z+=3;a[r][j]=z;}a[13][j]=1;}
 int rank=0;vector<int>piv;for(int col=0;col<np&&rank<14;col++){int q=-1;for(int r=rank;r<14;r++)if(a[r][col]){q=r;break;}if(q<0)continue;swap(a[rank],a[q]);if(a[rank][col]==2)for(int j=0;j<np;j++)a[rank][j]=(2*a[rank][j])%3;for(int r=0;r<14;r++)if(r!=rank&&a[r][col]){int f=a[r][col];for(int j=0;j<np;j++)a[r][j]=(a[r][j]+6-f*a[rank][j])%3;}piv.push_back(col);rank++;}
 vector<char>isp(np);for(int x:piv)isp[x]=1;vector<int>fr;for(int j=0;j<np;j++)if(!isp[j])fr.push_back(j);int d=fr.size();if(d>24)abort();vector<A>out;uint64_t M=1ULL<<d;vector<int>x(np);
 for(uint64_t m=0;m<M;m++){fill(x.begin(),x.end(),0);for(int k=0;k<d;k++)x[fr[k]]=(m>>k&1)?2:1;bool ok=true;for(int r=rank-1;r>=0;r--){int ss=0;for(int k=0;k<d;k++)ss=(ss+a[r][fr[k]]*x[fr[k]])%3;int z=(3-ss)%3;if(z!=1&&z!=2){ok=false;break;}x[piv[r]]=z;}if(!ok)continue;A p{};int sum=0;for(int j=0;j<np;j++){p[pi[j]]=x[j]==1?1:-1;sum+=p[pi[j]];}if(sum!=9||!crossok(p,c))continue;out.push_back(p);}return out;}

int main(int argc,char**argv){if(argc<4)return 2;int K0=atoi(argv[1]),kp=atoi(argv[2]),t=atoi(argv[3]),kc=K0-kp,m0=K0-25,B=(130-m0*m0)/2;if(K0%2==0||kp%2==0||kc<=0||kc%2||t<0||t>min(kp,kc)||(t&1)||B<0)return 2;int w=K0-2*t,ew=min(w,25-w);bool comp=w>12;auto Es=orbit_reps(ew);atomic<long long>supp{0},csigns{0},psol{0},hits{0};mutex mu;vector<pair<A,A>>outs;
#pragma omp parallel for schedule(dynamic,1)
 for(int ei=0;ei<(int)Es.size();ei++){U E=Es[ei],D=comp?(ALL^E):E;auto ker=kernel(E);auto st=stabilizer(E);uint64_t M=1ULL<<ker.b.size();long long ls=0,lc=0,lp=0,lh=0;vector<pair<A,A>>lo;for(uint64_t mm=0;mm<M;mm++){U P=0;for(int j=0;j<(int)ker.b.size();j++)if(mm>>j&1)P^=ker.b[j];if(__builtin_popcount(P)!=kp)continue;U C=P^D;if(__builtin_popcount(C)!=kc||canon_stab(P,st)!=P)continue;ls++;vector<int>pi,ci;for(int i=0;i<25;i++){if(P>>i&1)pi.push_back(i);if(C>>i&1)ci.push_back(i);}int negc=kc/2;
  for(U z=0;z<(1u<<(kc-1));z++){if(__builtin_popcount(z)!=negc)continue;lc++;A c{};c[ci[0]]=1;for(int j=1;j<kc;j++)c[ci[j]]=(z>>(j-1)&1)?-1:1;auto ps=solve_p(pi,c);lp+=ps.size();for(auto&p:ps)if(qminG(p,c)<=B){lh++;lo.push_back({p,c});}}
 }
 supp+=ls;csigns+=lc;psol+=lp;hits+=lh;if(!lo.empty()){lock_guard<mutex>g(mu);outs.insert(outs.end(),lo.begin(),lo.end());}}
 cout<<"H18K_SIGNEDC K="<<K0<<" budget="<<B<<" kp="<<kp<<" kc="<<kc<<" t="<<t<<" diff_orbits="<<Es.size()<<" support_orbits="<<supp<<" c_sign_systems="<<csigns<<" exact_p_solutions="<<psol<<" spectral="<<hits<<"\n";for(auto&z:outs){cout<<"HIT p=";for(int i=0;i<25;i++)cout<<(int)z.first[i]<<(i==24?'|':',');cout<<"c=";for(int i=0;i<25;i++)cout<<(int)z.second[i]<<(i==24?'\n':',');}}
