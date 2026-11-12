#!/usr/bin/env python3
"""Independently audit the clustered 36-point near-miss and its repair interface.

Graph6 file: results/clustered-36-14-defects-mincover5.g6.
The important constructive feature is a five-edge simultaneous red K4 cover,
as opposed to seven for the independently built 12-defect parents.
"""
import argparse
import collections
import itertools
import json
from pathlib import Path


def decode_graph6(line):
    n = ord(line[0]) - 63
    assert n == 36
    bits = (ord(c) - 63 >> k & 1 for c in line[1:]
            for k in (5, 4, 3, 2, 1, 0))
    g = [0] * n
    for j in range(1, n):
        for i in range(j):
            if next(bits):
                g[i] |= 1 << j
                g[j] |= 1 << i
    return g


def clique_list(graph, k):
    ans = []
    n = len(graph)
    def visit(candidates, vertices):
        if len(vertices) == k:
            ans.append(vertices)
            return
        while candidates.bit_count() >= k - len(vertices):
            bit = candidates & -candidates
            v = bit.bit_length() - 1
            candidates ^= bit
            visit(candidates & graph[v], vertices + (v,))
    visit((1 << n) - 1, ())
    return ans


def complement(graph):
    full = (1 << len(graph)) - 1
    return [full & ~row & ~(1 << i) for i, row in enumerate(graph)]


def score(graph):
    return len(clique_list(graph, 4)), len(clique_list(complement(graph), 6))


def red_edge_covers(graph):
    k4 = clique_list(graph, 4)
    assert len(k4) == 12
    masks = collections.Counter()
    for i, vertices in enumerate(k4):
        for edge in itertools.combinations(vertices, 2):
            masks[edge] |= 1 << i
    all_mask = (1 << len(k4)) - 1
    covers = []
    for subset in itertools.combinations(masks, 5):
        if (masks[subset[0]] | masks[subset[1]] | masks[subset[2]] |
                masks[subset[3]] | masks[subset[4]]) == all_mask:
            covers.append(subset)
    assert covers
    for size in range(1, 5):
        for subset in itertools.combinations(masks, size):
            covered = 0
            for edge in subset:
                covered |= masks[edge]
            assert covered != all_mask
    return covers, masks


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--g6", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    g = decode_graph6(args.g6.read_text().strip())
    k4, i6 = score(g)
    edges = sum(row.bit_count() for row in g) // 2
    assert (k4, i6, edges) == (12, 2, 264)
    covers, masks = red_edge_covers(g)
    best_after = 10**9
    best_cover = None
    for cover in covers:
        candidate = g[:]
        for u, v in cover:
            candidate[u] ^= 1 << v
            candidate[v] ^= 1 << u
        r4, b6 = score(candidate)
        assert r4 == 0
        if b6 < best_after:
            best_after, best_cover = b6, cover
    summary = {
        "n": 36, "edges": edges, "K4": k4, "I6": i6,
        "total_defects": k4 + i6,
        "minimum_red_edge_K4_cover": 5,
        "number_of_five_edge_covers": len(covers),
        "max_K4s_sharing_an_edge": max(mask.bit_count() for mask in masks.values()),
        "minimum_new_I6_after_five_deletions": best_after,
        "minimum_blue6_cover_edge_set": list(best_cover),
    }
    print(json.dumps(summary, sort_keys=True))
    assert len(covers) == 456
    assert best_after == 67
    if args.output:
        args.output.write_text(json.dumps(summary, indent=2) + "\n")


if __name__ == "__main__":
    main()
