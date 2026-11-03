# AGENTS.md — books

`git-mirror/books/` is the durable bookshelf for publicly redistributable book files preserved in `web-ingest`.

## Goal

Make stored books easy for a human or another Agent to find and use later. Keep the shelf boring: one book edition per directory, readable files under `files/`, concise human metadata in `README.md`, exact provenance in `source.json`.

## Book identity

- Use one `lowercase-kebab-case` directory per edition or translation.
- Multiple formats of the same edition belong in the same directory.
- A different edition, substantial revision, or different translation gets its own directory.
- Prefer a slug based on a recognizable short title; add author or edition only when needed to avoid ambiguity.

## Required contents

Each book directory must contain:

```text
<book-slug>/
├── README.md
├── source.json
└── files/
    └── <stored book files>
```

The human README should contain only useful human-facing information: title, author, edition/translation when relevant, language, source, redistribution basis, and direct file links.

`source.json` owns detailed provenance. Record the exact source URL(s), capture time, redistribution basis/license, and for every stored file its local path, original URL, byte size, media type, and SHA-256.

## Source and file rules

- Only preserve material that may be publicly redistributed from this public repository: public domain, open license, or explicit publication permission.
- Prefer authoritative or first-party distribution sources when available.
- Preserve original file bytes. Do not OCR, reflow, compress, convert, watermark, or otherwise modify a book unless the owner explicitly asks for a derived format.
- PDF and EPUB are preferred when available. Keep other genuinely useful original formats when they add value.
- Verify that downloaded files are non-empty and match the claimed file type before committing them.
- Compute SHA-256 for every stored file.
- Keep each committed book file below the repository's practical 90 MiB per-file ceiling unless the owner explicitly chooses another storage approach.

## Human shelf index

After a successful import, add exactly one concise row to `git-mirror/books/README.md` with:

- book title linked to the local book directory;
- author;
- language;
- available formats.

Do not put hashes, byte sizes, capture dates, URLs, or license details into the top-level table. Those belong inside the book directory.

## Temporary Actions

For binary downloads that are inconvenient through normal repository APIs, a one-shot workflow named `temp-book-<slug>.yml` may be used.

- No `schedule:` trigger.
- Scope its push trigger to its own workflow file and any exact durable files it needs.
- Download only the intended public source files.
- Validate file type, size, and SHA-256 before committing.
- Stage only the book directory and the workflow's own deletion.
- Rebase on current `main` before pushing.
- Remove the workflow after successful validated import.

Do not create a generic always-on book downloader until repeated real imports demonstrate a need for one.

## Boundaries

- Git repository mirrors stay under `git-mirror/data/`; books stay under `git-mirror/books/`.
- Do not place reading notes, highlights, summaries, or research analysis here.
- Do not silently replace an existing stored edition. If the owner wants a newer edition or replacement file, handle that explicitly and keep provenance clear.
