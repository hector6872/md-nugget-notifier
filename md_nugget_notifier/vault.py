"""Scanner and random note selector for markdown directories."""

import os
import random
import shutil
import stat
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Set, Union

DEFAULT_IGNORED_DIRS = {
    "node_modules",
    "venv",
    "__pycache__",
}

SF_DATALESS = getattr(stat, "SF_DATALESS", 0x40000000)


def is_dataless_file(target: Union[Path, os.stat_result]) -> bool:
    """Check if file is a dataless cloud placeholder on macOS (e.g. Dropbox 'Online-Only', iCloud)."""
    if sys.platform != "darwin":
        return False
    try:
        st = target if isinstance(target, os.stat_result) else target.stat()
        return bool(getattr(st, "st_flags", 0) & SF_DATALESS)
    except OSError:
        return False


def trigger_background_download(file_path: Path) -> None:
    """Trigger background download of evicted iCloud file on macOS using brctl."""
    if sys.platform == "darwin" and shutil.which("brctl"):
        try:
            subprocess.Popen(
                ["brctl", "download", str(file_path)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception:
            pass


def find_all_markdown_notes(
    directory: Path,
    ignored_dir_names: Optional[Set[str]] = None,
    min_size_bytes: int = 1,
    recursive: bool = True,
) -> List[Path]:
    """Scan directory for all markdown files, skipping all dot directories and ignored folders.

    Uses efficient top-down pruning to automatically skip any folder starting with a dot ('.')
    and any user-specified ignored directories.
    """
    if ignored_dir_names is None:
        ignored_dirs = DEFAULT_IGNORED_DIRS
    else:
        ignored_dirs = DEFAULT_IGNORED_DIRS.union(ignored_dir_names)

    notes = []
    if not directory.exists() or not directory.is_dir():
        return notes

    if not recursive:
        try:
            for entry in directory.iterdir():
                # Skip hidden files/directories and check .md extension
                if not entry.name.startswith(".") and entry.is_file() and entry.suffix.lower() == ".md":
                    try:
                        if entry.stat().st_size >= min_size_bytes:
                            notes.append(entry)
                    except OSError:
                        continue
        except OSError:
            pass
        return notes

    # Fast top-down walk with in-place directory pruning
    for root, dirs, files in os.walk(str(directory), topdown=True, followlinks=False):
        # Discard all hidden directories starting with '.' and any custom ignored folders
        dirs[:] = [
            d for d in dirs
            if not d.startswith(".") and d not in ignored_dirs
        ]

        root_path = Path(root)
        for f in files:
            # Skip hidden files starting with '.' and only match markdown files
            if not f.startswith(".") and f.lower().endswith(".md"):
                file_path = root_path / f
                try:
                    if file_path.stat().st_size >= min_size_bytes:
                        notes.append(file_path)
                except OSError:
                    continue

    return notes


def pick_random_note(
    directory: Path,
    ignored_dir_names: Optional[Set[str]] = None,
    min_size_bytes: int = 1,
    recursive: bool = True,
    exclude_files: Optional[Set[Path]] = None,
) -> Optional[Path]:
    """Select a random markdown note from the given directory.

    On macOS, prefers locally cached/hydrated notes over evicted iCloud dataless files.
    """
    notes = find_all_markdown_notes(
        directory=directory,
        ignored_dir_names=ignored_dir_names,
        min_size_bytes=min_size_bytes,
        recursive=recursive,
    )
    if exclude_files:
        notes = [n for n in notes if n not in exclude_files]

    if not notes:
        return None

    hydrated = [n for n in notes if not is_dataless_file(n)]
    if hydrated:
        return random.choice(hydrated)
    return random.choice(notes)
