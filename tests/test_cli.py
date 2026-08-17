"""Unit tests for the CLI interface."""

import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from md_nugget_notifier.cli import main


class TestCLI(unittest.TestCase):
    def test_cli_preview(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            note = Path(tmpdir) / "test.md"
            note.write_text("# My Great Idea\n\nThis is a test snippet.", encoding="utf-8")

            test_args = ["md-nugget-notifier", "--dir", tmpdir, "--preview"]
            with patch.object(sys, "argv", test_args):
                with patch("sys.stdout", new=io.StringIO()) as fake_out:
                    code = main()
                    self.assertEqual(code, 0)
                    out = fake_out.getvalue()
                    self.assertIn("💡 Title:   My Great Idea", out)
                    self.assertIn("📝 Snippet: This is a test snippet.", out)

    def test_cli_json_output(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            note = Path(tmpdir) / "data.md"
            note.write_text("Plain note content.", encoding="utf-8")

            test_args = ["md-nugget-notifier", "--dir", tmpdir, "--json"]
            with patch.object(sys, "argv", test_args):
                with patch("sys.stdout", new=io.StringIO()) as fake_out:
                    code = main()
                    self.assertEqual(code, 0)
                    data = json.loads(fake_out.getvalue())
                    self.assertEqual(data["title"], "data")
                    self.assertEqual(data["snippet"], "Plain note content.")

    def test_cli_nonexistent_directory(self):
        test_args = ["md-nugget-notifier", "--dir", "/path/to/nonexistent/folder/12345"]
        with patch.object(sys, "argv", test_args):
            with patch("sys.stderr", new=io.StringIO()):
                code = main()
                self.assertEqual(code, 1)

    def test_cli_empty_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_args = ["md-nugget-notifier", "--dir", tmpdir]
            with patch.object(sys, "argv", test_args):
                with patch("sys.stderr", new=io.StringIO()):
                    code = main()
                    self.assertEqual(code, 1)

    @patch("md_nugget_notifier.cli.send_notification")
    def test_cli_send_notification(self, mock_notify):
        with tempfile.TemporaryDirectory() as tmpdir:
            note = Path(tmpdir) / "note.md"
            note.write_text("Some content", encoding="utf-8")

            test_args = ["md-nugget-notifier", "--dir", tmpdir]
            with patch.object(sys, "argv", test_args):
                with patch("sys.stdout", new=io.StringIO()):
                    code = main()
                    self.assertEqual(code, 0)
                    mock_notify.assert_called_once()

    @patch("md_nugget_notifier.cli.show_alert")
    def test_cli_alert_mode(self, mock_alert):
        with tempfile.TemporaryDirectory() as tmpdir:
            note = Path(tmpdir) / "note.md"
            note.write_text("Some content", encoding="utf-8")

            test_args = ["md-nugget-notifier", "--dir", tmpdir, "--alert"]
            with patch.object(sys, "argv", test_args):
                with patch("sys.stdout", new=io.StringIO()):
                    code = main()
                    self.assertEqual(code, 0)
                    mock_alert.assert_called_once()

    @patch("md_nugget_notifier.cli.open_note")
    @patch("md_nugget_notifier.cli.send_notification")
    def test_cli_open_flag(self, mock_notify, mock_open):
        with tempfile.TemporaryDirectory() as tmpdir:
            note = Path(tmpdir) / "note.md"
            note.write_text("Some content", encoding="utf-8")

            test_args = ["md-nugget-notifier", "--dir", tmpdir, "--open"]
            with patch.object(sys, "argv", test_args):
                with patch("sys.stdout", new=io.StringIO()):
                    code = main()
                    self.assertEqual(code, 0)
                    mock_open.assert_called_once()


if __name__ == "__main__":
    unittest.main()
