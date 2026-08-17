"""Configuration loader for md-nugget-notifier."""

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class AppConfig:
    notes_dir: Path = field(default_factory=lambda: Path.cwd())
    opener: str = "system"
    ignored_dirs: List[str] = field(default_factory=list)
    max_snippet_length: int = 220
    min_size_bytes: int = 1
    recursive: bool = True


def get_default_config_paths() -> List[Path]:
    """Return prioritized list of possible config file locations."""
    paths = []
    # 1. Current working directory config.json
    paths.append(Path.cwd() / "config.json")
    # 2. XDG user config directory
    xdg_config = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config:
        paths.append(Path(xdg_config) / "md-nugget-notifier" / "config.json")
    else:
        paths.append(Path.home() / ".config" / "md-nugget-notifier" / "config.json")
    # 3. Home directory dotfile
    paths.append(Path.home() / ".md-nugget-notifier.json")
    return paths


def load_config(custom_config_path: Optional[Path] = None) -> AppConfig:
    """Load configuration from file or environment variables."""
    cfg = AppConfig()

    # Load from config file if found
    config_file = None
    if custom_config_path and custom_config_path.exists():
        config_file = custom_config_path
    else:
        for path in get_default_config_paths():
            if path.exists() and path.is_file():
                config_file = path
                break

    if config_file:
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            if "notes_dir" in data and data["notes_dir"]:
                cfg.notes_dir = Path(os.path.expanduser(data["notes_dir"])).resolve()
            elif "vault_path" in data and data["vault_path"]:
                cfg.notes_dir = Path(os.path.expanduser(data["vault_path"])).resolve()

            if "opener" in data and data["opener"]:
                cfg.opener = str(data["opener"])

            if "ignored_dirs" in data and isinstance(data["ignored_dirs"], list):
                cfg.ignored_dirs = data["ignored_dirs"]

            if "max_snippet_length" in data:
                cfg.max_snippet_length = int(data["max_snippet_length"])

            if "min_size_bytes" in data:
                cfg.min_size_bytes = int(data["min_size_bytes"])

            if "recursive" in data:
                cfg.recursive = bool(data["recursive"])
        except Exception as e:
            print(f"Warning: Failed to load config from {config_file}: {e}")

    # Environment variables override config file
    env_dir = (
        os.environ.get("MD_NOTES_DIR")
        or os.environ.get("NOTES_DIR")
        or os.environ.get("OBSIDIAN_VAULT_PATH")
    )
    if env_dir:
        cfg.notes_dir = Path(os.path.expanduser(env_dir)).resolve()

    env_opener = os.environ.get("MD_NOTIFIER_OPENER")
    if env_opener:
        cfg.opener = env_opener

    env_recursive = os.environ.get("MD_NOTIFIER_RECURSIVE")
    if env_recursive is not None:
        cfg.recursive = env_recursive.lower() not in ("0", "false", "no")

    return cfg
