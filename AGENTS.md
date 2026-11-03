# Agent Entrypoint - Knowledge Base Integrity

You are working in the **knowledge-base-integrity** repository — tooling for validating and enforcing knowledge base conventions.

## Before Making Changes

1. Read [knowledge-base.yaml](knowledge-base.yaml) for KB configuration
2. Follow [meta knowledge base conventions](vendor/meta-knowledge-base/README.md)
3. Follow [living specifications methodology](vendor/living-specifications/README.md)
4. Understand key policies:
   - **Authority**: specs/ canonical for tool behavior, docs/ canonical for usage
   - **Provenance**: Ground tool decisions in sources
   - **Lifecycle**: Mark status (draft/working/stable/deprecated)
   - **Write boundaries**: see [`knowledge-base.yaml`](knowledge-base.yaml) `rules.writes`

## Your Role

As a developer on KB integrity tooling:

- **Spec-first development** — Update specs before or alongside code changes
- **Test-driven** — Write tests that verify spec behavior
- **Dogfooding** — Run tools on this repo to verify integrity
- **Minimal dependencies** — Python stdlib only for runtime

## Content Organization

| Directory | Purpose |
|-----------|---------|
| `specs/` | Behavioral specifications for each tool |
| `src/` | Python implementations |
| `tests/` | Pytest test suite |
| `docs/` | Usage documentation |

## Workflow: Plan → Patch → Verify

1. **Plan**: State intent, files to touch, uncertainties
2. **Patch**: Make minimal changes to achieve goal
3. **Verify**: Run `pytest`, then run tools on this repo

## Write Boundaries

You may write to:
- `specs/**` — Tool specifications
- `src/**` — Python implementations
- `tests/**` — Test suite
- `docs/**` — Documentation

Never write to (enforced for Claude Code by `.claude/settings.json`):
- `secrets/**`, `credentials/**` — Sensitive paths

## Tool Architecture

Three tools share CLI infrastructure via `tool_cli`:

```
tool_cli (shared CLI runner)
   ├── backlink_scanner (spec traceability)
   ├── kb_linter (content validation)
   └── link_validator (link checking)
```

Each tool provides:
- `runner(root_dir)` — Core logic returning a result object
- `serializer(result)` — JSON conversion
- `has_failures(result)` — Exit code determination

## Development Commands

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov

# Lint code
uv run ruff check src tests

# Dogfood (run on this repo)
uv run backlink-scanner
uv run kb-linter
uv run link-validator
```

## Quick Reference

When making changes:
- **New behavior?** Update spec first, then implement
- **Bug fix?** Check if spec needs correction
- **Refactor?** Verify tests still pass
- **New tool?** Create spec, implement, add tests

---

**Remember**:
- Spec-first: Update specifications alongside code
- No external dependencies at runtime
- Dogfood the tools on this repository
- JSON output for all commands
