# Knowledge Base Integrity

Tooling for validating and enforcing knowledge base conventions.

## What This Is

This repository provides CLI tools that enforce structural integrity for knowledge bases following the [living-specifications](https://github.com/danielnaab/living-specifications) methodology. The tools detect:

- **Broken backlinks** — spec annotations (`# spec:`) referencing non-existent files
- **Orphan specs** — specification files with no implementation references
- **Content violations** — missing frontmatter status fields or provenance sections
- **Broken links** — internal markdown links pointing to non-existent files

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

- [Living Specifications Methodology](https://github.com/danielnaab/living-specifications)
- [Meta Knowledge Base Patterns](https://github.com/danielnaab/meta-knowledge-base)
