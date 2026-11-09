# GPT MV — code-native film in production

An original GPT/ChatGPT personification film, authored as deterministic Canvas scenes. The Claude lyric-MV repository is a **production-process benchmark only**; no source, imagery, music, timing, choreography, or character assets are reused from it.

## Status — 2026-11-04

**Technical pipeline works; visual film not yet approved.** A 60-second timeline exists and previous runs validated browser-per-frame rendering and encoding. The first 30 seconds still lack the reference's visual quality. A green CI is not artistic acceptance.

Active scene routing is opening_v11 (0–15 s), drafts_v13 (15–30 s), construct_v6 (30–45 s), ending_v3 (45–60 s). The last complete engineering gate was GitHub run 41181931335 at 960×540 / 15 fps.

## Character lab — isolated from the main film

The 60-second film still loads reach-hq (788×887), whose background-contaminated character crops are not suitable for closeups. The old SVG mascot, half-cut portrait experiments and hand-painted substitute body designs are rejected.

A new isolated 1080p character lab now tests the existing approved visual-study cutout:

- assets/gpt/bust_v3.webp — 550×640 transparent WebP derived from the approved new_conversation art; no new image generation.
- SHA-256: 76164bf82a81c67b9efb795033e71972a6c8512d1fa73370026736028dd6b0eb.
- src/components/gpt_bust_plate.js — binary loader with SHA-256 and dimension checks, silhouette and registration treatments.
- character_lab.html + src/character_lab.js + export/character_lab.mjs — 1920×1080 review sheet with color, registration, face and dark-field silhouette views.
- .github/workflows/temp-gpt-mv-character-lab.yml — temporary screenshot and alpha report gate.

The older bust_plate.b64.0..3 payload was corrupt (five Base64 characters missing) and is no longer loaded. Remove the unused chunks after a clean replacement passes.

**2026-11-08 matting iteration:** The original `bust_v3.webp` bytes and SHA remain unchanged. `gpt_bust_plate.js` now builds a browser-side matted cutout: selective upper navy-halo removal and a curved lower-bust fade, preserving face/hair and avoiding holes in clothing. The standalone character lab checks navy residue rather than treating every nearly full-width opaque row as proof of background contamination. This is an isolated candidate; it is not yet routed into the 60-second film. CI and rendered image review are required.

**2026-11-04 handoff review:** Direct inspection of the committed `bust_v3.webp` shows large surviving blue/white horizontal background bands. It is **visually rejected as a clean character cutout**, despite having an alpha channel. The lab now reports corner/edge coverage and full-width visible rows; the temporary CI rejects likely rectangular leakage and uploads the review image even on gate failure. No change to the 60-second film is justified by this asset.

This bust is **not yet an approved film master**. Inspect the navy silhouette residue, lower edge, hair detail and enlarged face. It cannot replace full-body or reaching poses.

## Next gate

Obtain the actual 1080p lab PNG/alpha report and confirm the source leak. Fix the cutout from existing approved art (no new image generation), then rerun the isolated visual gate. Only after a clean character plate passes should it replace suitable close/bust shots; inspect compositing and dense cut boundaries before rerendering section gates. Do not export a final 1080p30 film until the full visual review passes.

Keep everything under this temporary workspace. Delete one-off workflows after review; retained old scenes are historical studies, not approved footage.

## 2026-11-08 — Bust compositing into actual timeline

The 1080p character lab CI [42570400762](https://github.com/teddyli18000/web-ingest/actions/runs/42570400762) passed after code-only matting; inspected the resulting PNG and alpha statistics. The clean plate is intended for bust/face shots only. The previous 60s render had visible rectangular boundaries on the old reach crop around 4s and 16s. `opening_v11` and `drafts_v13` now use the matted bust at those two shots; reaching hands still use the existing pose art. The full-film render must be reviewed for scale, continuity and composition before this change can be accepted as a visual improvement.

Final bust matting revision `v5` also softly feathers the source image's left-side cutoff (65 source pixels); isolated and full-timeline review runs must use `gpt-bust-matted-v5`. Do not mistake this for an approved full-body pose.
