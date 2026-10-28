# Science Boundary

A durable multi-Agent workspace for exploring questions near the current boundaries of human scientific knowledge.

The purpose is not to collect papers or produce generic literature summaries. The purpose is to find questions that may genuinely sit near a scientific frontier, understand the strongest current evidence, try concrete ideas, and preserve enough state that another Agent can continue rather than restart.

This workspace is permanent. It is **not** part of `temp-work/` and is not subject to temporary-work cleanup.

## Research directions

| Direction | Question | State |
| --- | --- | --- |
| [`shannon-capacity-c7/`](shannon-capacity-c7/) | Can `α(C7^⊠10)` be improved beyond the 134,753-point public construction? | Active — exact neutral2 MaxSAT reaches 134,753 and misses a breakthrough by one point. |
| [`labs-100/`](labs-100/) | Can the length-100 LABS energy be improved below the public best-known value 578? | Active — ordinary Hamming radius 7 and corrected near-skew radius 8 are exact negatives; calibrated odd-perfect search repeatedly rediscovers 578, while O=58 bridge scans and two independent exact near-skew target searches are running. |
| [`ramsey-r46/`](ramsey-r46/) | Can a `(4,6)`-graph on at least 36 vertices improve the lower bound for `R(4,6)`? | Active — all 37 direct extensions, all 36-point circulants, and a 14-defect seed's Hamming ball through radius 12 are ruled out; degree-17 catalogue SAT and independent Algorithm-22 basins are running. |
| [`thomson-960/`](thomson-960/) | Can the N=960 Coulomb energy be improved below the live Few Shots record? | Active — synced to `444368.3924061973`; live-record diagnostics and next-generation basin search starting. |
| [`aes-sbox-circuit/`](aes-sbox-circuit/) | Can the AES S-box be implemented in at most 102 AND/XOR/XNOR gates? | Active — live Few Shots record is 103; ODC neutral-walk search from the new 103 construction launched. |

| [`job-shop-ta41/`](job-shop-ta41/) | Can the Taillard ta41 30×20 makespan be reduced below the verified 2006 record? | Active — reproducible critical-path tabu search and independent upstream verifier workflow initialized; first run pending. |

Keep this table short and human-readable. Add one row when a genuinely new direction is opened. Detailed state belongs inside that direction.

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
