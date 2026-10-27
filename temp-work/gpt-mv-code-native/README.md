# GPT MV — code-native rebuild

This workspace builds an original GPT/ChatGPT personification film as authored code, not as a slideshow of finished illustrations.

The public `Nyankomintsu/world-execute-me-lyric-mv` repository is a **production/process reference only**. Its directing discipline, staged review and deterministic render/QC define the quality bar. We do **not** copy or reuse its source, scene choreography, character art, compositions, timings, lyrics, audio or assets.

## Current status — 0–45 s locked

The old technical prototype is rejected and retained only as history. The active film now has three visually reviewed sections, accepted from real rendered video, contact sheets and dense transition frames rather than from code or green CI alone.

### 0–15 s — opening v8

- hand extreme close-up gives the character an immediate visual anchor;
- tangible context objects orbit/rearrange around GPT instead of generic HUD cards;
- the prompt becomes a physical proof sheet;
- send → nine paper strips → paper world is one continuous transformation;
- character, paper and foreground occlusion are explicitly staged rather than cross-faded.

### 15–30 s — revision v10

- 15 s world → revision desk is hidden by a physical proof-sheet wipe;
- the wrong route remains visible and receives one vermilion correction mark;
- 18.3–21.8 s uses one integrated thinking pose, not a framed portrait card or a second simultaneous GPT;
- corrected tracing proof is physically pulled from behind the wrong proof;
- the thinking pose stays solid and the 21.8 s pose/scene change happens behind a composed near-lens revision plate;
- 25.2–30 s turns the corrected proof into a handoff: its route leaves the page, reaches the user mark, then a proof-sheet wipe changes camera distance into a hand close-up from the **same** character master.

### 30–45 s — shared construction v5

- the 30 s handoff is physically swallowed by a rising paper floor; the blue correction line continues across the boundary instead of restarting;
- the map is no longer a floating board/card: it becomes the floor of a low-angle paper architecture space;
- arches, stairs, canopy, beacon and bridge have front/side/top faces, cast shadows and foreground occlusion;
- the rejected rectangular hand/photo overlay is gone from the final join;
- GPT and user are represented by cobalt/gold physical paper contributions inside the shared space;
- the final v5 join uses small perspective-folded pieces rather than long flat color bars, and the two sides complete the bridge gap together.

Full locked regression:

- GitHub Actions run: `40498732693`
- 0–45 s, 960×540, 15 fps
- full decode / duration / black-frame / freeze checks passed
- dense 30 s inspection confirmed handoff → paper-floor entry remains one physical action;
- dense 40.55 s inspection confirmed build → shared join is hidden by a near-lens paper wipe with no subject pop or opacity exit.

Engineering green checks alone do not count as visual approval; this state was accepted only after rendered-frame review.

## Character masters

Primary reach character: `src/components/gpt_art.js`

- `reach_hq.b64.0 … reach_hq.b64.10`
- decoded WebP: **788×887**
- SHA-256: `e44ef2e3a6d839f81104634c9d78dfdc3466ddfae909ac632da5b2cf0e8394ed`
- runtime source name: `reach-hq`

The old 420×473 master is an explicit fallback only. Review CI uses `--art-source reach-hq`, so silent fallback is rejected.

Secondary thinking pose: `src/components/gpt_poses.js`

- verified six-chunk WebP payload;
- used only as an integrated editorial cutout during the revision comparison;
- never presented as a framed screenshot/card in the active timeline.

## Active timeline

- `src/scenes/opening_v8.js` — 0–15 s
- `src/scenes/drafts_v10.js` — 15–30 s
- `src/scenes/construct_v5.js` — 30–45 s, with the immersive v3 space and refined v5 join
- `src/main.js` — active routing
- `src/components/gpt_art.js` — primary character source/crops/registration
- `src/components/gpt_poses.js` — secondary pose loader
- `export/render.mjs` — deterministic Playwright frame capture + ffmpeg encode/contact-sheet generation; review marks extend with the timeline instead of failing new sections.

## Production rules

- every shot has backdrop / subject / foreground depth;
- camera, subject and foreground do not move as one flat layer;
- text performs a semantic role instead of acting as filler HUD;
- the GPT character is never replaced by the rejected mascot path;
- major transitions inherit physical geometry from the previous shot instead of cross-fading finished states;
- opacity fade is not the main mechanism for important entrances/exits;
- correction remains visible as residue instead of being magically erased;
- a character source with an opaque background may not be pasted as a rectangular photo into a spatial scene;
- each section is rendered and visually reviewed before the next section starts;
- temporary CI workflows are removed immediately after their gate passes.

## Next gate — 45–60 s / quiet continuation

The last section must resolve the paper world without turning into a conventional “goodbye.” The completed bridge/world should fold back into one shared working page, keeping both cobalt and gold marks alive near an unfinished corner. The emotional read is continuation: the work can resume from here.

## Retained rejected material

Old scenes/assets may remain temporarily for comparison or reusable low-level techniques. Earlier opening/revision/construction versions and the original mascot are **not** approved film content and must not be reintroduced into the active timeline.
