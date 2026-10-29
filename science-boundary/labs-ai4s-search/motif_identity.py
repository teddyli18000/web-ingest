"""Independent exact check of LABS balanced-quartet Hamiltonian and 4-flip residual.
python3 motif_identity.py
"""
import itertools
import math
import random

def energy(s):
 n=len(s)
 return sum(sum(s[i]*s[i+k] for i in range(n-k))**2 for k in range(1,n))

def flipped(s,ids):
 v=s.copy()
 for i in ids:v[i]=-v[i]
 return v

def quartets_through(triple,n):
 p,q,r=sorted(triple)
 for x in (p+q-r,p+r-q,q+r-p):
  if 0<=x<n and x not in triple:
   z=tuple(sorted((*triple,x)))
   if z[0]+z[3]==z[1]+z[2]:yield z

def higher_residual(s,indices):
 affected=set()
 for triple in itertools.combinations(indices,3):
  affected.update(quartets_through(triple,len(s)))
 result=0
 S=set(indices)
 for quad in affected:
  count=sum(i in S for i in quad)
  if count>=3:result+=(-32 if count==3 else -64)*math.prod(s[i] for i in quad)
 return result

def direct_higher(s,indices):
 e=energy(s)
 single=sum(energy(flipped(s,[i]))-e for i in indices)
 pair=sum(energy(flipped(s,[i,j]))-energy(flipped(s,[i]))-
          energy(flipped(s,[j]))+e for i,j in itertools.combinations(indices,2))
 return energy(flipped(s,indices))-e-single-pair

def quartic_hamiltonian(s):
 n=len(s)
 q=set()
 for triple in itertools.combinations(range(n),3):
  q.update(quartets_through(triple,n))
 return n*(n-1)//2+2*sum(sum(s[i]*s[i+k] for i in range(n-k))
    for k in range(2,n,2))+4*sum(math.prod(s[i] for i in z) for z in q)

if __name__=="__main__":
 rng=random.Random(4928741)
 for n in (8,12,20,40,64,100):
  for trial in range(120):
   s=[rng.choice((-1,1)) for _ in range(n)]
   indices=sorted(rng.sample(range(n),4))
   assert higher_residual(s,indices)==direct_higher(s,indices)
   if trial<5:assert quartic_hamiltonian(s)==energy(s)
  print("PASS",n,"120 residuals and 5 full Hamiltonians")
 print("Verified: 720 exact residuals and 30 exact Hamiltonians.")
