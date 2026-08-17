"""Configurable file opener handling system defaults, custom apps, shell commands, or Obsidian URI."""

import os
import platform
import shlex
import subprocess
import urllib.parse
from pathlib import Path
from typing import Optional


def open_note(
    file_path: Path,
    opener: Optional[str] = None,
    vault_root: Optional[Path] = None,
) -> bool:
    """Open a markdown file using the configured opener strategy.

    Supported opener formats:
    - None / "default" / "system": Use OS default file handler.
    - "obsidian_uri" / "obsidian": Open via obsidian://open?vault=...&file=...
    - "app:<AppName>": Open with a specific application (e.g. "app:Obsidian", "app:Visual Studio Code").
    - "cmd:<command template>": Open with command (e.g. "cmd:code {path}", "cmd:nvim {path}").
    - "editor": Open with $EDITOR environment variable.
    """
    opener_mode = (opener or "system").strip()
    system = platform.system()
    abs_path = file_path.resolve()

    try:
        if opener_mode in ("obsidian_uri", "obsidian"):
            return _open_via_obsidian_uri(abs_path, vault_root)

        if opener_mode.startswith("app:"):
            app_name = opener_mode[4:].strip()
            return _open_with_app(abs_path, app_name, system)

        if opener_mode.startswith("cmd:"):
            cmd_template = opener_mode[4:].strip()
            cmd_str = cmd_template.replace("{path}", str(abs_path))
            subprocess.Popen(cmd_str, shell=True)
            return True

        if opener_mode == "editor":
            editor = os.environ.get("EDITOR", "nano")
            subprocess.Popen([editor, str(abs_path)])
            return True

        # System default
        return _open_with_system_default(abs_path, system)

    except Exception as e:
        print(f"Error opening note: {e}")
        return False


def _open_with_system_default(file_path: Path, system: str) -> bool:
    """Open with default system handler."""
    if system == "Darwin":
        subprocess.Popen(["open", str(file_path)])
    elif system == "Windows":
        os.startfile(str(file_path))  # type: ignore[attr-defined]
    else:  # Linux / Unix
        subprocess.Popen(["xdg-open", str(file_path)])
    return True


def _open_with_app(file_path: Path, app_name: str, system: str) -> bool:
    """Open file in a specific application."""
    if system == "Darwin":
        subprocess.Popen(["open", "-a", app_name, str(file_path)])
    elif system == "Windows":
        subprocess.Popen([app_name, str(file_path)])
    else:
        subprocess.Popen([app_name, str(file_path)])
    return True


def _open_via_obsidian_uri(file_path: Path, vault_root: Optional[Path]) -> bool:
    """Construct and launch obsidian:// URI."""
    if vault_root:
        vault_name = vault_root.name
        try:
            rel_path = file_path.relative_to(vault_root)
            file_param = rel_path.as_posix()
        except ValueError:
            file_param = file_path.name
    else:
        vault_name = file_path.parent.name
        file_param = file_path.name

    encoded_vault = urllib.parse.quote(vault_name)
    encoded_file = urllib.parse.quote(file_param)
    uri = f"obsidian://open?vault={encoded_vault}&file={encoded_file}"

    system = platform.system()
    if system == "Darwin":
        subprocess.Popen(["open", uri])
    elif system == "Windows":
        os.startfile(uri)  # type: ignore[attr-defined]
    else:
        subprocess.Popen(["xdg-open", uri])
    return True
