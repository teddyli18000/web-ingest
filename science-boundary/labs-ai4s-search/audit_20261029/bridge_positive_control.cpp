// N99 skew E577 -> non-skew E553 published GPU-MTS positive control.
// Uses *known answer* to calibrate barriers along shortest Hamming paths;
// NOT a discovery algorithm and no exact global minimum-barrier proof.
// Compile: g++ -O3 -std=c++17 bridge_positive_control.cpp -o bridge
// Run: ./bridge 10000 1500
#include <bits/stdc++.h>
using namespace std;
struct S {
 vector<int8_t> x;vector<int> c;int e=0,peak=0;uint64_t mask=0;
 explicit S(const string&b):x(b.size()),c(b.size()){
  for(int i=0;i<(int)b.size();i++)x[i]=b[i]=='1'?1:-1;
  int n=x.size();for(int k=1;k<n;k++){for(int i=0;i<n-k;i++)c[k]+=x[i]*x[i+k];e+=c[k]*c[k];}peak=e;
 }
 S()=default;
 void flip(int j){
  int de=0,n=x.size();for(int k=1;k<n;k++){
   int t=(j>=k?x[j-k]:0)+(j+k<n?x[j+k]:0),dc=-2*x[j]*t;
   de+=2*c[k]*dc+dc*dc;c[k]+=dc;
  }x[j]=-x[j];e+=de;peak=max(peak,e);
 }
};
string alternate(string s){for(int i=1;i<(int)s.size();i+=2)s[i]=(s[i]=='1'?'0':'1');return s;}
string negate(string s){for(char &c:s)c=(c=='1'?'0':'1');return s;}
vector<string> orbit(string s){
 vector<string>v;for(int rev=0;rev<2;rev++){
  string b=s;if(rev)reverse(b.begin(),b.end());
  for(int alt=0;alt<2;alt++){string a=alt?alternate(b):b;v.push_back(a);v.push_back(negate(a));}
 }return v;
}
int hamming(string a,string b){int k=0;for(int i=0;i<(int)a.size();i++)k+=a[i]!=b[i];return k;}
int direct_energy(string s){
 int n=s.size(),e=0;for(int k=1;k<n;k++){
  int c=0;for(int i=0;i<n-k;i++)c+=s[i]==s[i+k]?1:-1;e+=c*c;
 }return e;
}
int main(int argc,char**argv){
 string old="111110011111000001101100100111111111100010110011110100110000100101010101100011000110101101011001010";
 string hex="0CF30C003783CBCC8DA92AAD4",newer;
 for(char z:hex){
  int u=isdigit(z)?z-'0':z-'A'+10;
  for(int i=3;i>=0;i--)newer+=(u>>i&1)?'1':'0';
 }
 newer.resize(99);
 if(direct_energy(old)!=577 || direct_energy(newer)!=553)throw runtime_error("source energy check failed");
 int h=100;string goal;
 for(auto v:orbit(newer))if(hamming(old,v)<h){h=hamming(old,v);goal=v;}
 vector<int>difference;for(int i=0;i<99;i++)if(old[i]!=goal[i])difference.push_back(i);
 if(h!=41)throw runtime_error("orbit Hamming mismatch");
 S start(old),target(goal);mt19937_64 rng(123456);
 int iterations=argc>1?stoi(argv[1]):10000,width=argc>2?stoi(argv[2]):1500;
 vector<int>peaks;
 for(int r=0;r<iterations;r++){
  auto ids=difference;shuffle(ids.begin(),ids.end(),rng);S state=start;
  for(int i:ids)state.flip(i);
  if(state.e!=target.e)throw runtime_error("random path endpoint invalid");
  peaks.push_back(state.peak);
 }
 sort(peaks.begin(),peaks.end());
 S greedy=start;uint64_t used=0;
 for(int d=0;d<h;d++){
  int bestj=-1,score=INT_MAX;
  for(int j=0;j<h;j++)if(!(used>>j&1)){
   S t=greedy;t.flip(difference[j]);
   if(t.e<score){score=t.e;bestj=j;}
  }
  greedy.flip(difference[bestj]);used|=1ULL<<bestj;
 }
 vector<S>beam{start};
 for(int d=0;d<h;d++){
  unordered_map<uint64_t,S> next;next.reserve(size_t(width)*h);
  for(auto&state:beam)for(int j=0;j<h;j++)if(!(state.mask>>j&1)){
   S t=state;t.mask|=1ULL<<j;t.flip(difference[j]);
   auto it=next.find(t.mask);
   if(it==next.end()||make_pair(t.peak,t.e)<make_pair(it->second.peak,it->second.e))
      next.insert_or_assign(t.mask,std::move(t));
  }
  vector<S>v;v.reserve(next.size());
  for(auto&p:next)v.push_back(std::move(p.second));
  if(v.size()>(size_t)width){
   nth_element(v.begin(),v.begin()+width,v.end(),[](auto&a,auto&b){return tie(a.peak,a.e)<tie(b.peak,b.e);});
   v.resize(width);
  }
  beam.swap(v);
  sort(beam.begin(),beam.end(),[](auto&a,auto&b){return tie(a.peak,a.e)<tie(b.peak,b.e);});
 }
 if(beam.size()!=1||beam[0].e!=553||greedy.e!=553)throw runtime_error("beam endpoint invalid");
 cout<<"N=99 oldE=577 goalE=553 min_hamming="<<h
     <<" random_min_peak="<<peaks.front()<<" random_median_peak="<<peaks[iterations/2]
     <<" greedy_peak="<<greedy.peak<<" beam_peak="<<beam[0].peak
     <<" width="<<width<<" random_samples="<<iterations<<"\n";
}
