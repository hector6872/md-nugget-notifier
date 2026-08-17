"""Scanner and random note selector for markdown directories."""

import random
from pathlib import Path
from typing import List, Optional, Set

DEFAULT_IGNORED_DIRS = {
    ".git",
    ".obsidian",
    ".trash",
    ".stversions",
    ".stfolder",
    ".vscode",
    ".idea",
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
}


def find_all_markdown_notes(
    directory: Path,
    ignored_dir_names: Optional[Set[str]] = None,
    min_size_bytes: int = 1,
    recursive: bool = True,
) -> List[Path]:
    """Scan directory for all markdown files, skipping ignored folders.
    
    If recursive is True, scans all subdirectories; if False, only scans the top-level directory.
    """
    if ignored_dir_names is None:
        ignored_dirs = DEFAULT_IGNORED_DIRS
    else:
        ignored_dirs = DEFAULT_IGNORED_DIRS.union(ignored_dir_names)

    notes = []
    if not directory.exists() or not directory.is_dir():
        return notes

    iterator = directory.rglob("*.md") if recursive else directory.glob("*.md")

    for file_path in iterator:
        # Check if any parent folder matches ignored folders
        parts_set = set(file_path.parts[:-1])
        if parts_set.intersection(ignored_dirs):
            continue

        try:
            if file_path.is_file() and file_path.stat().st_size >= min_size_bytes:
                notes.append(file_path)
        except OSError:
            continue

    return notes


def pick_random_note(
    directory: Path,
    ignored_dir_names: Optional[Set[str]] = None,
    min_size_bytes: int = 1,
    recursive: bool = True,
) -> Optional[Path]:
    """Select a random markdown note from the given directory."""
    notes = find_all_markdown_notes(
        directory=directory,
        ignored_dir_names=ignored_dir_names,
        min_size_bytes=min_size_bytes,
        recursive=recursive,
    )
    if not notes:
        return None
    return random.choice(notes)
