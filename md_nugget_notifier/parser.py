"""Markdown note parser and snippet extractor."""

import re
from pathlib import Path
from typing import Optional, Tuple


def strip_yaml_frontmatter(content: str) -> Tuple[Optional[dict], str]:
    """Extract simple YAML frontmatter and return (frontmatter_dict, remaining_content)."""
    frontmatter = {}
    pattern = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
    match = pattern.match(content)
    if not match:
        return None, content

    raw_yaml = match.group(1)
    body = content[match.end():]

    # Simple regex-based YAML key-value extractor (no external dependency needed)
    for line in raw_yaml.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line:
            key, val = line.split(":", 1)
            key = key.strip()
            val = val.strip().strip("\"'")
            frontmatter[key] = val

    return frontmatter, body


def is_metadata_or_noise_line(line: str) -> bool:
    """Detect if a line is metadata noise (loose key-value, dataview fields, or pure tag lists)."""
    stripped = line.strip()
    if not stripped:
        return False
    # Loose key: value pairs (e.g. topic: Kintsugi, created: 2023-07-06, tags: #japan)
    if re.match(r"^[A-Za-z0-9_\-\s]{1,30}:\s*", stripped):
        # Ensure it's not a normal sentence with a colon like "Note: this is important"
        # by checking if it looks like a typical metadata key
        key = stripped.split(":", 1)[0].strip().lower()
        common_keys = {
            "topic", "summary", "created", "updated", "date", "tags", "tag",
            "author", "status", "aliases", "alias", "type", "category", "source",
            "url", "link", "id", "rating", "modified", "title", "subject"
        }
        if key in common_keys or re.match(r"^[a-z0-9_\-]+$", key):
            return True
    # Dataview field: key:: value or [key:: value]
    if re.match(r"^\[?[A-Za-z0-9_\-]+::\s*", stripped):
        return True
    # Pure tag line: e.g. #japan #culture #art
    if re.match(r"^(#[A-Za-z0-9_\-\/]+\s*)+$", stripped):
        return True
    # Obsidian callout markers e.g. > [!NOTE] or > [!INFO]
    if re.match(r"^>\s*\[![A-Za-z0-9_\-]+\]", stripped):
        return True
    return False


def strip_leading_metadata(text: str) -> str:
    """Remove loose metadata lines and tag headers from the start of the note."""
    lines = text.splitlines()
    cleaned_lines = []
    in_leading_block = True

    for line in lines:
        stripped = line.strip()
        if in_leading_block:
            if not stripped:
                continue
            if is_metadata_or_noise_line(stripped):
                continue
            in_leading_block = False
        cleaned_lines.append(line)

    return "\n".join(cleaned_lines)


def extract_title_and_snippet(file_path: Path, max_length: int = 220) -> Tuple[str, str]:
    """Parse a markdown file and extract clean title and first relevant paragraph snippet."""
    try:
        raw_text = file_path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return file_path.stem, f"Could not read note: {e}"

    frontmatter, body = strip_yaml_frontmatter(raw_text)

    # Strip loose leading metadata / tags
    body = strip_leading_metadata(body)

    # 1. Title Resolution
    # Preference: frontmatter title -> first # Heading -> file stem
    title = None
    if frontmatter and "title" in frontmatter and frontmatter["title"]:
        title = frontmatter["title"]

    if not title:
        heading_match = re.search(r"^#\s+(.+)$", body, re.MULTILINE)
        if heading_match:
            title = heading_match.group(1).strip()
            # Remove title heading line from body
            body = body[:heading_match.start()] + body[heading_match.end():]

    if not title:
        title = file_path.stem

    # Clean markdown title formatting if any
    title = clean_markdown_inline(title)

    # 2. Body Cleaning
    clean_text = clean_markdown_body(body)

    # 3. First relevant paragraph extraction
    paragraphs = [p.strip() for p in clean_text.split("\n\n") if p.strip()]
    
    # Filter out empty or noise paragraphs
    meaningful_paragraphs = []
    for p in paragraphs:
        # If paragraph is just metadata or tags that appeared mid-note, skip
        lines = [l for l in p.splitlines() if not is_metadata_or_noise_line(l)]
        clean_p = " ".join(lines).strip()
        if len(clean_p) > 5:
            meaningful_paragraphs.append(clean_p)

    if not meaningful_paragraphs:
        snippet = "(Empty or metadata-only note)"
    else:
        # Take the first meaningful paragraph
        snippet = meaningful_paragraphs[0]
        snippet = re.sub(r"\s+", " ", snippet).strip()

        if len(snippet) > max_length:
            snippet = snippet[:max_length].rstrip() + "…"

    return title, snippet


def clean_markdown_inline(text: str) -> str:
    """Clean inline markdown formatting."""
    # Obsidian wikilinks: [[Page|Custom Name]] -> Custom Name, [[Page]] -> Page
    text = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]+)\]\]", r"\1", text)
    # Standard Markdown links: [Link text](url) -> Link text
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
    # Image links: ![alt](url) or ![[image.png]]
    text = re.sub(r"!\[\[.*?\]\]", "", text)
    text = re.sub(r"!\[.*?\]\(.*?\)", "", text)
    # Bold / Italics / Highlight / Strikethrough / Inline code
    text = re.sub(r"==(.*?)==", r"\1", text)
    text = re.sub(r"~~(.*?)~~", r"\1", text)
    text = re.sub(r"[*_]{1,3}(.*?)[*_]{1,3}", r"\1", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    return text.strip()


def clean_markdown_body(content: str) -> str:
    """Clean full markdown content into plain text suitable for notifications."""
    # Remove HTML comments
    text = re.sub(r"<!--.*?-->", "", content, flags=re.DOTALL)
    # Remove code blocks
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    # Remove math blocks $$ ... $$
    text = re.sub(r"\$\$.*?\$\$", "", text, flags=re.DOTALL)
    # Remove images
    text = re.sub(r"!\[\[.*?\]\]", "", text)
    text = re.sub(r"!\[.*?\]\(.*?\)", "", text)
    # Remove HTML tags
    text = re.sub(r"<[^>]+>", "", text)
    # Clean inline markdown
    text = clean_markdown_inline(text)
    # Remove headers marker (#, ##, etc.)
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    # Remove blockquotes >
    text = re.sub(r"^\s*>\s?", "", text, flags=re.MULTILINE)
    # Remove list bullet markers (- [ ], - [x], *, -, +, 1.)
    text = re.sub(r"^\s*[-*+]\s+\[[ xX]\]\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*[-*+]\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*\d+\.\s+", "", text, flags=re.MULTILINE)
    # Remove horizontal rules
    text = re.sub(r"^[-*_]{3,}\s*$", "", text, flags=re.MULTILINE)

    # Normalize multiple line breaks
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
