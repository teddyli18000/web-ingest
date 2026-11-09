# GPT MV — original code-native film

An original GPT/ChatGPT character short film built from deterministic Canvas scenes. [The Claude lyric MV](https://github.com/Nyankomintsu/world-execute-me-lyric-mv) is a benchmark for production discipline, not a code or asset source. No code, character, lyrics, timing or music from that project are reused.

## Current state — 2026-11-09

**60-second technical timeline exists; full creative acceptance has not been granted.** We are replacing early motion-demo imagery with actual character performance, physical paper staging and directed shots.

| Time | Active source | Content | Review |
| --- | --- | --- | --- |
| 0–15 s | `src/scenes/opening_v12.js` | 7 shots: question, GPT reveal, desk, pen, revision, architecture and handoff | [CI 42586033152](https://github.com/teddyli18000/web-ingest/actions/runs/42586033152), passed |
| 15–30 s | `src/scenes/drafts_v14.js` | 8 shots: wrong turn, damage, recognition, repair, alignment and exchange | [CI 42587317645](https://github.com/teddyli18000/web-ingest/actions/runs/42587317645), passed |
| 30–45 s | `src/scenes/construct_v6.js` | Construct a paper world and bridge from the shared proof | Existing technical prototype |
| 45–60 s | `src/scenes/ending_v3.js` | Return and shared finish | Existing technical prototype |

**Integrated first 30 seconds:** [run 42587589396](https://github.com/teddyli18000/web-ingest/actions/runs/42587589396), passed at 960×540, 15fps, H.264/AAC, 30 seconds. We inspected 10 actual 1080p frames across the 15s and 30s boundaries. Adjacent 14.95→15.02s and 29.95→30.03s frames are continuous; the cut is made by the authored paper wipes.

**Full 60-second review:** [run 42588006788](https://github.com/teddyli18000/web-ingest/actions/runs/42588006788), initiated to validate the newly assembled timeline. The last *previous* full-film CI was [42571760984](https://github.com/teddyli18000/web-ingest/actions/runs/42571760984) before the director rewrite. Do not report the current full film as validated until the new run finishes and the artifact is reviewed.

## Character art and renderer

- Existing approved character study: `assets/gpt/bust_v3.webp`, 550×640, SHA-256 `76164bf82a81c67b9efb795033e71972a6c8512d1fa73370026736028dd6b0eb`.
- `src/components/gpt_bust_plate.js` creates code-matted `gpt-bust-matted-v5`: removes navy-paper residue and feathers hard image edges. Separate [1080p character lab 42571081419](https://github.com/teddyli18000/web-ingest/actions/runs/42571081419) passed.
- `src/components/gpt_art.js` loads the retained HQ reach pose for hand shots. It must not serve as a full-frame background or floating rectangular character.
- `src/engine/draw.js` and scene files author paper architecture, material, lighting, typography, fold paths, ink and camera transitions directly in Canvas.
- `export/render.mjs` captures deterministic frames with Playwright and encodes H.264/AAC through ffmpeg. `export/shot_stills.mjs` samples actual authored absolute-time frames at 1080p.

## Artistic decisions and review history

- Rejected directions: black-neon faceless mascot, product demo UI, six static illustration pans, crude Path2D anime person, rectangular character crop, floating portrait medallion, and three independent paper cards.
- The current 0–30s is more spatial and varied but **still below the reference film's acting, beat-level choreography and scene density**. CI success is technical, not evidence of artistic parity.
- See [OPENING_V12.md](OPENING_V12.md) and [DRAFTS_V14.md](DRAFTS_V14.md) for the current shot maps, intentional transitions and rejected attempts. Earlier `opening_v*.js`, `drafts_v*.js` and reboot folders are historical experiments, not the active route.

## Next work

1. Inspect the current full 60s video and its critical 15/30/45s cuts. Record the artifact and hash after success.
2. Choose and design an original audio track, cue sheet and beat-by-beat shot timings; the renderer's current synthesized tones are a **technical sound fixture**, not a finished MV soundtrack.
3. Bring 30–60s to the same directed standard and deepen GPT performance. Keep original code-native staging, not more generic explanatory graphics.
4. Remove temporary `temp-gpt-mv-*.yml` review workflows after the validation gates. The scene source and handoff records remain in this workspace until the project is promoted or allowed to expire under repository cleanup policy.

All task files are isolated to this temporary workspace; GitHub Actions only supplies build and review compute.
