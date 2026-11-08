// Exact one-/two-interval inheritance stitching of two N100 LABS parents:
// historical E578 and E606 lifted from published non-skew N99 E553.
// Build: g++ -O3 -std=c++20 code/two_parent_stitch_exact.cpp -o /tmp/stitch
// Run: /tmp/stitch 1; /tmp/stitch 2
#include <array>
#include <algorithm>
#include <cassert>
#include <climits>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <string>
using namespace std;
using u128=__uint128_t;
inline int pop(u128 x) {
    return __builtin_popcountll((uint64_t)x)+__builtin_popcountll((uint64_t)(x>>64));
}
array<u128,101> masks;
int energy(u128 b) {
    int E=0;
    for(int k=1;k<100;k++) {
        int len=100-k,d=pop((b^(b>>k))&masks[len]);
        int c=len-2*d;
        E+=c*c;
    }
    return E;
}
u128 from_pm(const string& s) {
    u128 b=0;
    for(int i=0;i<100;i++)if(s[i]=='+')b|=u128(1)<<i;
    return b;
}
string as_pm(u128 b) {
    string s;
    for(int i=0;i<100;i++)s+=((b>>i)&1)?'+':'-';
    return s;
}
const string a="++++++--+++++-----++-++--+--++++++++++---+-++--++++-+--++----+--+-+-+-+-++---++---++-+-++-+-++--+-+-";
const string b="+++++--++----++--++++--++++++++++++--+----+++++----++-+----++--++-+++--+--+-+-++-++-+-+-+-+-+--+-+-+";
int main(int argc,char**argv) {
    if(argc!=2)return 1;
    int blocks=atoi(argv[1]);
    if(blocks!=1&&blocks!=2)return 1;
    for(int i=1;i<=100;i++)masks[i]=(u128(1)<<i)-1;
    u128 A=from_pm(a);
    assert(energy(A)==578 && energy(from_pm(b))==606);
    array<u128,8> orbit{};
    for(int rev=0;rev<2;rev++)for(int neg=0;neg<2;neg++)for(int alt=0;alt<2;alt++) {
        string s=rev?string(a.rbegin(),a.rend()):a;
        for(int i=0;i<100;i++)if(neg^(alt&&(i&1)))s[i]=(s[i]=='+')?'-':'+';
        orbit[(rev*2+neg)*2+alt]=from_pm(s);
    }
    uint64_t tested=0,le650=0,le750=0,le900=0;
    int min_any=INT_MAX,min_far=INT_MAX,min_target_far=INT_MAX;
    u128 best_far=0,best_target_far=0;
    auto evaluate=[&](u128 child) {
        tested++;
        int E=energy(child);
        min_any=min(min_any,E);
        if(E>900)return;
        le900++;
        if(E<=750)le750++;
        if(E<=650)le650++;
        int distance=100;
        for(auto x:orbit)distance=min(distance,pop(child^x));
        if(distance>=8&&E<min_far) {
            min_far=E;best_far=child;
        }
        if(E%8==6&&distance>=8&&E<min_target_far) {
            min_target_far=E;best_target_far=child;
        }
    };
    for(int rev=0;rev<2;rev++)for(int neg=0;neg<2;neg++)for(int alt=0;alt<2;alt++) {
        string s=rev?string(b.rbegin(),b.rend()):b;
        for(int i=0;i<100;i++)if(neg^(alt&&(i&1)))s[i]=(s[i]=='+')?'-':'+';
        u128 delta=A^from_pm(s);
        if(blocks==1) {
            for(int i=0;i<100;i++)for(int j=i+1;j<=100;j++)
                evaluate(A^(delta&(masks[j]^masks[i])));
        } else {
            for(int i=0;i<98;i++)for(int j=i+1;j<99;j++)
                for(int k=j+1;k<100;k++)for(int l=k+1;l<=100;l++) {
                    u128 mask=(masks[j]^masks[i])|(masks[l]^masks[k]);
                    evaluate(A^(delta&mask));
                }
        }
    }
    assert(energy(best_far)==min_far&&energy(best_target_far)==min_target_far);
    cout<<"STITCH blocks="<<blocks<<" tested="<<tested
        <<" minAny="<<min_any<<" minOrbitFar="<<min_far
        <<" minTargetClassFar="<<min_target_far<<" le650="<<le650
        <<" le750="<<le750<<" le900="<<le900<<"\n";
    cout<<"BEST_FAR "<<as_pm(best_far)<<"\n";
    cout<<"BEST_TARGET_CLASS_FAR "<<as_pm(best_target_far)<<"\n";
}
