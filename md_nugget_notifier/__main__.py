"""Executable entrypoint for python -m md_nugget_notifier."""

import sys
from md_nugget_notifier.cli import main

if __name__ == "__main__":
    sys.exit(main())
