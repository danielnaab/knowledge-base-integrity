# Changelog

All notable changes to this project will be documented in this file.

## [1.0.0] - 2026-11-03

### Changed

- Exports for graft (https://github.com/danielnaab/graft): `.gitattributes` defines what repos
  that graft this get: README, CHANGELOG and `docs/`. `AGENTS.md`, `knowledge-base.yaml` and
  `vendor/` are this repo's own.
- meta-knowledge-base is grafted at `v1.0.0` into `vendor/`; AGENTS.md links into that copy.

## [0.1.0] - 2026-01-31

### Added

- Initial extraction from delivery-practices repository
- Core methodology documentation:
  - `docs/format.md` - Specification template structure
  - `docs/principles.md` - 16 governing principles for spec-driven development
  - `docs/relationships.md` - How specs relate to tests and code
  - `docs/verification.md` - Drift detection approaches
  - `docs/comprehension.md` - Making the system legible
- Guides for spec authoring:
  - `docs/guides/writing-specs.md` - How to write specifications
  - `docs/guides/ensemble-with-specs.md` - Mob programming with specs
  - `docs/guides/reviewing-against-specs.md` - PR review patterns
- Repository configuration:
  - `knowledge-base.yaml` - KB configuration importing meta-knowledge-base
  - `AGENTS.md` - Agent entrypoint
