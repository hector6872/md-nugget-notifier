"""Unit tests for vault scanning and random note selection."""

import tempfile
import unittest
from pathlib import Path

from md_nugget_notifier.vault import find_all_markdown_notes, pick_random_note


class TestVaultScanner(unittest.TestCase):
    def test_find_all_notes_filtering(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            # Create valid notes
            (root / "note1.md").write_text("Hello note 1", encoding="utf-8")
            sub = root / "Subfolder"
            sub.mkdir()
            (sub / "note2.md").write_text("Hello note 2", encoding="utf-8")

            # Create ignored folders
            obsidian_dir = root / ".obsidian"
            obsidian_dir.mkdir()
            (obsidian_dir / "workspace.md").write_text("Config", encoding="utf-8")

            git_dir = root / ".git"
            git_dir.mkdir()
            (git_dir / "COMMIT_EDITMSG.md").write_text("git msg", encoding="utf-8")

            # Non-md file
            (root / "image.png").write_text("fake image", encoding="utf-8")

            notes = find_all_markdown_notes(root)
            note_names = {n.name for n in notes}
            self.assertEqual(note_names, {"note1.md", "note2.md"})

    def test_pick_random_note(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "my_thought.md").write_text("An inspiring nugget", encoding="utf-8")
            chosen = pick_random_note(root)
            self.assertIsNotNone(chosen)
            self.assertEqual(chosen.name, "my_thought.md")

    def test_non_recursive_scanning(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "root_note.md").write_text("Root note", encoding="utf-8")
            sub = root / "Subfolder"
            sub.mkdir()
            (sub / "nested_note.md").write_text("Nested note", encoding="utf-8")

            # Recursive (default)
            notes_rec = find_all_markdown_notes(root, recursive=True)
            self.assertEqual({n.name for n in notes_rec}, {"root_note.md", "nested_note.md"})

            # Non-recursive
            notes_flat = find_all_markdown_notes(root, recursive=False)
            self.assertEqual({n.name for n in notes_flat}, {"root_note.md"})

    def test_empty_vault(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            chosen = pick_random_note(root)
            self.assertIsNone(chosen)


if __name__ == "__main__":
    unittest.main()
