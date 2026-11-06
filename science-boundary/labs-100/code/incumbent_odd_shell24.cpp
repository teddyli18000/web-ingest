// Exact ordinary Hamming-shell scanner at radius 2 or 4 around LABS-100 E578.
// Used only to test whether the O=66 odd-defect corridor is locally accessible.
// Compile: g++ -O3 -std=c++20 code/incumbent_odd_shell24.cpp -o /tmp/odd-shell
// Run: /tmp/odd-shell 2 ; /tmp/odd-shell 4
#include <array>
#include <algorithm>
#include <cstdint>
#include <iostream>
#include <string>
#include <chrono>
using namespace std;
using U=__uint128_t;
const string INC="++++++--+++++-----++-++--+--++++++++++---+-++--++++-+--++----+--+-+-+-+-++---++---++-+-++-+-++--+-+-";
U M[100];
int E(U b,int*oddOut){
 int o=0,e=0;
 for(int k=1;k<100;k++){
  U diff=(b^(b>>k))&M[k];
  int bits=__builtin_popcountll((uint64_t)diff)
          +__builtin_popcountll((uint64_t)(diff>>64));
  int c=100-k-2*bits;
  if(k&1)o+=c*c;else e+=c*c;
 }
 if(oddOut)*oddOut=o;
 return e+o;
}
int main(int argc,char**argv){
 int radius=argc>1?stoi(argv[1]):4;
 U orig=0;
 for(int i=0;i<100;i++)if(INC[i]=='+')orig|=(U(1)<<i);
 for(int k=1;k<100;k++)M[k]=(U(1)<<(100-k))-1;
 int minE=1<<30,bestO=0,minAt66=1<<30,minOutOdd=1<<30;
 long long tested=0,n66=0,n50=0,n74=0,near=0;
 auto t0=chrono::steady_clock::now();
 auto evaluate=[&](U z){
  int o=0,e=E(z,&o);tested++;
  if(e<minE){minE=e;bestO=o;}
  if(o>50)minOutOdd=min(minOutOdd,o);
  if(o==66){n66++;minAt66=min(minAt66,e);}
  if(o==74)n74++;
  if(o==50)n50++;
  if(o<=90)near++;
 };
 if(radius==2)
  for(int i=0;i<100;i++)for(int j=i+1;j<100;j++)
   evaluate(orig^(U(1)<<i)^(U(1)<<j));
 if(radius==4)
  for(int i=0;i<100;i++)for(int j=i+1;j<100;j++)
   for(int k=j+1;k<100;k++)for(int l=k+1;l<100;l++)
    evaluate(orig^(U(1)<<i)^(U(1)<<j)^(U(1)<<k)^(U(1)<<l));
 cout<<"SUMMARY radius="<<radius<<" tested="<<tested<<" bestE="<<minE
     <<" bestO="<<bestO<<" O50="<<n50<<" O66="<<n66<<" O74="<<n74
     <<" O_le_90="<<near<<" minNon50Odd="<<minOutOdd
     <<" ms="<<chrono::duration_cast<chrono::milliseconds>(
                  chrono::steady_clock::now()-t0).count()<<"\n";
}
