#include <array>
#include <algorithm>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <iterator>
#include <random>
#include <stdexcept>
#include <string>
#include <unordered_set>
#include <vector>

namespace {
constexpr int Q=7, D=5, U=16807, TARGET=367;
using Word=std::array<int,D>;

Word dec(int v){ Word w{}; for(int i=0;i<D;++i){w[i]=v%Q;v/=Q;} return w; }
int enc(const Word&w){ int v=0,m=1; for(int i=0;i<D;++i){v+=w[i]*m;m*=Q;} return v; }

std::vector<int> hood(int v){
  Word w=dec(v); std::vector<int> out; out.reserve(243);
  for(int code=0;code<243;++code){ int z=code; Word y=w; for(int j=0;j<D;++j){int d=z%3-1;z/=3;y[j]=(y[j]+d+Q)%Q;} out.push_back(enc(y)); }
  return out;
}

std::vector<int> parse_X(const std::string&path){
  std::ifstream in(path); if(!in) throw std::runtime_error("cannot open base json");
  std::string s((std::istreambuf_iterator<char>(in)),{});
  auto p=s.find("\"X\""); if(p==std::string::npos) throw std::runtime_error("X key missing");
  p=s.find('[',p); auto e=s.find(']',p); if(e==std::string::npos) throw std::runtime_error("X array unterminated");
  std::vector<int>x; int cur=-1;
  for(size_t i=p+1;i<e;++i){ char c=s[i]; if(c>='0'&&c<='9'){ if(cur<0)cur=0;cur=10*cur+(c-'0'); } else if(cur>=0){x.push_back(cur);cur=-1;} }
  if(cur>=0)x.push_back(cur); if(x.size()!=367) throw std::runtime_error("X size drift"); return x;
}

std::unordered_set<int> obstruction(){
  const int PH[9]={1553,3716,6494,13158,13065,13677,12277,15075,15384};
  const int PV[9]={15910,6110,8888,10708,13358,14027,14329,14733,15685};
  std::array<unsigned char,U> a{},b{};
  for(int x:PH) for(int y:hood(x)) a[y]=1;
  for(int x:PV) for(int y:hood(x)) b[y]=1;
  std::unordered_set<int>Dset; for(int v=0;v<U;++v) if(a[v]&&b[v])Dset.insert(v);
  if(Dset.size()!=1098 || !Dset.count(10665)) throw std::runtime_error("obstruction drift"); return Dset;
}

struct Search{
  std::vector<std::vector<int>> nb;
  std::vector<unsigned char> allowed, sel;
  std::vector<int> cnt, selected;
  std::unordered_set<int> b0,b1,b2;
  std::mt19937_64 rng;

  explicit Search(uint64_t seed):nb(U),allowed(U),sel(U),cnt(U),rng(seed){ for(int v=0;v<U;++v)nb[v]=hood(v); }
  void bucket_erase(int v,int c){ if(!allowed[v]||sel[v])return; if(c==0)b0.erase(v);else if(c==1)b1.erase(v);else if(c==2)b2.erase(v); }
  void bucket_add(int v,int c){ if(!allowed[v]||sel[v])return; if(c==0)b0.insert(v);else if(c==1)b1.insert(v);else if(c==2)b2.insert(v); }
  void add(int q){ if(sel[q]||!allowed[q]||cnt[q]!=0)throw std::runtime_error("bad add"); bucket_erase(q,0); sel[q]=1;selected.push_back(q); for(int v:nb[q]){ if(v!=q&&!sel[v])bucket_erase(v,cnt[v]); ++cnt[v]; if(v!=q&&!sel[v])bucket_add(v,cnt[v]); } }
  void rem(int q){ if(!sel[q])throw std::runtime_error("bad remove"); sel[q]=0; auto it=std::find(selected.begin(),selected.end(),q); if(it==selected.end())throw std::runtime_error("selected drift"); *it=selected.back();selected.pop_back(); for(int v:nb[q]){ if(v!=q&&!sel[v])bucket_erase(v,cnt[v]); --cnt[v]; if(v!=q&&!sel[v])bucket_add(v,cnt[v]); } bucket_add(q,cnt[q]); }
  int any(const std::unordered_set<int>&s){ if(s.empty())return -1; auto it=s.begin(); std::advance(it, rng()%s.size()); return *it; }
  std::vector<int> blockers(int q){ std::vector<int> r; for(int v:nb[q])if(sel[v])r.push_back(v); return r; }
  void rebuild(const std::vector<int>&start,const std::unordered_set<int>&Dset){
    std::fill(allowed.begin(),allowed.end(),1); for(int v:Dset)allowed[v]=0; std::fill(sel.begin(),sel.end(),0);std::fill(cnt.begin(),cnt.end(),0);selected.clear();b0.clear();b1.clear();b2.clear();
    for(int v=0;v<U;++v)if(allowed[v])b0.insert(v); for(int q:start){ if(!allowed[q])throw std::runtime_error("start hits D"); add(q); }
  }
  bool greedy(){
    while((int)selected.size()<TARGET&&!b0.empty()){
      int best=-1,bscore=1e9,tries=0; for(int q:b0){ int sc=0; for(int v:nb[q]) if(allowed[v]&&!sel[v]&&cnt[v]==0)++sc; if(sc<bscore){bscore=sc;best=q;} if(++tries>=64)break; }
      if(best<0)best=*b0.begin(); add(best);
    }
    return (int)selected.size()>=TARGET;
  }
};
}

int main(int argc,char**argv){
 try{
  if(argc<4||argc>5){std::cerr<<"usage: augment BASE_C7_JSON OUTPUT_IDS STEPS [SEED]\n";return 2;}
  auto X=parse_X(argv[1]); auto Dset=obstruction();
  if(std::find(X.begin(),X.end(),10665)==X.end())throw std::runtime_error("published bad point missing");
  X.erase(std::find(X.begin(),X.end(),10665)); if(X.size()!=366)throw std::runtime_error("start size");
  uint64_t steps=std::stoull(argv[3]), seed=argc==5?std::stoull(argv[4]):1;
  Search s(seed); s.rebuild(X,Dset); if(s.greedy())throw std::runtime_error("unexpected direct augmentation");
  int best=s.selected.size(); uint64_t plateau=0,kicks=0;
  for(uint64_t it=0;it<steps;++it){
    if((int)s.selected.size()>best){best=s.selected.size();std::cerr<<"best="<<best<<" iter="<<it<<"\n";}
    if((int)s.selected.size()>=TARGET){ std::ofstream out(argv[2]); std::sort(s.selected.begin(),s.selected.end()); for(int v:s.selected)out<<v<<"\n"; std::cout<<"FOUND size="<<s.selected.size()<<" iter="<<it<<" seed="<<seed<<"\n"; return 0; }
    if(!s.b0.empty()){ if(s.greedy())continue; }
    bool moved=false;
    if(!s.b1.empty() && (plateau<2000 || s.b2.empty())){
      int q=s.any(s.b1); auto bl=s.blockers(q); if(bl.size()==1){s.rem(bl[0]); if(s.cnt[q]!=0)throw std::runtime_error("swap count drift"); s.add(q); ++plateau; moved=true;}
    }
    if(!moved && !s.b2.empty()){
      int q=s.any(s.b2); auto bl=s.blockers(q); if(bl.size()==2){s.rem(bl[0]);s.rem(bl[1]);if(s.cnt[q]!=0)throw std::runtime_error("kick count drift");s.add(q);s.greedy();++kicks;plateau=0;moved=true;}
    }
    if(!moved || (it>0 && it%20000==0)){
      int k=2+(s.rng()%4); if((int)s.selected.size()<k)k=s.selected.size(); std::shuffle(s.selected.begin(),s.selected.end(),s.rng); std::vector<int> rm(s.selected.begin(),s.selected.begin()+k); for(int v:rm)if(s.sel[v])s.rem(v);s.greedy();plateau=0;++kicks;
    }
    if(it%100000==0)std::cerr<<"iter="<<it<<" size="<<s.selected.size()<<" b1="<<s.b1.size()<<" b2="<<s.b2.size()<<" kicks="<<kicks<<"\n";
  }
  std::cout<<"NONE best="<<best<<" final="<<s.selected.size()<<" steps="<<steps<<" seed="<<seed<<"\n"; return 0;
 }catch(const std::exception&e){std::cerr<<"error: "<<e.what()<<"\n";return 1;}
}
