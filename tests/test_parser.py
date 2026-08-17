"""Unit tests for the markdown parser and snippet extractor."""

import tempfile
import unittest
from pathlib import Path

from md_nugget_notifier.parser import (
    clean_markdown_body,
    clean_markdown_inline,
    extract_title_and_snippet,
    strip_yaml_frontmatter,
)


class TestMarkdownParser(unittest.TestCase):
    def test_strip_yaml_frontmatter(self):
        content = "---\ntitle: My Custom Title\ntags: [idea, notes]\n---\n\n# Body Heading\nThis is body content."
        fm, body = strip_yaml_frontmatter(content)
        self.assertIsNotNone(fm)
        self.assertEqual(fm.get("title"), "My Custom Title")
        self.assertIn("# Body Heading", body)

    def test_clean_inline_markdown(self):
        text = "This has [[WikiLink|Custom Label]] and [[BareWikiLink]] and [web link](https://example.com) and **bold** and *italic* and ==highlighted== text."
        cleaned = clean_markdown_inline(text)
        self.assertEqual(
            cleaned,
            "This has Custom Label and BareWikiLink and web link and bold and italic and highlighted text.",
        )

    def test_clean_markdown_body(self):
        md = """# Main Header
## Subheader
> A quoted block of wisdom.

- [x] Done item
- [ ] Todo item
* Another bullet

```python
def code_snippet():
    return 42
```

Here is a paragraph with **important** thoughts."""

        cleaned = clean_markdown_body(md)
        self.assertNotIn("```", cleaned)
        self.assertNotIn("def code_snippet", cleaned)
        self.assertNotIn("- [x]", cleaned)
        self.assertIn("A quoted block of wisdom.", cleaned)
        self.assertIn("Here is a paragraph with important thoughts.", cleaned)

    def test_extract_title_and_snippet_from_heading(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test_note.md"
            file_path.write_text(
                "# Deep Learning Reflections\n\nNeural networks improve with proper regularisation and scaling.",
                encoding="utf-8",
            )
            title, snippet = extract_title_and_snippet(file_path)
            self.assertEqual(title, "Deep Learning Reflections")
            self.assertEqual(
                snippet,
                "Neural networks improve with proper regularisation and scaling.",
            )

    def test_extract_title_from_stem_when_no_heading(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "Random Idea.md"
            file_path.write_text("Just some text without any header.", encoding="utf-8")
            title, snippet = extract_title_and_snippet(file_path)
            self.assertEqual(title, "Random Idea")
            self.assertEqual(snippet, "Just some text without any header.")

    def test_metadata_noise_filtering(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "kintsugi.md"
            content = """topic: Kintsugi
summary: 
created: 2023-07-06 18:15
tags: #japan #culture

# Kintsugi Philosophy
Kintsugi is the Japanese art of repairing broken pottery with golden lacquer.

Second paragraph with more reflections.
"""
            file_path.write_text(content, encoding="utf-8")
            title, snippet = extract_title_and_snippet(file_path)
            self.assertEqual(title, "Kintsugi Philosophy")
            self.assertEqual(
                snippet,
                "Kintsugi is the Japanese art of repairing broken pottery with golden lacquer.",
            )


if __name__ == "__main__":
    unittest.main()
