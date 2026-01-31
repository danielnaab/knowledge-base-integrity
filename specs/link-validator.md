---
status: working
last-verified: 2026-01-24
owners: [daniel]
---

# Link Validator

## Intent

Detect broken internal links in markdown content — files that reference paths which don't exist. This catches link rot caused by file renames, moves, or deletions without updating references.

This complements the [backlink scanner](backlink-scanner.md) (code→spec traceability) and [KB linter](kb-linter.md) (frontmatter/provenance rules) to form a structural integrity trio for the knowledge base.

## Non-goals

- External URL validation (network-dependent, slow, flaky — separate concern)
- Anchor/fragment validation (checking `#section-name` targets exist within files)
- Link content quality (whether link text is descriptive)
- Fixing broken links (detection only)
- Checking links inside code blocks or inline code spans (those are examples, not navigational)

## Behavior

### Link extraction

```gherkin
Given a markdown file
When the validator scans it
Then it extracts all [text](target) links where target is a relative path
  And it skips links inside fenced code blocks and inline code spans
  And it skips external links (starting with http://, https://, or mailto:)
```

### Path resolution

```gherkin
Given a link [text](../format.md) in file docs/living-specifications/guides/writing-specs.md
When the validator resolves the path
Then it resolves relative to the linking file's directory: docs/living-specifications/format.md
```

```gherkin
Given a link [text](living-specifications/format.md) in file docs/README.md
When the validator resolves the path
Then it resolves to docs/living-specifications/format.md
```

```gherkin
Given a link with a fragment [text](../docs/living-specifications/principles.md#principle-2)
When the validator resolves the path
Then it strips the fragment and checks only the file path: docs/living-specifications/principles.md
```

### Validation

```gherkin
Given a resolved path pointing to an existing file
When validation completes
Then no violation is reported
```

```gherkin
Given a resolved path pointing to an existing directory (e.g., ../docs/)
When validation completes
Then no violation is reported
```

```gherkin
Given a resolved path pointing to a file that does not exist
When validation completes
Then it reports a "broken-link" violation with the source file, link target, and resolved path
```

### Scanned paths

- Content directories: docs/, notes/, specs/
- Only `.md` files are scanned for links
- Files in subdirectories are included recursively
- Skips: .git/, .graft/, .venv/, node_modules/, __pycache__/

### Output structure

```gherkin
Given completed validation
When results are reported
Then output is a JSON object with a flat violations array and a summary object
```

Example output:
```json
{
  "violations": [
    {
      "file": "docs/guide.md",
      "target": "../old-reference.md",
      "resolved": "old-reference.md",
      "rule": "broken-link",
      "message": "Link target does not exist"
    }
  ],
  "summary": {
    "files_checked": 15,
    "links_checked": 42,
    "broken": 1
  }
}
```

### Exit codes

- **Exit 0**: no broken links found
- **Exit 1**: one or more broken links found
- **`--report-only` flag**: always exit 0

### Edge cases

- Links with query strings (e.g., `file.md?raw=true`): strip query, check file path
- Links to paths outside the repository root (e.g., `../../../etc/passwd`): report as broken (resolved path escapes root)
- Empty link targets `[text]()`: skip (not a path reference)
- Image links `![alt](path)`: check the path (images can rot too)
- Multiple links to the same broken target: report each occurrence separately
- Absolute paths starting with `/`: resolve from repository root

## Constraints

- Runs in Python (no runtime dependencies beyond standard library)
- Completes in under 1 second for knowledge bases up to 1,000 content files
- Does not access the network

## Open Questions

- [ ] Should links to `.graft/` managed directories be validated? (They exist but are external dependencies)

## Decisions

- 2026-01-24: Scan all content directories including notes/ and specs/. Unlike the KB linter (which skips notes/specs), link rot affects navigability regardless of content type.
- 2026-01-24: Skip links inside code blocks and inline code spans. Specs and playbooks contain example link syntax that is illustrative, not navigational.
- 2026-01-24: Check image links too. A broken image reference is as bad as a broken text link for content integrity.
- 2026-01-24: Strip fragments before checking. Anchor validation is a harder problem (requires parsing headings) and is explicitly a non-goal for v1.

## Sources

- [KB Linter](kb-linter.md) — sibling tool, structural patterns to follow
- [Backlink Scanner](backlink-scanner.md) — sibling tool, completes the integrity trio
- Living Specifications: Verification and Drift Detection — link validation as detection approach
