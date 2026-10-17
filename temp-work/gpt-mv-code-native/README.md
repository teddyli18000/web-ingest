# GPT MV — code-native reboot

This workspace replaces the rejected still-image edit pipeline.

## Goal

Build the film as authored code, not as a slideshow of finished illustrations.

The public `Nyankomintsu/world-execute-me-lyric-mv` repository is a production/process reference only. We inspected its scene/engine split, deterministic time-driven rendering, staged review discipline, and the v4 director prompt. We do **not** copy or reuse its source, scene choreography, character art, compositions, timings, lyrics, or assets.

## Hard rules

- no generated full-frame illustration is used as a shot background;
- every visible environment, interface element, transition, typography treatment, light pool and camera move is produced by this renderer;
- the GPT character is vector geometry authored in our own code (`Canvas Path2D`), not a raster still;
- every frame is a pure function of absolute time;
- first/key/last frames and dense transition sheets are reviewed before expanding runtime;
- CI renders the same browser code that the preview uses;
- temporary validation workflows are removed after a gate passes.

## Gate 01 — `boot / first reply` — PASSED

Runtime: 0–15 s.

1. **0–3 s — surface wakes.** One cobalt rule unfolds into a code-authored ChatGPT client.
2. **3–7 s — GPT resolves.** The character assembles from independent vector ink/color plates.
3. **7–10 s — user arrives.** A gold cursor crosses the page and types into the composer.
4. **10–15 s — reply becomes a world.** The same GPT walks out of the client while header/sidebar/composer geometry becomes horizon, perspective rails and page-buildings.

Gate 01 required three visual passes: debug-like construction copy and face-overlap were removed; the UI→world transition was rewritten from a crossfade into structural geometry morphing; finally one continuous `Path2D` GPT replaced the old disappear/re-enter transition.

Validated CI run: `39001763083`  
Artifact: `gpt-mv-code-native-39001763083` / ID `12088972944`  
Artifact digest: `sha256:e92f80ff06594a0924515fa067d9c30a9334c83ea100bde4c751bcf80a026cbc`

Technical gate: 640×360 / 12 fps / 15.000 s / H.264 + AAC; full decode, media assertions and black-interval check passed. Gate 01 workflow was removed after validation.

## Gate 02 — `revision room / handoff` — PASSED

Runtime: 15–30 s.

1. the seven skyline/page-buildings detach and move toward camera on individual trajectories;
2. the same objects settle around GPT as competing draft pages;
3. GPT selects one page while the other six fold/slide away;
4. coral appears only during revision: the old phrase is struck and rewritten as `keep what matters.`;
5. the selected page stretches continuously into a paper ribbon and is handed toward the user's gold cursor.

### Gate 02 review history

- first implemented cut exposed two likely double-draw handoffs (world→revision room and revision page→ribbon); both were rewritten to share exact endpoint/startpoint geometry before visual approval;
- dense 18 s / 22–25 s transition sheets confirmed page and GPT continuity;
- the first approved composition still let the final ribbon cross too much of GPT's face/body;
- final pass moved and shortened the ribbon so it leaves from the extended hand, keeps GPT readable, and keeps `keep what matters.` unobstructed.

Validated CI run: `39002362793`  
Artifact: `gpt-mv-code-native-gate02-39002362793` / ID `12089621537`  
Artifact digest: `sha256:3547cbcd8608b7acab9fdbb555150ff5ca4628fa1273c2661dcb22461da50d7c`

Technical gate: 640×360 / 12 fps / 15.000 s / H.264 + AAC; full decode, media assertions and black-interval check passed. Gate 02 workflow is removed after this validation.

## Next — integrated 0–30 s preview

Before authoring Gate 03, render Gates 01+02 as one higher-resolution preview and review the whole rhythm, especially the 14.6–15.4 s world→detached-page boundary. The integrated preview is a regression gate: fixing later sections must not quietly break the already-approved first 30 seconds.

## Current implementation

- `src/engine/` — Canvas drawing primitives, semantic palette, deterministic timing;
- `src/components/chat.js` — code-authored client, messages, composer, cursor and construction pieces;
- `src/components/gpt.js` — original multi-plate vector GPT character and poses;
- `src/scenes/boot.js` — line→client→character boot choreography;
- `src/scenes/reply.js` — first conversation and client→world structural morph;
- `src/scenes/drafts.js` — page detachment, revision room, selection/edit and user handoff;
- `export/render.mjs` — deterministic static-mode Playwright capture using system Chrome + ffmpeg encode/contact-sheet generation.

No generated illustration, reference-project image, or reference-project source code is part of the rendered film.
