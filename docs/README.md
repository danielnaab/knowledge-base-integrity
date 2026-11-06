---
status: working
---

# Knowledge Base Integrity Documentation

Documentation for using and extending the KB integrity tools.

## Quick Start

```bash
# Install
uv pip install -e .

# Run tools
backlink-scanner /path/to/kb
kb-linter /path/to/kb
link-validator /path/to/kb
```

## Tools Overview

| Tool | Purpose | Checks |
|------|---------|--------|
| `backlink-scanner` | Spec traceability | `# spec:` annotations point to real specs |
| `kb-linter` | Content rules | Frontmatter status, provenance sections |
| `link-validator` | Link integrity | Internal markdown links exist |

## Configuring scan scopes

By default the tools check `docs/`, `policies/`, `playbooks/` (the linter) and also `notes/`, `specs/`
(the link validator). To check another layout, add `rules.checks` to `knowledge-base.yaml`:

| Key | Tool | Meaning |
|-----|------|---------|
| `rules.checks.links.include` / `exclude` | link-validator | Markdown files whose links are checked |
| `rules.checks.lifecycle.include` / `exclude` | kb-linter | Files whose frontmatter `status` is checked |
| `rules.checks.lifecycle.extraStatuses` | kb-linter | Statuses allowed beyond `rules.lifecycle.statuses` (`living` is always allowed) |
| `rules.checks.provenance.include` / `exclude` | kb-linter | Files that need a `## Sources` section; replaces `sources.canonical` as the scope |

- Globs are repository-relative: `*` stays within a path segment, `**` crosses segments, `dir/**` is everything beneath `dir/`.
- Hidden directories (`.pi/`) are walked only when an include names them. `.git/`, `node_modules/` and directories graft wrote are never walked.
- `rules.lifecycle.statuses` may be an inline list (quoted or bare) or a block list.
- If a configured value cannot be read, the tool exits 2 and names the key.
- Example: a notebook-style KB with dated notes (no status) and wiki pages (status and Sources) sets
  `lifecycle.include` and `provenance.include` to `docs/**` and `notebook/wiki/**`, and `links.include` to everything.

## Sources

- [Specifications](../specs/) — Behavioral contracts for each tool
- [tool-cli: configuration and path scopes](../specs/tool-cli.md#configuration)
