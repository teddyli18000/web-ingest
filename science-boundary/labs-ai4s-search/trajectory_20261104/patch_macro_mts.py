#!/usr/bin/env python3
"""Source-pinned lMAts intervention: full solver, all costs within native timer.
Transiently patches public 2009-era C solver, leaves upstream GPL code unvendored.

Arms: 0 original, 1 single uniform 12-bit macro, 2 8x uniform+best E,
3 8x high-stress spectral lag-pairs + parity-corridor choice,
4 8x uniform lag-pairs + same parity-corridor choice,
5 8x high-stress lag-pairs + best ordinary E.
All are triggered from current GA global best only after prolonged GA stagnation.
"""
import pathlib,sys
def replace_once(s,a,b,label):
    if s.count(a)!=1:
        raise AssertionError(f'{label} anchor count={s.count(a)}')
    return s.replace(a,b,1)
def main(folder):
    folder=pathlib.Path(folder)
    p=folder/'GA.c'; s=p.read_text()
    s=replace_once(s,'#include "TabuSearch.h"', '#include "TabuSearch.h"\n#include "macro_labs.h"', 'include')
    s=replace_once(s,'    gaP->iter = 0;\n    initPopulation(gaP);',
       '    gaP->iter = 0;\n    initPopulation(gaP);\n    int last_record_iteration = 0;', 'record age')
    s=replace_once(s,
       '        mutateIndividual(gaP->child, gaP);\n        #endif',
       '        mutateIndividual(gaP->child, gaP);\n        #endif\n'
       '        if(macro_labs_arm() > 0 && gaP->iter-last_record_iteration>=gaP->chromosomeLgth*2\n'
       '           && (gaP->iter-last_record_iteration)%25==0) {\n'
       '            macro_labs_apply(gaP->child->chromosome,gaP->best->chromosome,\n'
       '              gaP->chromosomeLgth,gaP->rnd,gaP->iter);\n'
       '        }', 'inject macro in GA stagnation')
    s=replace_once(s,
       '        // replacement\n        if(!isAlreadyInPopulation(gaP, gaP->child)) {',
       '        // replacement\n        Fitness prior_global_best = gaP->best->fitness;\n'
       '        if(!isAlreadyInPopulation(gaP, gaP->child)) {', 'retain before replacement')
    s=replace_once(s,
       '        (gaP->iter)++;\n\n        if((GetElapsedTime',
       '        if(gaP->best->fitness < prior_global_best) last_record_iteration=gaP->iter;\n'
       '        (gaP->iter)++;\n\n        if((GetElapsedTime', 'global record reset')
    p.write_text(s)
    m=folder/'Makefile';s=m.read_text()
    s=replace_once(s,'OBJECTS=dynamicMem.o random.o GA.o timer.o LABS.o TabuSearch.o ',
        'OBJECTS=dynamicMem.o random.o GA.o timer.o LABS.o TabuSearch.o macro_labs.o ','objects')
    m.write_text(s)
    (folder/'macro_labs.h').write_text(HEADER)
    (folder/'macro_labs.c').write_text(CODE)
    print('PATCHED original lMAts with GA-stagnation macro arms, every cost in native timer')
HEADER=r'''#ifndef MACRO_LABS_H
#define MACRO_LABS_H
#include "types.h"
#include "random.h"
int macro_labs_arm(void);
void macro_labs_apply(Gene *child,const Gene *best,int n,Random rng,int generation);
#endif
'''
CODE=r'''#include "macro_labs.h"
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <limits.h>
#include <math.h>

int macro_labs_arm(void) {
 static int arm=-1;
 if(arm<0){const char *v=getenv("LABS_MACRO_ARM");arm=v?atoi(v):0;if(arm<0||arm>5){fprintf(stderr,"bad macro arm\n");exit(6);}}
 return arm;
}
static void corr(const Gene *s,int n,int *c,int *oe,int *ee){
 int odd=0,even=0;
 for(int k=1;k<n;k++){
  int z=0;for(int i=0;i<n-k;i++)z+=s[i]*s[i+k];
  c[k]=z;if(k&1)odd+=z*z;else even+=z*z;
 }
 *oe=odd;*ee=even;
}
static int random_mask(int n,int k,int *idx,unsigned char *used,Random rng){
 memset(used,0,n);
 int j=0;
 while(j<k){int x=RandomNextIntUntil(rng,n);if(used[x])continue;used[x]=1;idx[j++]=x;}
 return j;
}
static int pair_mask(int n,int k,int *idx,unsigned char *used,const int *c,
                     int weighted,Random rng){
 memset(used,0,n);int j=0,tries=0;
 while(j<k && tries++<n*20){
  int lag=1;
  if(weighted){
   double sum=0.;
   for(int x=1;x<n;x++)sum+=1.+(double)c[x]*c[x]/(n-x);
   double t=RandomNextDouble(rng)*sum;
   for(int x=1;x<n;x++){
    t-=1.+(double)c[x]*c[x]/(n-x);if(t<=0){lag=x;break;}
   }
  }else lag=1+RandomNextIntUntil(rng,n-1);
  int a=RandomNextIntUntil(rng,n-lag),b=a+lag;
  if(used[a]||used[b])continue;
  used[a]=used[b]=1;idx[j++]=a;idx[j++]=b;
 }
 if(j<k)for(int x=0;x<n&&j<k;x++)if(!used[x]){used[x]=1;idx[j++]=x;}
 return j;
}
void macro_labs_apply(Gene *child,const Gene *best,int n,Random rng,int generation){
 int arm=macro_labs_arm(),k=n>=12?12:(n/2)*2;
 if(arm==0||k<=0)return;
 Gene *trial=malloc(n*sizeof(*trial)),*picked=malloc(n*sizeof(*picked));
 int *idx=malloc(n*sizeof(*idx)),*c=malloc(n*sizeof(*c));
 unsigned char *used=malloc(n);
 if(!trial||!picked||!idx||!c||!used){perror("macro alloc");exit(7);}
 int eodd=0,eeven=0;
 corr(best,n,c,&eodd,&eeven);
 int bestval=INT_MAX, number=arm==1?1:8,original=eodd+eeven;
 double chosen=1.e99;
 for(int r=0;r<number;r++){
  memcpy(trial,best,n*sizeof(*trial));
  if(arm==1||arm==2)random_mask(n,k,idx,used,rng);
  else pair_mask(n,k,idx,used,c,(arm==3||arm==5),rng);
  for(int j=0;j<k;j++)trial[idx[j]]=-trial[idx[j]];
  int *scratch=malloc(n*sizeof(*scratch));if(!scratch){perror("macro");exit(7);}
  int odd=0,even=0;corr(trial,n,scratch,&odd,&even);free(scratch);
  int E=odd+even;
  // Fixed same geometry for both spectral and random-pair placebo.
  // If original odd energy is low, trade odd costs for even improvements.
  double cost;
  if(arm==3||arm==4){
   cost=(eodd<eeven)?(even+.25*odd):(odd+.25*even);
   if(E>original+2*n)cost+=2.*(E-original-2*n);
  }else cost=E;
  if(cost<chosen){chosen=cost;bestval=E;memcpy(picked,trial,n*sizeof(*picked));}
 }
 memcpy(child,picked,n*sizeof(*child));
 // Trigger metadata only; no published results inferred from scorer choice.
 fprintf(stdout,"\nMACRO arm=%d gen=%d sourceE=%d proposedE=%d k=%d proposals=%d\n",
         arm,generation,original,bestval,k,number);
 free(trial);free(picked);free(idx);free(c);free(used);
}
'''
if __name__=='__main__':
    if len(sys.argv)!=2:raise SystemExit('usage patch_macro_mts.py UPSTREAM_SRC')
    main(sys.argv[1])
