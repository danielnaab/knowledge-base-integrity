# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

## [0.2.0] - 2026-11-06

### Added

- Scan scopes are configurable in `knowledge-base.yaml` under `rules.checks` (`links`, `lifecycle`,
  `provenance`, each with `include`/`exclude` globs; `lifecycle.extraStatuses`). Defaults are the old
  directories, so KBs without the block behave as before. A KB with content under `notebook/` or at
  the root can now be checked in full, including hidden directories an include names (`.pi/skills/**`).
- Shared `tool_cli.config` (YAML-subset reader) and `tool_cli.scope` (globs and file collection).

### Fixed

- `rules.lifecycle.statuses` written as a bare YAML list (`[draft, working]`) or block list was read as
  empty, so the invalid-status check silently never ran. It is read correctly, and a value that cannot be
  read as a list now exits 2.
- `status: living` is accepted (the meta-knowledge-base temporal-layers policy prescribes it).
- `## Sources and verification` and similar headings count as a Sources section.

### Changed

- When `rules.checks.provenance.include` is set it replaces `sources.canonical` as the provenance scope.
- All three tools skip directories graft wrote (`scions/`, or wherever graft's `dir` puts
  them), recognized by the marker in their README.md. The link validator still checks links
  into them.

## [0.1.0] - 2026-01-31

### Added

- Initial extraction from delivery-practices repository
- Backlink Scanner (`backlink-scanner`):
  - Scan for `# spec:` and `// spec:` annotations
  - Detect dangling references and orphan specs
  - Section-level traceability via `spec-section:` annotations
- KB Linter (`kb-linter`):
  - Validate frontmatter status fields
  - Check provenance requirements for canonical content
  - Read rules from knowledge-base.yaml
- Link Validator (`link-validator`):
  - Detect broken internal markdown links
  - Skip code blocks and inline code
  - Handle relative paths and fragments
- Shared CLI infrastructure (`tool_cli`):
  - Consistent JSON output format
  - Exit codes: 0 (clean), 1 (issues), 2 (config error)
  - `--report-only` flag for informational runs
- Behavioral specifications for all tools
- Comprehensive test suite
