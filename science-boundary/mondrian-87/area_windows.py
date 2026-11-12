"""Compute arithmetic-feasible target area windows for D<=17, by shape-unique subset sum.

An area multiset can be chosen only when k distinct unordered dimensions within
[A,A+17] sum to 7569. This is a necessary feasibility filter for constructive
tiling searches, not a geometric solution.
"""
N=87
D=17
for k in range(8,29):
    windows=[]
    for a in range((N*N+k-1)//k-D,N*N//k+1):
        area=[w*h for w in range(1,N+1) for h in range(w,N+1)
              if a<=w*h<=a+D]
        dp=[0]*(k+1)
        dp[0]=1
        for x in area:
            for n in range(k,0,-1):
                dp[n]|=dp[n-1]<<x
        if dp[k]>>(N*N)&1:
            windows.append(a)
    print(k,windows)
