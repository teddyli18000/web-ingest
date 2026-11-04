// Exact O58/K34 2+14 sparse negacyclic fibre census.
#include <bits/stdc++.h>
using namespace std;
using A=array<int,25>;
int mod(int x){x%=3;if(x<0)x+=3;return x;}
struct Sol{
 int rank=0;array<array<int,25>,25>m{};
 array<int,25>rhs{},piv{};vector<int>fr;bool ok=true;
};
Sol rref(const A&alpha,int s,int orient,array<array<int,25>,25>&exact){
 Sol z;
 for(int j=0;j<25;j++)for(int i=0;i<25;i++)if(alpha[i]){
  int ep=i-j,v=alpha[i];if(ep<0){ep+=25;v=-v;}exact[ep][j]+=v;
  ep=j-i;v=-alpha[i];if(ep<0){ep+=25;v=-v;}exact[ep][j]+=v;
 }
 if(s){z.rhs[s]=mod(orient);z.rhs[25-s]=mod(orient);}
 for(int r=0;r<25;r++)for(int j=0;j<25;j++)z.m[r][j]=mod(exact[r][j]);
 for(int j=0;j<25;j++){
  int q=-1;for(int r=z.rank;r<25;r++)if(z.m[r][j]){q=r;break;}
  if(q<0)continue;
  swap(z.m[q],z.m[z.rank]);swap(z.rhs[q],z.rhs[z.rank]);
  if(z.m[z.rank][j]==2){for(int k=0;k<25;k++)z.m[z.rank][k]=mod(2*z.m[z.rank][k]);z.rhs[z.rank]=mod(2*z.rhs[z.rank]);}
  for(int r=0;r<25;r++)if(r!=z.rank&&z.m[r][j]){
   int f=z.m[r][j];for(int k=0;k<25;k++)z.m[r][k]=mod(z.m[r][k]-f*z.m[z.rank][k]);
   z.rhs[r]=mod(z.rhs[r]-f*z.rhs[z.rank]);
  }
  z.piv[z.rank++]=j;
 }
 for(int r=z.rank;r<25;r++)if(z.rhs[r])z.ok=false;
 bool isp[25]{};for(int r=0;r<z.rank;r++)isp[z.piv[r]]=true;
 for(int j=0;j<25;j++)if(!isp[j])z.fr.push_back(j);
 return z;
}
int sh(const A&a,const A&g){
 int sum=0;
 for(int r=1;r<=12;r++){
  int h=0;for(int i=0;i<25;i++){
   int j=i+r;h+=a[i]*(j<25?a[j]:-a[j-25])+g[i]*(j<25?g[j]:-g[j-25]);
  }
  sum+=h*h;
 }
 return sum;
}
int main(int argc,char**argv){
 int d=atoi(argv[1]),eps=atoi(argv[2]),s=atoi(argv[3]),orient=atoi(argv[4]);
 assert(1<=d&&d<=24&&(eps==1||eps==-1)&&(s==0||s==1||s==5));
 A alpha{};alpha[0]=1;alpha[d]=eps;
 array<array<int,25>,25>exact{};auto z=rref(alpha,s,orient,exact);
 long long total=0,wt14=0,integerExact=0,sh24=0;
 int minSH=9999;
 if(z.ok){
  uint64_t M=1;for(int k=0;k<(int)z.fr.size();k++)M*=3;
  for(uint64_t m=0;m<M;m++){
   int x[25]{};auto q=m;int w=0;
   for(int k=0;k<(int)z.fr.size();k++){int v=q%3;q/=3;x[z.fr[k]]=v;w+=v!=0;}
   for(int r=z.rank-1;r>=0;r--){
    int v=z.rhs[r];for(int f:z.fr)v-=z.m[r][f]*x[f];
    x[z.piv[r]]=mod(v);w+=x[z.piv[r]]!=0;
   }
   total++;if(w!=14)continue;wt14++;
   A gamma{};for(int j=0;j<25;j++)gamma[j]=x[j]==2?-1:x[j];
   bool okay=true;
   for(int r=0;r<25;r++){
    int v=0;for(int j=0;j<25;j++)v+=exact[r][j]*gamma[j];
    int goal=s&&(r==s||r==25-s)?orient:0;
    if(v!=goal){okay=false;break;}
   }
   if(!okay)continue;
   integerExact++;
   int shv=sh(alpha,gamma);
   minSH=min(minSH,shv);
   if(shv<=24){
    sh24++;
    cout<<"HIT d="<<d<<" eps="<<eps<<" s="<<s<<" orient="<<orient
        <<" SH="<<shv<<" gamma=";
    for(int x:gamma)cout<<(x>0?'+':x<0?'-':'0');
    cout<<"\n";
   }
  }
 }
 cout<<"FIBRE2_EXACT d="<<d<<" eps="<<eps<<" s="<<s
     <<" orient="<<orient<<" rank="<<z.rank
     <<" free="<<z.fr.size()<<" total="<<total
     <<" wt14="<<wt14<<" integerExact="<<integerExact
     <<" minSH="<<minSH<<" SHle24="<<sh24<<"\n";
}
