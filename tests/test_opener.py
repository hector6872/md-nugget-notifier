"""Unit tests for the file opener logic."""

import os
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from md_nugget_notifier.opener import (
    _open_via_obsidian_uri,
    _open_with_system_default,
    open_note,
)


@patch("md_nugget_notifier.opener.platform.system", return_value="Darwin")
class TestOpener(unittest.TestCase):
    @patch("md_nugget_notifier.opener.subprocess.Popen")
    def test_open_with_app(self, mock_popen, mock_sys):
        file_path = Path("/tmp/notes/idea.md")
        res = open_note(file_path, opener="app:Visual Studio Code")
        self.assertTrue(res)
        mock_popen.assert_called_once()

    @patch("md_nugget_notifier.opener.subprocess.Popen")
    def test_open_with_cmd(self, mock_popen, mock_sys):
        file_path = Path("/tmp/notes/idea.md")
        res = open_note(file_path, opener="cmd:code {path}")
        self.assertTrue(res)
        mock_popen.assert_called_once()

    @patch.dict(os.environ, {"EDITOR": "vim"})
    @patch("md_nugget_notifier.opener.subprocess.Popen")
    def test_open_with_editor(self, mock_popen, mock_sys):
        file_path = Path("/tmp/notes/idea.md")
        res = open_note(file_path, opener="editor")
        self.assertTrue(res)
        mock_popen.assert_called_once_with(["vim", str(file_path.resolve())])

    @patch("md_nugget_notifier.opener.subprocess.Popen")
    def test_open_obsidian_uri_macos(self, mock_popen, mock_sys):
        vault = Path("/tmp/MyVault")
        note = vault / "Folder" / "My Note.md"
        res = _open_via_obsidian_uri(note, vault_root=vault)
        self.assertTrue(res)
        mock_popen.assert_called_once()
        call_args = mock_popen.call_args[0][0]
        self.assertEqual(call_args[0], "open")
        self.assertIn("obsidian://open?vault=MyVault&file=Folder/My%20Note.md", call_args[1])

    @patch("md_nugget_notifier.opener.subprocess.Popen")
    def test_open_system_default_macos(self, mock_popen, mock_sys):
        file_path = Path("/tmp/note.md")
        res = _open_with_system_default(file_path, system="Darwin")
        self.assertTrue(res)
        mock_popen.assert_called_once_with(["open", str(file_path)])

    @patch("md_nugget_notifier.opener.subprocess.Popen")
    def test_open_system_default_linux(self, mock_popen, mock_sys):
        file_path = Path("/tmp/note.md")
        res = _open_with_system_default(file_path, system="Linux")
        self.assertTrue(res)
        mock_popen.assert_called_once_with(["xdg-open", str(file_path)])


if __name__ == "__main__":
    unittest.main()
