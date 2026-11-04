// Join exact O58/K34 2+14 low-SH fibres with every compatible
// centered-support periodic compressed sign solution. Necessary Q filter.
#include <bits/stdc++.h>
#include <omp.h>
using namespace std;
using U=uint32_t;
using A=array<int8_t,25>;
constexpr U ALL=(1u<<25)-1;
int mod(int x){x%=3;if(x<0)x+=3;return x;}
struct Key{
 int d,eps,s;U gs;
 bool operator<(Key const&o)const{return tie(d,eps,s,gs)<tie(o.d,o.eps,o.s,o.gs);}
};
struct Lin{
 array<array<uint8_t,23>,14>M{};
 array<int,14>rhs{},piv{};
 int rank=0;vector<int>fr;bool ok=true;
};
Lin solve(const A&c,const vector<int>&pi,int lag){
 Lin z;int nc=pi.size();assert(nc==23);
 for(int j=0;j<nc;j++){
  int pos=pi[j];
  for(int r=0;r<=12;r++)z.M[r][j]=mod(c[(pos+r)%25]+c[(pos-r+25)%25]);
  z.M[13][j]=1;
 }
 z.rhs[lag]=1;z.rhs[13]=1;
 for(int j=0;j<nc;j++){
  int q=-1;for(int r=z.rank;r<14;r++)if(z.M[r][j]){q=r;break;}
  if(q<0)continue;
  swap(z.M[q],z.M[z.rank]);swap(z.rhs[q],z.rhs[z.rank]);
  if(z.M[z.rank][j]==2){
   for(int k=0;k<nc;k++)z.M[z.rank][k]=mod(2*z.M[z.rank][k]);
   z.rhs[z.rank]=mod(2*z.rhs[z.rank]);
  }
  for(int r=0;r<14;r++)if(r!=z.rank&&z.M[r][j]){
   int f=z.M[r][j];
   for(int k=0;k<nc;k++)z.M[r][k]=mod(z.M[r][k]-f*z.M[z.rank][k]);
   z.rhs[r]=mod(z.rhs[r]-f*z.rhs[z.rank]);
  }
  z.piv[z.rank++]=j;
 }
 for(int r=z.rank;r<14;r++)if(z.rhs[r])z.ok=false;
 bool isp[23]{};for(int r=0;r<z.rank;r++)isp[z.piv[r]]=true;
 for(int j=0;j<nc;j++)if(!isp[j])z.fr.push_back(j);
 return z;
}
int cross(const A&p,const A&c,int r){int h=0;for(int i=0;i<25;i++)h+=p[i]*c[(i-r+25)%25]+c[i]*p[(i-r+25)%25];return h;}
int SG(const A&p,const A&c){
 int e=0;for(int r=1;r<=12;r++){
  int g=0;for(int i=0;i<25;i++)g+=p[i]*p[(i+r)%25]+c[i]*c[(i+r)%25];
  e+=g*g;
 }return e;
}
string seq(const A&a){string s;for(int v:a)s+=v>0?'+':v<0?'-':'0';return s;}
int main(int argc,char**argv){
 ifstream f(argv[1]);string line;map<Key,int>groups;long long totalHits=0;
 while(getline(f,line))if(line.rfind("HIT ",0)==0){
  stringstream ss(line);string w;map<string,string>kv;ss>>w;
  while(ss>>w){auto i=w.find('=');kv[w.substr(0,i)]=w.substr(i+1);}
  Key k{stoi(kv["d"]),stoi(kv["eps"]),stoi(kv["s"]),0};
  string g=kv["gamma"];
  for(int j=0;j<25;j++)if(g[j]!='0')k.gs|=1u<<j;
  int sh=stoi(kv["SH"]);auto it=groups.find(k);
  if(it==groups.end())groups[k]=sh;else it->second=min(it->second,sh);
  totalHits++;
 }
 vector<pair<Key,int>>vs(groups.begin(),groups.end());
 cerr<<"fibre_HITs="<<totalHits<<" support_groups="<<vs.size()<<"\n";
 atomic<long long>csigns{0},mod3systems{0},periodic{0},qpass{0};
 atomic<int>minSG{9999},minmargin{9999};
 #pragma omp parallel for schedule(dynamic,1)
 for(int idx=0;idx<(int)vs.size();idx++){
  auto [k,minSH]=vs[idx];
  U as=(1u<<0)|(1u<<k.d),ps=ALL^as,cs=ALL^k.gs;
  assert(__builtin_popcount(ps)==23&&__builtin_popcount(cs)==11);
  vector<int>pi,ci;
  for(int j=0;j<25;j++){if(ps>>j&1)pi.push_back(j);if(cs>>j&1)ci.push_back(j);}
  for(int neg=0;neg<(1<<11);neg++)if(__builtin_popcount((unsigned)neg)==5){
   csigns++;A c{};
   for(int j=0;j<11;j++)c[ci[j]]=(neg>>j&1)?-1:1;
   auto z=solve(c,pi,k.s);if(!z.ok)continue;
   mod3systems++;
   U lim=1u<<z.fr.size();
   for(U m=0;m<lim;m++){
    int x[23]{};
    for(int j=0;j<(int)z.fr.size();j++)x[z.fr[j]]=(m>>j&1)?2:1;
    bool ok=true;
    for(int r=z.rank-1;r>=0;r--){
     int v=z.rhs[r];for(int j:z.fr)v-=z.M[r][j]*x[j];
     v=mod(v);if(v==0){ok=false;break;}x[z.piv[r]]=v;
    }
    if(!ok)continue;
    A p{};int sum=0;
    for(int j=0;j<23;j++){p[pi[j]]=x[j]==1?1:-1;sum+=p[pi[j]];}
    if(sum!=1)continue;
    for(int r=0;r<=12;r++)if(cross(p,c,r)!=(r==k.s?1:0)){ok=false;break;}
    if(!ok)continue;periodic++;
    int e=SG(p,c),old=minSG.load();
    while(e<old&&!minSG.compare_exchange_weak(old,e)){}
    int margin=e+minSH-48;old=minmargin.load();
    while(margin<old&&!minmargin.compare_exchange_weak(old,margin)){}
    if(margin<=0){
     qpass++;
     #pragma omp critical
     cout<<"JOIN_QHIT d="<<k.d<<" eps="<<k.eps<<" s="<<k.s
         <<" support="<<k.gs<<" minSH="<<minSH<<" SG="<<e
         <<" p="<<seq(p)<<" c="<<seq(c)<<"\n";
    }
   }
  }
 }
 cout<<"K34_FIBRE2_JOIN hits="<<totalHits<<" groups="<<vs.size()
     <<" c_signs="<<csigns<<" systems="<<mod3systems
     <<" periodic="<<periodic<<" minSG="<<minSG
     <<" min_margin="<<minmargin<<" Qpass="<<qpass<<"\n";
}
