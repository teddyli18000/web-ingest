# Hero motion gate

This is the first moving test of the rebooted GPT film.

## What this test is for

It is deliberately short. The goal is to prove the production split before committing to a full MV:

- finished illustration carries character acting and world detail;
- code acts as camera/editor/compositor;
- motion does not collapse into a slideshow or generic AI visualizer;
- GPT still reads as warm, intelligent and present after crop/movement;
- the visual identity survives transitions.

## Current cut

- 18.0 s
- 1920×1080
- 30 fps iteration master
- six approved original style frames
- subtle per-shot pan/zoom plus short photographic crossfades
- sparse compositor-set copy instead of covering every frame in captions
- temporary original tonal bed; music is not locked

Local validated motion-test output:

- `gpt_hero_sequence_v3.mp4`
- sha256 `44dde149299356655bf352a8f97a8d4d93db04e8b8bbda71d34f6598f0dcf10f`
- full ffmpeg decode: pass

## Review result

The reboot direction passes the **visual-direction gate**. It is recognisably a different class of work from the discarded procedural prototype: character and environment now dominate; code is no longer visibly trying to impersonate an illustrator.

It does **not** yet pass the full-MV gate. Full-frame stills alone will become repetitive. Before extending runtime, Stage 3 must build the original GPT character pack and several reusable environment/foreground layers so scenes can be recomposed rather than merely reframed.

## Stage 3 next

Create a consistent, animation-ready original asset pack in the approved design language:

1. GPT neutral/listening bust
2. GPT thinking/profile
3. GPT reaching pose
4. happy close-up
5. uncertain/worried close-up
6. full-body standing
7. back view
8. hands / pointing / holding a note
9. user silhouettes and hands
10. desk, window, paper cards, chat panes, sky/world elements as separable layers

Then build a 30–45 s sequence with real shot recomposition, foreground parallax and match cuts. Only after that passes do we expand to the complete film.

## CI note

`hero/render.sh` is deterministic and CI-friendly once the approved binary art assets are present under `assets/styleframes/`. Keep CI temporary and one-shot while this remains under `temp-work/`.
