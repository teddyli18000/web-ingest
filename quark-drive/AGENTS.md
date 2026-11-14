# Quark Drive task

Read this README and `../tools/cloud-drive/README.md` before changing Quark automation. Keep Quark credentials, stage IDs, releases, files and state completely separate from Baidu. Follow the global three-worker cap and GitHub API-only supervisor; do not introduce a second independent master. Treat signed CDN URLs as ephemeral credentials, never commit or log them. Do not delete a staged Quark file before Drive independent checksum validation.
