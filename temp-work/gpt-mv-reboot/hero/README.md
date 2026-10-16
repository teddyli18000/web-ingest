# GPT MV — validated sequence gate

This directory contains the deterministic compositor/editor for the rebooted GPT concept film.

The production split is fixed:

- approved illustration carries character acting and world detail;
- Python/Pillow code acts as camera, compositor, editor, typography layer and deterministic frame renderer;
- ffmpeg encodes/muxes and provides decode/sanity checks;
- CI uses deliberately obvious fixture art so engineering validation never pretends to be visual approval.

## Current main path

- `render.py` — shared deterministic renderer and CI fixture generator.
- `render_v2.py` — thin visual-direction overrides accepted after the first 24 s review.
- `sequence.py` — current authored 54.0 s / 20-shot sequence.
- `requirements.txt` — renderer dependencies.

The earlier shell/ASS 18 s test has been retired and removed.

## 54-second review result

The sequence is structured as four phrases:

1. first contact;
2. collaboration / widening world;
3. uncertainty, revision and quiet support;
4. return motifs, handoff and open ending.

Repeated source illustrations are deliberately revisited with different crops and dramatic functions. Full-timeline review led to several targeted corrections instead of a blanket effects pass:

- the second `world` visit lost its labels and became light-only;
- the second `desk` visit became one `keep this` decision rather than another cloud of notes;
- the second chat/interface visit no longer duplicates the baked conversation with another compositor bubble;
- the sunset return no longer places a second text panel over lettering already present in the approved art.

Those changes make the later shots read as intentional returns rather than reused slides.

## Engineering validation

Full 54 s CI gate: run `38790208739`.

Validated there:

- 54.0 s deterministic render;
- 960×540 at 24 fps fixture review master;
- H.264/AAC output;
- complete ffmpeg decode;
- duration / dimensions / frame-rate assertions;
- long-freeze detection;
- black-interval detection;
- full-timeline contact sheet;
- artifact upload.

Artifact `11999527794`, ZIP digest `sha256:13e0a8837c4adf585f81589844a612617d8099b72a6c90e4786f11c5804cfe67`.

After the final two visual-cleanup changes, a disposable lightweight regression workflow ran the complete timeline again at 640×360 / 12 fps. Final check run `38925793794` passed decode, duration, dimensions/frame rate, freeze detection and black detection. That workflow was then removed.

## Real-art review master

The final code direction was also reviewed against the six actual approved full-resolution illustrations, not only fixtures.

A 1280×720 / 24 fps / 54.000 s real-art review master was rendered outside the repository so the binary art does not need to be committed here. It passed full ffmpeg decode, freeze detection and black-interval detection.

Review-master SHA-256: `fcabd5cc9c33516f25c35128662bb560a30ff3b627c9fb5b4fcbe2738d023bed`.

## What is still missing for a full MV

The six full-frame illustrations are enough to validate direction and sustain this 54 s authored sequence, but they are not enough for a polished 2–3 minute film without visible repetition.

Before a complete film, production needs either additional approved separable assets or a track-specific shot plan that earns reuse through much stronger crops/masks/physical transitions. Isolated character poses/hands, user silhouettes, desk/window/paper foregrounds and world plates would make substantially richer recomposition possible.

No copyrighted song audio or lyrics belong in this repository. A final track must be supplied separately and cue timing must be derived independently for this project.

## Gate status

**54 s sequence gate: PASS.**

The next meaningful step is song-map/storyboard work plus asset expansion, not more generic effects on the current six frames.