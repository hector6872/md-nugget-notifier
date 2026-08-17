"""Unit tests for notification and alert dispatchers."""

import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from md_nugget_notifier.notifier import (
    _send_linux_notification,
    _send_macos_notification,
    _send_windows_notification,
    send_notification,
    show_alert,
)


class TestNotifier(unittest.TestCase):
    @patch("shutil.which", return_value=None)
    @patch("subprocess.run")
    def test_macos_notification_osascript(self, mock_run, mock_which):
        mock_run.return_value = MagicMock(returncode=0)
        res = _send_macos_notification("My Title", "My Message")
        self.assertTrue(res)
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        self.assertEqual(args[0], "osascript")
        self.assertIn("display notification", args[2])

    @patch("shutil.which", return_value="/usr/local/bin/terminal-notifier")
    @patch("subprocess.run")
    def test_macos_notification_terminal_notifier(self, mock_run, mock_which):
        mock_run.return_value = MagicMock(returncode=0)
        res = _send_macos_notification(
            "My Title",
            "My Message",
            file_path=Path("/tmp/note.md"),
            opener="system",
        )
        self.assertTrue(res)
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        self.assertEqual(args[0], "terminal-notifier")

    @patch("shutil.which", return_value="/usr/bin/notify-send")
    @patch("subprocess.run")
    def test_linux_notification_notify_send(self, mock_run, mock_which):
        mock_run.return_value = MagicMock(returncode=0)
        res = _send_linux_notification("Linux Title", "Linux Message")
        self.assertTrue(res)
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        self.assertEqual(args[0], "notify-send")

    @patch("subprocess.run")
    def test_windows_notification_powershell(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        res = _send_windows_notification("Windows Title", "Windows Message")
        self.assertTrue(res)
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        self.assertEqual(args[0], "powershell")

    @patch("platform.system", return_value="Darwin")
    @patch("subprocess.run")
    def test_show_alert_macos(self, mock_run, mock_sys):
        mock_run.return_value = MagicMock(returncode=0)
        res = show_alert("Alert Title", "Alert Message")
        self.assertTrue(res)
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        self.assertEqual(args[0], "osascript")
        self.assertIn("display alert", args[2])

    @patch("platform.system", return_value="Linux")
    @patch("shutil.which", side_effect=lambda bin_name: "/usr/bin/zenity" if bin_name == "zenity" else None)
    @patch("subprocess.run")
    def test_show_alert_linux_zenity(self, mock_run, mock_which, mock_sys):
        mock_run.return_value = MagicMock(returncode=0)
        res = show_alert("Alert Title", "Alert Message")
        self.assertTrue(res)
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        self.assertEqual(args[0], "zenity")


if __name__ == "__main__":
    unittest.main()
