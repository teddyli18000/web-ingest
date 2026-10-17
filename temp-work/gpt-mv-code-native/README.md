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

Narrative:

1. **0–3 s — surface wakes.** A warm paper field is empty. One cobalt rule appears, unfolds into the ChatGPT client, and interface pieces settle into place.
2. **3–7 s — GPT resolves.** The character assembles from independent vector ink plates: coat, face, hair, eyes and register details.
3. **7–10 s — user arrives.** A gold cursor crosses the page and types a short message into the composer.
4. **10–15 s — reply becomes a world.** The same GPT character walks out of the client while header/sidebar/composer geometry itself becomes horizon, perspective rails and page-buildings.

### Review history

Gate 01 required three visual passes after the engineering path worked:

- **pass 1:** rejected visually — debug-like construction labels, message covered GPT's face, accidental double exposure in the client→world transition;
- **pass 2:** fixed composition and made sidebar/header/composer geometry morph into the world, but dense 11.25–13.35 s review exposed a washed-out gap where old/new states were still effectively crossfading;
- **pass 3:** passed — one continuous `Path2D` GPT remains visible through the transition, the client survives until its geometry has visibly transformed, and there is no blank transition gap.

Validated CI run: `39001763083`  
Artifact: `gpt-mv-code-native-39001763083` / ID `12088972944`  
Artifact digest: `sha256:e92f80ff06594a0924515fa067d9c30a9334c83ea100bde4c751bcf80a026cbc`

Technical gate: 640×360 / 12 fps / 15.000 s / H.264 + AAC; full decode, media assertions and black-interval check passed.

The temporary Gate 01 workflow is removed after this validation.

## Gate 02 — `revision room / handoff` — NEXT

Target: 15–30 s, still fully code-native.

The final paper skyline from Gate 01 becomes raw material rather than a background plate:

1. skyline pages detach and move toward camera;
2. they arrange around GPT as competing draft pages;
3. GPT works through the pages and selects one — no neural-network/AI-explainer graphics;
4. rejected pages fold away;
5. the selected page becomes a physical paper ribbon handed back toward the user's gold cursor.

Gate 02 must add authored camera movement and materially different staging while preserving the same palette/character identity.

## Current implementation

- `src/engine/` — Canvas drawing primitives, semantic palette, deterministic timing;
- `src/components/chat.js` — code-authored client, messages, composer, cursor and construction pieces;
- `src/components/gpt.js` — original multi-plate vector GPT character and poses;
- `src/scenes/boot.js` — line→client→character boot choreography;
- `src/scenes/reply.js` — first conversation and client→world structural morph;
- `export/render.mjs` — deterministic static-mode Playwright capture using system Chrome + ffmpeg encode/contact-sheet generation.

No generated illustration, reference-project image, or reference-project source code is part of the rendered film.
