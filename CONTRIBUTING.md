# Contributing to tidyfolder

Thank you for taking the time to improve this project. tidyfolder is a small
command-line tool, and the most useful contributions are ones that keep it
safe, predictable, and easy to read.

## Development setup

Python 3.9 or newer is required.

```bash
git clone https://github.com/<your-username>/tidyfolder.git
cd tidyfolder
python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

## Running tests

```bash
pytest
```

Please add tests for new behavior, especially anything that moves files,
writes the undo log, or changes default categories. Tests should use
temporary directories and must not touch files outside of those directories.

## Project guidelines

- Keep the default install on the Python standard library. The only allowed
  runtime dependency is `tomli`, and only on Python 3.9 and 3.10.
- Public functions should have type hints and a short docstring.
- Never overwrite or delete user files. If a destination name is taken, choose
  a numbered suffix instead.
- Hidden files, symbolic links, the undo log, and `tidyfolder.toml` stay put
  unless a documented flag says otherwise.
- Command-line flags override values from a config file.
- Commit messages should describe why the change exists, in the present tense
  (for example, "Skip empty files when hashing duplicates").

## Pull requests

1. Open a pull request against `main`.
2. Make sure `pytest` passes locally.
3. Update the README or CHANGELOG when the user-facing behavior changes.

If you are not sure whether an idea fits, open an issue first and we can talk
it through.
