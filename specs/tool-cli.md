---
status: working
last-verified: 2026-01-24
---

# Spec: tool-cli

Shared CLI runner that enforces consistent interface conventions across all knowledge-base-integrity tools.

## Intent

Three tools share identical CLI behavior: argument parsing, JSON output, exit codes, and `--report-only` mode. Rather than duplicating this logic, `tool_cli` provides a single entry point that accepts tool-specific functions and handles the rest.

## Non-goals

- **Argument parsing library** — no argparse/click; the interface is intentionally minimal
- **Output formatting options** — always JSON, always indented
- **Tool-specific logic** — the runner is generic; tools provide their own runner/serializer/has_failures

## Behavior

### Argument handling

- `--report-only` flag is extracted from argv regardless of position
- First non-flag argument is the root directory (defaults to `.`)
- Unknown flags are passed through as positional arguments (no validation)

### Execution

- Calls `runner(root_dir)` with the resolved directory path
- If `runner` raises `FileNotFoundError`, prints error to stderr and exits 2
- Other exceptions propagate (intentional — tool bugs should be visible)

### Output

- Calls `serializer(result)` and prints as JSON with 2-space indent to stdout
- Output is always valid JSON (one object, no streaming)

### Exit codes

- **0**: No failures found (or `--report-only` is set)
- **1**: `has_failures(result)` returns True (and `--report-only` is not set)
- **2**: Configuration error (FileNotFoundError from runner)

### `--report-only` mode

- When set: always exit 0 after printing output, regardless of failures
- Purpose: informational runs in contexts where non-zero exit would abort a pipeline

## Constraints

- No runtime dependencies beyond Python stdlib
- Generic over result type (uses TypeVar)
- Each tool provides three callables: `runner`, `serializer`, `has_failures`

## Decisions

- 2026-01-24: Extracted after 3 tools shared identical __main__.py patterns.
- 2026-01-24: No argparse — the minimal interface (one flag, one positional) doesn't justify the dependency. If more flags are added, reconsider.
- 2026-01-24: FileNotFoundError specifically (not general OSError) because tools raise it for missing config files (knowledge-base.yaml, spec directories).

## Related

- [backlink-scanner](backlink-scanner.md) — consumer
- [kb-linter](kb-linter.md) — consumer
- [link-validator](link-validator.md) — consumer

## Sources

- Extracted from: identical patterns in three __main__.py files
- Living Specifications Principles — #5 (low ceremony, high signal)
