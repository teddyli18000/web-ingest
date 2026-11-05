// Complete Hall-matching sweep of all 7^5 relative translations of two
// independent 367-word subsets of C7^5. No 368 witness is assumed.
//
// The conflict graph on A union (B+t), after removing common vertices,
// is bipartite. Konig's theorem gives
// alpha(A union (B+t)) = 367 + ((367-overlap) - matching_size).
//
// Any matching deficiency produces an exact independent-set witness by
// alternating-path extraction of a minimum vertex cover.
#include <algorithm>
#include <array>
#include <fstream>
#include <iostream>
#include <numeric>
#include <queue>
#include <stdexcept>
#include <string>
#include <vector>

constexpr int Q=7,D=5,N=16807,K=367;
constexpr int P[D]={1,7,49,343,2401};
using V=std::vector<int>;

std::array<int,D> decode(int x) {
    std::array<int,D> d{};
    for(int k=0;k<D;k++) d[k]=(x/P[k])%Q;
    return d;
}
bool conf(int x,int y) {
    for(int k=0;k<D;k++){
        int d=((x/P[k])-(y/P[k])+Q)%Q;
        if(d!=0&&d!=1&&d!=6)return false;
    }
    return true;
}
bool independent(const V& a) {
    V v=a;
    std::sort(v.begin(),v.end());
    if(std::adjacent_find(v.begin(),v.end())!=v.end())return false;
    for(size_t i=0;i<v.size();i++)
        for(size_t j=i+1;j<v.size();j++)
            if(conf(v[i],v[j]))return false;
    return true;
}
V load(const std::string& path){
    std::ifstream f(path);
    if(!f)throw std::runtime_error("input not found: "+path);
    V a;int x;
    while(f>>x){if(x<0||x>=N)throw std::runtime_error("input range");a.push_back(x);}
    if(a.size()!=K||!independent(a))throw std::runtime_error("bad 367 code: "+path);
    return a;
}

struct Matcher {
    V A;
    std::vector<V> owners;
    std::array<int,N> a_index{};
    std::vector<std::array<int,D>> b_digits;
    std::array<int,K> match_left{};
    std::array<int,K> seen{};
    std::array<bool,K> common{};
    V right;
    int epoch=0;

    Matcher(V a,V b):A(std::move(a)),owners(N){
        a_index.fill(-1);
        for(int i=0;i<K;i++)a_index[A[i]]=i;
        for(int i=0;i<K;i++){
            auto d=decode(A[i]);
            for(int k=0;k<243;k++){
                int t=k,v=0;
                for(int j=0;j<D;j++){
                    int step=(t%3)-1;
                    t/=3;
                    v+=((d[j]+step+Q)%Q)*P[j];
                }
                owners[v].push_back(i);
            }
        }
        for(int x:b)b_digits.push_back(decode(x));
    }

    bool augment(int ri){
        for(int li:owners[right[ri]]){
            if(common[li]||seen[li]==epoch)continue;
            seen[li]=epoch;
            if(match_left[li]<0||augment(match_left[li])){
                match_left[li]=ri;
                return true;
            }
        }
        return false;
    }

    // Return true on a positive gap; put the fully replayed independent
    // 368-or-larger witness into output on success.
    int evaluate(int shift,V& witness,int& overlap){
        auto t=decode(shift);
        common.fill(false);
        right.clear();
        for(const auto& d:b_digits){
            int x=0;
            for(int k=0;k<D;k++)x+=((d[k]+t[k])%Q)*P[k];
            int j=a_index[x];
            if(j>=0) common[j]=true;
            else right.push_back(x);
        }
        overlap=K-int(right.size());
        match_left.fill(-1);
        seen.fill(0);
        epoch=0;
        int matched=0;
        for(int ri=0;ri<(int)right.size();ri++){
            ++epoch;
            if(augment(ri))matched++;
        }
        int gap=int(right.size())-matched;
        if(gap==0)return 0;

        // Alternating reachability from every unmatched *right* vertex.
        V match_right(right.size(),-1);
        for(int li=0;li<K;li++)
            if(match_left[li]>=0)match_right[match_left[li]]=li;
        std::vector<char> seen_right(right.size(),0);
        std::array<char,K> seen_left{};
        std::queue<int> queue;
        for(int ri=0;ri<(int)right.size();ri++)
            if(match_right[ri]<0){seen_right[ri]=1;queue.push(ri);}
        while(!queue.empty()){
            int ri=queue.front();queue.pop();
            for(int li:owners[right[ri]]){
                if(common[li]||match_right[ri]==li||seen_left[li])continue;
                seen_left[li]=1;
                int r2=match_left[li];
                if(r2>=0&&!seen_right[r2]){
                    seen_right[r2]=1;queue.push(r2);
                }
            }
        }
        witness.clear();
        for(int li=0;li<K;li++)
            if(common[li]||!seen_left[li])witness.push_back(A[li]);
        for(int ri=0;ri<(int)right.size();ri++)
            if(seen_right[ri])witness.push_back(right[ri]);
        std::sort(witness.begin(),witness.end());
        if((int)witness.size()!=K+gap||!independent(witness))
            throw std::runtime_error("Hall witness extraction/replay failed");
        return gap;
    }
};

int main(int argc,char**argv)try{
    if(argc!=6)throw std::runtime_error("usage: hall TRANSLATE_FROM_A.ids B.ids partner STATUS.json WITNESS.ids");
    std::string partner=argv[3];
    auto a=load(argv[1]),b=load(argv[2]);
    Matcher m(std::move(a),std::move(b));
    V witness;
    int hist[K+1]={},tested=0,gap=0,winning_shift=-1,winning_overlap=0,smallest_overlap=K;
    for(int t=0;t<N;t++){
        int overlap=0;
        int g=m.evaluate(t,witness,overlap);
        tested++;
        hist[overlap]++;
        smallest_overlap=std::min(smallest_overlap,overlap);
        if(g>0){
            gap=g;winning_shift=t;winning_overlap=overlap;
            break;
        }
    }
    if(gap>0){
        std::ofstream out(argv[5]);
        for(int v:witness)out<<v<<'\n';
    }
    std::ofstream o(argv[4]);
    o<<"{\n\"method\":\"exact-C7p5-two-basin-Hall-translation\",\n"
      <<"\"partner\":\""<<partner<<"\",\n"
      <<"\"translations_checked\":"<<tested<<",\n"
      <<"\"all_translations_exhausted\":"<<(tested==N?"true":"false")<<",\n"
      <<"\"max_gain\":"<<gap<<",\n"
      <<"\"candidate_368\":"<<(gap>0?"true":"false")<<",\n"
      <<"\"winning_shift\":"<<winning_shift<<",\n"
      <<"\"winning_overlap\":"<<winning_overlap<<",\n"
      <<"\"witness_size\":"<<(gap>0?int(witness.size()):0)<<",\n"
      <<"\"min_overlap\":"<<smallest_overlap<<",\n\"overlap_histogram\":{";
    bool first=true;
    for(int i=0;i<=K;i++)if(hist[i]){
        if(!first)o<<",";
        o<<"\n\""<<i<<"\":"<<hist[i];first=false;
    }
    o<<"}\n}\n";
    std::cout<<"RESULT partner="<<partner<<" translations="<<tested
             <<" gain="<<gap<<" witness_size="<<(gap>0?witness.size():0)
             <<" min_overlap="<<smallest_overlap<<"\n";
    if(tested!=N&&gap==0)throw std::runtime_error("incomplete translation sweep");
    return 0;
}catch(const std::exception&e){
    std::cerr<<"ERROR "<<e.what()<<"\n";
    return 1;
}
