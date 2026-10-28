#include <array>
#include <chrono>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

using S = std::array<int8_t,100>;
using C = std::array<int,100>;

static S parse(const std::string& z) {
    if (z.size()!=100) throw std::runtime_error("sequence length must be 100");
    S s{};
    for (int i=0;i<100;i++) {
        if (z[i]=='+') s[i]=1;
        else if (z[i]=='-') s[i]=-1;
        else throw std::runtime_error("sequence must contain only +/-");
    }
    return s;
}

static std::string fmt(const S& s) {
    std::string z; z.reserve(100);
    for (auto v:s) z.push_back(v>0?'+':'-');
    return z;
}

static long long exact(const S& s, C* out=nullptr, long long* oddout=nullptr) {
    C c{}; long long e=0,o=0;
    for (int k=1;k<100;k++) {
        int x=0;
        for (int i=0;i<100-k;i++) x += int(s[i])*int(s[i+k]);
        c[k]=x; const long long q=1LL*x*x; e+=q; if(k&1)o+=q;
    }
    if(out)*out=c; if(oddout)*oddout=o; return e;
}

static bool canonical_nearskew(const S& s) {
    if (s[0]!=1) return false;
    for (int p=1;p<=49;p++) {
        const int want=(p&1)?-1:1;
        if (int(s[p])*int(s[100-p])!=want) return false;
    }
    return true;
}

static void flipcoord(S& s,C& c,long long& e,int v) {
    const int p=1+v, q=(v==49?-1:99-v);
    const int sp=s[p], sq=q>=0?s[q]:0;
    const int dist=q>=0?std::abs(q-p):-1;
    const int pq=q>=0?sp*sq:0;
    for (int k=1;k<100;k++) {
        int t=0;
        if(p+k<100)t += sp*int(s[p+k]);
        if(p-k>=0)t += int(s[p-k])*sp;
        if(q>=0) {
            if(q+k<100)t += sq*int(s[q+k]);
            if(q-k>=0)t += int(s[q-k])*sq;
            if(k==dist)t -= 2*pq;
        }
        const int nc=c[k]-2*t;
        e += 1LL*nc*nc-1LL*c[k]*c[k];
        c[k]=nc;
    }
    s[p]=-s[p]; if(q>=0)s[q]=-s[q];
}

int main(int argc,char**argv) {
    if(argc<3||argc>4) {
        std::cerr<<"usage: nearskew_cube <seq-a> <seq-b> [max-dim]\n";
        return 2;
    }
    const int maxdim=argc==4?std::stoi(argv[3]):25;
    S a=parse(argv[1]), b=parse(argv[2]);
    long long oa=0,ob=0; const long long ea=exact(a,nullptr,&oa), eb=exact(b,nullptr,&ob);
    if(!canonical_nearskew(a)||!canonical_nearskew(b)||oa!=50||ob!=50) {
        std::cerr<<"both endpoints must be canonical near-skew (s0=+1) with odd energy 50\n";
        return 2;
    }
    std::vector<int> diff;
    for(int v=0;v<50;v++) if(a[1+v]!=b[1+v]) diff.push_back(v);
    if((int)diff.size()>maxdim) {
        std::cout<<"SKIP dims="<<diff.size()<<" maxdim="<<maxdim<<" energy_a="<<ea<<" energy_b="<<eb<<"\n";
        return 3;
    }
    if(diff.size()>=63) return 2;
    const uint64_t total=1ULL<<diff.size();
    S s=a, bests=a; C c{}; long long e=exact(s,&c), best=e;
    uint64_t count=1, prev=0;
    const auto t0=std::chrono::steady_clock::now();
    for(uint64_t i=1;i<total;i++) {
        const uint64_t g=i^(i>>1), x=g^prev; prev=g;
        const int bit=__builtin_ctzll(x);
        flipcoord(s,c,e,diff[bit]);
        if((i&0x3fffffULL)==0) {
            long long odd=0; const long long check=exact(s,nullptr,&odd);
            if(check!=e||odd!=50||!canonical_nearskew(s)) {
                std::cerr<<"incremental/structure mismatch at state "<<i<<"\n";
                return 2;
            }
        }
        if(e<best){best=e;bests=s;count=1;}
        else if(e==best)++count;
    }
    long long odd=0; const long long check=exact(bests,nullptr,&odd);
    if(check!=best||odd!=50) return 2;
    const double sec=std::chrono::duration<double>(std::chrono::steady_clock::now()-t0).count();
    std::cout<<"CUBE dims="<<diff.size()<<" tested="<<total<<" energy_a="<<ea<<" energy_b="<<eb
             <<" best="<<best<<" count="<<count<<" seconds="<<sec<<"\n";
    std::cout<<"BESTSEQ "<<fmt(bests)<<"\n";
    return 0;
}
