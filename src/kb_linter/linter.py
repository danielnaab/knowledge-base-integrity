# spec: specs/kb-linter.md
# spec-section: Behavior/Frontmatter validation

"""Core linting logic for validating KB content against declared rules."""

import re
from dataclasses import dataclass, field
from pathlib import Path

from tool_cli import scope
from tool_cli.config import get_list, load_config

FRONTMATTER_PATTERN = re.compile(r"^---\s*\n(.*?)^---\s*\n", re.DOTALL | re.MULTILINE)
STATUS_PATTERN = re.compile(r"^status:\s*(.+?)\s*$", re.MULTILINE)
# "## Sources", optionally followed by more words ("## Sources and verification").
SOURCES_HEADING_PATTERN = re.compile(r"^## Sources(?:[ \t].*)?$", re.MULTILINE)

CONTENT_DIRS = ("docs", "policies", "playbooks")

# Decision records (ADRs) record a decision state, a separate axis from
# document lifecycle, so they may use these statuses as well as the KB's own.
DECISION_STATUSES = ("proposed", "accepted", "rejected", "superseded", "deprecated")

# Always allowed: marks an always-current document (meta-knowledge-base temporal-layers policy).
LIVING_STATUS = "living"


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
    # sources.canonical paths: the provenance scope unless provenance_include is set.
    provenance_paths: list[str] = field(default_factory=list)
    extra_statuses: list[str] = field(default_factory=list)
    lifecycle_include: list[str] = field(default_factory=list)
    lifecycle_exclude: list[str] = field(default_factory=list)
    provenance_include: list[str] | None = None
    provenance_exclude: list[str] = field(default_factory=list)


@dataclass
class LintResult:
    """Result of linting a KB directory."""

    violations: list[Violation] = field(default_factory=list)
    files_checked: int = 0


def parse_config(root: Path) -> LintConfig:
    """Read linting configuration from knowledge-base.yaml.

    Raises FileNotFoundError when the file is missing and ConfigError when a value the
    linter enforces is present but unreadable (the tool must not silently check nothing).
    """
    config = load_config(root, required=True)

    canonical = _canonical_paths(config)
    lifecycle_include = get_list(config, "rules.checks.lifecycle.include")
    return LintConfig(
        valid_statuses=get_list(config, "rules.lifecycle.statuses") or [],
        provenance_paths=canonical,
        extra_statuses=get_list(config, "rules.checks.lifecycle.extraStatuses") or [],
        lifecycle_include=(
            lifecycle_include
            if lifecycle_include is not None
            else [f"{d}/**" for d in CONTENT_DIRS]
        ),
        lifecycle_exclude=get_list(config, "rules.checks.lifecycle.exclude") or [],
        provenance_include=get_list(config, "rules.checks.provenance.include"),
        provenance_exclude=get_list(config, "rules.checks.provenance.exclude") or [],
    )


def _canonical_paths(config: dict) -> list[str]:
    """The `path:` of each sources.canonical entry."""
    sources = config.get("sources")
    entries = sources.get("canonical") if isinstance(sources, dict) else None
    paths: list[str] = []
    for entry in entries or []:
        if isinstance(entry, dict) and isinstance(entry.get("path"), str):
            paths.append(entry["path"])
    return paths


def _is_decision_record(path: str) -> bool:
    """A decision record lives under a decisions/ directory or is named adr-*.md."""
    parts = Path(path).parts
    name = parts[-1]
    return "decisions" in parts[:-1] or name.lower().startswith("adr-")


def _check_file(
    root: Path,
    file: str,
    config: LintConfig,
    check_status: bool,
    check_provenance: bool,
) -> list[Violation]:
    """Check a single file for violations."""
    violations: list[Violation] = []
    full_path = root / file

    try:
        content = full_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return violations

    # Check frontmatter presence
    fm_match = FRONTMATTER_PATTERN.match(content)
    if check_status and not fm_match:
        violations.append(
            Violation(
                file=file,
                rule="missing-frontmatter",
                message="No YAML frontmatter found",
            )
        )
    elif check_status and fm_match:
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
            allowed += [s for s in (LIVING_STATUS, *config.extra_statuses) if s not in allowed]
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

    if check_provenance and not SOURCES_HEADING_PATTERN.search(content):
        violations.append(
            Violation(
                file=file,
                rule="missing-provenance",
                message="No Sources section found (required for canonical content)",
            )
        )

    return violations


def _is_index(file: str) -> bool:
    """A README.md is an index of the docs beside it, not a source of truth: no Sources needed."""
    return Path(file).name == "README.md"


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

    status_files = set(scope.collect(root, config.lifecycle_include, config.lifecycle_exclude))
    if config.provenance_include is None:
        # Canonical paths inside the lifecycle scope; canonical paths elsewhere
        # (AGENTS.md, flake.nix) name sources of truth and are not scanned.
        provenance_files = {
            f for f in status_files if scope.matches_any(f, config.provenance_paths)
        }
    else:
        provenance_files = set(
            scope.collect(root, config.provenance_include, config.provenance_exclude)
        )
    provenance_files = {f for f in provenance_files if not _is_index(f)}

    files = sorted(status_files | provenance_files)
    all_violations: list[Violation] = []
    for file in files:
        all_violations.extend(
            _check_file(root, file, config, file in status_files, file in provenance_files)
        )

    return LintResult(violations=all_violations, files_checked=len(files))
