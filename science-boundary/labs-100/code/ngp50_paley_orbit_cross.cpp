// Exhaust the standard equivalence orbit (modulo independent global signs) of
// the public length-50 first-Paley negaperiodic Golay pair and test the LABS
// odd-perfect cyclic cross condition.
//
// Source for the negacyclic conference row: Balonin-Djokovic,
// "Negaperiodic Golay pairs and Hadamard matrices", Appendix A, v=50, q=49.
// Proposition 6 gives a=(+1,c1,...,c49), b=(-1,c1,...,c49).
#include <array>
#include <vector>
#include <iostream>
#include <numeric>
#include <algorithm>
#include <string>
using S=std::array<int,50>;

static S nsh(S a,int t){for(int z=0;z<t;z++){int x=-a[49];for(int i=49;i>0;i--)a[i]=a[i-1];a[0]=x;}return a;}
static S rev(S a){std::reverse(a.begin(),a.end());return a;}
static S alt(S a){for(int i=1;i<50;i+=2)a[i]=-a[i];return a;}
// Standard NGP equivalence transformation (iv).
static S mult(const S&a,int k){S b{};for(int i=0;i<50;i++){int r=(k*i)%100;int z=r<50?1:-1;b[i]=z*a[r%50];}return b;}

static int af(const S&a,int k){int x=0;for(int i=0;i<50-k;i++)x+=a[i]*a[i+k];return x;}
static bool ngp(const S&A,const S&B){for(int k=1;k<50;k++)if((af(A,k)-af(A,50-k))+(af(B,k)-af(B,50-k)))return false;return true;}

// H=A B* + x B A*=0 in Z[x]/(x^50-1).
static bool hzero(const S&A,const S&B){
 for(int r=0;r<50;r++){
  int x=0;for(int i=0;i<50;i++)x+=A[i]*B[(i+r)%50]+B[i]*A[(i+r+1)%50];
  if(x)return false;
 }
 return true;
}
static long long energy(const S&A,const S&B,long long&odd,long long&even){
 std::array<int,100>s{};for(int i=0;i<50;i++){s[2*i]=A[i];s[2*i+1]=B[i];}
 long long e=0;odd=even=0;for(int k=1;k<100;k++){int c=0;for(int i=0;i<100-k;i++)c+=s[i]*s[i+k];long long q=1LL*c*c;e+=q;if(k&1)odd+=q;else even+=q;}return e;
}
static int sum(const S&a){return std::accumulate(a.begin(),a.end(),0);}
static std::string fmt(const S&A,const S&B){std::string z;z.reserve(100);for(int i=0;i<50;i++){z+=A[i]>0?'+':'-';z+=B[i]>0?'+':'-';}return z;}

int main(){
 int raw[49]={+1,-1,-1,-1,+1,+1,-1,+1,-1,+1,-1,-1,-1,+1,-1,+1,-1,-1,+1,+1,+1,-1,-1,-1,-1,+1,-1,+1,+1,-1,+1,+1,-1,-1,-1,-1,-1,+1,-1,-1,-1,-1,-1,-1,+1,+1,-1,+1,+1};
 S a{},b{};a[0]=1;b[0]=-1;for(int i=1;i<50;i++)a[i]=b[i]=raw[i-1];
 if(!ngp(a,b)){std::cerr<<"source pair is not NGP\n";return 2;}
 std::vector<int> units;for(int k=1;k<50;k++)if(std::gcd(k,50)==1)units.push_back(k);
 long long tested=0,hits=0,best=1LL<<60;std::string bests;int besta=0,bestb=0;
 // Negashifts 0..49 are sufficient modulo an independent global sign because N^50=-I.
 // k+50 is the same signed permutation as k followed by common alternation, so k=1..49
 // plus the explicit alternation generator covers all multiplier choices modulo 100.
 for(int k:units){
  S am=mult(a,k),bm=mult(b,k);
  for(int ra=0;ra<2;ra++)for(int rb=0;rb<2;rb++){
   S aa=ra?rev(am):am,bb=rb?rev(bm):bm;
   for(int ta=0;ta<50;ta++){
    S A=nsh(aa,ta);
    for(int tb=0;tb<50;tb++){
     S B=nsh(bb,tb);
     for(int al=0;al<2;al++)for(int sw=0;sw<2;sw++){
      S X=al?alt(A):A,Y=al?alt(B):B;if(sw)std::swap(X,Y);tested++;
      if(!hzero(X,Y))continue;
      hits++;long long o,e;long long E=energy(X,Y,o,e);int sa=sum(X),sb=sum(Y);
      std::cout<<"HIT E="<<E<<" odd="<<o<<" even="<<e<<" sums="<<sa<<","<<sb
               <<" k="<<k<<" ra="<<ra<<" rb="<<rb<<" ta="<<ta<<" tb="<<tb<<" alt="<<al<<" sw="<<sw<<"\n";
      if(E<best){best=E;bests=fmt(X,Y);besta=sa;bestb=sb;}
     }
    }
   }
  }
 }
 std::cout<<"SUMMARY tested="<<tested<<" hits="<<hits<<" best="<<(best==(1LL<<60)?-1:best)<<" sums="<<besta<<","<<bestb<<"\n";
 if(best<(1LL<<60))std::cout<<"BESTSEQ "<<bests<<"\n";
}
