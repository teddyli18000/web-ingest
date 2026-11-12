"""Exhaustively test small coordinate-class moves around PR #62's 19 rectangles.

Run: python3 topology_probe.py
Only Python 3 standard library. Output is a local-topology negative result,
not an optimality proof.
"""
from collections import defaultdict
from itertools import combinations, product

R = [[8,0,66,6],[29,6,5,81],[17,6,12,33],[17,39,12,34],
     [0,73,29,14],[8,6,9,44],[0,50,17,23],[0,0,8,50],
     [34,6,40,10],[34,16,7,56],[34,72,26,15],[41,16,24,17],
     [41,33,10,39],[51,33,14,28],[51,61,36,11],[60,72,27,15],
     [65,16,9,45],[74,0,13,30],[74,30,13,31]]

def coordinate_groups(axis):
    edges = []
    for i, (x,y,w,h) in enumerate(R):
        low, high, a, b = (x,x+w,y,y+h) if axis == 0 else (y,y+h,x,x+w)
        edges.extend([(i,0,low,a,b),(i,1,high,a,b)])
    parent = list(range(len(edges)))
    def root(i):
        while parent[i] != i:
            i = parent[i]
        return i
    for i,e in enumerate(edges):
        for j,f in enumerate(edges[:i]):
            if e[2] == f[2] and max(e[3],f[3]) < min(e[4],f[4]):
                parent[root(i)] = root(j)
    groups = defaultdict(list)
    for i,e in enumerate(edges):
        groups[root(i)].append((i//2,i%2,e[2]))
    return [g for g in groups.values() if g[0][2] not in (0,87)]

GROUPS = [(axis,g) for axis in (0,1) for g in coordinate_groups(axis)]

def check(moves):
    rects = [r.copy() for r in R]
    for ind,delta in moves:
        axis,g = GROUPS[ind]
        for i,side,_ in g:
            if axis == 0:
                if side == 0:
                    rects[i][0] += delta
                    rects[i][2] -= delta
                else:
                    rects[i][2] += delta
            else:
                if side == 0:
                    rects[i][1] += delta
                    rects[i][3] -= delta
                else:
                    rects[i][3] += delta
    cells = bytearray(87*87)
    shapes = set()
    areas = []
    for x,y,w,h in rects:
        if w < 1 or h < 1 or min(x,y) < 0 or x+w > 87 or y+h > 87:
            return None
        shape = tuple(sorted((w,h)))
        if shape in shapes:
            return None
        shapes.add(shape)
        areas.append(w*h)
        for row in range(y,y+h):
            start = row*87+x
            if any(cells[start:start+w]):
                return None
            cells[start:start+w] = bytes([1])*w
    if not all(cells):
        return None
    return max(areas)-min(areas)

def run():
    counts = [0,0]
    best = 18
    for i in range(len(GROUPS)):
        for d in (-2,-1,1,2):
            score = check([(i,d)])
            counts[0] += 1
            if score is not None:
                counts[1] += 1
                best = min(best,score)
    for i,j in combinations(range(len(GROUPS)),2):
        for di,dj in product((-2,-1,1,2),repeat=2):
            score = check([(i,di),(j,dj)])
            counts[0] += 1
            if score is not None:
                counts[1] += 1
                best = min(best,score)
    for i,j,k in combinations(range(len(GROUPS)),3):
        for di,dj,dk in product((-1,1),repeat=3):
            score = check([(i,di),(j,dj),(k,dk)])
            counts[0] += 1
            if score is not None:
                counts[1] += 1
                best = min(best,score)
    print(dict(coordinate_classes=len(GROUPS),trials=counts[0],
               valid=counts[1],best=best))
if __name__ == "__main__":
    run()
