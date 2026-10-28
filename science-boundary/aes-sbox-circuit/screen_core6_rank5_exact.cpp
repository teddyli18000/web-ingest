// Exact physical mandatory-form screen for quotient-rank-six six-AND p008 cores.
// Covers all 496 zero-state completions whose nine target factors share the
// common five-dimensional nonlinear quotient space U.  For one of the 35
// possible first-AND classes r0 outside U, the final rank-six envelope is
// E=span(U,r0).  The search enumerates exact 16-state truth tables, AND/XOR/XNOR
// phases, all non-free affine operand forms, and all 496 target completions.
// A zero-hit completed run proves no 6-AND + <=11-linear fixed-interface core
// exists in that envelope.  This does not cover quotient-rank-five six-AND cores.

#include <algorithm>
#include <array>
#include <chrono>
#include <cstdint>
#include <iomanip>
#include <iostream>
#include <map>
#include <set>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>
using namespace std;
using Clock=chrono::steady_clock;
static array<uint16_t,65536> STRIP;
constexpr uint16_t ONES=0xffff, CARE=0xfffe;
constexpr int MAX_LINEAR=11;

uint16_t mobius16(uint16_t x){uint32_t y=x;y^=(y&0x5555u)<<1;y^=(y&0x3333u)<<2;y^=(y&0x0f0fu)<<4;y^=(y&0x00ffu)<<8;return y&0xffff;}
uint16_t stripf(uint16_t x){uint16_t a=mobius16(x);a&=uint16_t(~0x0117u);return mobius16(a);} 
uint16_t var(int i){uint16_t v=0;for(int x=0;x<16;x++)if((x>>i)&1)v|=uint16_t(1u<<x);return v;}
using Basis=vector<uint16_t>;
Basis cb(const Basis& vs){array<uint16_t,16> rows{};for(uint16_t x:vs){uint16_t y=x;while(y){int p=31-__builtin_clz((unsigned)y);if(rows[p]){y^=rows[p];continue;}for(int q=p-1;q>=0;--q)if(rows[q]&&((y>>q)&1))y^=rows[q];if(!y)break;p=31-__builtin_clz((unsigned)y);for(int q=p+1;q<16;++q)if(rows[q]&&((rows[q]>>p)&1))rows[q]^=y;rows[p]=y;break;}}Basis o;for(auto x:rows)if(x)o.push_back(x);return o;}
uint16_t red(uint16_t x,const Basis& b){uint16_t y=x;for(auto it=b.rbegin();it!=b.rend();++it){int p=31-__builtin_clz((unsigned)*it);if((y>>p)&1)y^=*it;}return y;}
vector<uint16_t> span(const Basis& b){vector<uint16_t> o{0};for(auto v:b){size_t n=o.size();for(size_t i=0;i<n;i++)o.push_back(o[i]^v);}return o;}
string bkey(const Basis& b){string s; s.resize(1+2*b.size());s[0]=char(b.size());for(size_t i=0;i<b.size();i++){s[1+2*i]=char(b[i]&255);s[2+2*i]=char(b[i]>>8);}return s;}
array<uint16_t,4> INPUTS; Basis LINEAR; array<uint16_t,9> TARGETS;
void init(){for(int i=0;i<65536;i++)STRIP[i]=stripf(i);for(int i=0;i<4;i++)INPUTS[i]=var(i);LINEAR=cb(Basis(INPUTS.begin(),INPUTS.end()));auto [a,b,c,d]=INPUTS;uint16_t q42=a&b,q43=q42^c,q44=q43&d,q45=b^q44,q46=q42&c,q47=d^q46,q48=a&q47,q49=q43^q48,q50=q48^b,q51=q49&q50,q52=q51^a,q53=q52^q49,q54=q45&q53,q55=q54^q47,q56=q55^q49,q57=q53^q45,q58=q56^q57,q59=q55^q45;TARGETS={q45,q59,q52,q57,q53,q49,q58,q55,q56};}

struct Completion{int pattern;array<uint16_t,9> norms;Basis T;};
vector<Completion> rank4_cases; Basis U; vector<int> R5P;
void init_cases(){map<Basis,vector<int>> by;for(int p=0;p<512;p++){Basis rs;for(int i=0;i<9;i++){uint16_t n=TARGETS[i]^(((p>>i)&1)?CARE:0);rs.push_back(STRIP[n]);}by[cb(rs)].push_back(p);}for(auto &kv:by){if(kv.first.size()==4){if(kv.second.size()!=1)throw runtime_error("r4 mult");int p=kv.second[0];Completion c{p,{},{}};for(int i=0;i<9;i++)c.norms[i]=TARGETS[i]^(((p>>i)&1)?CARE:0);c.T=kv.first;rank4_cases.push_back(c);}else if(kv.first.size()==5){if(!U.empty())throw runtime_error("multi U");U=kv.first;R5P=kv.second;if(kv.second.size()!=496)throw runtime_error("U patterns");}}sort(rank4_cases.begin(),rank4_cases.end(),[](auto&a,auto&b){return a.pattern<b.pattern;});if(rank4_cases.size()!=16)throw runtime_error("r4 count");}
vector<uint16_t> first_classes(){auto fs=span(LINEAR);set<uint16_t> s;for(size_t i=1;i<fs.size();i++)for(size_t j=0;j<i;j++){auto r=STRIP[fs[i]&fs[j]];if(r)s.insert(r);}return {s.begin(),s.end()};}

struct Cand{uint16_t l,r,norm,res;uint8_t phase;};
struct Bundle{vector<Cand> pairs;map<uint16_t,Basis> next;};
struct SearchCtx{Basis E,T;set<uint16_t> Evals;unordered_map<string,Bundle> cache;array<uint16_t,9> tnorm;array<uint8_t,9> tph;};
const Bundle& candidates(SearchCtx& C,const Basis& b){
    string k=bkey(b);auto it=C.cache.find(k);if(it!=C.cache.end())return it->second;
    Basis all(INPUTS.begin(),INPUTS.end());all.insert(all.end(),b.begin(),b.end());all.push_back(ONES);all=cb(all);auto fs=span(all);Bundle out;
    for(size_t i=1;i<fs.size();i++)for(size_t j=0;j<i;j++){
        uint16_t actual=fs[i]&fs[j],res=STRIP[actual];if(!res||!red(res,b)||!C.Evals.count(res))continue;
        if(!out.next.count(res)){Basis nb=b;nb.push_back(res);nb=cb(nb);if(nb.size()!=b.size()+1)continue;out.next.emplace(res,move(nb));}
        uint8_t ph=actual&1;uint16_t norm=actual^(ph?ONES:0);out.pairs.push_back({fs[i],fs[j],norm,res,ph});
    }
    auto [ii,_]=C.cache.emplace(k,move(out));return ii->second;
}

struct RawKey{array<uint16_t,6> raw{};uint8_t depth=0,phases=0;bool operator<(RawKey const&o)const{if(depth!=o.depth)return depth<o.depth;if(phases!=o.phases)return phases<o.phases;return raw<o.raw;}};
using Mand=vector<uint16_t>;
bool subset(const Mand&a,const Mand&b){size_t i=0,j=0;while(i<a.size()&&j<b.size()){if(a[i]==b[j]){i++;j++;}else if(a[i]>b[j])j++;else return false;}return i==a.size();}
Mand addform(const Mand&m,uint16_t f){auto it=lower_bound(m.begin(),m.end(),f);if(it!=m.end()&&*it==f)return m;Mand o=m;o.insert(o.begin()+(it-m.begin()),f);return o;}
vector<Mand> dominate(vector<Mand> v){sort(v.begin(),v.end(),[](auto&a,auto&b){if(a.size()!=b.size())return a.size()<b.size();return a<b;});v.erase(unique(v.begin(),v.end()),v.end());vector<Mand> keep;for(auto&m:v){bool dom=false;for(auto&k:keep)if(subset(k,m)){dom=true;break;}if(dom)continue;vector<Mand> nk;for(auto&k:keep)if(!subset(m,k))nk.push_back(move(k));nk.push_back(move(m));keep.swap(nk);}return keep;}

struct CoordMap{unordered_map<uint16_t,uint16_t> zero;};
CoordMap coordmap(const RawKey& rk){vector<pair<uint16_t,uint16_t>> pairs{{0,0}};for(int i=0;i<4;i++){size_t n=pairs.size();for(size_t j=0;j<n;j++)pairs.push_back({uint16_t(pairs[j].first^INPUTS[i]),uint16_t(pairs[j].second|(1u<<i))});}for(int i=0;i<rk.depth;i++){size_t n=pairs.size();for(size_t j=0;j<n;j++)pairs.push_back({uint16_t(pairs[j].first^rk.raw[i]),uint16_t(pairs[j].second|(1u<<(4+i)))});}CoordMap C;C.zero.reserve(pairs.size()*2);for(auto &p:pairs)C.zero[p.first]=p.second;return C;}
pair<uint16_t,uint8_t> affine_form(const CoordMap&C,uint16_t truth){auto it=C.zero.find(truth);if(it!=C.zero.end())return {it->second,0};it=C.zero.find(truth^ONES);if(it==C.zero.end())throw runtime_error("coord miss");return {it->second,1};}
bool isfree(uint16_t form,const RawKey& rk){uint16_t mask=form>>1;uint8_t phase=form&1;if(!mask || (mask&(mask-1)))return false;int idx=__builtin_ctz(mask);uint8_t sourcephase= idx<4?0:((rk.phases>>(idx-4))&1);return sourcephase==phase;}
uint16_t encodeform(pair<uint16_t,uint8_t> f){return uint16_t((f.first<<1)|f.second);}

int target_lb_appended(SearchCtx& C,const Basis& b,const RawKey& child,const CoordMap& parent_cm,uint16_t new_norm,const Mand& m){
    int add=0; uint16_t newbit=uint16_t(1u<<(4+child.depth-1));
    for(int i=0;i<9;i++){
        bool covered=false;
        for(int phase=0;phase<2;phase++){
            uint16_t norm=TARGETS[i]^(phase?CARE:0); uint16_t mask=0; bool have=false;
            auto it=parent_cm.zero.find(norm);
            if(it!=parent_cm.zero.end()){mask=it->second;have=true;}
            else {it=parent_cm.zero.find(norm^new_norm);if(it!=parent_cm.zero.end()){mask=uint16_t(it->second|newbit);have=true;}}
            if(!have) continue;
            uint16_t form=uint16_t((mask<<1)|phase);
            if(isfree(form,child)||binary_search(m.begin(),m.end(),form)){covered=true;break;}
        }
        if(!covered)add++;
    }
    Basis j=b;j.insert(j.end(),U.begin(),U.end());int join=cb(j).size();int future=max(0,join-(int)b.size());
    return int(m.size())+max(0,add-future);
}

using Groups=map<Basis,map<RawKey,vector<Mand>>>;
Groups advance(SearchCtx&C,const Groups& states,int depth,uint16_t firstres,long long &generated){map<Basis,map<RawKey,vector<Mand>>> buckets;generated=0;for(auto &bg:states){auto &b=bg.first;auto &bundle=candidates(C,b);auto &cs=bundle.pairs;for(auto &rg:bg.second){auto rk=rg.first;auto cm=coordmap(rk);for(auto &cand:cs){if(depth==0&&cand.res!=firstres)continue;auto lf=encodeform(affine_form(cm,cand.l)),rf=encodeform(affine_form(cm,cand.r));RawKey nr=rk;nr.raw[nr.depth]=cand.norm;if(cand.phase)nr.phases|=uint8_t(1u<<nr.depth);nr.depth++;for(auto &m:rg.second){Mand full=m;if(!isfree(lf,rk))full=addform(full,lf);if(!isfree(rf,rk))full=addform(full,rf);if((int)full.size()>MAX_LINEAR)continue;auto &nb=bundle.next.at(cand.res);if(target_lb_appended(C,nb,nr,cm,cand.norm,full)>MAX_LINEAR)continue;buckets[nb][nr].push_back(move(full));generated++;}}}}Groups out;for(auto &bg:buckets)for(auto &rg:bg.second)out[bg.first][rg.first]=dominate(move(rg.second));return out;}

pair<int,long long> finalcheck(SearchCtx&C,const Groups& st){
    int best=999; long long hits=0; auto it=st.find(C.E); if(it==st.end()) return {best,hits};
    for(auto &rg:it->second){
        auto rk=rg.first; auto cm=coordmap(rk);
        array<array<uint16_t,2>,9> forms{}; array<array<bool,2>,9> avail{};
        for(int i=0;i<9;i++) for(int phase=0;phase<2;phase++){
            uint16_t norm=TARGETS[i]^(phase?CARE:0); auto jt=cm.zero.find(norm);
            if(jt!=cm.zero.end()){avail[i][phase]=true; forms[i][phase]=uint16_t((jt->second<<1)|phase);}
        }
        for(auto &m:rg.second){
            for(int pat:R5P){
                Mand full=m; bool ok=true;
                for(int i=0;i<9;i++){
                    int phase=(pat>>i)&1; if(!avail[i][phase]){ok=false;break;}
                    uint16_t f=forms[i][phase]; if(!isfree(f,rk)) full=addform(full,f);
                    if((int)full.size()>MAX_LINEAR){ok=false;break;}
                }
                if(!ok) continue; best=min(best,(int)full.size()); if((int)full.size()<=MAX_LINEAR) hits++;
            }
        }
    }
    return {best,hits};
}

struct DfsStats{unsigned long long nodes=0,leaves=0,hits=0;int best=999;};
void dfs_suffix(SearchCtx& C,const Basis& b,const RawKey& rk,const Mand& m,DfsStats&S){
    ++S.nodes;
    if(rk.depth==6){Groups one;one[b][rk]={m};auto [best,hits]=finalcheck(C,one);S.best=min(S.best,best);S.hits+=hits;S.leaves++;return;}
    auto cm=coordmap(rk);auto &bundle=candidates(C,b);
    for(auto &cand:bundle.pairs){
        auto lf=encodeform(affine_form(cm,cand.l)),rf=encodeform(affine_form(cm,cand.r));Mand full=m;
        if(!isfree(lf,rk))full=addform(full,lf);if(!isfree(rf,rk))full=addform(full,rf);if((int)full.size()>MAX_LINEAR)continue;
        RawKey nr=rk;nr.raw[nr.depth]=cand.norm;if(cand.phase)nr.phases|=uint8_t(1u<<nr.depth);nr.depth++;
        auto &nb=bundle.next.at(cand.res);if(target_lb_appended(C,nb,nr,cm,cand.norm,full)>MAX_LINEAR)continue;
        dfs_suffix(C,nb,nr,full,S);
    }
}

int main(int argc,char**argv){
    init();init_cases();int fi=0;if(argc>1)fi=stoi(argv[1]);if(fi<0||fi>=35)return 2;
    auto first=first_classes();uint16_t r0=first[fi];Basis E=U;E.push_back(r0);E=cb(E);if(E.size()!=6)return 2;
    SearchCtx C;C.E=E;C.T=U;for(auto v:span(E))C.Evals.insert(v);
    Groups st;RawKey z;st[Basis{}][z]={Mand{}};auto started=Clock::now();
    for(int d=0;d<3;d++){long long gen=0;st=advance(C,st,d,r0,gen);}
    long long prefixes=0;DfsStats total;
    for(auto&bg:st)for(auto&rg:bg.second)for(auto&m:rg.second){DfsStats S;dfs_suffix(C,bg.first,rg.first,m,S);total.nodes+=S.nodes;total.leaves+=S.leaves;total.hits+=S.hits;total.best=min(total.best,S.best);prefixes++;}
    double sec=chrono::duration<double>(Clock::now()-started).count();
    cout<<"SUMMARY fi="<<fi<<" first=0x"<<hex<<r0<<dec<<" prefixes="<<prefixes<<" suffix_nodes="<<total.nodes<<" leaves="<<total.leaves<<" hits="<<total.hits<<" best="<<(total.best==999?-1:total.best)<<" complete=1 sec="<<fixed<<setprecision(6)<<sec<<"\n";
    return total.hits?10:0;
}
