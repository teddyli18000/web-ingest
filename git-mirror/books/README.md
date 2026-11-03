# Books

A small human-facing bookshelf inside `git-mirror` for book files worth keeping alongside the other mirrored public assets.

This is for the actual readable files, not a reading tracker or notes database.

## Library

| Book | Author | Language | Formats |
| --- | --- | --- | --- |
| _No books stored yet._ |  |  |  |

Keep this table short. One row per stored edition or translation. Link the book title to its local directory; put detailed provenance inside that directory.

## Layout

```text
git-mirror/books/
├── README.md
├── AGENTS.md
└── <book-slug>/
    ├── README.md
    ├── source.json
    └── files/
        ├── <book>.pdf
        └── <book>.epub
```

One edition/translation gets one `lowercase-kebab-case` directory. Multiple formats of the same edition belong together under `files/`; a materially different edition or translation gets its own directory.

The per-book `README.md` is for people. Keep it simple: title, author, edition/translation when relevant, language, source, redistribution basis, and direct links to the stored files.

`source.json` is the machine-readable provenance record. It should record at least:

- `schema_version` and `kind: "book"`;
- title and authors;
- edition/translation and language when known;
- original source page and/or file URL;
- license/public-domain/other redistribution basis;
- capture time;
- each stored file's local path, original URL, byte size, media type, and SHA-256.

## What belongs here

Store a book file here only when it can be publicly redistributed from this public repository: for example public-domain works, openly licensed books, or material the owner has permission to publish.

Prefer useful reading formats such as PDF and EPUB. Preserve the original content bytes; do not re-encode or rewrite a book merely for consistency.

Do not turn this area into a paper library, web clipper, citation manager, highlights database, or reading-notes system. Those are separate concerns.

## Adding a book

Read [`AGENTS.md`](AGENTS.md). In practice:

1. Identify the exact edition/translation and a redistribution-safe source.
2. Create one book directory and provenance record.
3. Save the useful original formats under `files/`.
4. Verify file hashes and that the files open as the claimed formats.
5. Add one concise row to the table above.

For binary downloads that are awkward to commit directly, a temporary path-scoped `temp-book-<slug>.yml` Action may download, hash, validate, commit the book directory, and remove itself. Do not create a recurring book workflow.
