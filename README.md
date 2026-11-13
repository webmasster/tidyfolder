# tidyfolder

Safely organize a messy folder — Downloads, the desktop, a camera dump — into
subfolders by file type, and optionally by month. Preview every change first,
undo a run if you change your mind, and find duplicate files by content hash.

tidyfolder never overwrites a file, never deletes a file, and refuses to touch
your home directory or system folders unless you explicitly pass `--force`.

## Why it exists

Folders like Downloads collect photos, PDFs, installers, and zip files in one
pile. Dragging them into subfolders by hand is slow and easy to get wrong.
tidyfolder does that job in a way that is easy to review and easy to reverse.

## Requirements

- Python 3.9 or newer
- A terminal (Windows, macOS, or Linux)
- No required third-party packages on Python 3.11+ (Python 3.9 and 3.10 need
  `tomli`, which is installed automatically)

## Install

From a local clone of this repository:

```bash
python -m pip install .
```

For development, including tests:

```bash
python -m pip install -e ".[dev]"
```

Once the project is on GitHub, you can also install it directly from git:

```bash
python -m pip install "git+https://github.com/<your-username>/tidyfolder.git"
```

Check that the command is available:

```bash
tidyfolder --version
```

You can also run it as a module: `python -m tidyfolder --help`.

## Usage

Always start with a dry run. Nothing is moved until you drop `--dry-run`.

### Preview, then organize

```bash
tidyfolder organize ~/Downloads --dry-run
```

```
Planned moves (dry run):

Archives (1)
  archive.zip  ->  Archives/archive.zip

Images (4)
  holiday (1).jpg  ->  Images/holiday (1).jpg
  holiday.jpg      ->  Images/holiday.jpg
  photo copy.jpg   ->  Images/photo copy.jpg
  screenshot.png   ->  Images/screenshot.png

Documents (3)
  invoice.pdf  ->  Documents/invoice.pdf
  notes.txt    ->  Documents/notes.txt
  resume.pdf   ->  Documents/resume.pdf

Audio (1)
  track.mp3  ->  Audio/track.mp3

Would move 9 file(s).
Dry run only. Re-run without --dry-run to apply these moves.
```

If the plan looks right:

```bash
tidyfolder organize ~/Downloads
```

```
Applied moves:
...
Moved 9 file(s).
Undo log written to /home/you/Downloads/.tidyfolder-undo.json.
Run 'tidyfolder undo /home/you/Downloads' to revert.
```

Group files by month as well (from each file's last-modified time):

```bash
tidyfolder organize ~/Downloads --by-date --dry-run
```

That would place `holiday.jpg` in `Images/2026-11/holiday.jpg`.

Useful flags:

| Flag | What it does |
| --- | --- |
| `--dry-run` | Show the plan; do not move anything |
| `--by-date` / `--no-by-date` | Also group into `YYYY-MM` folders |
| `--recursive` / `--no-recursive` | Include files in subfolders |
| `--include-hidden` | Include hidden files |
| `--exclude GLOB` | Skip matching names (repeatable) |
| `--config PATH` | Use a specific TOML config file |
| `--force` | Allow organizing a protected path such as your home directory |

By default only files in the top of the folder are moved. Files that are already
sitting in the correct category folder are left alone, so you can run the
command more than once.

### Undo a run

Each successful organize (or duplicate-move) writes a JSON undo log. Restore
the previous layout with:

```bash
tidyfolder undo ~/Downloads --dry-run
tidyfolder undo ~/Downloads
```

```
Planned undo (dry run):

  Audio/track.mp3         ->  track.mp3
  Images/screenshot.png   ->  screenshot.png
  Documents/resume.pdf    ->  resume.pdf
  ...

Would restore 9 file(s).
Dry run only. Re-run without --dry-run to apply this undo.
```

If a file's contents have changed since it was organized, tidyfolder skips it
and tells you why. Pass `--force` only if you still want it moved back. Use
`--log PATH` if the log is not at the default `.tidyfolder-undo.json`.

### Find duplicate files

Duplicates are detected by SHA-256, not by file name, so `holiday.jpg` and
`holiday (1).jpg` are flagged when they contain the same bytes.

```bash
tidyfolder dupes ~/Downloads --recursive
```

```
Found 1 duplicate group(s) in 9 file(s):

Group 1: 3 copies, 4 bytes, sha256=41e5787e9f28...
  keep   Images/holiday.jpg
  extra  Images/photo copy.jpg
  extra  Images/holiday (1).jpg

Wasted space: 8 byte(s) in extra copies.
```

The oldest copy is kept. Nothing is deleted. To set extras aside:

```bash
tidyfolder dupes ~/Downloads --recursive --move-to Duplicates --dry-run
tidyfolder dupes ~/Downloads --recursive --move-to Duplicates
```

That move also writes an undo log, so you can put the extras back.

### List categories

```bash
tidyfolder categories
```

prints every built-in category and the extensions it matches. Pass a folder
(or `--config`) to see the rules after your config is applied.

## Configuration

tidyfolder looks for a TOML file in this order:

1. The path you pass with `--config`
2. `tidyfolder.toml` or `.tidyfolder.toml` in the folder you are organizing
3. `~/.config/tidyfolder/config.toml`

A complete annotated example is in [`tidyfolder.example.toml`](tidyfolder.example.toml).
A short version:

```toml
[general]
by_date = false
include_hidden = false
recursive = false
other_folder = "Other"

# Replaces the built-in Images list; other default categories stay as they are.
[categories.Images]
extensions = [".jpg", ".jpeg", ".png", ".gif", ".webp", ".heic"]

# Adds a new category.
[categories.Design]
extensions = [".psd", ".ai", ".fig"]
```

Set `extensions` to an empty list to remove a built-in category. Command-line
flags always win over the config file (`--by-date`, `--no-by-date`, and so on).

## Safety notes

- **Preview first.** `--dry-run` is a complete preview and touches no files.
- **No overwrites.** If `Images/photo.jpg` already exists, the next file is
  saved as `photo_1.jpg`, then `photo_2.jpg`, and so on.
- **No deletes.** Organize, undo, and duplicate handling only move files.
- **Hidden files and symbolic links are skipped** unless you ask otherwise.
  The tool also never moves its own undo log or `tidyfolder.toml`.
- **Protected paths.** The home directory, filesystem root, and common system
  folders are refused without `--force`.
- **Undo checks content.** A SHA-256 digest is stored for every moved file.
  Undo will not blindly restore a file that has been edited.
- **This is not a backup tool.** If the files matter, keep a copy somewhere
  else before you reorganize a large folder.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup and test instructions. Bug
reports and small, well-tested improvements are welcome.

## License

[MIT](LICENSE) © 2026 Mohammadreza Safari
