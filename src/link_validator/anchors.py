# spec: specs/link-validator.md
# spec-section: Behavior/Anchors

"""The fragments a markdown file answers to: heading slugs, heading text, block ids, HTML ids."""

import re
from functools import cache
from pathlib import Path

from tool_cli.okf import split_frontmatter

ATX_HEADING = re.compile(r"^ {0,3}(#{1,6})(?:[ \t]+(.*?))?(?:[ \t]+#+)?[ \t]*$")
SETEXT_UNDERLINE = re.compile(r"^ {0,3}(=+|-+)[ \t]*$")
FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
BLOCK_ID = re.compile(r"(?:^|\s)\^([A-Za-z0-9-]+)[ \t]*$")
HTML_ID = re.compile(r"""<[A-Za-z][^>]*?\s(?:id|name)\s*=\s*["']([^"']+)["']""")
MARKDOWN_LINK = re.compile(r"!?\[([^\]]*)\]\([^)]*\)")
GITHUB_DROP = re.compile(r"[^\w\- ]")
NON_WORD_RUN = re.compile(r"[^\w]+")
OBSIDIAN_DROP = re.compile(r"[\[\]#|^:\\]")


def github_slug(text: str) -> str:
    """GitHub's heading id: plain text, lower case, punctuation dropped, spaces to hyphens."""
    plain = MARKDOWN_LINK.sub(r"\1", text)
    plain = re.sub(r"[`*~]", "", plain)  # emphasis and code marks; "_" stays, as in snake_case
    return GITHUB_DROP.sub("", plain.strip().lower()).replace(" ", "-")


def dashed_slug(text: str) -> str:
    """The slug some renderers write instead: every run of punctuation and space becomes one "-"."""
    plain = re.sub(r"[`*~]", "", MARKDOWN_LINK.sub(r"\1", text))
    return NON_WORD_RUN.sub("-", plain.strip().lower()).strip("-")


def _obsidian_key(text: str) -> str:
    """Heading text as Obsidian compares it in a link: link syntax and spacing ignored, any case."""
    return " ".join(OBSIDIAN_DROP.sub(" ", text).split()).lower()


@cache
def _anchors(path: Path, mtime_ns: int) -> tuple[frozenset[str], frozenset[str], frozenset[str]]:
    """(GitHub slugs, Obsidian heading keys, block and HTML ids) of a markdown file."""
    del mtime_ns  # part of the cache key only
    try:
        content = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return frozenset(), frozenset(), frozenset()
    _, body = split_frontmatter(content)

    headings: list[str] = []
    ids: set[str] = set()
    fence = ""  # the open fence's marker; a closing fence repeats its character, at least as long
    previous = ""
    for line in body.splitlines():
        marker = FENCE.match(line)
        if fence:
            closes = marker and line.strip() == marker.group(1)
            if closes and marker.group(1)[0] == fence[0] and len(marker.group(1)) >= len(fence):
                fence = ""
            continue
        if marker:
            fence = marker.group(1)
            previous = ""
            continue
        atx = ATX_HEADING.match(line)
        if atx:
            headings.append(atx.group(2) or "")
            previous = ""
            continue
        if (
            previous.strip()
            and SETEXT_UNDERLINE.match(line)
            and not previous.startswith(("-", "*", ">"))
        ):
            headings.append(previous.strip())
            previous = ""
            continue
        block = BLOCK_ID.search(line)
        if block:
            ids.add("^" + block.group(1))
        ids.update(HTML_ID.findall(line))
        previous = line

    slugs: set[str] = set()
    seen: dict[str, int] = {}
    for heading in headings:
        slug = github_slug(heading)
        count = seen.get(slug, 0)
        seen[slug] = count + 1
        slugs.add(slug if count == 0 else f"{slug}-{count}")
    slugs.update(dashed_slug(h) for h in headings)
    keys = frozenset(_obsidian_key(h) for h in headings)
    return frozenset(slugs), keys, frozenset(ids)


def has_anchor(path: Path, fragment: str) -> bool:
    """True if the file answers to the (decoded) fragment.

    Accepted: a GitHub heading slug (any case), Obsidian heading text (`Heading text`, or nested
    `Parent#Child`, matched on the last part), an Obsidian block id (`^id`), or an HTML id/name.
    """
    try:
        mtime = path.stat().st_mtime_ns
    except OSError:
        return False
    slugs, keys, ids = _anchors(path, mtime)
    if fragment in ids:
        return True
    if fragment.lower() in slugs:
        return True
    last = fragment.split("#")[-1]
    return _obsidian_key(last) in keys or github_slug(last) in slugs
