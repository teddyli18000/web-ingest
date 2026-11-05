#!/usr/bin/env python3
"""Patch pinned public unrestricted lMAts source with native event traces.

Runs on one thread per OS process; parallel searches use isolated trace files.
Upstream GPL source remains in runner temp directory and is never vendored.
"""
from pathlib import Path
import argparse

HEADER = r'''#ifndef LABS_TRACE_LAB_H
#define LABS_TRACE_LAB_H
#include "types.h"
void trace_lab_context(int generation);
void trace_lab_episode(void);
int trace_lab_stride(void);
void trace_lab_event(const char *event,int step,int e,int best_e,
                     const Gene *current,const Gene *best,const int *expiry,int n);
#endif
'''
TRACE = r'''/* Instrumented GPL lMAts during transient build; not a solver replacement. */
#include "trace_lab.h"
#include <stdlib.h>
#include <stdio.h>
#include <time.h>
#include <stdint.h>
static FILE *lab_trace=NULL;
static int lab_initialized=0,lab_gen=0,lab_episode=0,lab_stride=32;
static uint64_t lab_events=0;
static struct timespec lab_t0;
static void trace_lab_close(void) {if(lab_trace) {fflush(lab_trace);fclose(lab_trace);lab_trace=NULL;}}
static void trace_lab_init(void) {
 if(lab_initialized)return;
 lab_initialized=1;
 const char *p=getenv("LABS_TRACE_FILE"),*str=getenv("LABS_TRACE_STRIDE");
 if(str){int z=atoi(str);if(z>=1)lab_stride=z;}
 if(!p||!*p)return;
 lab_trace=fopen(p,"w");if(!lab_trace){perror("LABS_TRACE_FILE");exit(4);}
 setvbuf(lab_trace,NULL,_IOFBF,1<<20);
 clock_gettime(CLOCK_MONOTONIC,&lab_t0);
 fprintf(lab_trace,"event\tgen\tepisode\tstep\tn\tenergy\tbest_energy\twall_s\tseq\tbest_seq\ttabu_remaining\n");
 atexit(trace_lab_close);
}
void trace_lab_context(int generation){trace_lab_init();lab_gen=generation;}
void trace_lab_episode(void){trace_lab_init();lab_episode++;}
int trace_lab_stride(void){trace_lab_init();return lab_stride;}
void trace_lab_event(const char *tag,int step,int e,int best_e,const Gene *cur,
                     const Gene *best,const int *expiry,int n){
 trace_lab_init();if(!lab_trace)return;
 struct timespec now;clock_gettime(CLOCK_MONOTONIC,&now);
 double t=(now.tv_sec-lab_t0.tv_sec)+(now.tv_nsec-lab_t0.tv_nsec)*1.e-9;
 fprintf(lab_trace,"%s\t%d\t%d\t%d\t%d\t%d\t%d\t%.6f\t",tag,lab_gen,lab_episode,step,n,e,best_e,t);
 for(int i=0;i<n;i++)fputc(cur[i]>0?'1':'0',lab_trace);
 fputc('\t',lab_trace);
 for(int i=0;i<n;i++)fputc(best[i]>0?'1':'0',lab_trace);
 fputc('\t',lab_trace);
 if(expiry&&step>=0){for(int i=0;i<n;i++){
   int remaining=expiry[i]-step;if(remaining<0)remaining=0;
   if(i)fputc(',',lab_trace);fprintf(lab_trace,"%d",remaining);
 }} else fputc('-',lab_trace);
 fputc('\n',lab_trace);
 if(++lab_events%8192==0)fflush(lab_trace);
}
'''
def replace_once(text,old,new,name):
    if text.count(old)!=1: raise RuntimeError(f'{name}: expected one anchor, got {text.count(old)}: {old[:90]}')
    return text.replace(old,new,1)

def patch(root:Path):
    ga=root/'GA.c';ts=root/'TabuSearch.c';mk=root/'Makefile'
    a=ga.read_text();b=ts.read_text();m=mk.read_text()
    a=replace_once(a,'#include "TabuSearch.h"','#include "TabuSearch.h"\n#include "trace_lab.h"','GA includes')
    a=replace_once(a,'    if(_hasBetterFitnessThan_(ind, gaP->best)) {\n\n        copyIndividualFromTo(ind, gaP->best, gaP);',
      '    if(_hasBetterFitnessThan_(ind, gaP->best)) {\n\n        copyIndividualFromTo(ind, gaP->best, gaP);\n        trace_lab_event("GA_RECORD",-1,gaP->best->fitness,gaP->best->fitness,gaP->best->chromosome,gaP->best->chromosome,NULL,gaP->chromosomeLgth);','GA record')
    a=replace_once(a,'void crossover(IndividualP parent1P, IndividualP parent2P, IndividualP childP, GAP gaP) {',
       'void crossover(IndividualP parent1P, IndividualP parent2P, IndividualP childP, GAP gaP) {\n'
       '    trace_lab_event("PARENT_1",-1,parent1P->fitness,parent1P->fitness,parent1P->chromosome,parent1P->chromosome,NULL,gaP->chromosomeLgth);\n'
       '    trace_lab_event("PARENT_2",-1,parent2P->fitness,parent2P->fitness,parent2P->chromosome,parent2P->chromosome,NULL,gaP->chromosomeLgth);','GA parent capture')
    a=replace_once(a,'      while(!(gaP->stop)) {','      while(!(gaP->stop)) {\n        trace_lab_context(gaP->iter);','GA generation context')
    a=replace_once(a,'        gaP->child->fitness = TabuSearch(gaP->child->chromosome, gaP->chromosomeLgth, gaP->rnd, gaP->timerP,&gaP->NFEs);',
       '        gaP->child->fitness = TabuSearch(gaP->child->chromosome, gaP->chromosomeLgth, gaP->rnd, gaP->timerP,&gaP->NFEs);\n'
       '        trace_lab_event("GA_CHILD_POST",-1,gaP->child->fitness,gaP->child->fitness,gaP->child->chromosome,gaP->child->chromosome,NULL,gaP->chromosomeLgth);','GA child post')
    b=replace_once(b,'#include "TabuSearch.h"','#include "TabuSearch.h"\n#include "trace_lab.h"','TS includes')
    b=replace_once(b,'    Fitness bestFitness = initialFitness;','    Fitness bestFitness = initialFitness;\n    trace_lab_episode();\n    trace_lab_event("TS_START",0,currentFitness,bestFitness,currentSeq,seq,tabuList,N);','TS begin')
    b=replace_once(b,'                bestFitness = bestMoveFitness;','                bestFitness = bestMoveFitness;\n                trace_lab_event("TS_BEST",iter,currentFitness,bestFitness,currentSeq,seq,tabuList,N);','TS improvement')
    b=replace_once(b,'        }\n    }\n\n    return bestFitness;',
       '        }\n        if(iter%trace_lab_stride()==0)\n            trace_lab_event("TS_STEP",iter,currentFitness,bestFitness,currentSeq,seq,tabuList,N);\n    }\n    trace_lab_event("TS_END",maxIter,currentFitness,bestFitness,currentSeq,seq,tabuList,N);\n\n    return bestFitness;','TS end')
    m=replace_once(m,'OBJECTS=dynamicMem.o random.o GA.o timer.o LABS.o TabuSearch.o ',
        'OBJECTS=dynamicMem.o random.o GA.o timer.o LABS.o TabuSearch.o trace_lab.o ','Makefile objects')
    ga.write_text(a);ts.write_text(b);mk.write_text(m)
    (root/'trace_lab.h').write_text(HEADER)
    (root/'trace_lab.c').write_text(TRACE)
    print(f'Patched original GA.c/TabuSearch.c with native trace at {root}')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('src',type=Path)
    a=p.parse_args();patch(a.src)
