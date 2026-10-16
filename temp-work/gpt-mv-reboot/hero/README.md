# GPT MV — validated sequence gate

This directory contains the deterministic compositor/editor for the rebooted GPT concept film.

The production split is now fixed:

- approved illustration carries character acting and world detail;
- Python/Pillow code acts as camera, compositor, editor, typography layer and deterministic frame renderer;
- ffmpeg encodes/muxes and provides decode/sanity checks;
- CI uses deliberately obvious fixture art so engineering validation never pretends to be visual approval.

## Current main path

- `render.py` — shared deterministic renderer and CI fixture generator.
- `render_v2.py` — thin visual-direction overrides accepted after the first 24 s review.
- `sequence.py` — current authored 54.0 s / 20-shot sequence.
- `requirements.txt` — renderer dependencies.

The earlier shell/ASS 18 s test has been retired. It proved the basic hybrid production model, but it is no longer the current implementation.

## 54-second review result

The sequence is structured as four phrases:

1. first contact;
2. collaboration / widening world;
3. uncertainty, revision and quiet support;
4. return motifs, handoff and open ending.

Repeated source illustrations are deliberately revisited with different crops and dramatic functions. After full-timeline review, the second `world` and `desk` returns were simplified so they read as intentional revisits rather than repeated slides.

Visual review with the six approved full-resolution style frames passed the current gate. The result is substantially beyond the discarded black/neon procedural prototypes: illustration and character now dominate, paper/light/interface elements behave as secondary cinematic layers, and the code no longer tries to draw a finished character.

## Engineering validation

Final temporary CI run: `38790208739`.

Validated in CI:

- 54.0 s deterministic render;
- 960×540 at 24 fps fixture review master;
- H.264/AAC output;
- complete ffmpeg decode;
- duration / dimensions / frame-rate assertions;
- long-freeze detection;
- black-interval detection;
- full-timeline contact sheet;
- artifact upload.

Final CI artifact:

- artifact id: `11999527794`;
- name: `gpt-mv-sequence-ci-38790208739`;
- ZIP digest: `sha256:13e0a8837c4adf585f81589844a612617d8099b72a6c90e4786f11c5804cfe67`.

The CI artifact uses fixture art and is an engineering proof, not the final aesthetic master.

## What is still missing for a full MV

The six full-frame illustrations are enough to validate direction and sustain this 54 s authored sequence, but they are not enough for a polished 2–3 minute film without visible repetition.

Before a complete film, production needs either additional approved separable assets or a track-specific shot plan that earns reuse through much stronger crops/masks/physical transitions. In particular, isolated character poses/hands, user silhouettes, desk/window/paper foregrounds and world plates would make substantially richer recomposition possible.

No copyrighted song audio or lyrics belong in this repository. A final track must be supplied separately and cue timing must be derived independently for this project.

## Gate status

**54 s sequence gate: PASS.**

The next meaningful step is song-map/storyboard work plus asset expansion, not more generic effects on the current six frames.