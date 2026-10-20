"""Unit tests for the CLI interface."""

import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import md_nugget_notifier.cli
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

    @patch("md_nugget_notifier.cli.send_notification")
    def test_cli_length_flag(self, mock_notify):
        with tempfile.TemporaryDirectory() as tmpdir:
            note = Path(tmpdir) / "note.md"
            note.write_text("A" * 300, encoding="utf-8")

            test_args = [
                "md-nugget-notifier",
                "--dir", tmpdir,
                "--length", "50",
            ]
            with patch.object(sys, "argv", test_args):
                with patch("sys.stdout", new=io.StringIO()):
                    code = main()
                    self.assertEqual(code, 0)
                    mock_notify.assert_called_once()
                    kwargs = mock_notify.call_args[1]
                    # Check snippet length truncated to ~50 + ellipsis
                    self.assertTrue(len(kwargs.get("message")) <= 55)

    @patch("md_nugget_notifier.cli.pick_random_note")
    def test_cli_no_recursive_flag(self, mock_pick):
        mock_pick.return_value = None
        with tempfile.TemporaryDirectory() as tmpdir:
            test_args = ["md-nugget-notifier", "--dir", tmpdir, "--no-recursive"]
            with patch.object(sys, "argv", test_args):
                with patch("sys.stderr", new=io.StringIO()):
                    main()
                    mock_pick.assert_called_once()
                    self.assertFalse(mock_pick.call_args[1].get("recursive"))

    @patch("md_nugget_notifier.cli.pick_random_note")
    @patch("md_nugget_notifier.cli.trigger_background_download")
    @patch("md_nugget_notifier.cli.send_notification")
    def test_cli_retries_on_resource_deadlock(self, mock_notify, mock_trigger, mock_pick):
        with tempfile.TemporaryDirectory() as tmpdir:
            note1 = Path(tmpdir) / "deadlocked.md"
            note1.write_text("dummy", encoding="utf-8")
            note2 = Path(tmpdir) / "healthy.md"
            note2.write_text("Hello healthy world", encoding="utf-8")

            mock_pick.side_effect = [note1, note2]

            original_extract = md_nugget_notifier.cli.extract_title_and_snippet

            def mock_extract(path, max_length=220):
                if path.name == "deadlocked.md":
                    raise OSError(11, "Resource deadlock avoided")
                return original_extract(path, max_length=max_length)

            with patch("md_nugget_notifier.cli.extract_title_and_snippet", side_effect=mock_extract):
                test_args = ["md-nugget-notifier", "--dir", tmpdir]
                with patch.object(sys, "argv", test_args):
                    with patch("sys.stdout", new=io.StringIO()):
                        code = main()
                        self.assertEqual(code, 0)
                        mock_notify.assert_called_once()
                        self.assertEqual(mock_notify.call_args[1]["title"], "healthy")
                        mock_trigger.assert_called_once_with(note1)

    @patch("md_nugget_notifier.cli.extract_title_and_snippet")
    def test_cli_all_notes_deadlocked_error_message(self, mock_extract):
        mock_extract.side_effect = OSError(11, "Resource deadlock avoided")
        with tempfile.TemporaryDirectory() as tmpdir:
            note = Path(tmpdir) / "offline.md"
            note.write_text("dummy", encoding="utf-8")

            test_args = ["md-nugget-notifier", "--dir", tmpdir]
            with patch.object(sys, "argv", test_args):
                with patch("sys.stderr", new=io.StringIO()) as fake_err:
                    code = main()
                    self.assertEqual(code, 1)
                    err_out = fake_err.getvalue()
                    self.assertIn("Resource deadlock avoided", err_out)
                    self.assertIn("Make available offline", err_out)


if __name__ == "__main__":
    unittest.main()
