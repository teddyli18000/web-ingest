// Generic exact compressed enumeration for odd-perfect (a,b)=(18,0).
// Input: K kp overlap. For odd K, m=K-25 and E<=570 gives
// B=floor((130-m^2)/2), so Q+R<=B. For compressed spectrum G,
// q_min(G)=sum_j ceil(G_j^2/2) is the exact minimum possible Q.
#include <bits/stdc++.h>
#include <omp.h>
using namespace std;using U=uint32_t;static const U ALL=(1u<<25)-1;static const int N=25;using A=array<int8_t,25>;
U rot(U x,int k){k%=25;return((x<<k)|(x>>(25-k)))&ALL;}U star(U x){U y=0;for(int i=0;i<25;i++)if(x>>i&1)y|=1u<<((25-i)%25);return y;}U mul(U a,U b){U y=0;for(int i=0;i<25;i++)if(a>>i&1)y^=rot(b,i);return y;}
vector<int> units(){vector<int>u;for(int a=1;a<25;a++)if(gcd(a,25)==1)u.push_back(a);return u;}U aff(U x,int a,int b){U y=0;for(int i=0;i<25;i++)if(x>>i&1)y|=1u<<((a*i+b)%25);return y;}
vector<U> orbit_reps(int w){vector<U>reps;unordered_set<U>seen;auto us=units();seen.reserve(5000000);U x=(1u<<w)-1;while(x<(1u<<25)){if(!seen.count(x)){reps.push_back(x);for(int a:us)for(int b=0;b<25;b++)seen.insert(aff(x,a,b));}U c=x&-x,r=x+c;if(!r||r>=(1u<<25))break;x=(((r^x)>>2)/c)|r;}return reps;}
struct Ker{vector<U>b;};Ker kernel(U D){U rows[25]{};U Ds=star(D);for(int j=0;j<25;j++){U col=mul(1u<<j,Ds)^mul(D,star(1u<<j));for(int r=0;r<25;r++)if(col>>r&1)rows[r]|=1u<<j;}int pr=0;vector<int>pc;for(int c=0;c<25&&pr<25;c++){int q=-1;for(int r=pr;r<25;r++)if(rows[r]>>c&1){q=r;break;}if(q<0)continue;swap(rows[pr],rows[q]);for(int r=0;r<25;r++)if(r!=pr&&(rows[r]>>c&1))rows[r]^=rows[pr];pc.push_back(c);pr++;}bool isp[25]{};for(int c:pc)isp[c]=1;Ker K;for(int f=0;f<25;f++)if(!isp[f]){U v=1u<<f;for(int r=0;r<pr;r++)if(rows[r]>>f&1)v|=1u<<pc[r];K.b.push_back(v);}return K;}
vector<pair<int,int>> stabilizer(U E){vector<pair<int,int>>s;auto us=units();for(int a:us)for(int b=0;b<25;b++)if(aff(E,a,b)==E)s.push_back({a,b});return s;}U canon_stab(U P,const vector<pair<int,int>>&st){U z=P;for(auto[a,b]:st)z=min(z,aff(P,a,b));return z;}
static int qminG(const A&p,const A&c){int q=0;for(int r=1;r<=12;r++){int g=0;for(int i=0;i<25;i++)g+=p[i]*p[(i+r)%25]+c[i]*c[(i+r)%25];q+=(g*g+(abs(g)&1))/2;}return q;}
bool crossok(const A&p,const A&c){for(int r=0;r<25;r++){int h=0;for(int i=0;i<25;i++)h+=p[i]*c[(i-r+25)%25]+c[i]*p[(i-r+25)%25];if(h)return false;}return true;}
struct Sol{int rank;vector<A>cs;};Sol csolve(const A&p,const vector<int>&ci){int nc=ci.size();if(nc==0){A c{};return Sol{-1,{c}};}int a[14][25]{};for(int j=0;j<nc;j++){int pos=ci[j];for(int r=0;r<=12;r++){int z=p[(pos+r)%25]+p[(pos-r+25)%25];z%=3;if(z<0)z+=3;a[r][j]=z;}a[13][j]=1;}int piv[25],rank=0;for(int col=0;col<nc;col++){int q=-1;for(int r=rank;r<14;r++)if(a[r][col]){q=r;break;}if(q<0)continue;for(int j=0;j<nc;j++)swap(a[rank][j],a[q][j]);if(a[rank][col]==2)for(int j=0;j<nc;j++)a[rank][j]=(2*a[rank][j])%3;for(int r=0;r<14;r++)if(r!=rank&&a[r][col]){int f=a[r][col];for(int j=0;j<nc;j++){a[r][j]=(a[r][j]-f*a[rank][j])%3;if(a[r][j]<0)a[r][j]+=3;}}piv[rank++]=col;}Sol S{rank,{}};if(rank==nc)return S;if(rank==nc-1){bool isp[25]{};for(int r=0;r<rank;r++)isp[piv[r]]=1;int f=0;while(isp[f])f++;int v[25]{};v[f]=1;for(int r=0;r<rank;r++)v[piv[r]]=(3-a[r][f])%3;bool ok=true;for(int j=0;j<nc;j++)if(v[j]!=1&&v[j]!=2)ok=false;if(ok){A c{};for(int j=0;j<nc;j++)c[ci[j]]=v[j]==1?1:-1;if(c[ci[0]]<0)for(int pos:ci)c[pos]=-c[pos];if(crossok(p,c))S.cs.push_back(c);}return S;}for(int m=0;m<(1<<(nc-1));m++){A c{};c[ci[0]]=1;for(int j=1;j<nc;j++)c[ci[j]]=(m>>(j-1)&1)?-1:1;int ss=0;for(int pos:ci)ss+=c[pos];if(ss||!crossok(p,c))continue;S.cs.push_back(c);}return S;}
int main(int argc,char**argv){
 if(argc<4)return 2;int K0=atoi(argv[1]),kp=atoi(argv[2]),t=atoi(argv[3]);int m0=K0-25,B=(130-m0*m0)/2,kc=K0-kp,pneg=(kp-9)/2;
 if(K0<19||K0>35||(K0%2)==0||B<0||kp<9||kp>K0||(kp%2)==0||kc<0||(kc%2)||t<0||t>min(kp,kc)||(t&1))return 2;
 int w=K0-2*t;if(w<0||w>25)return 2;int ew=min(w,25-w);bool comp=w>12;auto Es=orbit_reps(ew);cerr<<"E_REPS "<<Es.size()<<" ew="<<ew<<"\n";
 atomic<long long>supp{0},pt{0},rfull{0},rproj{0},rlo{0},hm{0},gh{0};mutex om;vector<pair<A,A>>hits;
#pragma omp parallel for schedule(dynamic,1)
 for(int ei=0;ei<(int)Es.size();ei++){
  U E=Es[ei],D=comp?(ALL^E):E;auto ker=kernel(E);auto st=stabilizer(E);uint64_t M=1ULL<<ker.b.size();long long ls=0,lpt=0,lf=0,lp=0,ll=0,lh=0,lg=0;vector<pair<A,A>>local;
  for(uint64_t mm=0;mm<M;mm++){
   U P=0;for(int j=0;j<(int)ker.b.size();j++)if(mm>>j&1)P^=ker.b[j];if(__builtin_popcount(P)!=kp)continue;U C=P^D;if(__builtin_popcount(C)!=kc||canon_stab(P,st)!=P)continue;ls++;
   vector<int>pi,ci;for(int i=0;i<25;i++){if(P>>i&1)pi.push_back(i);if(C>>i&1)ci.push_back(i);}uint32_t neg=pneg?((1u<<pneg)-1):0;bool first=true;
   while(true){if(!first&&pneg==0)break;first=false;lpt++;A p{};for(int j=0;j<kp;j++)p[pi[j]]=(neg>>j&1)?-1:1;auto S=csolve(p,ci);if(S.rank==kc)lf++;else{if(S.rank==kc-1)lp++;else ll++;for(auto&c:S.cs){lh++;if(qminG(p,c)<=B){lg++;local.push_back({p,c});}}}if(pneg==0)break;U cc=neg&-neg,rr=neg+cc;if(!rr||rr>=(1u<<kp))break;neg=(((rr^neg)>>2)/cc)|rr;}
  }
  supp+=ls;pt+=lpt;rfull+=lf;rproj+=lp;rlo+=ll;hm+=lh;gh+=lg;if(!local.empty()){lock_guard<mutex>g(om);hits.insert(hits.end(),local.begin(),local.end());}
 }
 cout<<"H18K_COMPRESSED K="<<K0<<" budget="<<B<<" kp="<<kp<<" kc="<<kc<<" t="<<t<<" diff_orbits="<<Es.size()<<" support_orbits="<<supp<<" ptests="<<pt<<" rankfull="<<rfull<<" rankproj="<<rproj<<" ranklo="<<rlo<<" Hmatches_halfC="<<hm<<" spectral="<<gh<<"\n";
 for(auto&z:hits){cout<<"HIT p=";for(int i=0;i<25;i++)cout<<(int)z.first[i]<<(i==24?'|':',');cout<<"c=";for(int i=0;i<25;i++)cout<<(int)z.second[i]<<(i==24?'\n':',');}
}
