---
status: working
last-verified: 2026-10-30
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
  And it skips links inside fenced code blocks, inline code spans and HTML comments
  And it still extracts links whose text is or contains a code span ([`name.py`](path))
  And it skips external links (any target that begins with a URI scheme)
```

```gherkin
Given a link whose target begins with a URI scheme
  (a letter, then letters, digits, "+", "-" or ".", then ":", per RFC 3986)
When the validator scans it
Then it treats the link as external and does not check or count it
  Examples: http:, https:, mailto:, tel:, file:, data:, airmail:, app:
```

```gherkin
Given a link inside an HTML comment (<!-- ... -->), on one line or spanning several
When the validator scans it
Then it does not check or count it, and a code fence inside the comment does not open a block
```

```gherkin
Given a link whose first ":" comes after a "/", "?" or "#" (e.g., sub/a:b.md)
When the validator scans it
Then it treats the link as a relative path and checks it
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

```gherkin
Given a link with a percent-encoded target [text](../transcripts/Weekly%20Sync%2C%20Notes.md)
When the validator resolves the path
Then it strips the fragment and query, then decodes the percent-encoding
  And it checks the decoded path: transcripts/Weekly Sync, Notes.md
```

```gherkin
Given a link with an angle-bracket destination [text](<Name with spaces.md>)
When the validator resolves the path
Then it removes the angle brackets and resolves the path inside them: Name with spaces.md
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

- Scope: `rules.checks.links.include` minus `.exclude` in knowledge-base.yaml (see [tool-cli](tool-cli.md#path-scopes)); default `docs/`, `policies/`, `playbooks/`, `notes/`, `specs/`
- knowledge-base.yaml is optional here: without it (or without `rules.checks.links`) the default scope applies
- A configured value of the wrong shape exits 2
- Root-level files (README.md, AGENTS.md) and hidden directories (`.pi/`) are scanned when an include glob names them
- Only `.md` files are scanned for links
- Files in subdirectories are included recursively
- Skips: .git/, .graft/, .venv/, node_modules/, __pycache__/
- Skips directories graft wrote (see [tool-cli](tool-cli.md#graft-directories)); links *into* them are still checked, since the target exists

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

- [x] Should links into graft's directories be validated? Yes: they are this repo's links, and a target an upgrade removed is exactly the breakage to catch. Links *inside* graft's directories are not (2026-11-05).

## Decisions

- 2026-01-24: Scan all content directories including notes/ and specs/. Unlike the KB linter (which skips notes/specs), link rot affects navigability regardless of content type.
- 2026-01-24: Skip links inside code blocks and inline code spans. Specs and playbooks contain example link syntax that is illustrative, not navigational.
- 2026-01-24: Check image links too. A broken image reference is as bad as a broken text link for content integrity.
- 2026-01-24: Strip fragments before checking. Anchor validation is a harder problem (requires parsing headings) and is explicitly a non-goal for v1.
- 2026-10-30: Treat any URI scheme as external, not just http:, https: and mailto:. App-specific schemes (Airmail's `airmail://message?...`, `tel:`, `data:`, `app:`) were resolved as relative paths and reported as broken: 264 false findings across 18 knowledge bases. `file:` links are external too, since they point outside the repository.
- 2026-10-30: Decode percent-encoding after stripping the fragment and query. CommonMark and Obsidian decode `%20` and `%2C`, so `Meeting%20Notes.md` names `Meeting Notes.md`. Decoding last keeps an encoded `%23` in the path from being mistaken for a fragment. Violations report the target as written and the decoded resolved path.
- 2026-10-30: Accept CommonMark angle-bracket destinations (`<Name with spaces.md>`). Obsidian writes them for filenames with spaces.
- 2026-10-30: Replace inline code spans with placeholder text, not nothing, before matching links. Removing them outright also removed code-span link text, so `` [`gate.py`](path) `` was never checked and a real broken link went unreported. A link written entirely inside a code span is still ignored.
- 2026-10-30: Skip links inside HTML comments. They aren't rendered, and templates use them for commented-out example entries: henry-papa-workbench's notes/README.md had four example links in a `<!-- ... -->` block reported as broken.
- 2026-11-05: Skip directories graft wrote, found by the marker in their README.md (`tool_cli.graft.is_graft_dir`), wherever they sit: `scions/`, a hidden `.scions/`, or `docs/Grafted/`. A grafted directory is another repo's export, checked by that repo, and graft's `nix flake check` fails if it is edited here, so a finding inside one can't be acted on. Before this, only steward's check-kb-integrity duty filtered them, so a direct run reported upstream content as this repo's.

- 2026-11-05: Scan scope is configurable (`rules.checks.links`) through the shared [tool-cli](tool-cli.md#configuration) reader, defaults unchanged. A notebook-style KB keeps its content under `notebook/` and at the root, which the hardcoded directories never reached. The configuration file stays optional for this tool, as before.

## Sources

- [KB Linter](kb-linter.md) — sibling tool, structural patterns to follow
- [Backlink Scanner](backlink-scanner.md) — sibling tool, completes the integrity trio
- Living Specifications: Verification and Drift Detection — link validation as detection approach
