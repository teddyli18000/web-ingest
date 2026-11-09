# Opening V12 — shot and acceptance notes

**Status:** code authored and linked on main; 1080p review and edited reel gate pending as of 2026-11-09. This is a visual prototype, not the final MV.

## Story in one sentence
A human question and GPT's answer become two strips of actual paper, are torn and revised together, then construct a world that leads directly into act II.

## Director's cut (absolute time)
| Time | Frame language | On-screen action | Why this shot exists |
| --- | --- | --- | --- |
| 0–1.88 | Extreme macro / pressed ink | Gold and cobalt ribbons approach the same embossed paper mark | Give the relationship a physical beginning |
| 1.88–3.68 | Character reveal / torn shutter | Folded pages open to GPT's face; a gold strip crosses the lower field | Introduce the character without a floating avatar |
| 3.68–5.82 | Oblique worktable / foreground occlusion | GPT studies the paper; one ribbon travels across the table | Show two presences sharing one surface |
| 5.82–8.05 | Pen nib and letterform macro | The mark is written, doubted and rewritten | Perform uncertainty with objects, not a product diagram |
| 8.05–10.35 | Red correction / misregistered paper | The first attempt is rejected; paper facets are rethreaded | Make revision an action |
| 10.35–12.55 | Low-angle fold-to-city | The sheet reveals a paper-built space with arches and depth | Transform a page into a world |
| 12.55–15 | Tracking paper roads / key piece | Blue and gold physically meet; a travelling paper wipe reveals act II | Make the cut causal, not a dissolve |

## Acceptance standards
- Review actual full-resolution stills per shot and the complete reel. A passing CI does not constitute visual approval.
- The GPT plate must be spatially behind foreground material, not a pasted face or an independent UI object.
- No generic AI network, chatbot demo cards, fixed right-side avatar, or reused Claude designs.
- Cuts must change camera distance and material action; no title card should be carrying a full scene.
- Inspect 10.35–12.55 for empty screens and 14.65–15.15 for ghosting or a discontinuous stage.
- This 15s animation is still using a technical sound fixture. The song, beat/cue map, performance timings and full-film director pass are unsolved.

## Implementation and limits
- Source: `src/scenes/opening_v12.js`, not imported from the Claude repository.
- Approved image source: existing GPT bust plate for character performance; all paper, architecture, ribbons, light and transition geometry code-drawn.
- The final wipe renders the current first frame of `drafts_v13` into a second Canvas for a geometrically contiguous stage.
- Current review workflow is a **disposable** CI under `.github/workflows/temp-gpt-mv-opening-v12.yml`; remove it after verification and document the last good artifact.
