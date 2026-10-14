# GPT MV reboot — render architecture

## Decision

Do not ask code to draw finished character art.

The renderer is a **camera, compositor, motion-graphics engine, and editor**. Finished character/world illustrations are authored as image assets; code makes them move, cuts them together, overlays interface/typography/paper elements, and exports deterministic frames.

This is the useful production lesson from studying the reference repo. We are not reusing its source, scene logic, art treatment, palette, story, or assets.

## Why this split

The approved GPT style frames depend on illustration quality that would collapse if recreated as procedural geometry. The previous prototype failed exactly here: the renderer became the art director and produced generic black-neon AI graphics.

Hybrid production keeps the strengths separate:

- **Illustration assets:** character acting, facial expression, detailed desk/world environments, painterly light.
- **Code:** camera motion, timing, transitions, UI, text, masks, paper/card motion, deterministic particles, scene ordering, export, regression checks.
- **CI:** repeatable preview/export once assets are present in the workspace.

## Pipeline

1. `assets/styleframes/` — approved full-frame illustrations and later isolated character poses.
2. `hero/` — short motion test. This must pass before any long film is built.
3. `src/` — later deterministic scene engine. Scenes are pure functions of time; no frame-to-frame hidden state.
4. ffmpeg — final encode/audio mux and decode validation.
5. QA — contact sheets at meaningful moments before full preview export.

## Rendering rules

- 1920×1080 working master; 30 fps for iteration, 60 fps only after motion language is approved.
- Camera movement stays small enough that illustration detail survives: typically 2–7% scale travel over a shot.
- Never animate the character by deforming her face/body. Use camera, crop, masks, foreground cards, light and match cuts.
- A still must not merely sit on screen: every shot needs at least two independent motions (camera + foreground/card/light), but motion must remain subordinate to acting.
- Transitions are motivated by objects already in the visual world: paper, window light, message cards, page turns, focus shifts. Generic glitch is prohibited unless the story specifically earns it.
- Embedded AI-generated lettering is treated as texture, not canonical copy. Important final copy is typeset by the compositor.
- No black-neon neural-network visual vocabulary, no glowing chest core, no occult halo, no graph-of-nodes filler.

## Hero gate

Before building the full film, make an 18–20 s sequence from the six approved style frames.

Pass conditions:

- it feels like a moving MV, not a slideshow;
- the GPT character remains appealing and recognisable after motion/crop;
- text/UI overlays do not fight the illustration;
- transitions preserve the warm blue/cream/gold visual identity;
- final frame feels brighter and more open than the opening;
- full ffmpeg decode succeeds.

If the hero gate fails, fix the visual system rather than extending duration.
