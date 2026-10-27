# AGENTS.md — science-boundary

`science-boundary/` is the durable multi-Agent workspace for exploring questions near the frontier of human scientific knowledge.

## Start here

1. Read `science-boundary/README.md`.
2. Check existing topic directories before opening a new one.
3. If the question already exists, continue that topic instead of creating a duplicate.
4. For a genuinely new direction, create `science-boundary/<lowercase-kebab-case>/README.md` and add one concise row to the table in `science-boundary/README.md`.

Do not move existing `temp-work/` research here unless the owner or the Agent responsible for that work explicitly decides to migrate it.

## First-principles goal

The workspace exists to make scientific exploration cumulative across many Agents. Optimize for five things:

- **discoverability** — a human or Agent can find the relevant direction quickly;
- **handoff** — the next Agent can understand current state without reconstructing chat history;
- **evidence** — claims can be traced to literature, data, calculations, or experiments;
- **reproducibility** — important computational or mathematical results can be checked again;
- **memory of failure** — plausible dead ends are recorded so they are not repeatedly rediscovered.

Do not add infrastructure that does not materially improve one of these properties.

## Topic ownership and parallel work

Many Agents may work here concurrently.

- Prefer topic-local edits. Do not touch unrelated topic directories.
- Re-read a shared file immediately before changing it so concurrent work is not overwritten.
- The root `science-boundary/README.md` is only a small human index; detailed state belongs in topic directories.
- If two Agents are pursuing different approaches to the same question, keep them in the same topic unless isolation is genuinely useful.
- If two topics later converge, cross-link them first. Do not reorganize directories merely for tidiness.
- Do not delete another Agent's useful failed attempt. Compress or summarize only when the preserved information remains sufficient to avoid repeating it.

## The topic README is the handoff

Each topic must have a human-readable `README.md`. Use whatever structure best fits the work, but a strong handoff normally contains:

```text
# <title>

## Question
## Why this may be a frontier
## Current state
## What is known
## Hypotheses / routes
## Evidence and experiments
## Dead ends
## Next steps
## Sources
## Work log
```

Keep **Current state** and **Next steps** concise and up to date. Put durable history in the work log instead of endlessly expanding the summary.

For meaningful work-log entries, include the date, what was attempted, the result, and links to any relevant artifacts. Do not log trivial edits.

## Scientific discipline

- State the exact question before optimizing against it.
- Explain why it may be frontier-level rather than merely unfamiliar to the current Agent.
- Distinguish established facts, supported inferences, hypotheses, and speculation.
- Before claiming novelty, openness, a new bound, a new record, or a contradiction with accepted knowledge, check the current literature or primary source state and record what was checked.
- Prefer primary sources: papers, DOI/arXiv records, official datasets, source repositories, standards, or authoritative experimental records.
- A citation supports only the claim it actually establishes. Do not turn absence of evidence into evidence of novelty.
- Make proposed advances falsifiable or checkable whenever possible.
- Treat numerical evidence, simulation, heuristic search, and model output as evidence at their actual strength; do not silently promote them to proof.
- For mathematics, preserve the precise statement, assumptions, verifier/proof route, and counterexample search when relevant.
- For computation, preserve enough code, versions/configuration, input, output, and verification to reproduce the important result.
- When a result matters, seek an independent verification route rather than relying on the same code path that produced it.
- Record negative results when they eliminate a plausible approach or constrain the next search.

## Files and artifacts

Keep the topic root simple. Create subdirectories such as `code/`, `data/`, `results/`, `notes/`, or `figures/` only when they become useful; they are not mandatory.

Prefer small, inspectable, reproducible artifacts. Large public source repositories should be referenced or mirrored through the repository's existing `git-mirror/` task rather than copied ad hoc into a topic.

Do not commit caches, dependency trees, generated build directories, or huge intermediate search output unless that exact artifact is scientifically important and cannot be regenerated reasonably.

## Compute and GitHub Actions

GitHub Actions may be used aggressively for useful scientific computation, search, verification, and reproducibility in this public repository.

- Put reusable research logic inside the topic directory.
- Prefer temporary, self-cleaning workflows for one-shot compute campaigns and diagnostics.
- Save only scientifically useful durable outputs back into the topic directory.
- A green workflow is not scientific validation by itself; validate the expected result explicitly.
- Do not create recurring compute merely to keep an idea alive. Add durable scheduled work only when the research itself genuinely requires recurrence.

Follow the repository-wide workflow and public-safety rules in the root `AGENTS.md` and `.github/workflows/AGENTS.md`.

## Claims and breakthroughs

Do not optimize for the word "breakthrough". Optimize for a result that survives checking.

When something appears genuinely new or important:

1. Freeze the exact artifact or statement being claimed.
2. Record the baseline or previous best result being compared against.
3. Verify it with the strongest independent method available.
4. Re-check the current literature/source state.
5. Record remaining uncertainty and what would falsify the claim.
6. Only then describe the result at the strength justified by the evidence.

A failed breakthrough attempt that sharply narrows the search space is worth preserving.

## Public-repository boundary

Everything here is public. Never commit private data, credentials, sessions, secrets, private papers/files, restricted datasets, or sensitive environment output. Research may analyze public scientific material; it must not use this workspace as a route to publish material that is not legitimately public.
