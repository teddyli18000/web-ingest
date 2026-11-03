#include <bits/stdc++.h>
using namespace std;
int main(){
  for(int defect: {0,1,5}){
    vector<int> pairs;for(int r=1;r<=12;r++)if(r!=defect)pairs.push_back(r);
    int bestSG=1e9,bestQ=1e9;long long total=0,sgpass=0,qpass=0;
    array<int,25> best{};
    constexpr int np=7;
    for(unsigned mask=0;mask<(1u<<pairs.size());mask++)if(__builtin_popcount(mask)==np){
      vector<int> rs;for(int j=0;j<(int)pairs.size();j++)if((mask>>j)&1)rs.push_back(pairs[j]);
      for(int sign=0;sign<(1<<np);sign++){
        for(int orientation=0;orientation<(defect?2:1);orientation++){
          array<int,25> c{};
          if(defect)c[orientation?25-defect:defect]=1;
          else c[0]=1;
          for(int i=0;i<np;i++){int sg=((sign>>i)&1)?-1:1;c[rs[i]]=sg;c[25-rs[i]]=-sg;}
          assert(2*c[0]==(defect==0?2:0));
          for(int r=1;r<=12;r++)assert(c[r]+c[25-r]==(r==defect?1:0));
          int ss=0,norm=0;for(int a:c){ss+=a;norm+=a*a;}assert(ss==1&&norm==15);
          int SG=0,Q=0;
          for(int r=1;r<=12;r++){
            int g=0;for(int i=0;i<25;i++)g+=c[i]*c[(i+r)%25];
            SG+=g*g;Q+=(g*g+(abs(g)&1))/2;
          }
          total++;sgpass+=SG<=48;qpass+=Q<=24;
          if(SG<bestSG){bestSG=SG;best=c;}bestQ=min(bestQ,Q);
        }
      }
    }
    cout<<"defect="<<defect<<" complete="<<total<<" bestSG="<<bestSG<<" bestQ="<<bestQ<<" SG<=48="<<sgpass<<" qmin<=24="<<qpass<<" witness=";
    for(int v:best)cout<< (v>0?'+':v<0?'-':'0');cout<<'\n';
  }
}
