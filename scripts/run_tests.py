"""Run the repository’s unittests without installing the package."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT / "src"
if SRC_DIR.exists():
    sys.path.insert(0, str(SRC_DIR))


def main() -> int:
    loader = unittest.defaultTestLoader
    suite = loader.discover(str(ROOT / "tests"))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
