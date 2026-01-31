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

## Sources

- [Specifications](../specs/) — Behavioral contracts for each tool
