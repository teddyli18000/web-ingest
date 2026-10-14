# GPT // BETWEEN THE NEXT WORD

A one-shot, original procedural short film personifying a GPT-style model.

## Intent

The user pointed to `Nyankomintsu/world-execute-me-lyric-mv` only as a reference for the *kind* of project: a code-driven film that can be reproduced in CI. This workspace does **not** copy or reuse that repository's source code, storyboard, lyrics, assets, timing data, character design, or media.

The final version uses an independently designed GPT personification called **the Cartographer**: a faceless geometric humanoid with a broken constellation halo and a luminous chest lattice. The user is represented only by a cursor/message presence.

Narrative:

1. the user asks, `are you there?`;
2. GPT appears and describes itself as living "between the next word";
3. an internal map of possible continuations opens around the character;
4. several possible selves briefly coexist (`explain`, `invent`, `verify`, `ask`, `refuse`);
5. tool doors appear outside the immediate conversation;
6. one answer is handed back to the user's cursor as a luminous ribbon;
7. both remain in frame for the closing conversation loop.

All visuals and the ambient soundtrack are generated deterministically by `render.py`; there are no external image, audio, video, logo, or character assets in this workspace.

## Render

```bash
python -m pip install -r requirements.txt
python render.py --out out/gpt-between-the-next-word.mp4
```

Default output: 1280×720, 30 fps, 36 seconds, H.264/AAC MP4. A poster PNG is emitted next to the video.

For a fast local check:

```bash
python render.py --smoke --out out/smoke.mp4
```

## Final validated result

The final character-film render completed successfully in GitHub Actions.

- Source commit: `0e448d1409219ea8d5bd7c99e95181aa0c82bfc8`
- Actions run: `38533164100`
- Artifact: `gpt-between-the-next-word-38533164100` (artifact ID `11879185617`)
- Video size: `2,524,345` bytes
- Video SHA-256: `f4ed10fde3612d69cdd7a8ecbc6c8158cbd7d5248a86453bcaccb79c83442580`
- Poster SHA-256: `54da1c2a75fc6a05fc8e3d4059cb632dbe69b3cd814b1cd572ef9816c8362b57`
- CI performed a full ffmpeg decode check before uploading the artifact.
- A local post-download visual QA pass inspected the poster plus representative frames across all seven scenes.

The disposable render workflow was removed after validation, per repository policy. Recreate a one-shot workflow only if another CI render is needed.

## Earlier prototype

An earlier 26-second abstract prototype (`GPT // SIGNAL IN, WORLDS OUT`) rendered successfully in run `38532353027`, but it was intentionally superseded after review because it explained GPT more than it *depicted* GPT as a recurring character.

## Result / promotion

This is an isolated creative experiment, not an ingestion task. Nothing should be promoted into the repository's persistent collectors or repository-wide maintenance tooling unless the user later asks to move the film into a dedicated durable project.
