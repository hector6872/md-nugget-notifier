# 💡 md-nugget-notifier

[![Test Suite](https://github.com/hector6872/md-nugget-notifier/actions/workflows/test.yml/badge.svg?branch=main)](https://github.com/hector6872/md-nugget-notifier/actions/workflows/test.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> Pick a random Markdown note (a "nugget" of wisdom, idea, or reference) from any directory or Obsidian vault and push it as a native desktop notification.

---

## ✨ Features

- **Zero Mandatory Dependencies**: Runs with standard Python 3.8+ on macOS, Linux, and Windows.
- **Any Markdown Folder**: Recursively scans `.md` files while ignoring `.git`, `.obsidian`, `.trash`, and temporary directories.
- **Smart Snippet Extraction**: Strips YAML frontmatter, headers, wikilinks (`[[Link|Alias]]` → `Alias`), markdown formatting, and images to generate clean, readable notification snippets.
- **Configurable Opener**:
  - System default application (Markdown editor, viewer, etc.)
  - Obsidian URI scheme (`obsidian://open?vault=...&file=...`)
  - Specific apps (e.g. `app:Visual Studio Code`, `app:Obsidian`, `app:Typora`)
  - Custom shell commands (e.g. `cmd:code "{path}"`, `cmd:nvim "{path}"`)
  - Terminal `$EDITOR`
- **Automation Ready**: Easy to schedule via macOS `launchd` or `cron`.

---

## 🚀 Quick Start

### 1. Run Directly with Python
```bash
python3 -m md_nugget_notifier --dir /path/to/your/notes
```

### 2. Install as a CLI tool (editable mode)
```bash
pip install -e .
md-nugget-notifier --dir /path/to/your/notes
```

---

## 🍎 macOS Notifications & Sequoia (macOS 15+)

On **macOS Sequoia (macOS 15+)**, Apple restricts ad-hoc terminal scripts from posting passive banner notifications without a registered signed bundle ID.

To receive beautiful banner notifications with click-to-open support on macOS:

1. **Install `terminal-notifier` (Recommended):**
   ```bash
   brew install terminal-notifier
   ```
   `md-nugget-notifier` will automatically detect it, display native macOS banners, and configure click actions.

2. **Or use the `--alert` / `-a` modal dialog (Zero extra dependencies):**
   ```bash
   md-nugget-notifier --dir /path/to/your/notes --alert
   ```
   This displays an instant native macOS pop-up modal on your screen.

---

## 🛠️ CLI Usage

```text
usage: md-nugget-notifier [-h] [-d NOTES_DIR] [-o] [-a] [--no-recursive] [-l MAX_LENGTH] [--icon ICON] [-q] [-p] [--json] [--opener OPENER] [-c CONFIG_PATH] [-v]

Pick a random Markdown note and send it as a native desktop notification.

options:
  -h, --help            show this help message and exit
  -d, --dir NOTES_DIR   Directory containing your markdown notes/vault.
  -o, --open            Open the selected note using the configured opener.
  -a, --alert           Display as an interactive pop-up dialog/alert window.
  --no-recursive, --flat
                        Only search for .md notes in the specified root directory (non-recursive).
  -l, --length, --max-length MAX_LENGTH
                        Maximum length of the preview snippet (characters). Default: 220.
  --icon ICON           Icon for notification: image path or 'obsidian' (macOS app icon).
  -q, --quiet           Do not print dispatch confirmation to terminal.
  -p, --preview         Print the selected note title and snippet to the terminal without sending a notification.
  --json                Output the selected note details in JSON format.
  --opener OPENER       Opener strategy: 'system' (default), 'obsidian', 'app:<App Name>', 'cmd:<Template with {path}>', 'editor'.
  -c, --config CONFIG   Path to a custom JSON configuration file.
  -v, --version         show program's version number and exit
```

### Examples

**Preview a random note in terminal (only in the top-level folder, non-recursive):**
```bash
md-nugget-notifier --dir ~/Notes --no-recursive --preview
```

**Display as an interactive modal pop-up (macOS dialog):**
```bash
md-nugget-notifier --dir ~/Notes --alert
```

**Send notification and open the note in default app:**
```bash
md-nugget-notifier --dir ~/Notes --open
```

**Open in VS Code when triggered:**
```bash
md-nugget-notifier --dir ~/Notes --open --opener "app:Visual Studio Code"
# Or using command template:
md-nugget-notifier --dir ~/Notes --open --opener "cmd:code {path}"
```

**Open inside Obsidian via URI scheme:**
```bash
md-nugget-notifier --dir ~/Notes --open --opener obsidian
```

**Get JSON output for scripts:**
```bash
md-nugget-notifier --dir ~/Notes --json
```

---

## ⚙️ Configuration File

You can set a default configuration by creating `~/.config/md-nugget-notifier/config.json` or `config.json` in the current folder:

```json
{
  "notes_dir": "~/Documents/MyVault",
  "opener": "system",
  "ignored_dirs": [
    "templates",
    "archive",
    ".attachments"
  ],
  "max_snippet_length": 220,
  "min_size_bytes": 10
}
```

### Environment Variables
You can also configure via environment variables:
- `MD_NOTES_DIR` or `NOTES_DIR` or `OBSIDIAN_VAULT_PATH`: Default path to markdown folder.
- `MD_NOTIFIER_OPENER`: Default opener strategy.

---

## ⏰ Scheduling Automated Daily / Hourly Notifications

### Option A: macOS `launchd` (Recommended on macOS)

Create a file at `~/Library/LaunchAgents/com.user.md-nugget-notifier.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.user.md-nugget-notifier</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>-m</string>
        <string>md_nugget_notifier</string>
        <string>--dir</string>
        <string>/Users/your-user/Documents/Notes</string>
    </array>
    <key>StartCalendarInterval</key>
    <!-- Run every day at 9:00 AM -->
    <dict>
        <key>Hour</key>
        <integer>9</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
</dict>
</plist>
```

Load it into launchd:
```bash
launchctl load ~/Library/LaunchAgents/com.user.md-nugget-notifier.plist
```

> **Tip:** You can generate and customize macOS launchd `.plist` files visually using [Launched (launched.zerowidth.com)](https://launched.zerowidth.com/).

### Option B: `cron` (macOS / Linux)

Run `crontab -e` and add an entry:

```bash
# Run every day at 09:00 and 15:00
0 9,15 * * * /usr/bin/python3 -m md_nugget_notifier --dir /path/to/notes
```

---

## 🧪 Testing

Run test suite:
```bash
python3 -m unittest discover tests
```

---

## 📄 License
MIT
