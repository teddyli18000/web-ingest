// Exact O58/K26, (kp,kc)=(13,13), overlap t=1, normalized common site 0.
// Mod2 periodic cross forces reflection-symmetric support and centered defect.
// Enumerates all 924 supports, all balanced p signs, full GF3 free ternary
// assignments for c, then original integer equations, no witness cap.
#include <bits/stdc++.h>
using namespace std;
using A=array<int,25>;
using U=uint32_t;
int md(int x){x%=3;return x<0?x+3:x;}
struct Sol{int rank=0,piv[12]{},rhs[13]{},M[13][12]{};bool good=true;vector<int>fr;};
Sol rref(A const&p,vector<int>const&cs,int common){
 Sol z;assert(cs.size()==12);
 for(int j=0;j<12;j++){int i=cs[j];for(int r=1;r<=12;r++)z.M[r-1][j]=md(p[(i-r+25)%25]+p[(i+r)%25]);z.M[12][j]=1;}
 for(int r=1;r<=12;r++)z.rhs[r-1]=md(-common*(p[r]+p[25-r]));
 z.rhs[12]=md(1-common);
 for(int c=0;c<12;c++){
  int q=-1;for(int r=z.rank;r<13;r++)if(z.M[r][c]){q=r;break;}
  if(q<0)continue;swap(z.M[q],z.M[z.rank]);swap(z.rhs[q],z.rhs[z.rank]);
  if(z.M[z.rank][c]==2){for(int j=0;j<12;j++)z.M[z.rank][j]=md(2*z.M[z.rank][j]);z.rhs[z.rank]=md(2*z.rhs[z.rank]);}
  for(int r=0;r<13;r++)if(r!=z.rank&&z.M[r][c]){
   int f=z.M[r][c];for(int j=0;j<12;j++)z.M[r][j]=md(z.M[r][j]-f*z.M[z.rank][j]);
   z.rhs[r]=md(z.rhs[r]-f*z.rhs[z.rank]);
  }
  z.piv[z.rank++]=c;
 }
 for(int r=z.rank;r<13;r++)if(z.rhs[r])z.good=false;
 bool is[12]{};for(int r=0;r<z.rank;r++)is[z.piv[r]]=1;
 for(int j=0;j<12;j++)if(!is[j])z.fr.push_back(j);
 return z;
}
int H(A const&p,A const&c,int r){int x=0;for(int i=0;i<25;i++)x+=p[i]*c[(i+r)%25]+c[i]*p[(i+r)%25];return x;}
int G(A const&p,A const&c,int r){int x=0;for(int i=0;i<25;i++)x+=p[i]*p[(i+r)%25]+c[i]*c[(i+r)%25];return x;}
int qmin(A const&p,A const&c,int&sg){int q=0;sg=0;for(int r=1;r<=12;r++){int g=G(p,c,r);sg+=g*g;q+=(g*g+(abs(g)&1))/2;}return q;}
void print(A const&p){for(int i=0;i<25;i++){if(i)cout<<',';cout<<p[i];}}
int main(){
 long long supports=0,ptests=0,consistent=0,exact=0,spectral=0;
 int minSG=INT_MAX,minQ=INT_MAX,maxfree=0,rankdef=0;
 for(int pair=0;pair<(1<<12);pair++)if(__builtin_popcount((unsigned)pair)==6){
  U ps=1u;for(int r=1;r<=12;r++)if(pair>>(r-1)&1)ps|=1u<<r|1u<<(25-r);
  U cs=(((1u<<25)-1)^ps)|1u;
  assert(__builtin_popcount(ps)==13&&__builtin_popcount(cs)==13);supports++;
  vector<int>pp,cc;
  for(int i=0;i<25;i++){if(ps>>i&1)pp.push_back(i);if((cs>>i&1)&&i!=0)cc.push_back(i);}
  assert(pp[0]==0&&cc.size()==12);
  for(int sign=0;sign<(1<<13);sign++)if(__builtin_popcount((unsigned)sign)==6){
   ptests++;A p{};for(int j=0;j<13;j++)p[pp[j]]=(sign>>j&1)?-1:1;
   auto z=rref(p,cc,p[0]);if(!z.good)continue;
   consistent++;maxfree=max(maxfree,int(z.fr.size()));rankdef+=!z.fr.empty();
   long long lim=1;for(int f:z.fr)lim*=3;
   for(long long t=0;t<lim;t++){
    int x[12]{};auto w=t;for(int f:z.fr){x[f]=w%3;w/=3;}
    for(int r=z.rank-1;r>=0;r--){int y=z.rhs[r];for(int f:z.fr)y-=z.M[r][f]*x[f];x[z.piv[r]]=md(y);}
    int nplus=0;bool ok=true;for(int j=0;j<12;j++){if(!x[j]){ok=false;break;}nplus+=x[j]==1;}
    if(!ok||nplus!=(p[0]==1?6:7))continue;
    A c{};c[0]=p[0];for(int j=0;j<12;j++)c[cc[j]]=x[j]==1?1:-1;
    for(int r=0;r<=12;r++)if(H(p,c,r)!=(r==0?2:0)){ok=false;break;}
    if(!ok)continue;exact++;
    int sg,q=qmin(p,c,sg);minSG=min(minSG,sg);minQ=min(minQ,q);
    if(q<=64){spectral++;cout<<"HIT SG="<<sg<<" qmin="<<q<<" p=";print(p);cout<<"|c=";print(c);cout<<'\n';}
   }
  }
 }
 cout<<"SUMMARY supports="<<supports<<" signed_p="<<ptests<<" mod3_consistent="<<consistent
     <<" rank_deficient="<<rankdef<<" maxfree="<<maxfree<<" exact="<<exact
     <<" minSG="<<minSG<<" minQ="<<minQ<<" qmin64="<<spectral<<'\n';
}
