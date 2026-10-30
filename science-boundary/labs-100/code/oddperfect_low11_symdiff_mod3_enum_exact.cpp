// Exact low11 symmetric-difference solver by complete +/-1 enumeration of the
// mod-3 nullspace of the signed-c linear system.
//
// Reuse the affine/support machinery and exact low11 checker from the durable
// projective modular solver.  Rename its main so this translation unit can use
// the same audited support enumeration without duplicating it.
#define main legacy_projective_modular_main
#include "oddperfect_low11_symdiff_modular_exact.cpp"
#undef main

// For fixed signed p and c support, the equations H_r=0 (r=0..12) together
// with sum c=0 are a homogeneous 14 x kc integer system M c=0.  Any genuine
// c_j in {-1,+1} reduces modulo 3 to 1 or 2.  RREF over F_3 therefore gives an
// exact finite enumeration: assign each free coordinate either 1 or 2, derive
// every pivot coordinate, require every derived coordinate to remain in
// {1,2}, then verify the resulting sign vector in the original integer
// equations.  Every integer +/-1 solution appears in this list, so no MITM or
// heuristic pruning is required.
struct R3 {
  int nc=0, rank=0;
  int a[14][14]{};
  int piv[14]{};
  bool isp[14]{};
};

static R3 rref3_full(const array<int8_t,25>& p,const vector<int>& ci){
  R3 R; R.nc=(int)ci.size();
  for(int j=0;j<R.nc;j++){
    int pos=ci[j];
    for(int r=0;r<=12;r++){
      int z=(p[(pos+r)%25]+p[(pos-r+25)%25])%3;
      if(z<0) z+=3;
      R.a[r][j]=z;
    }
    R.a[13][j]=1;
  }
  for(int col=0;col<R.nc;col++){
    int q=-1;
    for(int r=R.rank;r<14;r++) if(R.a[r][col]) { q=r; break; }
    if(q<0) continue;
    for(int j=0;j<R.nc;j++) swap(R.a[R.rank][j],R.a[q][j]);
    if(R.a[R.rank][col]==2)
      for(int j=0;j<R.nc;j++) R.a[R.rank][j]=(2*R.a[R.rank][j])%3;
    for(int r=0;r<14;r++) if(r!=R.rank && R.a[r][col]){
      int f=R.a[r][col];
      for(int j=0;j<R.nc;j++){
        R.a[r][j]=(R.a[r][j]-f*R.a[R.rank][j])%3;
        if(R.a[r][j]<0) R.a[r][j]+=3;
      }
    }
    R.piv[R.rank]=col;
    R.isp[col]=true;
    R.rank++;
  }
  return R;
}

static vector<array<int8_t,25>> exact_c_solutions_mod3(
    const array<int8_t,25>& p,const vector<int>& ci){
  auto R=rref3_full(p,ci);
  const int d=R.nc-R.rank;
  vector<int> freec;
  for(int j=0;j<R.nc;j++) if(!R.isp[j]) freec.push_back(j);
  vector<array<int8_t,25>> out;
  const uint64_t total=1ULL<<d;
  for(uint64_t mask=0;mask<total;mask++){
    int x[14]{};
    for(int z=0;z<d;z++) x[freec[z]]=(mask>>z&1)?2:1;
    bool ok=true;
    for(int rr=R.rank-1;rr>=0;rr--){
      int col=R.piv[rr],v=0;
      for(int j=0;j<R.nc;j++) if(j!=col)
        v=(v+R.a[rr][j]*x[j])%3;
      v=(3-v)%3;
      if(v!=1 && v!=2){ ok=false; break; }
      x[col]=v;
    }
    if(!ok) continue;
    array<int8_t,25> c{};
    for(int j=0;j<R.nc;j++) c[ci[j]]=(x[j]==1)?1:-1;
    // Quotient the exact global c -> -c symmetry.
    if(c[ci[0]]<0) continue;
    int ss=0;
    for(int pos:ci) ss+=c[pos];
    if(ss) continue;
    for(int r=0;r<=12 && ok;r++){
      int h=0;
      for(int pos:ci)
        h+=c[pos]*(p[(pos+r)%25]+p[(pos-r+25)%25]);
      if(h) ok=false;
    }
    if(ok) out.push_back(c);
  }
  return out;
}

struct EnumStats {
  long long ptests=0, nonempty=0, hmatch=0, ghit=0;
};

static EnumStats search_signs_mod3_enum(
    U P,U C,int kp,
    vector<pair<array<int8_t,25>,array<int8_t,25>>>* outs=nullptr){
  vector<int> pi,ci;
  for(int i=0;i<25;i++){
    if(P>>i&1) pi.push_back(i);
    if(C>>i&1) ci.push_back(i);
  }
  const int np=(int)pi.size();
  const int pneg=(kp-10)/2;
  EnumStats ST;
  U pmask=pneg?((1u<<pneg)-1):0;
  bool first=true;
  while(true){
    if(!first && pneg==0) break;
    first=false;
    ST.ptests++;
    array<int8_t,25> p{};
    for(int j=0;j<np;j++) p[pi[j]]=(pmask>>j&1)?-1:1;
    auto cs=exact_c_solutions_mod3(p,ci);
    ST.nonempty += !cs.empty();
    for(const auto& c:cs){
      ST.hmatch++;
      if(!low11G(p,c)) continue;
      ST.ghit++;
      if(outs && outs->size()<100) outs->push_back({p,c});
    }
    if(pneg==0) break;
    U cc=pmask&-pmask,rr=pmask+cc;
    if(!rr || rr>=(1u<<np)) break;
    pmask=(((rr^pmask)>>2)/cc)|rr;
  }
  return ST;
}

int main(int argc,char** argv){
  int t=-1,kp=-1,ibeg=0,iend=-1;
  for(int i=1;i<argc;i++){
    string a=argv[i];
    if(a=="--overlap" && i+1<argc) t=atoi(argv[++i]);
    else if(a=="--kp" && i+1<argc) kp=atoi(argv[++i]);
    else if(a=="--begin" && i+1<argc) ibeg=atoi(argv[++i]);
    else if(a=="--end" && i+1<argc) iend=atoi(argv[++i]);
    else { cerr<<"unknown arg "<<a<<"\n"; return 2; }
  }
  if(t<2 || t>12 || (t&1) || (kp!=12 && kp!=14)){
    cerr<<"need even --overlap 2..12 and --kp 12|14\n";
    return 2;
  }
  const int kc=26-kp,s=26-2*t,ew=min(s,25-s);
  const bool comp=s>12;
  auto Es=orbit_reps(ew);
  if(iend<0) iend=(int)Es.size();
  if(ibeg<0 || iend<ibeg || iend>(int)Es.size()){
    cerr<<"bad orbit range total="<<Es.size()<<"\n";
    return 2;
  }
  cerr<<"E_REPS "<<Es.size()<<" range=["<<ibeg<<","<<iend<<")\n";
  atomic<long long> supp{0},ptests{0},nonempty{0},hmatch{0},hits{0};
  vector<pair<array<int8_t,25>,array<int8_t,25>>> outs;
  mutex om;
#pragma omp parallel for schedule(dynamic,1)
  for(int ei=ibeg;ei<iend;ei++){
    U E=Es[ei],D=comp?(ALL^E):E;
    auto K=kernel(E);
    auto st=stabilizer(E);
    long long ls=0,lp=0,ln=0,lm=0,lh=0;
    vector<pair<array<int8_t,25>,array<int8_t,25>>> lo;
    const uint64_t total=1ULL<<K.b.size();
    for(uint64_t m=0;m<total;m++){
      U P=0;
      for(int j=0;j<(int)K.b.size();j++) if(m>>j&1) P^=K.b[j];
      if(__builtin_popcount(P)!=kp) continue;
      U C=P^D;
      if(__builtin_popcount(C)!=kc || canon_stab(P,st)!=P) continue;
      ls++;
      auto z=search_signs_mod3_enum(P,C,kp,&lo);
      lp+=z.ptests; ln+=z.nonempty; lm+=z.hmatch; lh+=z.ghit;
    }
    supp+=ls; ptests+=lp; nonempty+=ln; hmatch+=lm; hits+=lh;
    if(!lo.empty()){
      lock_guard<mutex> g(om);
      for(auto& x:lo) if(outs.size()<100) outs.push_back(x);
    }
  }
  cout<<"SUMMARY overlap="<<t<<" kp="<<kp<<" kc="<<kc
      <<" difference_orbits="<<Es.size()
      <<" support_pair_orbits="<<supp
      <<" p_sign_tests="<<ptests
      <<" modular_nonempty_p="<<nonempty
      <<" H_matches="<<hmatch
      <<" compressed_hits="<<hits
      <<" range_begin="<<ibeg<<" range_end="<<iend
      <<" processed="<<(iend-ibeg)<<"\n";
  for(auto& z:outs){
    cout<<"HIT p=";
    for(int i=0;i<25;i++) cout<<(int)z.first[i]<<(i==24?'|':' ');
    cout<<"c=";
    for(int i=0;i<25;i++) cout<<(int)z.second[i]<<(i==24?'\n':' ');
  }
  return 0;
}
