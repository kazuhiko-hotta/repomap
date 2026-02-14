name: Memory
description: Long-term repository rules, constraints, and troubleshooting notes for contributors.

# Memory

- Repository now ships with `src/repomap` helpers plus `scripts/cli.py` CLI that honor `.gitignore` when generating `repo_map.md` for imports, HTTP clients, and URL literals.
- Install optional testing extras with `python -m pip install -e .[testing]` before running `python -m pytest`; lightweight unit tests already exist under `tests/` and currently rely on `unittest` under `PYTHONPATH=src`.
- Troubleshooting: if `pip install -e .[testing]` fails because `setuptools>=68.0` cannot be downloaded (e.g., repeated “Failed to establish a new connection” to `/simple/setuptools`), rerun later when network access to PyPI is restored; until then run `PYTHONPATH=src python -m unittest discover tests` instead of `pytest`.
