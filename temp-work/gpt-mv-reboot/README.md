# GPT MV reboot

A clean restart of the GPT music-video experiment.

The earlier `gpt-signal-mv` prototypes are treated as failed studies, not a base to extend. This workspace starts again from directing, character design, visual language, storyboard discipline, and staged review.

## Target

Create an original GPT/ChatGPT personification MV at the quality bar of a real authored music video rather than an AI explainer or technology visualizer.

The user supplied `Nyankomintsu/world-execute-me-lyric-mv` as a production reference. Its public prompts and process documents are treated as a **quality/process brief**: explicit directing rules, staged section work, render-and-review gates, deterministic rendering, and final QC. We do not copy or reuse its source code, assets, character design, storyboard, scene compositions, rendered media, or implementation.

## Production model

The reference repo confirmed the correct division of labour: high-quality character art is supplied as image assets while code acts as camera, compositor, editor and deterministic exporter. The reboot now follows that hybrid model rather than trying to procedurally draw finished character art.

See `RENDER_ARCHITECTURE.md` and `ASSET_MANIFEST.md`.

## Completed gates

### Stage 1 — direction and visual system

- `DIRECTOR_BRIEF.md` — story, visual modes, shot rules, quality bar.
- `ART_BIBLE.md` — GPT character, palette, typography, motif, environments.
- `PRODUCTION_PLAN.md` — gated workflow from style frames to final export.
- `ORIGINALITY.md` — explicit boundary between reference methodology and our original work.

### Stage 2 — style frames and hero motion test

Six original 1672×941 style frames established the approved visual direction: luminous anime-inspired illustration, blue/cream/gold light, a silver-haired GPT character, a dark-haired user, desk/chat/world imagery, and paper-fragment motifs.

`hero/render.sh` turns them into a deterministic 18 s 1080p motion test using restrained camera movement, sparse compositor-set text and short photographic crossfades. The locally rendered gate passed full ffmpeg decode.

See `hero/README.md`.

## Current stage

**Stage 3 — build an animation-ready original character/environment asset pack, then a 30–45 s recomposed sequence.**

Do not extend to a full film using only the six full-frame illustrations. That would become a slideshow. Stage 3 needs isolated GPT poses, hands, user silhouettes, desk/window/paper/chat elements and world backgrounds so the compositor can create new shots and parallax rather than simply crop stills.

## Source media boundary

Do not commit copyrighted song audio or lyrics. If the final project is cut to a copyrighted track, the renderer must consume user-supplied local audio/lyrics that remain ignored by Git, and timing must be measured independently for this project rather than copied from another MV.

## Status

Reboot direction accepted; hero motion gate completed; character-pack production is next. The rejected cyber/neon prototypes remain separate failed studies and are not reused.
