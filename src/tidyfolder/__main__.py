"""Allow ``python -m tidyfolder``."""

from __future__ import annotations

from tidyfolder.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
