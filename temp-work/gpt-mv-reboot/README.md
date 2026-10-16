# GPT MV reboot

A clean restart of the GPT music-video experiment.

The earlier `gpt-signal-mv` prototypes are failed studies, not a base to extend. This workspace was rebuilt from directing, character design, visual language, storyboard discipline and staged review.

## Target

Create an original GPT/ChatGPT personification MV at the quality bar of an authored music video rather than an AI explainer or technology visualizer.

The user supplied `Nyankomintsu/world-execute-me-lyric-mv` as a production reference. Its public process documents are used only as a quality/process brief: strong directing constraints, staged render-and-review gates, deterministic export and final QC. We do not copy or reuse its source code, assets, character design, storyboard, scene compositions, timing or rendered media.

## Production model

The accepted split is hybrid:

- finished illustration supplies character acting and world detail;
- code is camera, compositor, editor, typography/motion layer and deterministic exporter;
- CI proves reproducibility and media integrity with obvious fixture art;
- artistic approval comes from separately reviewing renders made from the real approved style frames.

See `RENDER_ARCHITECTURE.md`, `ART_BIBLE.md`, `ASSET_MANIFEST.md` and `hero/README.md`.

## Completed gates

### Stage 1 — direction and visual system

Completed director brief, art bible, originality boundary, production/QC plan and six style-frame briefs.

### Stage 2 — visual direction / hero gate

Six original 1672×941 style frames established the accepted visual language: luminous anime-inspired illustration, blue/cream/gold light, a silver-haired GPT character, a dark-haired user, desk/chat/world imagery and tactile paper fragments.

The initial moving gate proved that code could behave as a camera/editor without collapsing back into procedural cyber-neon illustration.

### Stage 3 — authored 54-second sequence

`hero/sequence.py` drives a 54.0 s / 20-shot sequence using the approved six-image system. It adds distinct visual grammar for questions, revisions, breathing room, handoff, return motifs and the final world opening.

The real-art timeline was reviewed repeatedly at contact-sheet and key-frame level. Repeated `chat`, `world` and `desk` motifs were re-cropped and simplified until they read as narrative returns instead of accidental reuse. The final review also removed a duplicate chat bubble on the return visit and removed a redundant compositor text panel from the sunset shot.

Full 54 s CI run `38790208739` passed complete rendering, decode, timing/dimension assertions, freeze/black checks, full-timeline contact sheet and artifact upload. Artifact `11999527794`, digest `sha256:13e0a8837c4adf585f81589844a612617d8099b72a6c90e4786f11c5804cfe67`.

After the final two visual-cleanup changes, lightweight full-timeline CI run `38925793794` also passed. Its disposable workflow was removed immediately after validation.

A real-art 1280×720 / 24 fps / 54.000 s review master was then rendered and passed decode, freeze and black-interval checks. SHA-256: `fcabd5cc9c33516f25c35128662bb560a30ff3b627c9fb5b4fcbe2738d023bed`.

## Current conclusion

The reboot has crossed the important line from “style demo” into an authored sequence. The remaining limitation is no longer renderer quality; it is source-shot variety. Six full-frame illustrations cannot support a polished 2–3 minute film indefinitely without obvious reuse.

The next meaningful production stage is therefore:

1. establish a final song/cue map from user-supplied local audio, without committing copyrighted audio or lyrics;
2. storyboard the complete film around that cue map;
3. expand the approved separable asset pack only where the storyboard genuinely needs new poses/layers;
4. produce and review sections incrementally;
5. only then make the full preview and high-resolution export.

## Source media boundary

Do not commit copyrighted song audio or lyrics. A final track must be supplied separately; timing must be measured independently for this project and must not be copied from the reference MV.

## Status

**54-second sequence gate passed and temporary CI cleaned up.** The rejected cyber/neon prototypes remain separate failed studies and are not reused.