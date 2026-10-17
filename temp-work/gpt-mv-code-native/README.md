# GPT MV — code-native rebuild

This workspace builds the film as authored code, not as a slideshow of finished illustrations.

The public `Nyankomintsu/world-execute-me-lyric-mv` repository is a production/process reference only. Its director prompt, review discipline, beat-driven timing and scene/engine separation define the **quality bar**. We do **not** copy or reuse its source, scene choreography, character art, compositions, timings, lyrics or assets.

## Current status

The previously validated 30 s cut is **TECH PROTOTYPE ONLY — visually rejected**.

It proved deterministic browser rendering, code-authored geometry, CI export and scene continuity. It did **not** meet the reference film's shot density, character performance, layered composition, musical editing or finish. Engineering green checks are not artistic approval.

Do not extend that cut as if it were a finished film.

## Production rules for the rebuild

- every shot has at least backdrop / subject / foreground-interface layers;
- cuts and major actions sit on the beat grid; secondary actions can fall between them;
- a shot must contain authored internal events, not one transform stretched for several seconds;
- camera, subject and foreground do not all move as one flat layer;
- fast motion uses stagger / ghost exposure / secondary motion, never opacity fade alone;
- text is an actor or a semantic element, never filler HUD;
- the GPT character must react, look, move and hand objects through the scene rather than behave as a static mascot;
- key transitions must transform existing geometry into the next shot instead of cross-fading two finished states;
- each stage is rendered and visually reviewed before the next stage starts;
- temporary CI workflows are removed after a gate passes.

## Opening v2 — 0–15 s — IN REVIEW

The old `boot.js + reply.js` opening has been replaced in the active timeline by `src/scenes/opening_v2.js`.

It contains four independently staged shots on one beat grid:

1. **threads** — four semantic strands and paper cards arrive from different depths and weave the conversation frame;
2. **context orbit** — context / tools / memory / style move on separate arcs around GPT, with parallax, ghost exposure and a context spine forming behind the character;
3. **composer performance** — the user types a false start, pauses, deletes it, types the real line, and sends; typing produces physical paper ticks and GPT reacts in the background;
4. **reply architecture** — the sent words break into moving paper strips, cross the character's reach, then register into three large spatial planes instead of becoming a subtitle card.

Review gate: 960×540 / 15 fps / 15 s. Contact sheet plus dense sheets around all three cut boundaries are required before this opening can pass.

## Retained technical prototype

The old 0–30 s implementation remains in the repository only as reusable technical material:

- `src/scenes/boot.js`
- `src/scenes/reply.js`
- `src/scenes/drafts.js`

Its final engineering validation was run `39002735464`, but that status must not be interpreted as artistic approval.

## Rendering architecture

- `src/engine/` — Canvas drawing primitives, semantic palette, deterministic timing;
- `src/components/chat.js` — code-authored client, composer, cursor and construction pieces;
- `src/components/gpt.js` — original multi-plate vector GPT character;
- `src/scenes/opening_v2.js` — current dense opening rebuild;
- `export/render.mjs` — static-mode Playwright capture through system Chrome + ffmpeg encode/contact-sheet generation.

No generated full-frame illustration, reference-project image, or reference-project source code is part of the rendered film.
