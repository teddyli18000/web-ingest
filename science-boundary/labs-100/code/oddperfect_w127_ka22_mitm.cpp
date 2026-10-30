// Exact meet-in-the-middle exclusion for the W127 order-25 shard ka=22,kc=4.
//
// For ka=22 and sum(p)=10, p has 16 entries +1, 6 entries -1 and 3 zeros.
// Write p = 1 - z - 2n where z is the 3-zero indicator and n is the 6-negative
// indicator.  For fixed c, the cross condition p c* + c p*=0 is linear in p.
// Because sum(c)=0, the all-ones vector lies in its kernel, so the condition is
// exactly M z + 2 M n = 0.  We hash all 6-subset column sums and look up every
// 3-subset zero support.  Every hit is then rechecked against all 25 integer
// cross coefficients and the complete W127 order-25 PAF requirement.
//
// The kc=4 sequence c has two +1 and two -1 entries.  Common affine maps of
// Z_25 and an independent global sign of c preserve all equations.  The program
// constructs the complete set of canonical c orbits internally and asserts that
// there are 88 of them.
#include <bits/stdc++.h>
using namespace std;
static const int N=25, R=13;
struct Key { array<signed char,R> a{}; bool operator==(Key const&o) const {return a==o.a;} };
struct Hash { size_t operator()(Key const&k) const { size_t h=1469598103934665603ULL; for(auto x:k.a){h^=(unsigned char)(x+32);h*=1099511628211ULL;} return h;} };
static vector<array<pair<int,int>,4>> reps;

static string canon(const array<int,N>& c){
    vector<int> units; for(int a=1;a<N;a++) if(std::gcd(a,N)==1) units.push_back(a);
    string best(100,'z');
    vector<pair<int,int>> sup;for(int i=0;i<N;i++)if(c[i])sup.push_back({i,c[i]});
    for(auto [x0,v0]:sup) for(int a:units){int b=(-a*x0)%N;if(b<0)b+=N;for(int sg:{1,-1}){
        vector<pair<int,int>> t;for(auto [x,v]:sup)t.push_back({(a*x+b)%N,sg*v});sort(t.begin(),t.end());
        string s;for(auto [x,v]:t){char buf[16];sprintf(buf,"%02d%c",x,v>0?'+':'-');s+=buf;}
        best=min(best,s);
    }}
    return best;
}
static void gen_reps(){
    unordered_map<string,array<pair<int,int>,4>> mp;
    for(int a=0;a<N;a++)for(int b=a+1;b<N;b++){
      for(int c=0;c<N;c++)if(c!=a&&c!=b)for(int d=c+1;d<N;d++)if(d!=a&&d!=b){
        array<int,N> x{};x[a]=x[b]=1;x[c]=x[d]=-1; string k=canon(x);
        if(!mp.count(k)){
          array<pair<int,int>,4> r{};int p=0;
          for(int q=0;q<4;q++){int pos=stoi(k.substr(3*q,2));int v=k[3*q+2]=='+'?1:-1;r[p++]={pos,v};}
          mp.emplace(k,r);
        }
      }
    }
    for(auto &kv:mp) reps.push_back(kv.second);
    sort(reps.begin(),reps.end(),[](auto&A,auto&B){return A<B;});
}

static array<int,R> colvec(const array<int,N>&c,int j){array<int,R> v{};for(int r=0;r<R;r++)v[r]=c[(j-r+N)%N]+c[(j+r)%N];return v;}
static int paf(const array<int,N>&x,int r){int s=0;for(int i=0;i<N;i++)s+=x[i]*x[(i+r)%N];return s;}
int main(){
  gen_reps(); cerr<<"classes="<<reps.size()<<"\n"; if(reps.size()!=88)return 2;
  long long total_cross=0,total_target=0; int ci=0;
  for(auto rep:reps){
    array<int,N> c{};for(auto [i,v]:rep)c[i]=v;
    array<array<int,R>,N> cols{};for(int j=0;j<N;j++)cols[j]=colvec(c,j);
    unordered_map<Key,vector<uint32_t>,Hash> sums; sums.reserve(300000);
    // Enumerate the 6 negative positions of p.
    for(int a=0;a<N;a++)for(int b=a+1;b<N;b++)for(int d=b+1;d<N;d++)for(int e=d+1;e<N;e++)for(int f=e+1;f<N;f++)for(int g=f+1;g<N;g++){
      Key k;for(int r=0;r<R;r++){int s=cols[a][r]+cols[b][r]+cols[d][r]+cols[e][r]+cols[f][r]+cols[g][r];k.a[r]=(signed char)s;}
      uint32_t mask=(1u<<a)|(1u<<b)|(1u<<d)|(1u<<e)|(1u<<f)|(1u<<g);sums[k].push_back(mask);
    }
    long long cc=0,tt=0;
    // Enumerate the 3 zero positions and solve Mz+2Mn=0 by hash lookup.
    for(int a=0;a<N;a++)for(int b=a+1;b<N;b++)for(int d=b+1;d<N;d++){
      Key target; bool ok=true;for(int r=0;r<R;r++){int s=cols[a][r]+cols[b][r]+cols[d][r];if(s&1){ok=false;break;}target.a[r]=(signed char)(-s/2);}if(!ok)continue;
      auto it=sums.find(target);if(it==sums.end())continue;uint32_t zm=(1u<<a)|(1u<<b)|(1u<<d);
      for(uint32_t nm:it->second){if(nm&zm)continue;cc++;
        array<int,N> p; p.fill(1);for(int i=0;i<N;i++){if(zm>>i&1)p[i]=0;else if(nm>>i&1)p[i]=-1;}
        // Independent exact cross check over all 25 coefficients.
        bool good=true;for(int r=0;r<N;r++){int h=0;for(int i=0;i<N;i++)h+=p[i]*c[(i-r+N)%N]+c[i]*p[(i-r+N)%N];if(h){good=false;break;}}if(!good){cerr<<"cross bug\n";return 3;}
        int sm=0;for(int r=1;r<=12;r++){int z=paf(p,r)+paf(c,r);if(z<2||z>4){good=false;break;}sm+=z;}
        if(good&&sm==37){tt++; cout<<"SURV class="<<ci<<" p=";for(int x:p)cout<<(x+1);cout<<" c=";for(int x:c)cout<<(x+1);cout<<"\n";}
      }
    }
    total_cross+=cc;total_target+=tt;
    cerr<<"class "<<ci<<" cross="<<cc<<" target="<<tt<<"\n";ci++;
  }
  cout<<"SUMMARY classes="<<reps.size()<<" cross="<<total_cross<<" target="<<total_target<<"\n";
  if(total_target!=0) return 1;
}
