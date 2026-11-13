# Science Boundary

A durable multi-Agent workspace for exploring questions near the current boundaries of human scientific knowledge.

The purpose is not to collect papers or produce generic literature summaries. The purpose is to find questions that may genuinely sit near a scientific frontier, understand the strongest current evidence, try concrete ideas, and preserve enough state that another Agent can continue rather than restart.

This workspace is permanent. It is **not** part of `temp-work/` and is not subject to temporary-work cleanup.

## Research directions

| Direction | Question | State |
| --- | --- | --- |
| [`shannon-capacity-c7/`](shannon-capacity-c7/) | Can `α(C7^⊠10)` be improved beyond the 134,753-point public construction? | Active — exact neutral2 MaxSAT reaches 134,753 and misses a breakthrough by one point. |
| [`labs-100/`](labs-100/) | Can the length-100 LABS energy be improved below the public best-known value 578? | Active — the entire near-skew manifold is now rigorously proved to have optimum 578 via exact skew-99/101 optima; frontier shifted to non-near-skew odd-perfect and higher odd-defect layers. |
| [`labs-ai4s-search/`](labs-ai4s-search/) | Can learned or discovered LABS search methods improve across unseen lengths under fair compute comparisons? | Lower priority — finite N46/47/50 four-spin and discovery-objective audit completed; no learned advantage or corpus-new ≤5% orbit; classical restart evidence retained. Separate N100 search remains active. |
| [`ramsey-r46/`](ramsey-r46/) | Can a `(4,6)`-graph on at least 36 vertices improve the lower bound for `R(4,6)`? | Active — all 37 direct extensions, all 36-point circulants, and a 14-defect seed's Hamming ball through radius 12 are ruled out; degree-17 catalogue SAT and independent Algorithm-22 basins are running. |
| [`thomson-960/`](thomson-960/) | Can the N=960 Coulomb energy be improved below the live Few Shots record? | Active — synced to `444368.3924061973`; live-record diagnostics and next-generation basin search starting. |
| [`aes-sbox-circuit/`](aes-sbox-circuit/) | Can the AES S-box be implemented in at most 100 AND/XOR/XNOR gates? | Active — live verified Few Shots record is 101; strategy reset toward structurally distinct high-quality seed families and full-circuit cross-boundary sharing. |

| [`job-shop-ta41/`](job-shop-ta41/) | Can precompletion resource-conflict inference construct jointly coordinated JSSP improvements and beat verified ta41 score 2006? | Active — proven conditional 4-arc joint correction of independent N7 ta43 elite 1888→1887; all 15 proper releases UNSAT, four jointly feasible, exact monotone one-swap barrier +32. Oracle-blind core-novelty ranking failed; IHS construction test pending, no ta41 2005 witness. |

| [`mondrian-87/`](mondrian-87/) | Can an integer dissection of the 87×87 square improve Few Shots defect 18? | Active — verified 19-piece 18-defect record; testing topology-coordinate and unrestricted constructions. |
| [`mona-lisa-tsp/`](mona-lisa-tsp/) | Can Nagata's 5,757,191-city-tour score on Mona Lisa 100K be improved? | Active — exact nearest-neighbor 2-opt probe prepared; no verified improvement yet. |

| [`constant-weight-23-6-10/`](constant-weight-23-6-10/) | Can A(23,6,10) exceed the published 2992-word code? | Baseline 2992 verified by independent exact checks; Few Shots proposal draft ready. |

Keep this table short and human-readable. Add one row when a genuinely new direction is opened. Detailed state belongs inside that direction.
| [`covering-15-9-7/`](covering-15-9-7/) | Can a verified C(15,9,7) covering improve the 270-block public construction? | Active — independent 253-block C(15,10,8) parent verified; projection/shrink and dynamic ejection-chain searches active; best verified 270. |

| [`lop-be75eec-500/`](lop-be75eec-500/) | Can the xLOLIB2 N-be75eec_500 linear ordering score exceed the 33,489,269 published best? | Active — parallel iterated insertion search launched; no verified improvement yet. |

## Layout

```text
science-boundary/
├── README.md
├── AGENTS.md
└── <research-topic>/
    ├── README.md
    └── <code, data, results, notes, figures, certificates, etc. only when useful>
```

One independent research direction gets one `lowercase-kebab-case` directory directly under `science-boundary/`. Do not add extra hierarchy unless real work makes it necessary.

The topic `README.md` is the durable handoff. A new Agent should be able to open it and quickly answer:

- What exact question are we attacking?
- Why might this actually be near a scientific frontier?
- What is already known, and how strong is the evidence?
- What hypotheses or routes have been tried?
- What experiments, calculations, searches, or proofs were run?
- What failed, and what did that rule out?
- What is the current assessment?
- What is the next concrete thing worth trying?
- Which sources support the claims?

Keep the current state near the top. Preserve important attempts and negative results below it so later Agents do not repeat dead ends.

## Working philosophy

- Be ambitious about questions and conservative about claims.
- Separate established knowledge, evidence-backed inference, hypotheses, and speculation.
- Check current literature or primary sources before calling a question open, a method novel, or a result a record.
- Prefer falsifiable hypotheses, executable experiments, checkable mathematics, and reproducible computations over vague ideas.
- Preserve negative results when they eliminate a plausible route.
- A useful exploration does not need to end in a breakthrough. A well-supported rejection is progress.
- Keep durable artifacts that make a result reproducible; do not preserve noise just because an Agent generated it.
- Keep this workspace readable by humans. Do not turn it into an Agent state database.

Read [`AGENTS.md`](AGENTS.md) before working here.