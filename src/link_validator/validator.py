# spec: specs/link-validator.md
# spec-section: Behavior/Link extraction

"""Core validation logic for detecting broken internal markdown links."""

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import unquote

# Matches [text](target) and ![alt](target)
LINK_PATTERN = re.compile(r"!?\[(?:[^\]]*)\]\(([^)]*)\)")

# Matches opening/closing code fences
FENCE_PATTERN = re.compile(r"^(`{3,}|~{3,})")

# Matches inline code spans (backtick-wrapped)
INLINE_CODE_PATTERN = re.compile(r"(`+)(.+?)\1")

# HTML comments: links inside one are not rendered, so they are not checked.
COMMENT_OPEN = "<!--"
COMMENT_CLOSE = "-->"

SKIP_DIRS = frozenset({".git", ".graft", ".venv", "node_modules", "__pycache__"})

CONTENT_DIRS = ("docs", "policies", "playbooks", "notes", "specs")

# A target that begins with a URI scheme (RFC 3986 section 3.1: a letter, then
# letters, digits, "+", "-" or ".", then ":") is external: http:, mailto:,
# airmail:, tel:, file:, data:, app: and so on. A relative path cannot match
# because "/", "?" and "#" are not scheme characters, so the colon must come
# before any of them.
URI_SCHEME_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9+.\-]*:")


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


def _strip_comments(line: str, in_comment: bool) -> tuple[str, bool]:
    """Remove the parts of a line inside HTML comments, which may span lines.

    Returns the visible text and whether a comment is still open at the end.
    """
    visible = ""
    rest = line
    while rest:
        if in_comment:
            end = rest.find(COMMENT_CLOSE)
            if end == -1:
                return visible, True
            rest = rest[end + len(COMMENT_CLOSE):]
            in_comment = False
        else:
            start = rest.find(COMMENT_OPEN)
            if start == -1:
                return visible + rest, False
            visible += rest[:start]
            rest = rest[start + len(COMMENT_OPEN):]
            in_comment = True
    return visible, in_comment


def _extract_links(content: str) -> list[str]:
    """Extract link targets from markdown, skipping fenced code blocks and HTML comments."""
    targets: list[str] = []
    in_fence = False
    in_comment = False
    fence_char = ""
    fence_len = 0

    for line in content.splitlines():
        # Inside an HTML comment nothing counts, fences included, until it closes.
        if in_comment:
            line, in_comment = _strip_comments(line, True)
            if in_comment:
                continue

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

        # Replace inline code spans with a neutral placeholder before extracting
        # links: a link written inside a code span disappears, but a code span
        # used as link text ([`name`](path)) leaves a matchable [code](path).
        # Code spans go first, so a `<!--` written inside one doesn't open a comment.
        line_without_code = INLINE_CODE_PATTERN.sub("code", line)
        visible, in_comment = _strip_comments(line_without_code, False)

        for match in LINK_PATTERN.finditer(visible):
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
    # CommonMark angle-bracket destination: [text](<Name with spaces.md>)
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1].strip()

    if URI_SCHEME_PATTERN.match(target):
        return None

    # Decode percent-encoding (%20, %2C) as CommonMark and Obsidian do
    stripped = unquote(_strip_target(target))
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
