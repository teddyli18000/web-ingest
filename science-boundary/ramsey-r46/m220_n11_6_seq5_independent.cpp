// Independent exact bitset verifier for m220 n11=6 seq5 exclusion.
// Compile: g++ -O2 -std=c++17 m220_n11_6_seq5_independent.cpp -o /tmp/r46_seq5
// Run: /tmp/r46_seq5
#include <bits/stdc++.h>
using namespace std;
vector<uint32_t> decode(const string& s){
 int n=int(s[0])-63;vector<uint32_t> a(n);int t=0;
 for(int j=1;j<n;j++)for(int i=0;i<j;i++){
   int b=((s[1+t/6]-63)>>(5-t%6))&1;t++;
   if(b){a[i]|=1u<<j;a[j]|=1u<<i;}
 }
 return a;
}
int main(){
 int cnt=0,n22=0,n24=0,min_gap=999;
 for(int R:{22,24})for(int x=0;x<=28;x++)for(int y=0;y<=24;y++)for(int z=0;z<=3;z++){
  int e11_12=66-R,e12_13=104-2*x-y,e12_14=42-y-2*z;
  int rem=228-e11_12-e12_13-e12_14;
  if(e12_13<0||e12_14<0||rem<0||(rem&1))continue;
  int e12_12=rem/2;
  int S12=11*e11_12+24*e12_12+13*e12_13+14*e12_14;
  int S13=1248+2*x+2*y,S14=504+y+4*z;
  if(S12<132*19||S12>147*19||S13<143*8||S13>164*8||S14<154*3||S14>178*3)continue;
  int D=8*164-S13;assert(D>=0&&D<=6);
  int ycap=z==3?8+D:8+2*D;
  assert(y>ycap);min_gap=min(min_gap,y-ycap);cnt++;if(R==22)n22++;else n24++;
 }
 assert(cnt==84&&n22==54&&n24==30&&min_gap==1);
 cout<<"class matrices="<<cnt<<" R22="<<n22<<" R24="<<n24<<" min_gap="<<min_gap<<"\n";
 const vector<string> b88={
  R"G6(U?`@?bGKdWSWRELSWk?fGtHUMVEuH@VP`}HA[Ui?)G6",
  R"G6(U?`D@`gFCkIWwcbK\CPVOdQWu[Cqsadm@ddCRPM?)G6",
  R"G6(U?`@?bGpDcCY[PCyTahjgxobZG@tbAxIaMYGRY`?)G6"
 };
 for(auto &s:b88){
  auto a=decode(s);int n=a.size();int ee=0;for(auto t:a)ee+=__builtin_popcount(t);ee/=2;
  assert(n==22&&ee==88);
  array<int,2> copycnt{};array<int,2> maxq{-1,-1};
  uint32_t mask=(1u<<6)-1;
  while(mask <(1u<<22)){
   int h[6],nv=0;
   for(int i=0;i<22;i++)if(mask>>i&1)h[nv++]=__builtin_popcount(a[i]&mask);
   sort(h,h+6);
   for(int r=0;r<2;r++){
    bool match=r==0 ? (h[0]==3&&h[1]==3&&h[2]==4&&h[3]==4&&h[4]==4&&h[5]==4)
                    : (h[0]==4&&h[1]==4&&h[2]==4&&h[3]==4&&h[4]==4&&h[5]==4);
    if(match){
      copycnt[r]++;int q=0;
      for(int v=0;v<22;v++)if(!(mask>>v&1) && !(a[v]&mask))q++;
      maxq[r]=max(maxq[r],q);
    }
   }
   uint32_t c=mask&-mask,rr=mask+c;mask=(((rr^mask)>>2)/c)|rr;
  }
  cout<<"deg_334444 copies="<<copycnt[0]<<" maxQ="<<maxq[0]
      <<" deg_444444 copies="<<copycnt[1]<<" maxQ="<<maxq[1]<<"\n";
 }
}