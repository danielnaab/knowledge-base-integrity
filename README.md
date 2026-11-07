# Knowledge Base Integrity

Tooling for validating and enforcing knowledge base conventions.

## What This Is

This repository provides CLI tools that enforce structural integrity for knowledge bases following the [living-specifications](scions/living-specifications/README.md) methodology. The tools detect:

- **Broken backlinks** — spec annotations (`# spec:`) referencing non-existent files
- **Orphan specs** — specification files with no implementation references
- **Content violations** — missing frontmatter status fields or provenance (Sources sections or `sources` frontmatter)
- **Broken links** — internal markdown links pointing to non-existent files or headings
- **OKF conformance** — for a declared [OKF](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md) bundle: note types, index and log shapes, and links to notes not written yet

## Tools

| Tool | Command | Purpose |
|------|---------|---------|
| Backlink Scanner | `backlink-scanner` | Spec-to-implementation traceability via `# spec:` annotations |
| KB Linter | `kb-linter` | Validates frontmatter status and provenance requirements |
| Link Validator | `link-validator` | Detects broken internal markdown links |

## Installation

```bash
pip install -e .
```

Or with uv:

```bash
uv pip install -e .
```

## Usage

From a knowledge base's root, through this repo's flake (`nix run github:danielnaab/knowledge-base-integrity#lint`),
or re-exported by a repo that takes it as a flake input:

```
nix run .#validate         # links, then lint findings
nix run .#lint             # frontmatter status and provenance
nix run .#check-links      # broken internal markdown links
nix run .#scan-backlinks   # spec-to-implementation traceability
```

All tools share the same CLI conventions:

```bash
# Run on current directory
backlink-scanner
kb-linter
link-validator

# Run on specific directory
backlink-scanner /path/to/kb

# Informational mode (always exit 0)
kb-linter --report-only
```

### Exit Codes

- **0**: No issues found (or `--report-only` flag is set)
- **1**: Issues detected
- **2**: Configuration error (e.g., missing knowledge-base.yaml)

### Output Format

All tools produce JSON output:

```json
{
  "violations": [...],
  "summary": {
    "files_checked": 15,
    "violations": 2
  }
}
```

## Configuration

Defaults check `docs/`, `policies/`, `playbooks/` (and `notes/`, `specs/` for links). A KB with another
layout declares its scopes in `knowledge-base.yaml`; every key is optional:

```yaml
rules:
  lifecycle:
    statuses: [draft, working, stable, deprecated]
  checks:
    links:
      include: [README.md, AGENTS.md, docs/**, notebook/**]
      exclude: [notebook/raw/**]
    lifecycle:               # files whose frontmatter status is checked
      include: [docs/**, notebook/wiki/**]
      extraStatuses: [reference]   # `living` is always allowed
    provenance:              # files that need a ## Sources section (README.md files are exempt)
      include: [docs/**, notebook/wiki/**]
```

Globs: `*` within a segment, `**` across segments. A value of the wrong shape exits 2.
See [tool-cli](specs/tool-cli.md#configuration) for details.

## Specifications

Each tool has a living specification in the `specs/` directory:

- [backlink-scanner.md](specs/backlink-scanner.md) — Scan for spec annotations
- [kb-linter.md](specs/kb-linter.md) — Validate content rules
- [link-validator.md](specs/link-validator.md) — Detect broken links
- [tool-cli.md](specs/tool-cli.md) — Shared CLI conventions

## Architecture

```
meta-knowledge-base (KB organization patterns)
        ↓
living-specifications (spec-writing methodology)
        ↓
knowledge-base-integrity (this repo: enforcement tooling)
        ↓
your-project (uses tools to validate content)
```

## Development

```bash
# Install with dev dependencies
uv sync

# Run tests
uv run pytest

# Run linter
uv run ruff check src tests

# Dogfood: run tools on this repo
uv run backlink-scanner
uv run kb-linter
uv run link-validator
```

## Sources

- [Living Specifications Methodology](scions/living-specifications/README.md)
- [Meta Knowledge Base Patterns](scions/meta-knowledge-base/README.md)
