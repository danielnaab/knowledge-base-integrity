# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Changed

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
