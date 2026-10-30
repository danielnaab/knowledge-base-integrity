# spec: specs/kb-linter.md
# spec-section: Behavior/Frontmatter validation

"""Core linting logic for validating KB content against declared rules."""

import contextlib
import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path

FRONTMATTER_PATTERN = re.compile(r"^---\s*\n(.*?)^---\s*\n", re.DOTALL | re.MULTILINE)
STATUS_PATTERN = re.compile(r"^status:\s*(.+?)\s*$", re.MULTILINE)
SOURCES_HEADING_PATTERN = re.compile(r"^## Sources\s*$", re.MULTILINE)

SKIP_DIRS = frozenset({".git", ".graft", ".venv", "node_modules", "__pycache__"})

CONTENT_DIRS = ("docs", "policies", "playbooks")

# Decision records (ADRs) record a decision state, a separate axis from
# document lifecycle, so they may use these statuses as well as the KB's own.
DECISION_STATUSES = ("proposed", "accepted", "rejected", "superseded", "deprecated")


@dataclass
class Violation:
    """A single linting violation."""

    file: str
    rule: str
    message: str


@dataclass
class LintConfig:
    """Configuration read from knowledge-base.yaml."""

    valid_statuses: list[str] = field(default_factory=list)
    provenance_paths: list[str] = field(default_factory=list)


@dataclass
class LintResult:
    """Result of linting a KB directory."""

    violations: list[Violation] = field(default_factory=list)
    files_checked: int = 0


def parse_config(root: Path) -> LintConfig:
    """Read linting configuration from knowledge-base.yaml.

    Extracts the specific values needed for linting from the known schema.
    This is targeted extraction, not a general YAML parser.
    """
    config_path = root / "knowledge-base.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"knowledge-base.yaml not found in {root}")

    content = config_path.read_text(encoding="utf-8")

    # Extract statuses from inline list: statuses: ["draft", "working", ...]
    statuses_match = re.search(r"statuses:\s*(\[.+?\])", content)
    valid_statuses = []
    if statuses_match:
        with contextlib.suppress(json.JSONDecodeError):
            valid_statuses = json.loads(statuses_match.group(1))

    # Extract canonical paths from sources.canonical entries. The block ends at
    # the next key at the same or lesser indentation as "canonical:" (a sibling
    # such as "interpretation:", or a top-level key). List items may sit at the
    # same indentation as their parent key, which YAML allows.
    provenance_paths = []
    canonical_indent: int | None = None
    for line in content.splitlines():
        stripped = line.strip()
        indent = len(line) - len(line.lstrip())
        if canonical_indent is None:
            if stripped == "canonical:":
                canonical_indent = indent
            continue
        if stripped == "" or stripped.startswith("#"):
            continue
        if stripped.startswith("- path:"):
            if indent < canonical_indent:
                break
            path_value = stripped.removeprefix("- path:").strip().strip('"')
            provenance_paths.append(path_value)
        elif indent <= canonical_indent and not stripped.startswith("- "):
            break  # Sibling or parent key: exited the canonical block

    return LintConfig(valid_statuses=valid_statuses, provenance_paths=provenance_paths)


def _get_content_files(root: Path) -> list[str]:
    """Collect markdown files in content directories."""
    files: list[str] = []
    for content_dir in CONTENT_DIRS:
        dir_path = root / content_dir
        if not dir_path.exists():
            continue
        for dirpath, dirnames, filenames in os.walk(dir_path):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
            for filename in filenames:
                if filename.endswith(".md"):
                    full_path = os.path.join(dirpath, filename)
                    rel_path = os.path.relpath(full_path, root)
                    files.append(rel_path)
    return sorted(files)


def _path_matches_glob(path: str, pattern: str) -> bool:
    """Check if a path matches a simple glob pattern (supports trailing /**)."""
    if pattern.endswith("/**"):
        prefix = pattern[:-3]
        return path.startswith(prefix + "/") or path == prefix
    return path == pattern


def _is_decision_record(path: str) -> bool:
    """A decision record lives under a decisions/ directory or is named adr-*.md."""
    parts = Path(path).parts
    name = parts[-1]
    return "decisions" in parts[:-1] or name.lower().startswith("adr-")


def _check_file(root: Path, file: str, config: LintConfig) -> list[Violation]:
    """Check a single file for violations."""
    violations: list[Violation] = []
    full_path = root / file

    try:
        content = full_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return violations

    # Check frontmatter presence
    fm_match = FRONTMATTER_PATTERN.match(content)
    if not fm_match:
        violations.append(
            Violation(
                file=file,
                rule="missing-frontmatter",
                message="No YAML frontmatter found",
            )
        )
    else:
        frontmatter = fm_match.group(1)
        status_match = STATUS_PATTERN.search(frontmatter)
        if not status_match:
            violations.append(
                Violation(
                    file=file,
                    rule="missing-status",
                    message="No status field in frontmatter",
                )
            )
        elif config.valid_statuses:
            status_value = status_match.group(1)
            allowed = list(config.valid_statuses)
            if _is_decision_record(file):
                allowed += [s for s in DECISION_STATUSES if s not in allowed]
            if status_value not in allowed:
                violations.append(
                    Violation(
                        file=file,
                        rule="invalid-status",
                        message=(
                            f"Invalid status '{status_value}', allowed: {allowed}"
                        ),
                    )
                )

    # Check provenance for canonical paths. A README.md is an index of the
    # canonical docs beside it, not a source of truth itself, so it is exempt.
    is_index = Path(file).name == "README.md"
    needs_provenance = not is_index and any(
        _path_matches_glob(file, pattern) for pattern in config.provenance_paths
    )
    if needs_provenance and not SOURCES_HEADING_PATTERN.search(content):
        violations.append(
            Violation(
                file=file,
                rule="missing-provenance",
                message="No Sources section found (required for canonical content)",
            )
        )

    return violations


def lint(root_dir: str) -> LintResult:
    """Lint a KB directory against its declared rules.

    Reads configuration from knowledge-base.yaml and validates content files
    for frontmatter status and provenance requirements.

    Args:
        root_dir: The KB root directory.

    Returns:
        LintResult with violations and file count.
    """
    root = Path(root_dir).resolve()
    config = parse_config(root)
    files = _get_content_files(root)
    all_violations: list[Violation] = []

    for file in files:
        file_violations = _check_file(root, file, config)
        all_violations.extend(file_violations)

    return LintResult(violations=all_violations, files_checked=len(files))
