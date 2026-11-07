# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

Planned as 0.4.0.

### Added

- OKF bundles: `rules.checks.okf.bundle` declares a directory as an OKF v0.2 bundle, and `.okfignore` at its
  root (`.gitignore` syntax) excludes files from it.
  - kb-linter checks conformance: every note has frontmatter with a non-empty `type`; `index.md` has no
    frontmatter (the root's may hold `okf_version`) and lists headings and entries; `log.md` headings are dates.
    `rules.checks.okf.version` pins the root's `okf_version`.
  - link-validator classifies links in the bundle: a missing note is an `unwritten-link` or `likely-typo`
    notice and does not fail; `escapes-bundle`, `malformed-link`, `misdirected-link` and `wikilink` fail.
    `/` links resolve from the bundle root. Output gains a `notices` array and `unwritten`/`likely_typos` counts.
- Structured provenance (meta-knowledge-base v1.1.0): a `sources` frontmatter list whose entries each have a
  `resource` counts as provenance in every KB; a malformed one is `invalid-sources`.
- link-validator checks heading anchors in every KB (`missing-anchor`), accepting GitHub and dashed slugs,
  Obsidian heading text and block ids, and HTML ids.
- The configuration reader reads inline mappings (`{ by: x, at: y }`) and nested inline lists.

### Changed

- meta-knowledge-base v1.1.0 (structured provenance; raw-sources and historical layers).

### Fixed

- Link titles (`[x](path.md "Title")`) are no longer read as part of the path.

### Upgrading

- A KB without `rules.checks.okf` sees two changes: links to missing headings fail (`missing-anchor`), and
  same-file `#heading` links count toward `links_checked`. Fix the anchor or the heading, or set
  `rules.checks.links.anchors: false` until you can.
- Anything parsing link-validator's JSON should read the new `notices` array; notices never fail a run.

## [0.3.0] - 2026-11-06

### Added

- The tools are flake apps: `nix run .#lint`, `.#check-links`, `.#scan-backlinks` and `.#validate`,
  run from a knowledge base's root. A repo takes this flake as an input and re-exports the ones it
  wants, in place of wrapping the modules itself.

### Changed

- graft v2.6.0.

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
