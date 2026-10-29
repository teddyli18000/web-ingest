// Independent small interface to upstream GPX2 (Tinos/Whitley/Ochoa).
// Build links upstream GPL-3.0 files at workflow run time; GPX2 itself is
// NOT copied into this research repository.  Input tour is TSPLIB TOUR_SECTION
// or Few Shots {"tour":[1,...]} JSON; all node identifiers are 1-based.
// Output plain 1-based city list, one per line, to be independently verified.
#include "defs.h"
#include <algorithm>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>
#include <cctype>
#include <cstring>
using namespace std;

vector<int> load_tour(const string &path, int n){
    ifstream f(path);
    if(!f)throw runtime_error("cannot open tour "+path);
    string all((istreambuf_iterator<char>(f)),istreambuf_iterator<char>());
    vector<int> t;t.reserve(n);
    if(all.find("\"tour\"")!=string::npos){
       size_t k=all.find("\"tour\"");
       k=all.find('[',k);
       if(k==string::npos)throw runtime_error("missing JSON tour bracket");
       while(k<all.size() && all[k]!=']'){
           if(isdigit((unsigned char)all[k])){
               unsigned long long v=0;
               while(k<all.size()&&isdigit((unsigned char)all[k])){
                   v=v*10+(all[k++]-'0');
                   if(v>1000000)throw runtime_error("city overflow");
               }
               t.push_back(int(v)-1);
           }else k++;
       }
    }else{
       size_t k=all.find("TOUR_SECTION");
       if(k==string::npos)throw runtime_error("unknown tour format");
       k=all.find('\n',k);
       while(k<all.size()){
          if(isdigit((unsigned char)all[k])){
            int v=0;
            while(k<all.size()&&isdigit((unsigned char)all[k])){
              v=v*10+(all[k++]-'0');
            }
            if(v>=1&&v<=n)t.push_back(v-1);
            else break;
          }else if(all[k]=='-')break;
          else if(all.compare(k,3,"EOF")==0)break;
          else k++;
       }
    }
    if((int)t.size()!=n)throw runtime_error("wrong tour length "+to_string(t.size())+"/"+to_string(n));
    vector<unsigned char> mark(n,0);
    for(int i:t){if(i<0||i>=n||mark[i])throw runtime_error("invalid repeated city");mark[i]=1;}
    return t;
}
long long exact_cost(const vector<int>& t){
    long long cost=0;
    for(int i=0;i<n_cities;i++)
       cost+=weight(t[i],t[(i+1)%n_cities]);
    return cost;
}
int main(int argc,char**argv){
    try{
        if(argc!=5)throw runtime_error("usage: GPX2-wrapper instance.tsp tourA tourB output.tour");
        read_problem(argv[1]);
        if(n_cities!=100000)throw runtime_error("wrong city count");
        vector<int>a=load_tour(argv[2],n_cities),b=load_tour(argv[3],n_cities),child(n_cities,-1);
        cout<<"stage=parents scoreA="<<exact_cost(a)<<" scoreB="<<exact_cost(b)<<endl;
        double approx=gpx(a.data(),b.data(),child.data());
        // Independently validate permutation and compute the exact integer
        // objective before saving (additional original verifier downstream).
        vector<unsigned char> mark(n_cities,0);
        for(int z:child){if(z<0||z>=n_cities||mark[z])throw runtime_error("GPX child invalid permutation");mark[z]=1;}
        auto childcost=exact_cost(child);
        cout<<"stage=gpx2 score="<<childcost<<" internal="<<approx<<endl;
        ofstream f(argv[4]);
        if(!f)throw runtime_error("cannot open output");
        for(int z:child)f<<(z+1)<<"\n";
        f.close();
        if(!f)throw runtime_error("failed writing offspring");
        return 0;
    }catch(const exception &e){
        cerr<<"FAIL "<<e.what()<<endl;return 3;
    }
}
