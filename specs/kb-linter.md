---
status: working
last-verified: 2026-01-24
owners: [daniel]
---

# KB Linter

## Intent

Enforce the content rules declared in [`knowledge-base.yaml`](../knowledge-base.yaml) — validating that content files have proper frontmatter status fields and provenance (Sources sections) where required.

This gives Principle #2 ("source-of-truth requires enforcement") its mechanical backing: rules declared in configuration are checked by tooling, not just convention.

## Non-goals

- Prose quality or completeness checking
- Write boundary enforcement (agent entrypoint handles this)
- Markdown link validation (separate concern, handled by [link-validator](link-validator.md))
- Spec-to-implementation traceability (handled by [backlink scanner](backlink-scanner.md))
- Semantic analysis of whether content qualifies as "practice-recommendations" vs. other types

## Behavior

### Configuration

```gherkin
Given a knowledge-base.yaml file in the root directory
When the linter starts
Then it reads rules.lifecycle.statuses for valid status values
  And it reads sources.canonical paths for provenance-required directories
```

```gherkin
Given a knowledge-base.yaml where sources has sibling blocks after canonical
  (e.g. interpretation: and tracking: at the same indentation as canonical:)
When the linter reads sources.canonical paths
Then it reads only the "- path:" entries inside the canonical block
  And the block ends at the next key at the same or lesser indentation as canonical:
  And nested lines such as note: are skipped
```

### Frontmatter validation

```gherkin
Given a markdown file in a content directory (docs/)
When the file has no YAML frontmatter
Then it reports a "missing frontmatter" violation
```

```gherkin
Given a markdown file with frontmatter
When the frontmatter has no status field
Then it reports a "missing status" violation
```

```gherkin
Given a frontmatter status field
When the value is not in rules.lifecycle.statuses
Then it reports an "invalid status" violation with the invalid value and allowed values
```

```gherkin
Given a frontmatter with a valid status field
When the status value is in the allowed set
Then no violation is reported for that file's frontmatter
```

```gherkin
Given a decision record: a file under a decisions/ directory (docs/decisions/0003-x.md)
  or a file named adr-*.md or ADR-*.md anywhere
When its status is proposed, accepted, rejected, superseded, or deprecated
Then no invalid-status violation is reported
  And a status in rules.lifecycle.statuses is also accepted
  And a missing status is still reported as "missing status"
```

```gherkin
Given a file that is not a decision record (docs/guide.md, docs/decisions.md)
When its status is a decision status not in rules.lifecycle.statuses (accepted)
Then it reports an "invalid status" violation
```

### Provenance validation

```gherkin
Given a file in a path matching sources.canonical entries (docs/**)
When the file does not contain a ## Sources heading
Then it reports a "missing provenance" violation
```

```gherkin
Given a file in a canonical path with a ## Sources heading
When the section exists (regardless of content)
Then no provenance violation is reported
```

```gherkin
Given a file in a non-canonical path (notes/)
When the file lacks a Sources section
Then no provenance violation is reported (provenance is optional for these paths)
```

```gherkin
Given a README.md in a path matching sources.canonical entries (docs/decisions/README.md)
When the file lacks a Sources section
Then no provenance violation is reported (a README indexes canonical docs; it is not one)
  And its frontmatter status is still checked
  And other files in the same canonical path still need a Sources section
```

### Scanned paths

- Content directories: docs/
- Only `.md` files are checked
- README.md files are included (they carry status; they are exempt from provenance)
- Files in subdirectories are included recursively
- Skips: .git/, .graft/, .venv/, node_modules/, __pycache__/
- Does not scan: specs/, src/, tests/, notes/ (specs have their own lifecycle; code and tests don't need frontmatter; notes are ephemeral)

### Output structure

```gherkin
Given completed linting
When results are reported
Then output is a JSON object with a flat violations array and a summary object
```

Example output:
```json
{
  "violations": [
    {
      "file": "docs/example.md",
      "rule": "missing-status",
      "message": "No status field in frontmatter"
    },
    {
      "file": "docs/living-specifications/example.md",
      "rule": "missing-provenance",
      "message": "No Sources section found (required for canonical content)"
    }
  ],
  "summary": {
    "files_checked": 12,
    "files_passing": 10,
    "violations": 2
  }
}
```

### Exit codes

- **Exit 0**: no violations found
- **Exit 1**: one or more violations found
- **`--report-only` flag**: always exit 0

### Edge cases

- Files with empty frontmatter (`---\n---`): reports "missing status"
- Files with malformed frontmatter: reports "missing status" (regex extraction, not full YAML parsing)
- Binary files: skipped (UnicodeDecodeError caught)
- File symlinks: resolved normally; directory symlinks: not followed (os.walk default)
- knowledge-base.yaml missing: exit with error message (not a violation, a misconfiguration)

## Constraints

- Runs in Python (no runtime dependencies beyond standard library)
- Reads configuration from `knowledge-base.yaml` (not hardcoded)
- Completes in under 1 second for knowledge bases up to 1,000 content files

## Open Questions

- [ ] Should notes/ files be checked for frontmatter status? (Currently excluded as ephemeral, but they do use status fields)
- [ ] Should the linter support a `# kb-lint: ignore` annotation for intentional exceptions?

## Decisions

- 2026-01-24: Read rules from knowledge-base.yaml rather than hardcoding. Keeps the tool adaptable to different KBs and avoids drift between declared rules and enforcement.
- 2026-01-24: Provenance checking uses `sources.canonical` paths to determine which files need Sources sections. This is more precise than checking all files (notes are ephemeral).
- 2026-01-24: Notes excluded from linting. They're ephemeral explorations — enforcing structure on them contradicts their purpose.
- 2026-10-30: End the sources.canonical block at the next sibling key, not only at a top-level key. Paths in sibling blocks such as interpretation: were read as canonical, so the docs listed there got false missing-provenance findings (daniel/digital-strategy: docs/README.md, docs/agents.md). Parsing stays targeted extraction, not a general YAML parser.
- 2026-10-30: Decision records keep decision statuses. An ADR's status records the decision (proposed, accepted, rejected, superseded, deprecated), a separate axis from document lifecycle, so decision records may use those values as well as rules.lifecycle.statuses. Relabelling an accepted ADR as "stable" to satisfy the linter loses that information; Daniel rejected doing so. Evidence: graft's 9 accepted ADRs (docs/decisions/ and a grove adr-001 under docs/specifications/grove/) were flagged invalid-status. A decision record is a file under a decisions/ directory or named adr-*.md; a status is still required.
- 2026-10-30: README.md files are exempt from provenance even when a sources.canonical glob (docs/decisions/**) covers them. A README indexes the canonical docs beside it; it is not a source of truth, and a Sources section on an index has nothing to cite. Status is still checked.

## Sources

- Living Specifications Principles — #2 (enforcement), #14 (fight tribal knowledge)
- Living Specifications Format — "Status is non-negotiable"
- [Backlink Scanner](backlink-scanner.md) — sibling tool, structural patterns to follow
