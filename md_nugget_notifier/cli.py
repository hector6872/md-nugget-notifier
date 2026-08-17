"""CLI interface for md-nugget-notifier."""

import argparse
import json
import os
import sys
from pathlib import Path

from . import __version__
from .config import load_config
from .notifier import send_notification, show_alert
from .opener import open_note
from .parser import extract_title_and_snippet
from .vault import pick_random_note


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="md-nugget-notifier",
        description="Pick a random Markdown note and send it as a native desktop notification.",
    )
    parser.add_argument(
        "-d",
        "--dir",
        dest="notes_dir",
        type=str,
        help="Directory containing your markdown notes/vault.",
    )
    parser.add_argument(
        "-o",
        "--open",
        action="store_true",
        help="Open the selected note using the configured opener (e.g. default app, Obsidian, editor).",
    )
    parser.add_argument(
        "-a",
        "--alert",
        action="store_true",
        help="Display as an interactive pop-up dialog/alert window instead of a passive notification banner.",
    )
    parser.add_argument(
        "--no-recursive",
        "--flat",
        dest="recursive",
        action="store_false",
        default=None,
        help="Only search for .md notes in the specified root directory, without traversing subfolders.",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Do not print dispatch confirmation to terminal.",
    )
    parser.add_argument(
        "-p",
        "--preview",
        action="store_true",
        help="Print the selected note title and snippet to the terminal without sending a notification.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output the selected note details in JSON format.",
    )
    parser.add_argument(
        "-l",
        "--length",
        "--max-length",
        dest="max_length",
        type=int,
        help="Maximum length of the preview snippet (in characters). Default: 220.",
    )
    parser.add_argument(
        "--icon",
        type=str,
        help="Icon for notification: path to image/icns file, or 'obsidian' to use Obsidian's app icon.",
    )
    parser.add_argument(
        "--opener",
        type=str,
        help="Opener strategy: 'system' (default), 'obsidian', 'app:<App Name>', 'cmd:<Template with {path}>', 'editor'.",
    )
    parser.add_argument(
        "-c",
        "--config",
        dest="config_path",
        type=str,
        help="Path to a custom JSON configuration file.",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    args = parser.parse_args()

    # Load configuration
    custom_cfg = Path(args.config_path).resolve() if args.config_path else None
    cfg = load_config(custom_cfg)

    # CLI args override configuration
    if args.notes_dir:
        cfg.notes_dir = Path(os.path.expanduser(args.notes_dir)).resolve()
    if args.opener:
        cfg.opener = args.opener
    if args.max_length is not None:
        cfg.max_snippet_length = args.max_length
    if args.icon:
        cfg.icon = args.icon
    if args.recursive is not None:
        cfg.recursive = args.recursive

    if not cfg.notes_dir.exists() or not cfg.notes_dir.is_dir():
        err_msg = f"Error: Notes directory '{cfg.notes_dir}' does not exist or is not a directory."
        print(err_msg, file=sys.stderr)
        if args.alert:
            show_alert(title="Error", message=err_msg)
        elif not args.preview and not args.json:
            send_notification(title="Error", message=err_msg)
        return 1

    # Pick a random note
    chosen_file = pick_random_note(
        directory=cfg.notes_dir,
        ignored_dir_names=set(cfg.ignored_dirs),
        min_size_bytes=cfg.min_size_bytes,
        recursive=cfg.recursive,
    )

    if not chosen_file:
        err_msg = f"Error: No markdown (.md) notes found in '{cfg.notes_dir}'."
        if args.json:
            print(json.dumps({"error": err_msg}))
        else:
            print(err_msg, file=sys.stderr)

        if args.alert:
            show_alert(title="Error: No Notes Found", message=err_msg)
        elif not args.preview and not args.json:
            send_notification(
                title="Error: No Notes Found",
                message=f"No markdown (.md) notes found in {cfg.notes_dir.name or cfg.notes_dir}.",
            )
        return 1

    title, snippet = extract_title_and_snippet(
        chosen_file, max_length=cfg.max_snippet_length
    )

    # Output / Action handling
    if args.json:
        result = {
            "title": title,
            "snippet": snippet,
            "path": str(chosen_file.resolve()),
            "opener": cfg.opener,
        }
        print(json.dumps(result, indent=2))
    elif args.preview:
        print("=" * 50)
        print(f"💡 Title:   {title}")
        print(f"📁 Path:    {chosen_file}")
        print(f"📝 Snippet: {snippet}")
        print("=" * 50)
    elif args.alert:
        show_alert(
            title=title,
            message=snippet,
            file_path=chosen_file,
            opener=cfg.opener,
            vault_root=cfg.notes_dir,
            icon=cfg.icon,
        )
        if not args.quiet:
            print(f"💡 Alert dialog shown: \"{title}\" ({chosen_file.name})")
    else:
        send_notification(
            title=title,
            message=snippet,
            file_path=chosen_file,
            opener=cfg.opener,
            vault_root=cfg.notes_dir,
            icon=cfg.icon,
        )
        if not args.quiet:
            print(f"💡 Notification sent: \"{title}\" ({chosen_file.name})")

    if args.open:
        open_note(chosen_file, opener=cfg.opener, vault_root=cfg.notes_dir)

    return 0


if __name__ == "__main__":
    sys.exit(main())
