#!/usr/bin/env python3
"""Patch pinned c7-five exchange_dfs.cpp with exact second-choice sharding.

The patch does not change the search predicate or candidate ordering.  It adds
optional [second_start, second_prefix) filtering when exactly one candidate has
already been selected, plus progress accounting for that second-level interval.
Use together with a singleton root interval [r,r+1) to partition one expensive
root subtree into disjoint exhaustive shards.
"""
from pathlib import Path
import argparse


def replace_once(text: str, old: str, new: str) -> str:
    if text.count(old) != 1:
        raise RuntimeError(f"patch anchor count {text.count(old)} != 1 for {old[:80]!r}")
    return text.replace(old, new, 1)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("source", type=Path)
    ap.add_argument("output", type=Path)
    args = ap.parse_args()
    s = args.source.read_text()

    s = replace_once(
        s,
        "    unsigned root_start = 0;\n    int last_completed_root = -1;\n",
        "    unsigned root_start = 0;\n    int last_completed_root = -1;\n"
        "    int second_prefix = -1;\n    unsigned second_start = 0;\n    int last_completed_second = -1;\n",
    )

    s = replace_once(
        s,
        "                if (chosen.empty() && root_prefix >= 0 && i >= unsigned(root_prefix)) return false;\n"
        "                ++started;\n",
        "                if (chosen.empty() && root_prefix >= 0 && i >= unsigned(root_prefix)) return false;\n"
        "                if (chosen.size() == 1) {\n"
        "                    if (i < second_start) continue;\n"
        "                    if (second_prefix >= 0 && i >= unsigned(second_prefix)) return false;\n"
        "                }\n"
        "                ++started;\n",
    )

    s = replace_once(
        s,
        "                        if (chosen.empty()) last_completed_root = int(i);\n"
        "                        continue;\n",
        "                        if (chosen.empty()) last_completed_root = int(i);\n"
        "                        if (chosen.size() == 1) last_completed_second = int(i);\n"
        "                        continue;\n",
    )

    s = replace_once(
        s,
        "                    chosen.pop_back();\n"
        "                    if (timed_out || output_limited) return false;\n"
        "                }\n"
        "                ++completed;\n"
        "                if (chosen.empty()) last_completed_root = int(i);\n",
        "                    chosen.pop_back();\n"
        "                    if (timed_out || output_limited) return false;\n"
        "                    if (chosen.size() == 1) last_completed_second = int(i);\n"
        "                }\n"
        "                ++completed;\n"
        "                if (chosen.empty()) last_completed_root = int(i);\n"
        "                if (chosen.size() == 1) last_completed_second = int(i);\n",
    )

    s = replace_once(
        s,
        "            else if (option == \"--anchor-bounds\" && a + 1 < argc) {\n",
        "            else if (option == \"--second-start\" && a + 1 < argc) {\n"
        "                int first = std::stoi(argv[++a]);\n"
        "                if (first < 0 || first > 20000) throw std::runtime_error(\"Invalid second start\");\n"
        "                s.second_start = unsigned(first);\n"
        "            }\n"
        "            else if (option == \"--second-prefix\" && a + 1 < argc) {\n"
        "                s.second_prefix = std::stoi(argv[++a]);\n"
        "                if (s.second_prefix < 0 || s.second_prefix > 20000)\n"
        "                    throw std::runtime_error(\"Invalid second prefix\");\n"
        "            }\n"
        "            else if (option == \"--anchor-bounds\" && a + 1 < argc) {\n",
    )

    s = replace_once(
        s,
        "        s.last_completed_root = int(s.root_start) - 1;\n"
        "        if (s.anchor_prefix > s.n) throw std::runtime_error(\"Anchor prefix exceeds dimensions\");\n",
        "        s.last_completed_root = int(s.root_start) - 1;\n"
        "        unsigned second_end = s.second_prefix >= 0 ? unsigned(s.second_prefix) : unsigned(s.n);\n"
        "        bool second_shard = s.second_start > 0 || s.second_prefix >= 0;\n"
        "        if (s.second_start > second_end || second_end > s.n)\n"
        "            throw std::runtime_error(\"Second range exceeds dimensions\");\n"
        "        if (second_shard && root_end != s.root_start + 1)\n"
        "            throw std::runtime_error(\"Second-level sharding requires a singleton root interval\");\n"
        "        s.last_completed_second = int(s.second_start) - 1;\n"
        "        if (s.anchor_prefix > s.n) throw std::runtime_error(\"Anchor prefix exceeds dimensions\");\n",
    )

    s = replace_once(
        s,
        "        std::cout << \",\\\"root_start\\\":\" << s.root_start << \",\\\"root_end\\\":\" << root_end\n"
        "                  << \",\\\"next_root\\\":\" << next_root;\n",
        "        std::cout << \",\\\"root_start\\\":\" << s.root_start << \",\\\"root_end\\\":\" << root_end\n"
        "                  << \",\\\"next_root\\\":\" << next_root;\n"
        "        unsigned next_second = !second_shard ? 0 : (!found && !s.timed_out && !s.output_limited\n"
        "            ? second_end : unsigned(s.last_completed_second + 1));\n"
        "        std::cout << \",\\\"second_start\\\":\" << s.second_start\n"
        "                  << \",\\\"second_end\\\":\" << second_end\n"
        "                  << \",\\\"next_second\\\":\" << next_second;\n",
    )

    args.output.write_text(s)
    print(f"patched {args.source} -> {args.output}")


if __name__ == "__main__":
    main()
