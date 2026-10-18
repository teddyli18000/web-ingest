# GPT MV — code-native rebuild

This workspace builds an original GPT/ChatGPT personification film as authored code, not as a slideshow of finished illustrations.

The public `Nyankomintsu/world-execute-me-lyric-mv` repository is a **production/process reference only**. Its directing discipline, staged review and deterministic render/QC define the quality bar. We do **not** copy or reuse its source, scene choreography, character art, compositions, timings, lyrics, audio or assets.

## Current status — 0–30 s visual language locked

The old technical prototype is rejected and retained only as history. The active timeline now has two visually reviewed sections:

- **0–15 s — opening v8 — PASS**
  - character hand extreme close-up → midshot;
  - tangible context objects, not generic HUD cards;
  - composer unfolds into a physical proof sheet;
  - send → nine paper strips → paper city/world is one continuous transformation;
  - character/building/foreground occlusion was explicitly reviewed.
- **15–30 s — revision v3 — PASS**
  - opening world is wiped by the same physical paper language into a revision desk;
  - a confident wrong route is visibly corrected by one vermilion user mark;
  - corrected proof duplicates into three perspective sheets, fans out, then registers back together;
  - the final sheet keeps the old wrong route as a faint graphite ghost;
  - the final character is revealed by the moving paper edge at full opacity rather than fading in.

Both sections were reviewed from rendered video, contact sheets and dense boundary frames. Engineering green checks alone do not count as visual approval.

## Character master

The active character is the approved silver-haired GPT artwork loaded through `src/components/gpt_art.js`.

Primary source:

- `reach_hq.b64.0 … reach_hq.b64.10`
- decoded WebP: **788×887**
- SHA-256: `e44ef2e3a6d839f81104634c9d78dfdc3466ddfae909ac632da5b2cf0e8394ed`
- runtime source name: `reach-hq`

The old 420×473 master exists only as an explicit fallback. Review CI uses `--art-source reach-hq`, so a silent fallback fails the gate.

## Active timeline

- `src/scenes/opening_v8.js` — 0–15 s
- `src/scenes/drafts_v3.js` — 15–30 s
- `src/main.js` — active routing
- `src/components/gpt_art.js` — verified character source/crops/registration
- `export/render.mjs` — deterministic Playwright frame capture + ffmpeg encode/contact-sheet generation

## Production rules

- every shot has backdrop / subject / foreground depth;
- camera, subject and foreground do not move as one flat layer;
- text must perform a semantic role, not act as filler HUD;
- the GPT character is never replaced by the rejected mascot path;
- major transitions inherit physical geometry from the previous shot instead of cross-fading finished states;
- opacity fade is not the main mechanism for important entrances/exits;
- a correction remains visible as residue instead of being magically erased;
- each section is rendered and visually reviewed before the next section starts;
- temporary CI workflows are removed immediately after their gate passes.

## Retained rejected material

Old scenes/assets may remain temporarily for comparison or reusable low-level techniques, including `boot.js`, `reply.js`, `drafts.js` and earlier opening/revision versions. They are **not** approved film content and must not be reintroduced into the active timeline.
