// Exact odd-perfect endpoint-support search in reflection-linearized coordinates,
// strengthened with the exact separable-convex even-correlation lower bound.
//
// The support of the nonzero odd autocorrelations of R=s[0..98] determines its
// skew-reflection defect pattern. After normalizing one bad reflection anchor,
// all odd-perfect constraints become linear signed-sum equations. The remaining
// objective is the 49 even correlations. Their exact sum is fixed by the two
// parity-half sums, so at every branch node we minimize sum C_even^2 exactly
// over the interval/parity relaxation subject to that sum. This is a rigorous
// lower bound: it ignores sequence realizability and therefore cannot overprune.
#include <algorithm>
#include <array>
#include <atomic>
#include <chrono>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <map>
#include <queue>
#include <sstream>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

constexpr int N=100;
using Seq=std::array<int8_t,N>;
using Used=std::array<uint8_t,N>;
using Ints=std::array<int,N>;
struct State{Seq s{};Used used{};Ints fixed{},count{};int sumA=0,sumB=0,countA=0,countB=0;};

static void assign_pos(State&st,int p,int v){
    if(st.used[p]){if(st.s[p]!=v)throw std::runtime_error("assignment conflict");return;}
    for(int j=0;j<N;j++)if(st.used[j]){int k=std::abs(p-j);if(k){st.fixed[k]+=v*int(st.s[j]);st.count[k]++;}}
    st.s[p]=int8_t(v);st.used[p]=1;
    if(p&1){st.sumB+=v;st.countB++;}else{st.sumA+=v;st.countA++;}
}
static void unassign_pos(State&st,int p){
    if(!st.used[p])return;int v=st.s[p];
    if(p&1){st.sumB-=v;st.countB--;}else{st.sumA-=v;st.countA--;}
    st.used[p]=0;
    for(int j=0;j<N;j++)if(st.used[j]){int k=std::abs(p-j);if(k){st.fixed[k]-=v*int(st.s[j]);st.count[k]--;}}
    st.s[p]=0;
}
static bool sum_abs_feasible(int cur,int used,int target_abs){
    int rem=50-used;
    auto one=[&](int target){int d=target-cur;return std::abs(d)<=rem&&(((d-rem)&1)==0);};
    return target_abs==0?one(0):(one(target_abs)||one(-target_abs));
}
static std::vector<int> parse_support(const std::string&x){
    std::vector<int>v;std::stringstream ss(x);std::string p;
    while(std::getline(ss,p,',')){int h=std::stoi(p);if(h<1||h>97||!(h&1))throw std::runtime_error("bad support lag");v.push_back(h);}
    std::sort(v.begin(),v.end());
    if(v.empty()||std::unique(v.begin(),v.end())!=v.end())throw std::runtime_error("empty or duplicate support");
    return v;
}
static bool contains(const std::vector<int>&v,int x){return std::binary_search(v.begin(),v.end(),x);}
static std::array<int,49> reflection_pattern(const std::vector<int>&support){
    std::array<int,49>rho{};rho.fill(1);
    for(int h:support){auto toggle=[&](int j){rho[j]=-rho[j];};if(h==49)toggle(48);else if(h<49){toggle(h-1);toggle(h);}else{toggle(98-h);toggle(99-h);}}
    return rho;
}
struct QTerm{int a,b,c;};
struct QEq{int lag;std::vector<QTerm>terms;};
static std::pair<int,int> map_r_position(int p,const std::array<int,49>&rho){
    if(p<=49)return{p,1};int j=98-p;return{j,(((49-j)&1)?-1:1)*rho[j]};
}
static std::vector<QEq> make_quadratic_equations(const std::array<int,49>&left_rho){
    std::array<int,99>rho{};rho.fill(1);for(int j=0;j<49;j++)rho[j]=rho[98-j]=left_rho[j];rho[49]=1;
    std::vector<QEq>out;
    for(int k=1;k<=97;k+=2){
        int q=(99-k)/2;std::map<std::pair<int,int>,int>acc;
        for(int i=0;i<q;i++){
            int j=2*q-1-i,diff=rho[i]-rho[j];if(!diff)continue;
            int coeff=(((49-i)&1)?-1:1)*(diff/2);
            auto[a,ma]=map_r_position(i,left_rho);auto[b,mb]=map_r_position(j,left_rho);if(a>b)std::swap(a,b);
            acc[{a,b}]+=coeff*ma*mb;
        }
        QEq e{k,{}};for(auto&[ab,c]:acc)if(c)e.terms.push_back({ab.first,ab.second,c});out.push_back(std::move(e));
    }
    return out;
}
struct LTerm{int var,coeff;};
struct LEq{std::vector<LTerm>terms;int constant=0;};
static std::vector<LEq> linearize(
    const std::vector<QEq>&qeq,const std::vector<int>&support,
    const std::array<int,49>&rho,const std::array<int,50>&uconst,int endpoint_ratio){
    std::vector<LEq>out;out.reserve(qeq.size());
    for(const auto&q:qeq){
        LEq e;std::map<int,int>acc;
        for(const auto&t:q.terms){
            bool bad_a=(t.a<49&&rho[t.a]==-1),bad_b=(t.b<49&&rho[t.b]==-1);
            if(bad_a==bad_b)throw std::runtime_error("reflection cross invariant failed");
            int bad=bad_a?t.a:t.b,good=bad_a?t.b:t.a,c=t.c*uconst[bad];
            if(uconst[good])e.constant+=c*uconst[good];else acc[good]+=c;
        }
        if(contains(support,q.lag)){
            auto[j,mult]=map_r_position(99-q.lag,rho);int c=mult*endpoint_ratio;
            if(uconst[j])e.constant+=c*uconst[j];else acc[j]+=c;
        }
        for(auto&[v,c]:acc)if(c)e.terms.push_back({v,c});out.push_back(std::move(e));
    }
    return out;
}
static bool linear_equations_feasible(const std::array<int8_t,50>&u,const std::vector<LEq>&eqs){
    for(const auto&e:eqs){
        int fixed=e.constant,remaining=0;
        for(const auto&t:e.terms){if(u[t.var])fixed+=t.coeff*int(u[t.var]);else remaining+=std::abs(t.coeff);}
        if(std::abs(fixed)>remaining||((remaining-fixed)&1))return false;
    }
    return true;
}

// Exact minimum over the interval/parity relaxation of the completed even
// correlations, additionally enforcing their exact total sum. Write
// d_r=C_(2r)/2. Their sum is (a^2+b^2-100)/4. Starting from the closest-to-zero
// value in each interval, a priority queue applies the cheapest unit changes
// until the target sum is met. Convexity makes this exact for the relaxation.
static long long even_convex_lb(const State&st,int Aabs,int Babs,int cap){
    const int target=(Aabs*Aabs+Babs*Babs-100)/4;
    struct V{int d,lo,hi;};std::array<V,49>vs{};
    int n=0,cur=0,minsum=0,maxsum=0;long long cost=0;
    for(int k=2;k<N;k+=2){
        int L=N-k,unknown=L-st.count[k],f=st.fixed[k];
        int lo=(f-unknown)/2,hi=(f+unknown)/2;if(lo>hi)return cap+1;
        int d=std::clamp(0,lo,hi);vs[n++]={d,lo,hi};cur+=d;minsum+=lo;maxsum+=hi;cost+=1LL*d*d;
    }
    if(target<minsum||target>maxsum)return cap+1;
    using P=std::pair<int,int>;std::priority_queue<P,std::vector<P>,std::greater<P>>pq;
    if(cur<target){
        for(int i=0;i<n;i++)if(vs[i].d<vs[i].hi)pq.push({2*vs[i].d+1,i});
        while(cur<target){if(pq.empty())return cap+1;auto[mc,i]=pq.top();pq.pop();cost+=mc;vs[i].d++;cur++;if(4*cost>cap)return 4*cost;if(vs[i].d<vs[i].hi)pq.push({2*vs[i].d+1,i});}
    }else if(cur>target){
        for(int i=0;i<n;i++)if(vs[i].d>vs[i].lo)pq.push({-2*vs[i].d+1,i});
        while(cur>target){if(pq.empty())return cap+1;auto[mc,i]=pq.top();pq.pop();cost+=mc;vs[i].d--;cur--;if(4*cost>cap)return 4*cost;if(vs[i].d>vs[i].lo)pq.push({-2*vs[i].d+1,i});}
    }
    return 4*cost;
}
static bool prune(
    const State&st,const std::array<int8_t,50>&u,const std::vector<LEq>&eqs,
    int Aabs,int Babs,int cap){
    if(!sum_abs_feasible(st.sumA,st.countA,Aabs)||!sum_abs_feasible(st.sumB,st.countB,Babs))return true;
    if(!linear_equations_feasible(u,eqs))return true;
    return even_convex_lb(st,Aabs,Babs,cap)>cap;
}

struct Var{int j,p,q,mult;};
static std::vector<Var> make_variables(
    const std::array<int,49>&rho,const std::array<int,50>&uconst,const std::vector<LEq>&eqs){
    std::array<int,50>freq{};for(const auto&e:eqs)for(const auto&t:e.terms)freq[t.var]++;
    std::vector<Var>vars;
    for(int j=0;j<50;j++)if(!uconst[j]){
        if(j==49)vars.push_back({j,49,-1,0});
        else vars.push_back({j,j,98-j,(((49-j)&1)?-1:1)*rho[j]});
    }
    std::stable_sort(vars.begin(),vars.end(),[&](const Var&a,const Var&b){
        if(freq[a.j]!=freq[b.j])return freq[a.j]>freq[b.j];
        int oa=std::min(a.p,99-a.p),ob=std::min(b.p,99-b.p);return oa<ob;
    });
    return vars;
}
static bool assign_variable(State&st,std::array<int8_t,50>&u,const Var&v,int value,std::vector<int>&added){
    u[v.j]=int8_t(value);
    if(!st.used[v.p]){assign_pos(st,v.p,value);added.push_back(v.p);}else if(st.s[v.p]!=value)return false;
    if(v.q>=0){int y=v.mult*value;if(!st.used[v.q]){assign_pos(st,v.q,y);added.push_back(v.q);}else if(st.s[v.q]!=y)return false;}
    return true;
}
static void undo_variable(State&st,std::array<int8_t,50>&u,const Var&v,std::vector<int>&added){
    for(int i=int(added.size())-1;i>=0;i--)unassign_pos(st,added[i]);u[v.j]=0;
}
static std::string format(const State&st){std::string z;z.reserve(N);for(int i=0;i<N;i++)z+=st.s[i]>0?'+':'-';return z;}
static bool verify(
    const std::string&z,const std::vector<int>&support,int Aabs,int Babs,int cap,long long&energy){
    std::array<int,N>s{},c{};for(int i=0;i<N;i++)s[i]=z[i]=='+'?1:-1;
    energy=0;long long odd=0;
    for(int k=1;k<N;k++){int x=0;for(int i=0;i<N-k;i++)x+=s[i]*s[i+k];c[k]=x;energy+=1LL*x*x;if(k&1)odd+=1LL*x*x;}
    int A=0,B=0;for(int i=0;i<50;i++){A+=s[2*i];B+=s[2*i+1];}
    std::vector<int>right_support;for(int k=1;k<=97;k+=2)if(c[k]!=s[99-k]*s[99])right_support.push_back(k);
    return odd==50&&std::abs(A)==Aabs&&std::abs(B)==Babs&&right_support==support&&energy<=cap+50;
}
struct Shared{
    unsigned long long nodes=0,leaves=0;bool found=false,timeout=false;std::string seq;
    double seconds=0;std::chrono::steady_clock::time_point start;
};
static void dfs(
    State&st,std::array<int8_t,50>&u,const std::vector<Var>&vars,const std::vector<LEq>&eqs,
    const std::vector<int>&support,int Aabs,int Babs,int cap,int depth,Shared&sh){
    if(sh.found||sh.timeout)return;
    ++sh.nodes;
    if((sh.nodes&0x3ffff)==0&&sh.seconds>0&&
       std::chrono::duration<double>(std::chrono::steady_clock::now()-sh.start).count()>=sh.seconds){sh.timeout=true;return;}
    if(prune(st,u,eqs,Aabs,Babs,cap))return;
    if(depth==int(vars.size())){
        ++sh.leaves;auto z=format(st);long long e=0;
        if(verify(z,support,Aabs,Babs,cap,e)){sh.seq=z;sh.found=true;std::cerr<<"FOUND_E="<<e<<"\n";}
        return;
    }
    for(int value:{-1,+1}){
        std::vector<int>added;
        if(assign_variable(st,u,vars[depth],value,added))dfs(st,u,vars,eqs,support,Aabs,Babs,cap,depth+1,sh);
        undo_variable(st,u,vars[depth],added);
        if(sh.found||sh.timeout)return;
    }
}
int main(int argc,char**argv){
    std::string support_arg="1";int Aabs=2,Babs=0,cap=524;double seconds=60;
    for(int i=1;i<argc;i++){
        std::string a=argv[i];auto need=[&](){if(i+1>=argc)throw std::runtime_error("missing argument after "+a);return std::string(argv[++i]);};
        if(a=="--support")support_arg=need();else if(a=="--A")Aabs=std::stoi(need());else if(a=="--B")Babs=std::stoi(need());else if(a=="--cap")cap=std::stoi(need());else if(a=="--seconds")seconds=std::stod(need());else return 2;
    }
    auto support=parse_support(support_arg);auto rho=reflection_pattern(support);
    std::vector<int>bad;for(int j=0;j<49;j++)if(rho[j]==-1)bad.push_back(j);
    if(bad.empty())throw std::runtime_error("nonempty support produced no reflection defect");
    int ref=bad.front();auto qeq=make_quadratic_equations(rho);
    unsigned long long total_nodes=0,total_leaves=0;auto t0=std::chrono::steady_clock::now();
    int ratio_cases=1<<int(bad.size()-1);
    for(int mask=0;mask<ratio_cases;mask++)for(int endpoint_ratio:{-1,+1}){
        State st;std::array<int8_t,50>u{};std::array<int,50>uconst{};
        uconst[ref]=1;u[ref]=1;assign_pos(st,ref,+1);
        int rm=(((49-ref)&1)?-1:1)*rho[ref];assign_pos(st,98-ref,rm);
        for(int bi=1;bi<int(bad.size());bi++){
            int j=bad[bi],g=(mask>>(bi-1)&1)?+1:-1;uconst[j]=g;u[j]=int8_t(g);assign_pos(st,j,g);
            int m=(((49-j)&1)?-1:1)*rho[j];assign_pos(st,98-j,m*g);
        }
        assign_pos(st,99,endpoint_ratio);
        auto eqs=linearize(qeq,support,rho,uconst,endpoint_ratio);auto vars=make_variables(rho,uconst,eqs);
        Shared sh;sh.seconds=seconds;sh.start=std::chrono::steady_clock::now();
        dfs(st,u,vars,eqs,support,Aabs,Babs,cap,0,sh);total_nodes+=sh.nodes;total_leaves+=sh.leaves;
        if(sh.found){std::cout<<"FOUND support="<<support_arg<<" A="<<Aabs<<" B="<<Babs<<" seq="<<sh.seq<<"\n";return 0;}
        if(sh.timeout){std::cout<<"TIMEOUT support="<<support_arg<<" A="<<Aabs<<" B="<<Babs<<" mask="<<mask<<" endpoint_ratio="<<endpoint_ratio<<" nodes="<<sh.nodes<<"\n";return 1;}
    }
    double wall=std::chrono::duration<double>(std::chrono::steady_clock::now()-t0).count();
    std::cout<<"COMPLETE support="<<support_arg<<" A="<<Aabs<<" B="<<Babs<<" bad="<<bad.size()<<" nodes="<<total_nodes<<" leaves="<<total_leaves<<" seconds="<<wall<<"\n";
    return 0;
}
