"""Unit tests for the file opener logic."""

import unittest
from pathlib import Path
from unittest.mock import patch

from md_nugget_notifier.opener import open_note


class TestOpener(unittest.TestCase):
    @patch("subprocess.Popen")
    def test_open_with_app(self, mock_popen):
        file_path = Path("/tmp/notes/idea.md")
        res = open_note(file_path, opener="app:Visual Studio Code")
        self.assertTrue(res)
        mock_popen.assert_called_once()

    @patch("subprocess.Popen")
    def test_open_with_cmd(self, mock_popen):
        file_path = Path("/tmp/notes/idea.md")
        res = open_note(file_path, opener="cmd:code {path}")
        self.assertTrue(res)
        mock_popen.assert_called_once()


if __name__ == "__main__":
    unittest.main()
