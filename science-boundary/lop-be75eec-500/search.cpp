#include <bits/stdc++.h>
using namespace std;
constexpr int N=500;
int D[N][N];
int W[N][N];
using Perm=array<int,N>;
long long score(const Perm &p){long long s=0;for(int i=0;i<N;i++)for(int j=i+1;j<N;j++)s+=W[p[i]][p[j]];return s;}
void move_at(Perm &p,int i,int j){int v=p[i];if(i<j)for(int k=i;k<j;k++)p[k]=p[k+1];else for(int k=i;k>j;k--)p[k]=p[k-1];p[j]=v;}
int descent(Perm &p,mt19937_64 &rng){
  int iterations=0;
  while(true){
    int best=0,bi=-1,bj=-1;
    int start=rng()%N;
    for(int t=0;t<N;t++){
      int i=(start+t)%N, v=p[i], gain=0;
      for(int j=i-1;j>=0;j--){int u=p[j];gain+=D[v][u]-D[u][v];if(gain>best){best=gain;bi=i;bj=j;}}
      gain=0;
      for(int j=i+1;j<N;j++){int u=p[j];gain+=D[u][v]-D[v][u];if(gain>best){best=gain;bi=i;bj=j;}}
    }
    if(best<=0)break;
    move_at(p,bi,bj);iterations++;
  }
  return iterations;
}
void perturb(Perm &p,mt19937_64 &rng,int type,int strength){
  if(type==0){
    for(int k=0;k<strength;k++){int i=rng()%N,j=rng()%N;move_at(p,i,j);}
  }else if(type==1){
    for(int k=0;k<strength;k++){int i=rng()%N,j=rng()%N;swap(p[i],p[j]);}
  }else if(type==2){
    for(int k=0;k<strength;k++){int i=rng()%N,j=rng()%N;if(i>j)swap(i,j);reverse(p.begin()+i,p.begin()+j+1);}
  }else{
    // partial ruin followed by high-value greedy reinsertion
    vector<int> removed; vector<int> q(p.begin(),p.end());
    for(int k=0;k<strength;k++){int pos=rng()%q.size();removed.push_back(q[pos]);q.erase(q.begin()+pos);}
    shuffle(removed.begin(),removed.end(),rng);
    for(int v:removed){
      int gain=0,best=INT_MIN,bpos=0;
      for(int j=0;j<=(int)q.size();j++){
        if(gain>best){best=gain;bpos=j;}
        if(j<(int)q.size())gain-=D[v][q[j]];
      }
      q.insert(q.begin()+bpos,v);
    }
    copy(q.begin(),q.end(),p.begin());
  }
}
mutex mx;
Perm global_best;
long long best_score;
int total_trials=0;
chrono::steady_clock::time_point deadline;
string output;
void persist(Perm p,long long value,int worker,int trial){
  lock_guard<mutex> lk(mx);
  if(value<=best_score)return;
  best_score=value;global_best=p;
  string tmp=output+".tmp."+to_string(worker);
  ofstream f(tmp);f<<"{\"order\":[";for(int i=0;i<N;i++){if(i)f<<",";f<<p[i];}f<<"]}";f.close();
  rename(tmp.c_str(),output.c_str());
  cerr<<"BEST "<<value<<" worker="<<worker<<" trial="<<trial<<endl;
}
void worker(int id,int seed,int seconds){
  mt19937_64 rng(seed+id*100003LL);
  Perm base; {lock_guard<mutex> lk(mx);base=global_best;}
  Perm current=base;
  long long current_score=score(current);
  int stagnant=0,trial=0;
  while(chrono::steady_clock::now()<deadline){
    ++trial;
    if(trial%29==0){lock_guard<mutex> lk(mx);base=global_best;}
    Perm cand=(trial%7==0)?base:current;
    int type=rng()%4;
    int strength=1+rng()%((stagnant<40)?6:(stagnant<150?18:60));
    perturb(cand,rng,type,strength);
    descent(cand,rng);
    long long s=score(cand);
    persist(cand,s,id,trial);
    if(s>current_score || (rng()%1000 < (stagnant<30?70:180))){
      current=cand;current_score=s;
    }
    if(s>=current_score)stagnant=0;else stagnant++;
    if(stagnant>300){current=base;current_score=score(current);stagnant=0;}
  }
  lock_guard<mutex> lk(mx);total_trials+=trial;
}
int main(int argc,char **argv){
  if(argc<5){cerr<<"usage solver matrix.txt baseline.txt best.json seconds [threads]"<<endl;return 2;}
  ifstream f(argv[1]);int n;f>>n;if(n!=N)return 3;
  long long M[N][N];
  for(int i=0;i<N;i++)for(int j=0;j<N;j++)f>>M[i][j];
  for(int i=0;i<N;i++)for(int j=0;j<N;j++){W[i][j]=int(M[i][j]);D[i][j]=int(M[i][j]-M[j][i]);}
  Perm p;ifstream g(argv[2]);for(int &x:p)g>>x;
  output=argv[3];best_score=score(p);global_best=p;
  cerr<<"INITIAL "<<best_score<<endl;
  int seconds=atoi(argv[4]),threads=argc>5?atoi(argv[5]):4;
  deadline=chrono::steady_clock::now()+chrono::seconds(seconds);
  vector<thread> pool;for(int i=0;i<threads;i++)pool.emplace_back(worker,i,1234567+i*233,seconds);
  for(auto &t:pool)t.join();
  cerr<<"FINAL "<<best_score<<" TRIALS "<<total_trials<<endl;
  cout<<best_score<<endl;
}