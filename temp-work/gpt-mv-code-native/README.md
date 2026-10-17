# GPT MV — code-native reboot

This workspace replaces the rejected still-image edit pipeline.

## Goal

Build the film as authored code, not as a slideshow of finished illustrations.

The public `Nyankomintsu/world-execute-me-lyric-mv` repository is a production/process reference only. We inspected its scene/engine split, deterministic time-driven rendering, staged review discipline, and the v4 director prompt. We do **not** copy or reuse its source, scene choreography, character art, compositions, timings, lyrics, or assets.

## Hard rules

- no generated full-frame illustration is used as a shot background;
- every visible environment, interface element, transition, typography treatment, light pool and camera move is produced by this renderer;
- the GPT character in this gate is also vector geometry authored in our own code (Canvas `Path2D`), not a raster still;
- every frame is a pure function of absolute time;
- first/key/last frames and a contact sheet are reviewed before expanding runtime;
- CI renders the same browser code that the preview uses;
- temporary validation workflows are removed after a gate passes.

## Gate 01 — `boot / first reply`

Target: 15 seconds.

Narrative:

1. **0–3 s — surface wakes.** A warm paper field is empty. One cobalt rule appears, unfolds into the ChatGPT client, and interface pieces settle into place.
2. **3–7 s — GPT resolves.** The character is assembled from independent vector ink plates behind the glass: coat, face, hair, eyes. Nothing is faded in as a finished picture.
3. **7–10 s — user arrives.** A gold cursor crosses the page and types a short message into the composer. The UI reacts physically.
4. **10–15 s — reply becomes a world.** GPT answers. The window opens into layered paper geometry and a moving horizon; the reply is integrated into the scene instead of being a caption pasted on top.

This gate deliberately proves the production method before any longer song map is attempted.

## Implemented for first render review

- Canvas drawing primitives and semantic palette;
- deterministic time/easing helpers;
- code-authored ChatGPT client geometry;
- code-authored multi-plate GPT character using `Path2D`;
- independent boot and reply/world scenes;
- Playwright frame exporter + ffmpeg encode/contact-sheet generation;
- temporary CI gate at 640×360 / 12 fps for fast visual review.

The first CI review is intentionally low-resolution. It exists to expose composition and choreography errors cheaply before the 1080p gate.

## Layout

```text
temp-work/gpt-mv-code-native/
├── README.md
├── package.json
├── index.html
├── src/
│   ├── main.js
│   ├── engine/
│   │   ├── draw.js
│   │   ├── palette.js
│   │   └── timing.js
│   ├── components/
│   │   ├── chat.js
│   │   └── gpt.js
│   └── scenes/
│       ├── boot.js
│       └── reply.js
└── export/
    └── render.mjs
```

## Review criterion

If the contact sheet can be mistaken for six finished illustrations with pan/zoom, this gate fails. The construction itself must be visible in the motion language: strokes become panels, panels become rooms, vector plates register into a character, and interface geometry turns into the final world.
