// Exact moving insertion certificate search for LABS N=60 and N=100.
// Sources: QOBLIB N59 E205; Zhang et al. (2025/2026) N99 E553.
// Build: g++ -O3 -std=c++20 code/moving_insertion_exact.cpp -o /tmp/lift
// Run: /tmp/lift 99 3, /tmp/lift 59 4
#include <algorithm>
#include <array>
#include <cassert>
#include <climits>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <string>
using namespace std;
using u128=__uint128_t;
array<u128,101> prefix_mask;
inline int pop(u128 x) {
    return __builtin_popcountll((uint64_t)x)+__builtin_popcountll((uint64_t)(x>>64));
}
int E(u128 b,int n) {
    int value=0;
    for(int lag=1;lag<n;lag++) {
        int len=n-lag, mismatch=pop((b^(b>>lag))&prefix_mask[len]);
        int corr=len-2*mismatch;
        value+=corr*corr;
    }
    return value;
}
u128 encode(const string& s) {
    u128 b=0;
    for(int i=0;i<(int)s.size();i++)if(s[i]=='+')b|=u128(1)<<i;
    return b;
}
string decode(u128 b,int n) {
    string s;
    for(int i=0;i<n;i++)s+=((b>>i)&1)?'+':'-';
    return s;
}
u128 insert_bit(u128 source,int index,int plus) {
    return (source&prefix_mask[index]) | (u128(plus)<<index) |
           ((source>>index)<<(index+1));
}
struct Lift { int energy=INT_MAX,index=0,plus=0;u128 sequence=0;};
Lift best_insertion(u128 source,int n) {
    Lift best;
    for(int index=0;index<=n;index++)for(int plus=0;plus<2;plus++) {
        u128 s=insert_bit(source,index,plus);
        int e=E(s,n+1);
        if(e<best.energy)best={e,index,plus,s};
    }
    return best;
}
int main(int argc,char**argv) {
    if(argc!=3)return 1;
    int n=atoi(argv[1]),radius=atoi(argv[2]);
    if((n!=59&&n!=99)||radius<0||radius>4)return 1;
    for(int i=1;i<=100;i++)prefix_mask[i]=(u128(1)<<i)-1;
    string source=n==59?
        "+++++++-------++----+--++----++-+--++---+-++--+-+-+--+-+-+-":
        "++++--++----++--++++--++++++++++++--+----+++++----++-+----++--++-+++--+--+-+-++-++-+-+-+-+-+--+-+-+";
    assert((int)source.size()==n);
    u128 base=encode(source);
    assert(E(base,n)==(n==59?205:553));
    Lift best;u128 best_base=base;
    uint64_t sources=0,lifted=0;
    auto visit=[&](u128 b) {
        Lift candidate=best_insertion(b,n);
        sources++;lifted+=2*(n+1);
        if(candidate.energy<best.energy) {best=candidate;best_base=b;}
    };
    auto recurse=[&](auto&& self,int offset,int remaining,u128 bits)->void {
        if(remaining==0){visit(bits);return;}
        for(int i=offset;i<=n-remaining;i++)
            self(self,i+1,remaining-1,bits^(u128(1)<<i));
    };
    recurse(recurse,0,radius,base);
    assert(E(best.sequence,n+1)==best.energy);
    cout<<"SHELL length="<<n+1<<" source_radius="<<radius
        <<" sources="<<sources<<" lifted_states="<<lifted
        <<" minE="<<best.energy<<" best_source_E="<<E(best_base,n)
        <<" insertion="<<best.index<<" inserted_sign="<<(best.plus?'+':'-')<<"\n";
    cout<<"BEST_LIFT "<<decode(best.sequence,n+1)<<"\n";
    cout<<"BEST_SOURCE "<<decode(best_base,n)<<"\n";
}
