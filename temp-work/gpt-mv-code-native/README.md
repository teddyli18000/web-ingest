# GPT MV — code-native film in production

An original GPT/ChatGPT personification film, authored as deterministic Canvas scenes. The Claude lyric-MV repository is a **production-process benchmark only**; no source, imagery, music, timing, choreography, or character assets are reused from it.

## Status — 2026-11-08

**Technical pipeline works; visual film not yet approved as a full MV.** A 60-second timeline exists and previous runs validated browser-per-frame rendering and encoding. The first 30 seconds still lack the reference's visual quality. A green CI is not artistic acceptance.

Active scene routing is opening_v11 (0–15 s), drafts_v13 (15–30 s), construct_v6 (30–45 s), ending_v3 (45–60 s). The latest complete engineering gate is GitHub run [42571760984](https://github.com/teddyli18000/web-ingest/actions/runs/42571760984) at 960×540 / 15 fps / 60 seconds.

## Character lab — isolated from the main film

The 60-second film still loads reach-hq (788×887) for reaching/hand poses, but one opening half-body shot now uses the code-matted v5 source. The reach-hq crop has visible rectangular edges, so it is no longer used for the opening bust. The old SVG mascot, half-cut portrait experiments and hand-painted substitute body designs are rejected.

A new isolated 1080p character lab now tests the existing approved visual-study cutout:

- assets/gpt/bust_v3.webp — 550×640 transparent WebP derived from the approved new_conversation art; no new image generation.
- SHA-256: 76164bf82a81c67b9efb795033e71972a6c8512d1fa73370026736028dd6b0eb.
- src/components/gpt_bust_plate.js — binary loader with SHA-256 and dimension checks, silhouette and registration treatments.
- character_lab.html + src/character_lab.js + export/character_lab.mjs — 1920×1080 review sheet with color, registration, face and dark-field silhouette views.
- .github/workflows/temp-gpt-mv-character-lab.yml — temporary screenshot and alpha report gate.

The older bust_plate.b64.0..3 payload was corrupt (five Base64 characters missing) and is no longer loaded. Remove the unused chunks after a clean replacement passes.

**2026-11-08 matting iteration:** The original `bust_v3.webp` bytes and SHA remain unchanged. `gpt_bust_plate.js` now builds a browser-side matted cutout: selective upper navy-halo removal and a curved lower-bust fade, preserving face/hair and avoiding holes in clothing. The standalone character lab checks navy residue rather than treating every nearly full-width opaque row as proof of background contamination. This is an isolated candidate; it is not yet routed into the 60-second film. CI and rendered image review are required.

**2026-11-04 handoff review:** Direct inspection of the committed `bust_v3.webp` shows large surviving blue/white horizontal background bands. It is **visually rejected as a clean character cutout**, despite having an alpha channel. The lab now reports corner/edge coverage and full-width visible rows; the temporary CI rejects likely rectangular leakage and uploads the review image even on gate failure. No change to the 60-second film is justified by this asset.

The **v5 code-matted bust passes its isolated visual lab** and replaces only the 3.4–7.15s opening half-body shot. It cannot replace full-body or reaching poses.

## Next gate

Obtain the actual 1080p lab PNG/alpha report and confirm the source leak. Fix the cutout from existing approved art (no new image generation), then rerun the isolated visual gate. Only after a clean character plate passes should it replace suitable close/bust shots; inspect compositing and dense cut boundaries before rerendering section gates. Do not export a final 1080p30 film until the full visual review passes.

Keep everything under this temporary workspace. Delete one-off workflows after review; retained old scenes are historical studies, not approved footage.

## 2026-11-08 — Bust compositing into actual timeline

The 1080p character lab CI [42570400762](https://github.com/teddyli18000/web-ingest/actions/runs/42570400762) passed after code-only matting; inspected the resulting PNG and alpha statistics. The clean plate is intended for bust/face shots only. The previous 60s render had visible rectangular boundaries on the old reach crop around 4s and 16s. `opening_v11` and `drafts_v13` now use the matted bust at those two shots; reaching hands still use the existing pose art. The full-film render must be reviewed for scale, continuity and composition before this change can be accepted as a visual improvement.

Final bust matting revision `v5` also softly feathers the source image's left-side cutoff (65 source pixels); isolated and full-timeline review runs must use `gpt-bust-matted-v5`. Do not mistake this for an approved full-body pose.

## Visual review after the first full v5 export (2026-11-08)

Full-timeline run [42571083633](https://github.com/teddyli18000/web-ingest/actions/runs/42571083633) passed 960×540/15fps, but visual review **rejected** the first 16-second portrait insertion: the isolated bust floated in front of paper architecture. The 4-second portrait was materially cleaner than the original rectangular crop, but sat too high above the desk; its placement is lowered toward the foreground tabletop. The 16-second scene now omits the bust, leaving the route and paper structures to communicate the wrong turn. Rerender/review these two sections before treating the visual change as accepted. The full film remains a prototype, not an approved MV.

## Final review master — 2026-11-08

- Character lab: [run 42571081419](https://github.com/teddyli18000/web-ingest/actions/runs/42571081419), **success** at 1920×1080; code-matted v5 removes the navy halo, lower paper remnants, and harsh left crop edge.
- Focused scenes: [run 42571765248](https://github.com/teddyli18000/web-ingest/actions/runs/42571765248), **success**; actual MP4 frames checked at 4.2s and 16.2s. The opening bust has been lowered toward the desk plane; the inappropriate floating world bust was rejected and removed.
- Full 60s: [run 42571760984](https://github.com/teddyli18000/web-ingest/actions/runs/42571760984), **success**; 960×540 at 15fps, H.264/AAC, duration 60.000s, full media decode and black-interval validation passed.
- Final review MP4 SHA-256: `467acc3d170bf09d78c70b31d57e05bd5370e14a3a09908b87694456f7d918a8`.
- Reproduce: `node export/render.mjs --start 0 --end 60 --width 960 --height 540 --fps 15 --art-source reach-hq --bust-source gpt-bust-matted-v5 --out out/gpt_review.mp4` with Chrome/ffmpeg dependencies as in the temporary CI.
- **Visual judgment:** the rectangular character paste-in is substantially improved, but the broader film remains too sparse and diagrammatic to match the reference's choreography and shot density. This is a technical/aesthetic checkpoint, **not a finished MV**.
- Temporary test workflows are removed after successful review, per repository rules. The reproducible renderer, scene source, art and this handoff remain in the workspace.
