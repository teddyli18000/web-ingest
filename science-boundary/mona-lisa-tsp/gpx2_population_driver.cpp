// Small GPL-compatible driver for Renato Tinos's published GPX2 implementation.
// Place in a clone of https://github.com/rtinos/gpx2 as main.cpp and compile.
// Parents: raw 0-based city ids, exactly n integers separated by whitespace.
// Output: raw 1-based tour for subsequent *independent* official verification.
#include "defs.h"
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <string>
#include <vector>
using namespace std;

int main(int argc,char** argv){
    if(argc!=5){cerr<<"usage: GPX2 instance.tsp parentA.raw parentB.raw offspring.raw\n";return 2;}
    prob_name=argv[1];
    read_problem(prob_name);
    if(n_cities!=100000){cerr<<"dimension mismatch\n";return 3;}
    int *p1=aloc_vectori(n_cities);
    int *p2=aloc_vectori(n_cities);
    int *offspring=aloc_vectori(n_cities);
    for(int z=0;z<2;z++){
        ifstream in(argv[2+z]);
        if(!in){cerr<<"missing parent\n";return 4;}
        vector<char> seen(n_cities,0);
        int *p=z==0?p1:p2;
        for(int i=0;i<n_cities;i++){
            if(!(in>>p[i])||p[i]<0||p[i]>=n_cities||seen[p[i]]++){
                cerr<<"bad parent route "<<z<<" "<<i<<"\n";return 5;
            }
        }
    }
    double recombinationCost=gpx(p1,p2,offspring);
    vector<char> seen(n_cities,0);
    for(int i=0;i<n_cities;i++){
        if(offspring[i]<0||offspring[i]>=n_cities||seen[offspring[i]]++){
            cerr<<"invalid offspring "<<i<<"\n";return 6;
        }
    }
    ofstream out(argv[4]);
    for(int i=0;i<n_cities;i++)out<<offspring[i]+1<<"\n";
    cout<<"GPX2_CROSSOVER_RETURNED "<<recombinationCost<<"\n";
    return 0;
}
