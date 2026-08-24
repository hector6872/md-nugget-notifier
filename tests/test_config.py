"""Unit tests for configuration loading."""

import json
import tempfile
import unittest
from pathlib import Path

from md_nugget_notifier.config import AppConfig, get_default_config_paths, load_config


class TestConfig(unittest.TestCase):
    def test_default_config(self):
        cfg = AppConfig()
        self.assertTrue(cfg.recursive)
        self.assertEqual(cfg.opener, "system")
        self.assertEqual(cfg.max_snippet_length, 220)
        self.assertEqual(cfg.min_size_bytes, 1)

    def test_load_config_from_custom_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "custom_config.json"
            data = {
                "notes_dir": tmpdir,
                "opener": "app:Obsidian",
                "ignored_dirs": ["archive", "temp"],
                "max_snippet_length": 150,
                "min_size_bytes": 5,
                "recursive": False,
            }
            config_file.write_text(json.dumps(data), encoding="utf-8")

            cfg = load_config(config_file)
            self.assertEqual(cfg.notes_dir, Path(tmpdir).resolve())
            self.assertEqual(cfg.opener, "app:Obsidian")
            self.assertEqual(cfg.ignored_dirs, ["archive", "temp"])
            self.assertEqual(cfg.max_snippet_length, 150)
            self.assertEqual(cfg.min_size_bytes, 5)
            self.assertFalse(cfg.recursive)

    def test_load_config_with_vault_path_key(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.json"
            data = {"vault_path": tmpdir}
            config_file.write_text(json.dumps(data), encoding="utf-8")

            cfg = load_config(config_file)
            self.assertEqual(cfg.notes_dir, Path(tmpdir).resolve())

    def test_get_default_config_paths(self):
        paths = get_default_config_paths()
        self.assertTrue(len(paths) >= 2)
        self.assertTrue(any(p.name == "config.json" for p in paths))


if __name__ == "__main__":
    unittest.main()
