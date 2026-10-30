// Self-contained exact binary row-domain CSP for the final m=219 degree sequences.
//
// For a degree-11 anchor v, A=N(v) has 11 vertices and B is the 24-vertex
// antineighborhood. In the two remaining m=219 degree sequences every vertex
// has degree 11, 12, or 13. Therefore each A-row R_a of cross-neighbours in B
// has size |R_a| in [10-deg_A(a), 12-deg_A(a)].
//
// We intentionally relax the real gluing problem: no B-column degree bounds,
// no global degree-class counts, no total cross-edge constraint, and no mixed
// constraints involving 3 or more A vertices are imposed. We keep only:
//   (i) each row is triangle-free in B (no K4 of type 1A+3B),
//  (ii) for an A-edge ab, R_a intersect R_b is independent in B
//       (no K4 of type 2A+2B),
// (iii) for an A-nonedge ab, R_a union R_b hits every independent 4-set of B
//       (no independent 6-set of type 2A+4B).
// Every genuine Ramsey gluing is in this relaxed binary CSP. Hence UNSAT is a
// rigorous exclusion of the fixed A/B pair.
#include <bits/stdc++.h>
using namespace std;
static const vector<string> A25={
R"G6(J?~EE?vLpm?)G6",
R"G6(JEhIQOvLpm?)G6",
R"G6(J`G`C}]Va{?)G6",
R"G6(JcKp``NRq]?)G6",
R"G6(JgeQa_nJp]?)G6",
R"G6(JodIQOvLpm?)G6"
};
static const vector<string> A26={
R"G6(JiQC@{}N`{?)G6",
R"G6(JqPA@{}N`{?)G6"
};
static const vector<string> B116={
R"G6(W?jIhu?OG_cD`ZIfAnQTiyJIp[UhiJdsQU_seQobWKbkYLE)G6",
R"G6(WkGjGVA_SdqKItLBGiIoSFPNoRsxd@eoOEsZQXWoXQjkF~?)G6",
R"G6(WoCJ?j?@XDBBmGr@shMaHUgKrRiMU`[cuh{PbnIBb{CIvg_)G6",
R"G6(WoCJ?j?GgJBBmGsPx_dIbUgKrIh[UqMfIM{Wi^Obb{AIvc_)G6",
R"G6(WoCOZBSmLKXOLQUPDWAM@oE]_fgLlGgysWetAeuhBqigLtT)G6",
R"G6(Wt@IXqOg?W`SCYGTGQqHQjH]YZfDMmg|?jYwF\SAfYaKnSA)G6",
R"G6(Wt@IXqOg?W`SCYGTGQqHQjH]YZnDMeg|?jYqF\SAfYaKnSA)G6",
R"G6(Wt@IXqOg?W`SCYGTGQqHQjH]YZnDMeg|?jYqF\SQfY_KnS@)G6",
R"G6(Wv?IXZ?gGT?kAU@dE@a_FiZZIVUIfdLXgtZOTjg`teoJNcC)G6"
};
static const vector<string> B117={
R"G6(W?C[aKjkEGlBbALCJ?ecRiKldF\mdEZR@yf?_tpHDZagNTR)G6",
R"G6(W?GPiXOWM?r@IfcltO?zXqYypXaYdItWDfT@lWBCLpe{cuE)G6",
R"G6(W?GSQIFQ}CwKJjFVtOaiPe`PdIAol|HRxqcokUKBk_XvK@e)G6",
R"G6(W?KyCAOWGmDWEzHvPjA\GwRFQKmeeFFEAgyiTLTRR`iQuFO)G6",
R"G6(W?K}fA@OaAoSikeRKpaj_Ujad[RRhClq?WqrHKsog^Xd@ne)G6",
R"G6(W?K}fA@OaAoSikhRJPaj_XjaX[RRhClq?cqrEKsog^Xd@ne)G6",
R"G6(W?K~Ea@OaAoSikeRKpaj_Ujad[RRhClq?WqrHKsog^Xd@ne)G6",
R"G6(W?YSA?`Cgfc]kp[qxKEK`MIksTq]SS]INh[OtjGIxaqTeSo)G6",
R"G6(W?a`pSPQSWxglcwgCmiHtFKgyKMCJitY`PWJXWRK`Sl}Nw?)G6",
R"G6(W?dbCebSuIXOLWMcJ_dWOOi[PlhClsAmkW]UaIyXHrKgerL)G6",
R"G6(W?ddYx?_@@aEbMRLaZ`FXuFFckjbkDdqCyIaLPSUQbHwsRF)G6",
R"G6(W?hP?``cdDiNPoao[Y}fUpIRGUHtGXioWnFDFqqbXbAReQP)G6",
R"G6(W?hP?aQWTDiNaoPoOxyU]pEfGdhjPXsgyvb?]soCxaAleOT)G6",
R"G6(W?hPht?_@DaMH^EnPYaNOZ?i[@^OwehXFcrCuKqBApzQSfq)G6",
R"G6(W?hSA?bCrDQIPZafC}?v_MEwsf^M@mu@riu?t]OJWZAR`qP)G6",
R"G6(W?hTAeRWpkFGqPpaRcBW_CUwafSCtyBJyGlRPFgohixdFTe)G6",
R"G6(W?iQh?yJSIMRPifC{[ET_CTOsqWzPRqAd?Mn_q]^Q[WWN}?)G6",
R"G6(W@G[ACUIW^wHobdPLO\_e[HIiKYiS|NgPZqObCyqXJh]]K?)G6",
R"G6(W@G[ACUIW^wHobdPLO\_f[HYiKIiSlNgPZqObCrqXHl]]K?)G6",
R"G6(W@G]EEqYciHgiWT`MHC[_Ohm@dqAu{CvWSs{IJN?XuFeBw])G6",
R"G6(W@NE?|C`ADOQSxRVPZCjX\E@isLdsDXI?He\CUYx`LidB\T)G6",
R"G6(W@d_?M`SISeFEpaZk`cmBJ{@TqEKgs[tZbHE[_}MTLKVNE?)G6",
R"G6(W@eZBCxLcGpCOmO\IhtIIUfQiiEQSeKJ?Sh\GUXoollcSr])G6",
R"G6(W@hTQgxLcPGa_lO]L`KwKcrTbMeRKEKq?g[VDJIoaflcS^M)G6",
R"G6(W@hTQgxLcPGa_lO]L`KwLcvPbmEQKEKQCg[VDJIoaflcS^M)G6",
R"G6(WBAKZOjRUEShN?U_iBp`ikgJSOOXYgSt[`ZXOXZkDMiofTT)G6",
R"G6(WBAKZOlQtEWkM_KJIBqwas_qsG_WlWTQ{`VUOYm[DlJOfJR)G6",
R"G6(WBAKZPJJTEWiM_VGEFI`ks_isGOSzOX[l@X]GXj[DMkob\L)G6",
R"G6(WD]cH[bK?GkUaIRSyUEYOIMkPjdgKI@I}R[TPfoasPUwN}?)G6",
R"G6(WEhcPLR_@?gBeDTBdb[dqIrdDs|qoMkgPkkO`qohbLBhUKZ)G6",
R"G6(WEhcaKj_A?cBeDJBib[TqH\LRM\qoUhW`mSC`qopdbDhKsN)G6",
R"G6(WGQRgS[GQuStlOpKXk?asA[oRc{opS?M{ypRXE[vOkw[N{?)G6",
R"G6(WIE_s[__gT`LdBC{LA`JNeHpdhDX`RcSfBEf|kAAGzYzB]_)G6",
R"G6(WK?GWWUIOtcmp`qQSoiqSqdrDjDT`aj`eqWk[XFJcvAUKyO)G6",
R"G6(WKDL`\{_?PgFPBcD{?WwugmhdS[qpKMUFES_IX[WuZXMQQ])G6",
R"G6(WKQF__[@YvCKherGWa_eeArSGsxvhCoFlcLhlSBJYKg{N{?)G6",
R"G6(WLpwGTAG[DASPqQJPJZAeoLEQVheJc`Ssk[jJ{PS}Wo]No?)G6",
R"G6(WPTw?SoBuEWEWWgUbSkaJPdTGjgj{cctLrAXijBC^D_{v_C)G6",
R"G6(WQSMSUCi\IHd[EDgcQ`gRwhypdAkHjX__Xgt@qpoadVg^}?)G6",
R"G6(WQV@tGDA`BaSSBg@OaYPaIxsVZbbJaY|EMlOkekMhig\FT@)G6",
R"G6(WQV@tGIC_JCJgGSEhCcGdYYui[o]j`fV@TUpdjof`hoXfW`)G6",
R"G6(WQV@tGIC`A_lSDgGoaIPPYXyi[o]t`fMdTXodjoN`poXew`)G6",
R"G6(WQV@tG`A_JaSSB`@SAYPaBxsrZajJbQ|EilOdekN`igXfT@)G6",
R"G6(WQYO`CI@YQSC`bSFEEw]UdNPVMAt@tI`mjYIYlSUZiG]\S?)G6",
R"G6(WQ`@OgZHtaMObQR`?lGSkCT{ajsPZaG|a_uNSMRvG`kzCFL)G6",
R"G6(WQd_`?J@tCIGaFPJBIxLUbjPL]DR@ik`upuP[mWfMkOZ\G_)G6",
R"G6(WQd_`?J@tCIGaFPJBIxLUbjPL]LR@ik`upuP[mWfMk?Z\G@)G6",
R"G6(WQd`?SEC[PSBSaPPciwtURj`p\Qh`dU@}NTAkygeriO[vOC)G6",
R"G6(WQddQgDA`DaMg@SAPCYGekY\qUpMm_vVAL]PRjWepko[fK`)G6",
R"G6(WQddQgDA`DaMg@SAPCYGekY\qUpMm_vVEL]ORjWMpko[fK`)G6",
R"G6(WQhO`?DA_rCqgpSqPFiH{betLfclWRQwMppa[kc^NB?ZYQ@)G6",
R"G6(WQhO`?I@OqcsgpSqPFiH{bitLVckwRRWMppa[kcVMb?z[QC)G6",
R"G6(WQhP?OECPIbSaXgeIRqJYRgxpVShwBUW]NPQkygerao[uSC)G6",
R"G6(WQhSjOH@_dCIgBSBPEIHcbjdL\_un@NUaqTp[Ykepsg[el@)G6",
R"G6(WQhSjOH@_dCIgBSBPEIHcbjdL\_un@NUeqTo[YkNHjOZFQ`)G6",
R"G6(WQlwGO`ChDaMGqCpwHuCYRYYMUVApedHacfkUEvBNcER]GW)G6",
R"G6(WRMagM?EoxDhoqWk?LoPuDUL?B{ZbMKgXXcUghX^PDq]Nw?)G6",
R"G6(WROHL`GaNWicBWBcOYL`iUSkbhOFlHk[VyB?DXxMCXZw`}S)G6",
R"G6(WRQItGI@PBaUSA`GhAT?JItmqj_nUbajaM[qRZoUhhg\FX@)G6",
R"G6(WR`G`?J@tCIGaFPJBIxLUbjPL]DR@ik`upuH[mPfMk_Z\K?)G6",
R"G6(WR`G`?J@tCIGaFPJBIxLUbjPL]DR@ik`upuP[mWfMkOZ\G_)G6",
R"G6(WR`H?SEC[PSBSaPPciwtURj`p\Qh`dU@}NTAkygeriO[vOC)G6",
R"G6(WR`LQgDA`DaMg@SAPCYGeHtsZjdbRbclaL]QRjWUpkg[fL@)G6",
R"G6(WR`LQgDA`DaMg@SAPCYGekY\qUpMm_vVAL]PRjWepko[fK`)G6",
R"G6(WTPJcWH@OdCQPEgHqBAPHdZpUToul`NUah[pYiwfHhoZFW`)G6",
R"G6(W_hEgowIphQhgESwkecT_@CkFiXYIk`Ht[JJ[uBVQNOWN}?)G6",
R"G6(W_hU_owIphQHhETwkEcT_@CkBiXYIkhHtMKm[uBVQNOWN}?)G6",
R"G6(W`GOzWGDIDSa@rc[QS]OyMaQiwrplEhSTLoPphIHA^p{Jx_)G6",
R"G6(W`GkioCIABqECoA~MAuP{oPwt{I\ETLerck_saH_]t@vCQV)G6",
R"G6(WbQKXCIIHNJCbFRSMRCf@MPSSRhngIARic`XkN_]AK^WN}?)G6",
R"G6(WdPMG_rK@WohQsXLTDSd_BG[FWxyKgu{AGTZWyB^aNOWN}?)G6",
R"G6(WflELcL\IHE@IAAchCmWD_[MImHI]oNJKS\PCqyHCkxk^{?)G6",
R"G6(WhW[KJIaX}CQPPD_iBNA\cYaATxYaHoMXUeICLKwVBUk^{?)G6",
R"G6(WkG\QkCAGT_mGhCUQTZAnad`DhF@b]`czKK{{r?@wmIfdXQ)G6",
R"G6(Wkr?GSQGWidSErHrEVHbk`{@JoBG{[pYYqAi[OT[WjhHdVB)G6",
R"G6(WoCPXmGomhSRq@DD?twvSV?gwNAIeHXO\oPwwWSxBkvH]La)G6",
R"G6(WoCQ[QblTOWVwODH_zgusNAHUAPHUIYcSj`k[G}ABW}jBg{)G6",
R"G6(WoCQkQ`lTOWFwoDH_jgusNAHW\A\H`LUGj`m[G}AFWqhiPx)G6",
R"G6(WoCQkQ`lTOWFwoDHbZOIyNADMcqoy@LUDLQJIwVaFXRMC^`)G6",
R"G6(Wt?guAdcvWzSAKBX`ZQIiOyGl?ouAZ?udOel\_e?gu\cSuy)G6",
R"G6(Wt]_?KYOAPqM?~YgQt@ZD@sWaRUGiwazWmWKUPEmiSJ{P{E)G6",
R"G6(Wvx{?K_OG_@@ayguQReBvPxDImHLiPTrGVSeS\I?Z[EeJwE)G6",
R"G6(Ww?W}A_qlYUWtIAr@eOixCmosdieB`V@TLpO]?@x@]dgItj)G6",
R"G6(Ww?W}A_slUUgrIAkaXgYwDMckdiib`fAPJ_p]?@x@\dgIxj)G6",
R"G6(W{CWZCSE@A_tAcOWfKYiwlFbWfULUTSy?fr@Q~GE?jqsDUt)G6",
R"G6(W{CWZCSE@A_tAcOWij`NEuIqs]ULeDSyCxf_Q~AE?jisDVT)G6",
R"G6(W{CWZCSE@A_tAcOWij`NEuIqs]ULeDSyOxf_Q~?e?jisDVT)G6",
R"G6(W{CZ?[SE@D?kAUOdDYiNStFQwjDJsURi_uVCUjgE@FksBfL)G6",
R"G6(W{cAgwl_EYyQiK@K_yjKQLOCWTZAdZ@JWEmHE_}hStjINgU)G6",
R"G6(W}ZLci``ipBPIWBT`^IOlCDsTcOmSPCckc{NWgZAAPu_pwj)G6"
};
static vector<uint32_t> parseg6(const string&s){
 vector<int>x;for(char c:s)x.push_back((unsigned char)c-63);
 int n=x.at(0),k=0;vector<int>bits;
 for(size_t q=1;q<x.size();q++)for(int i=5;i>=0;i--)bits.push_back((x[q]>>i)&1);
 vector<uint32_t>a(n);
 for(int j=1;j<n;j++)for(int i=0;i<j;i++){if(k>=(int)bits.size())throw runtime_error("bad graph6");if(bits[k++])a[i]|=1u<<j,a[j]|=1u<<i;}
 return a;
}
static int edges(const vector<uint32_t>&g){long long s=0;for(auto x:g)s+=__builtin_popcount(x);return int(s/2);}
static bool hasK4(const vector<uint32_t>&g){int n=g.size();for(int a=0;a<n;a++)for(int b=a+1;b<n;b++)if((g[a]>>b)&1u)for(int c=b+1;c<n;c++)if(((g[a]>>c)&1u)&&((g[b]>>c)&1u))for(int d=c+1;d<n;d++)if(((g[a]>>d)&1u)&&((g[b]>>d)&1u)&&((g[c]>>d)&1u))return true;return false;}
static bool hasTriangle(const vector<uint32_t>&g){int n=g.size();for(int a=0;a<n;a++)for(int b=a+1;b<n;b++)if((g[a]>>b)&1u)for(int c=b+1;c<n;c++)if(((g[a]>>c)&1u)&&((g[b]>>c)&1u))return true;return false;}
static bool hasIndependentK(const vector<uint32_t>&g,int k){int n=g.size();function<bool(int,int,uint32_t)>dfs=[&](int start,int left,uint32_t chosen){if(!left)return true;if(n-start<left)return false;for(int v=start;v<=n-left;v++){if(g[v]&chosen)continue;if(dfs(v+1,left-1,chosen|(1u<<v)))return true;}return false;};return dfs(0,k,0);}
struct Solver{
 vector<uint32_t>A,B,I4;array<vector<uint32_t>,11>D;array<uint32_t,11>asg{};array<char,11>done{};long long nodes=0;int maxDepth=0;
 Solver(const string&as,const string&bs):A(parseg6(as)),B(parseg6(bs)){buildI4();buildDomains();}
 bool eA(int u,int v)const{return(A[u]>>v)&1u;}
 bool indep(uint32_t m)const{uint32_t q=m;while(q){int u=__builtin_ctz(q);q&=q-1;if(B[u]&q)return false;}return true;}
 bool triangleFree(uint32_t m)const{uint32_t q=m;while(q){int u=__builtin_ctz(q);q&=q-1;uint32_t z=B[u]&q;while(z){int v=__builtin_ctz(z);z&=z-1;if(B[v]&q)return false;}}return true;}
 bool hitsI4(uint32_t m)const{for(uint32_t z:I4)if(!(m&z))return false;return true;}
 void buildI4(){for(int i=0;i<24;i++)for(int j=i+1;j<24;j++)if(!((B[i]>>j)&1u))for(int k=j+1;k<24;k++)if(!((B[i]>>k)&1u)&&!((B[j]>>k)&1u))for(int l=k+1;l<24;l++)if(!((B[i]>>l)&1u)&&!((B[j]>>l)&1u)&&!((B[k]>>l)&1u))I4.push_back((1u<<i)|(1u<<j)|(1u<<k)|(1u<<l));}
 vector<uint32_t> rowMasks(int k)const{vector<uint32_t>o;if(k<0||k>24)return o;if(k==0){o.push_back(0);return o;}uint32_t x=(1u<<k)-1,L=1u<<24;while(x<L){if(triangleFree(x))o.push_back(x);uint32_t c=x&-x,r=x+c;if(!r||r>=L)break;x=(((r^x)>>2)/c)|r;}return o;}
 void buildDomains(){map<int,vector<uint32_t>>cache;for(int a=0;a<11;a++){int da=__builtin_popcount(A[a]),lo=10-da,hi=12-da;for(int k=lo;k<=hi;k++){if(!cache.count(k))cache[k]=rowMasks(k);D[a].insert(D[a].end(),cache[k].begin(),cache[k].end());}}}
 bool compatible(int a,uint32_t x,int b,uint32_t y)const{return eA(a,b)?indep(x&y):hitsI4(x|y);}
 vector<uint32_t> candidates(int a)const{vector<uint32_t>o;for(uint32_t m:D[a]){bool ok=true;for(int b=0;b<11;b++)if(done[b]&&!compatible(a,m,b,asg[b])){ok=false;break;}if(ok)o.push_back(m);}return o;}
 bool dfs(int dep){nodes++;maxDepth=max(maxDepth,dep);if(dep==11)return true;int best=-1;vector<uint32_t>bc;for(int a=0;a<11;a++)if(!done[a]){auto c=candidates(a);if(c.empty())return false;if(best<0||c.size()<bc.size()){best=a;bc.swap(c);}}for(uint32_t m:bc){done[best]=1;asg[best]=m;if(dfs(dep+1))return true;done[best]=0;}return false;}
 bool run(){return dfs(0);}
};
struct Row{string family;int ai,bi;bool sat;long long nodes;int depth;};
static vector<Row> runFamily(const string&name,const vector<string>&AA,const vector<string>&BB,int threads){vector<pair<int,int>>jobs;for(int a=0;a<(int)AA.size();a++)for(int b=0;b<(int)BB.size();b++)jobs.push_back({a,b});vector<Row>out(jobs.size());atomic<size_t>next{0};vector<thread>ts;for(int q=0;q<threads;q++)ts.emplace_back([&](){for(;;){size_t i=next.fetch_add(1);if(i>=jobs.size())break;auto[a,b]=jobs[i];Solver s(AA[a],BB[b]);bool sat=s.run();out[i]={name,a,b,sat,s.nodes,s.maxDepth};}});for(auto&t:ts)t.join();return out;}
static void validateCatalog(const vector<string>&V,int n,int e,bool A){for(auto&s:V){auto g=parseg6(s);if((int)g.size()!=n||edges(g)!=e)throw runtime_error("catalog size/edge mismatch");if(A){if(hasTriangle(g)||hasIndependentK(g,6))throw runtime_error("bad A Ramsey graph");}else{if(hasK4(g)||hasIndependentK(g,5))throw runtime_error("bad B Ramsey graph");}}}
int main(int argc,char**argv){int threads=thread::hardware_concurrency()?thread::hardware_concurrency():1;if(argc>1)threads=max(1,atoi(argv[1]));validateCatalog(A25,11,25,true);validateCatalog(A26,11,26,true);validateCatalog(B116,24,116,false);validateCatalog(B117,24,117,false);vector<Row>rows;auto add=[&](auto v){rows.insert(rows.end(),v.begin(),v.end());};add(runFamily("r3_A26_B116",A26,B116,threads));add(runFamily("r4_A25_B116",A25,B116,threads));add(runFamily("r4_A26_B117",A26,B117,threads));long long maxNodes=0;int maxDepth=0;bool anySat=false;for(auto&r:rows){maxNodes=max(maxNodes,r.nodes);maxDepth=max(maxDepth,r.depth);anySat|=r.sat;}cout<<"{\n  \"campaign\":\"m219-r34-binary-row-csp\",\n  \"threads\":"<<threads<<",\n  \"catalog_counts\":{\"A25\":6,\"A26\":2,\"B116\":9,\"B117\":90},\n  \"pair_counts\":{\"r3_A26_B116\":18,\"r4_A25_B116\":54,\"r4_A26_B117\":180},\n  \"total_pairs\":"<<rows.size()<<",\n  \"all_unsat\":"<<(anySat?"false":"true")<<",\n  \"max_nodes\":"<<maxNodes<<",\n  \"max_depth\":"<<maxDepth<<",\n  \"rows\":[\n";for(size_t i=0;i<rows.size();i++){auto&r=rows[i];cout<<"    {\"family\":\""<<r.family<<"\",\"a\":"<<r.ai<<",\"b\":"<<r.bi<<",\"status\":\""<<(r.sat?"SAT":"UNSAT")<<"\",\"nodes\":"<<r.nodes<<",\"max_depth\":"<<r.depth<<"}"<<(i+1<rows.size()?",":"")<<"\n";}cout<<"  ]\n}\n";return anySat?1:0;}
