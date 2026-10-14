# Production plan — GPT MV reboot

## Principle

Do not jump from concept directly to a full renderer.

The film is built through visual gates. A stage advances only after its outputs are actually inspected. “The script ran” and “CI passed” are engineering facts, not artistic approval.

## Stage 1 — direction and visual system

Deliverables:
- director brief;
- character/art bible;
- originality boundary;
- six style-frame briefs;
- production/QC rules.

Pass criteria:
- the protagonist has a clear non-cyber identity;
- the user is visibly a co-author;
- palette roles are semantic;
- the film can be described without mentioning tokens, neural networks, tools, or “AI visuals”;
- the visual system supports both quiet acting and large imaginative scenes.

Current status: **in progress**.

## Stage 2 — style frames

Create six 1920×1080 frames from `DIRECTOR_BRIEF.md`.

For each frame produce:
- full-resolution PNG;
- 320 px thumbnail;
- 4–6 sentence review;
- pass/fail against: character read, user presence, tactile depth, focal clarity, generic-AI rejection.

Do not animate anything yet except tiny tests needed to judge material behavior.

If the character design fails, fix it here. Do not carry a weak character into animation.

## Stage 3 — visual grammar tests

Build short 2–5 second tests for:
- GPT character acting and hand motion;
- page fold / paper world transition;
- cursor + GPT collaboration without awkward interaction;
- proof-sheet TRACE alignment;
- DESK → WORLD match cut;
- WORLD → DESK return;
- type integrated physically in frame;
- camera crossing paper/glass foreground.

Each test should be isolated and cheap. Keep failed tests; record why they failed.

Pass criteria:
- motion has anticipation/settle/secondary action;
- no opacity-only primary action;
- no generic glitch/particle fallback;
- character face remains readable through motion;
- transitions feel authored rather than templated.

## Stage 4 — song map and storyboard

The final track/lyrics are user-supplied locally and never committed.

Independent timing workflow:
1. ingest the user's audio locally/CI secret-safe workspace;
2. detect BPM/onsets/sections independently;
3. store only our own cue map, not copied timing from another MV;
4. write a storyboard card for every shot.

Every storyboard card contains:
- id;
- start/end cue;
- mode: DESK / WORLD / TRACE;
- lyric line reference by local index only, no committed lyric text;
- moment;
- action verb;
- GPT pose/expression;
- user mark;
- camera;
- layers;
- transition in/out;
- review frames.

Target density: enough shots to create musical phrasing rather than five long tableaux. Exact count comes from the song map, not a quota.

## Stage 5 — animatic

Use crude geometry, temporary character blocking, and still style frames.

Goals:
- timing;
- shot density;
- emotional arc;
- visual recurrence;
- whether quiet moments are actually quiet;
- whether WORLD shots arrive for a reason and return for a reason.

The animatic is reviewed as a complete film before detailed rendering.

No polish pass may rescue a weak animatic.

## Stage 6 — section production

Work one section at a time.

For each section:
1. implement;
2. render first/key/last frames for every shot;
3. make a contact sheet;
4. inspect at full size and thumbnail size;
5. render the section video;
6. inspect motion and cut rhythm;
7. run decode/safety checks;
8. record known compromises;
9. only then move forward.

Shared engine changes require regression sheets for already-approved sections.

## Stage 7 — full preview

Render one 1080p preview after all sections are approved.

Required checks:
- full decode succeeds;
- audio sync measured against source;
- every cut/cue audit passes;
- no missing lyric coverage in local runtime;
- flash/safety threshold check;
- luma/contrast scan;
- frame-drop/duplicate-frame scan;
- final hold duration check;
- no debug/fallback text;
- full human watch-through.

Any failure is fixed in the smallest owning section, then only affected regions are re-rendered until the final preview pass.

## Stage 8 — high-resolution export

Only after preview approval:
- 4K/high-quality export;
- final decode;
- selected full-resolution frame inspection, especially face/hands/type edges;
- manifest with source commit and hashes;
- artifact upload.

Temporary render workflows are removed after validation per `web-ingest` policy.

## Repository layout for this reboot

```text
temp-work/gpt-mv-reboot/
├── README.md
├── DIRECTOR_BRIEF.md
├── ART_BIBLE.md
├── ORIGINALITY.md
├── PRODUCTION_PLAN.md
├── styleframes/        # only after Stage 2 starts
├── animatic/           # later
├── src/                # only after visual grammar is approved
├── reviews/            # contact sheets + written pass/fail notes
└── out/                # ignored/transient render outputs
```

Do not reuse code from `temp-work/gpt-signal-mv`; it is a failed prototype and a reference only for lessons learned.
