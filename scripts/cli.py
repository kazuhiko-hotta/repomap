"""Thin wrapper that exposes the repomap CLI to python scripts."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT / "src"
if SRC_DIR.exists():
    sys.path.insert(0, str(SRC_DIR))

from repomap.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
