"""Native cross-platform desktop notification dispatcher."""

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional


def send_notification(
    title: str,
    message: str,
    file_path: Optional[Path] = None,
    opener: Optional[str] = None,
    vault_root: Optional[Path] = None,
    icon: Optional[str] = None,
) -> bool:
    """Send a native OS notification.

    On macOS, if terminal-notifier is installed, click actions can trigger opening the file.
    Otherwise falls back to AppleScript osascript display notification or platform defaults.
    """
    system = platform.system()

    if system == "Darwin":
        return _send_macos_notification(title, message, file_path, opener, vault_root, icon)
    elif system == "Linux":
        return _send_linux_notification(title, message, icon)
    elif system == "Windows":
        return _send_windows_notification(title, message)
    else:
        return _send_fallback_notification(title, message)


def show_alert(
    title: str,
    message: str,
    file_path: Optional[Path] = None,
    opener: Optional[str] = None,
    vault_root: Optional[Path] = None,
    icon: Optional[str] = None,
) -> bool:
    """Display an interactive modal alert/dialog window across macOS, Linux, and Windows.
    
    The window stays pinned on screen until the user dismisses it or clicks 'Abrir' / 'Open'.
    """
    system = platform.system()

    if system == "Darwin":
        clean_title = title.replace('"', '\\"')
        clean_msg = message.replace('"', '\\"')
        if file_path:
            script = f'''
            set theAlert to display alert "💡 {clean_title}" message "{clean_msg}" buttons {{"Cerrar", "Abrir Nota"}} default button "Abrir Nota"
            return button returned of theAlert
            '''
        else:
            script = f'display alert "💡 {clean_title}" message "{clean_msg}" as informational'

        try:
            res = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
            if file_path and "Abrir Nota" in res.stdout:
                from .opener import open_note
                open_note(file_path, opener=opener, vault_root=vault_root)
            return res.returncode == 0
        except Exception:
            pass

    elif system == "Linux":
        # 1. Try zenity (GNOME / standard desktop)
        if shutil.which("zenity"):
            try:
                cmd = ["zenity", "--info", f"--title=💡 {title}", f"--text={message}", "--width=350"]
                if icon:
                    cmd.append(f"--window-icon={icon}")
                res = subprocess.run(cmd, capture_output=True, text=True)
                return res.returncode == 0
            except Exception:
                pass
        # 2. Try kdialog (KDE)
        if shutil.which("kdialog"):
            try:
                cmd = ["kdialog", "--msgbox", message, f"--title=💡 {title}"]
                if icon:
                    cmd.extend(["--icon", icon])
                res = subprocess.run(cmd, capture_output=True, text=True)
                return res.returncode == 0
            except Exception:
                pass

    elif system == "Windows":
        # PowerShell WinForms message box
        ps_cmd = f"""
        Add-Type -AssemblyName System.Windows.Forms
        [System.Windows.Forms.MessageBox]::Show('{message.replace("'", "''")}', '💡 {title.replace("'", "''")}', [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Information)
        """
        try:
            res = subprocess.run(["powershell", "-Command", ps_cmd], capture_output=True, text=True)
            if res.returncode == 0:
                return True
        except Exception:
            pass

    # Universal Python tkinter fallback
    try:
        import tkinter as tk
        from tkinter import messagebox

        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        messagebox.showinfo(f"💡 {title}", message)
        root.destroy()
        return True
    except Exception:
        print(f"\n================ 💡 {title} ================\n{message}\n==================================================")
        return False


def _send_macos_notification(
    title: str,
    message: str,
    file_path: Optional[Path] = None,
    opener: Optional[str] = None,
    vault_root: Optional[Path] = None,
    icon: Optional[str] = None,
) -> bool:
    """Send notification on macOS."""
    clean_title = title.replace('"', '\\"')
    clean_msg = message.replace('"', '\\"')

    # If terminal-notifier is available and we have a target file, attach direct click action
    if shutil.which("terminal-notifier") and file_path:
        args = [
            "terminal-notifier",
            "-title", title,
            "-message", message,
            "-group", "md-nugget-notifier",
            "-sound", "default",
        ]

        # Handle Icon
        if icon:
            icon_lower = icon.lower()
            if icon_lower in ("obsidian", "md.obsidian"):
                args.extend(["-sender", "md.obsidian"])
            elif icon_lower in ("notes", "apple-notes", "apple_notes"):
                args.extend(["-sender", "com.apple.Notes"])
            elif icon_lower in ("textedit", "text-edit"):
                args.extend(["-sender", "com.apple.TextEdit"])
            else:
                icon_path = Path(os.path.expanduser(icon)).resolve()
                if icon_path.exists():
                    args.extend(["-contentImage", str(icon_path)])
                else:
                    args.extend(["-sender", icon])
        elif opener in ("obsidian_uri", "obsidian"):
            args.extend(["-sender", "md.obsidian"])
        else:
            # Default to macOS TextEdit (notes) icon instead of black terminal icon
            args.extend(["-sender", "com.apple.TextEdit"])

        # Handle Click Action
        if opener in ("obsidian_uri", "obsidian"):
            import urllib.parse
            vault_name = vault_root.name if vault_root else file_path.parent.name
            try:
                rel = file_path.relative_to(vault_root) if vault_root else file_path
                param = rel.as_posix()
            except ValueError:
                param = file_path.name
            uri = f"obsidian://open?vault={urllib.parse.quote(vault_name)}&file={urllib.parse.quote(param)}"
            args.extend(["-open", uri])
        elif opener and opener.startswith("app:"):
            app_name = opener[4:].strip()
            args.extend(["-execute", f'open -a "{app_name}" "{file_path.resolve()}"'])
        elif opener and opener.startswith("cmd:"):
            cmd_template = opener[4:].strip()
            cmd_str = cmd_template.replace("{path}", str(file_path.resolve()))
            args.extend(["-execute", cmd_str])
        else:
            # Default system open
            args.extend(["-open", f"file://{file_path.resolve()}"])

        try:
            # Launch detached/non-blocking so it posts notification without blocking the CLI
            subprocess.Popen(
                args,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            return True
        except Exception:
            pass

    # Built-in AppleScript notification with sound
    script = f'display notification "{clean_msg}" with title "💡 {clean_title}" sound name "default"'
    try:
        res = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
        if res.returncode != 0 and res.stderr:
            print(f"Warning (osascript): {res.stderr.strip()}", file=sys.stderr)
        return res.returncode == 0
    except Exception as e:
        print(f"Error displaying macOS notification: {e}", file=sys.stderr)
        return False


def _send_linux_notification(title: str, message: str, icon: Optional[str] = None) -> bool:
    """Send notification using notify-send on Linux."""
    if shutil.which("notify-send"):
        try:
            icon_arg = icon or "dialog-information"
            res = subprocess.run(
                ["notify-send", f"💡 {title}", message, "-i", icon_arg],
                capture_output=True,
                text=True,
            )
            return res.returncode == 0
        except Exception:
            pass
    return _send_fallback_notification(title, message)


def _send_windows_notification(title: str, message: str) -> bool:
    """Send notification on Windows using PowerShell toast."""
    ps_script = f"""
    [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
    [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null
    $template = @"
    <toast>
        <visual>
            <binding template="ToastText02">
                <text id="1">💡 {title}</text>
                <text id="2">{message}</text>
            </binding>
        </visual>
    </toast>
"@
    $xml = New-Object Windows.Data.Xml.Dom.XmlDocument
    $xml.LoadXml($template)
    $toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
    [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("Markdown Notifier").Show($toast)
    """
    try:
        res = subprocess.run(["powershell", "-Command", ps_script], capture_output=True, text=True)
        if res.returncode == 0:
            return True
    except Exception:
        pass
    return _send_fallback_notification(title, message)


def _send_fallback_notification(title: str, message: str) -> bool:
    """Try plyer if installed, or print to console."""
    try:
        from plyer import notification
        notification.notify(
            title=f"💡 {title}",
            message=message,
            app_name="Markdown Notifier",
            timeout=10,
        )
        return True
    except Exception:
        # If no notification system is available, output to console
        print(f"[NOTIFICATION] 💡 {title}\n{message}")
        return False
