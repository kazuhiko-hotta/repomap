name: README
description: Overview and quickstart guide for the repomap project.

# repomap

`repomap` inspects Python repositories to summarize their top-level layout, imports, HTTP client usage, and literal URLs. It powers the `repo_map.md` file in this repository so contributors and AI assistants alike can quickly understand where the code lives and what it touches.

## Quickstart
1. Create a virtual environment (optional but recommended): `python -m venv .venv && source .venv/bin/activate` on Unix or the equivalent on Windows.
2. Install the package and testing extras to get the CLI and unit test dependencies: `python -m pip install -e .[testing]`.
3. Generate or refresh the repository map with the CLI described below.

### Optional: use `uv` instead of `venv`
If you prefer `uv` (https://github.com/uvtools/uv) as your build/runtime shim, install it via `pip install --user uv` and then run the CLI/tests through `uv` so the tool manages the isolated environment for you:

```
uv run python -m pip install -e .[testing]  # install deps inside uv session
uv run python scripts/run_tests.py           # run the test suite
uv run python scripts/cli.py --dry-run       # preview the repo map
uv shell                                     # drop into a shell where uv propels every command
```

While `uv run` lets you invoke single commands, `uv shell` keeps using the same isolated environment interactively. When you exit the shell, uv cleans up automatically. Use the wrapper scripts above (`scripts/run_tests.py` and `scripts/cli.py`) so you never have to set `PYTHONPATH` manually.

## CLI usage
After installing the package, use `python -m repomap` (or the `repomap` console script) to regenerate `repo_map.md`. The CLI wraps the same helpers used by `scripts/cli.py`, adds a few ergonomics, and defaults to honoring `.gitignore` plus the built-in excludes (e.g., `.git`, `.venv`, `__pycache__`, `.idea`).

Example calls:
```
python -m repomap              # scan current directory and overwrite repo_map.md
repomap -r ../other-project     # target a different repository root
repomap --exclude build --dry-run  # preview output without modifying files
repomap -o -                   # print the report to stdout instead of a file
```

Common options:
- `-r / --root DIR`: directory to scan (default: the current working directory).
- `-e / --exclude DIR`: add another top-level directory to ignore.
- `-o / --output FILE`: write the report to FILE (`repo_map.md` by default, use `-` to print to stdout).
- `--dry-run`: render the report on stdout without writing any files.
- `--list-excludes`: print the combined exclude set (defaults + `.gitignore` + any `--exclude` values).
- `--show-defaults`: show only the built-in default excludes and exit.
- `--quiet`: suppress the final confirmation message after writing the file.

The thin wrapper in `scripts/cli.py` still lets you run the CLI without installing the package: it just ensures `src/` is on `sys.path` before handing off to `repomap.cli`.

The generated file always highlights:
1. Top-level directories you care about.
2. Imports grouped by directory.
3. HTTP client usage (`requests`, `httpx`, `aiohttp`).
4. Literal URLs found in parsed Python files.

## Library usage
Import the helpers from `repomap` (package source lives under `src/repomap`). The public API includes `build_exclude_set`, `generate_repo_report`, and `render_repo_map` if you need tighter control:

```python
from repomap import build_exclude_set, generate_repo_report, render_repo_map
from pathlib import Path

root = Path('.')
exclude = build_exclude_set(root, extra=[])
report = generate_repo_report(root, exclude)
lines = render_repo_map(report, exclude)
print('\n'.join(lines))
```

## Testing
Run the lightweight unit tests shipped under `tests/` without installing anything by executing:

```
python scripts/run_tests.py
```

Testing currently relies on the `repomap` helpers and covers `.gitignore` handling plus detection of HTTP imports/URLs. If you install the optional extras above, you can also run `python -m pytest` once `pytest` is available in the environment.

### Testing and CLI usage without installing
If you prefer not to install the package, the scripts under `scripts/` already add `src/` to `sys.path` for you. From the repository root you can run:

```
python scripts/run_tests.py               # run the unit tests
python scripts/cli.py                     # regenerate repo_map.md without installing
python scripts/cli.py --dry-run           # preview the report
python scripts/cli.py --show-defaults     # inspect the default excludes
```

You can still run `python -m repomap` directly if you like, but these helper scripts spare you from setting `PYTHONPATH`.

## Notes
- `repo_map.md` is intended to be human-readable; regenerate it whenever the import landscape or directory layout changes.
- The CLI respects `.gitignore` entries at all directory levels (hierarchical .gitignore support with pathspec). Patterns such as `*`, `?`, `**/` and negation (`!`) are fully supported.
- Keep `AGENTS.md` untouched—it's the global agent guide.
