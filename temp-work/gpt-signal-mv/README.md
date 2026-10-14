# GPT // SIGNAL IN, WORLDS OUT

A one-shot, original procedural short film about a GPT-style model turning a prompt into an answer.

## Intent

The user pointed to `Nyankomintsu/world-execute-me-lyric-mv` only as a reference for the *kind* of project: a code-driven music/video-style render that can be reproduced in CI. This workspace does **not** copy or reuse that repository's source code, storyboard, lyrics, assets, timing data, or media.

This implementation was designed independently around a different visual metaphor and toolchain:

1. prompt / signal enters;
2. token-like fragments move toward a central abstract model core;
3. an attention graph lights up;
4. alternative continuations branch and one path wins;
5. tool nodes orbit the model;
6. a response crystallizes into text;
7. the conversation loop remains open.

All visuals and the short ambient soundtrack are generated deterministically by `render.py`; there are no external image, audio, font, or video assets in this workspace.

## Render

```bash
python -m pip install -r requirements.txt
python render.py --out out/gpt-signal-worlds-out.mp4
```

Default output: 1280×720, 30 fps, 26 seconds, H.264/AAC MP4. A poster PNG is emitted next to the video.

For a fast local check:

```bash
python render.py --smoke --out out/smoke.mp4
```

## CI

A disposable workflow at `.github/workflows/temp-gpt-signal-mv.yml` renders and validates the film, then uploads the MP4, poster, and SHA-256 manifest as a GitHub Actions artifact. Per repository policy, the workflow should be removed after a successful validated render; the workspace itself can remain until normal `temp-work` cleanup.

## Result / promotion

This is an isolated creative experiment, not an ingestion task. Nothing should be promoted into the repository's persistent collectors or maintenance tooling unless the user later asks to turn the renderer into a durable project elsewhere.
