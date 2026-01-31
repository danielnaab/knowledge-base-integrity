# spec: specs/link-validator.md
# spec-section: Behavior/Link extraction

"""Core validation logic for detecting broken internal markdown links."""

import os
import re
from dataclasses import dataclass, field
from pathlib import Path

# Matches [text](target) and ![alt](target)
LINK_PATTERN = re.compile(r"!?\[(?:[^\]]*)\]\(([^)]*)\)")

# Matches opening/closing code fences
FENCE_PATTERN = re.compile(r"^(`{3,}|~{3,})")

# Matches inline code spans (backtick-wrapped)
INLINE_CODE_PATTERN = re.compile(r"(`+)(.+?)\1")

SKIP_DIRS = frozenset({".git", ".graft", ".venv", "node_modules", "__pycache__"})

CONTENT_DIRS = ("docs", "policies", "playbooks", "notes", "specs")

EXTERNAL_PREFIXES = ("http://", "https://", "mailto:")


@dataclass
class LinkViolation:
    """A single broken link."""

    file: str
    target: str
    resolved: str
    rule: str = "broken-link"
    message: str = "Link target does not exist"


@dataclass
class ValidateResult:
    """Result of validating links across a KB."""

    violations: list[LinkViolation] = field(default_factory=list)
    files_checked: int = 0
    links_checked: int = 0


def _extract_links(content: str) -> list[str]:
    """Extract link targets from markdown, skipping fenced code blocks."""
    targets: list[str] = []
    in_fence = False
    fence_char = ""
    fence_len = 0

    for line in content.splitlines():
        stripped = line.strip()
        fence_match = FENCE_PATTERN.match(stripped)

        if fence_match:
            char = fence_match.group(1)[0]
            length = len(fence_match.group(1))

            if not in_fence:
                in_fence = True
                fence_char = char
                fence_len = length
                continue
            elif char == fence_char and length >= fence_len and stripped == char * length:
                # Closing fence: same char, at least as long, nothing else on line
                in_fence = False
                continue

        if in_fence:
            continue

        # Remove inline code spans before extracting links
        line_without_code = INLINE_CODE_PATTERN.sub("", line)

        for match in LINK_PATTERN.finditer(line_without_code):
            target = match.group(1).strip()
            if target:
                targets.append(target)

    return targets


def _strip_target(target: str) -> str:
    """Strip fragment and query string from a link target."""
    # Strip query string first
    if "?" in target:
        target = target[: target.index("?")]
    # Strip fragment
    if "#" in target:
        target = target[: target.index("#")]
    return target


def _resolve_path(target: str, file_dir: str) -> str | None:
    """Resolve a link target to a path relative to the file's directory.

    Returns None if the target is external or empty after stripping.
    """
    if any(target.startswith(prefix) for prefix in EXTERNAL_PREFIXES):
        return None

    stripped = _strip_target(target)
    if not stripped:
        return None

    # Absolute paths resolve from root
    if stripped.startswith("/"):
        resolved = os.path.normpath(stripped.lstrip("/"))
    else:
        resolved = os.path.normpath(os.path.join(file_dir, stripped))

    # Check for path escape
    if resolved.startswith(".."):
        return resolved  # Will be reported as broken (escapes root)

    return resolved


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


def validate(root_dir: str) -> ValidateResult:
    """Validate internal links across a KB directory.

    Scans markdown files for links and checks that targets exist.

    Args:
        root_dir: The KB root directory.

    Returns:
        ValidateResult with violations, file count, and link count.
    """
    root = Path(root_dir).resolve()
    files = _get_content_files(root)
    all_violations: list[LinkViolation] = []
    total_links = 0

    for file in files:
        full_path = root / file
        try:
            content = full_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue

        file_dir = os.path.dirname(file)
        targets = _extract_links(content)

        for target in targets:
            resolved = _resolve_path(target, file_dir)
            if resolved is None:
                continue  # External or empty

            total_links += 1
            resolved_full = root / resolved

            # Check if target exists as file or directory
            if not resolved_full.exists():
                all_violations.append(
                    LinkViolation(
                        file=file,
                        target=target,
                        resolved=resolved,
                    )
                )

    return ValidateResult(
        violations=all_violations,
        files_checked=len(files),
        links_checked=total_links,
    )
