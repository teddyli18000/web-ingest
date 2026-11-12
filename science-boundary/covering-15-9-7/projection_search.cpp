// Project an independent (15,10,8) cover to 9-blocks, optimize 7-set coverage,
// then patch uncovered 7-sets with greedy exact set cover. Every complete result
// is independently checkable by Few Shots' authoritative p015 verifier.
#include <bits/stdc++.h>
using namespace std;
static constexpr int V=15;
vector<int> b9,b7,ten;
int ix9[1<<V],ix7[1<<V];
vector<array<int,36>> covers;
vector<array<int,10>> options;
vector<int> cnt,sel,bestsel;
mt19937_64 rng;
int missing=0,bestmissing=100000;

void setup(){
  fill(begin(ix9),end(ix9),-1);fill(begin(ix7),end(ix7),-1);
  for(int m=0;m<(1<<V);m++){
    if(__builtin_popcount((unsigned)m)==9){ix9[m]=b9.size();b9.push_back(m);}
    if(__builtin_popcount((unsigned)m)==7){ix7[m]=b7.size();b7.push_back(m);}
  }
  covers.resize(b9.size());
  for(int i=0;i<(int)b9.size();i++){
    int q=0;
    for(int s=b9[i];s;s=(s-1)&b9[i])
      if(__builtin_popcount((unsigned)s)==7)covers[i][q++]=ix7[s];
    assert(q==36);
  }
}
void swap_choice(int i,int nw){
  int old=sel[i];if(old==nw)return;
  for(int s:covers[options[i][old]])if(--cnt[s]==0)missing++;
  for(int s:covers[options[i][nw]])if(cnt[s]++==0)missing--;
  sel[i]=nw;
}
int change_cost(int i,int nw){
  int old=sel[i];if(old==nw)return 0;
  int oldmask=b9[options[i][old]],newmask=b9[options[i][nw]];
  int delta=0;
  for(int s:covers[options[i][old]])
    if((b7[s]&newmask)!=b7[s] && cnt[s]==1)delta++;
  for(int s:covers[options[i][nw]])
    if((b7[s]&oldmask)!=b7[s] && cnt[s]==0)delta--;
  return delta;
}
vector<int> fill_holes(const vector<int>& choices){
  vector<int> cov(b7.size());
  vector<int> result;
  for(int i=0;i<(int)choices.size();i++){
    int a=options[i][choices[i]];result.push_back(a);
    for(int s:covers[a])cov[s]++;
  }
  while(true){
    bool finished=true;
    for(int x:cov)if(x==0){finished=false;break;}
    if(finished)break;
    int best=-1,gain=0;
    for(int a=0;a<(int)b9.size();a++){
      int g=0;for(int s:covers[a])g+=(cov[s]==0);
      if(g>gain){gain=g;best=a;}
    }
    assert(gain>0);
    result.push_back(best);
    for(int s:covers[best])cov[s]++;
  }
  return result;
}
void save(const vector<int>& blocks,const string& path){
  ofstream out(path);out<<"{\"blocks\":[";
  for(int i=0;i<(int)blocks.size();i++){
    if(i)out<<",";
    out<<"[";int q=0;
    for(int p=0;p<V;p++)if(b9[blocks[i]]>>p&1){if(q++)out<<",";out<<p;}
    out<<"]";
  }
  out<<"]}";
}
int main(int argc,char**argv){
  if(argc!=6){cerr<<"usage: projection_search parent10.txt seconds seed full.json projected.json\n";return 2;}
  setup();rng.seed(stoull(argv[3]));
  ifstream in(argv[1]);string line;
  while(getline(in,line)){
    if(line.empty())continue;
    istringstream ss(line);int mask=0,p,q=0;array<int,10> pts{};
    while(ss>>p){mask|=1<<p;pts[q++]=p;}
    assert(q==10&&__builtin_popcount((unsigned)mask)==10);
    ten.push_back(mask);
    array<int,10> vs{};
    for(int j=0;j<10;j++)vs[j]=ix9[mask&~(1<<pts[j])];
    options.push_back(vs);
  }
  cerr<<"PARENTS "<<ten.size()<<"\n";
  const double seconds=atof(argv[2]);
  sel.assign(ten.size(),0);cnt.assign(b7.size(),0);
  for(int i=0;i<(int)sel.size();i++){
    sel[i]=rng()%10;
    for(int s:covers[options[i][sel[i]]])cnt[s]++;
  }
  for(int x:cnt)missing+=(x==0);
  bestmissing=missing;bestsel=sel;
  vector<int> incumbent=fill_holes(sel);
  int bestfull=incumbent.size();save(incumbent,argv[4]);
  auto start=chrono::steady_clock::now();
  uniform_real_distribution<double> U(0.,1.);
  long long step=0;
  while(true){
    if((step&65535)==0 && chrono::duration<double>(chrono::steady_clock::now()-start).count()>=seconds)break;
    step++;
    int i=rng()%ten.size(),j=rng()%10;
    int delta=change_cost(i,j);
    double phase=(step%250000)/250000.;
    double temp=.15+2.4*pow(1.-phase,2);
    if(delta<=0||U(rng)<exp(-delta/temp)){
      swap_choice(i,j);
      if(missing<bestmissing){
        bestmissing=missing;bestsel=sel;
        if(bestmissing%20==0||bestmissing<400){
          auto patched=fill_holes(sel);int total=patched.size();
          if(total<bestfull){
            bestfull=total;incumbent=move(patched);save(incumbent,argv[4]);
          }
          cerr<<"BEST missing="<<bestmissing<<" greedy_total="<<total<<" best_full="<<bestfull<<" step="<<step<<"\n";
        }
      }
    }
    if(step%250000==0){
      cerr<<"PROGRESS step="<<step<<" best_miss="<<bestmissing<<" best_full="<<bestfull<<"\n";
      if(bestmissing+200<missing)
        for(int i=0;i<(int)sel.size();i++)swap_choice(i,bestsel[i]);
    }
  }
  auto final=fill_holes(bestsel);
  if((int)final.size()<bestfull){bestfull=final.size();save(final,argv[4]);}
  vector<int> projected;
  for(int i=0;i<(int)bestsel.size();i++)projected.push_back(options[i][bestsel[i]]);
  save(projected,argv[5]);
  cout<<"RESULT projection_miss="<<bestmissing<<" full_blocks="<<bestfull<<" steps="<<step<<"\n";
}
