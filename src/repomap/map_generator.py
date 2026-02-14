"""Core helpers for assembling a repository map."""
import ast
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Set, Tuple

URL_PATTERN = re.compile(r"https?://[\w\-./?&=%+#,;:~$@!]+")
HTTP_LIBS = {"requests", "httpx", "aiohttp"}
DEFAULT_EXCLUDE = {".git", ".venv", "__pycache__", ".idea"}
_GITIGNORE_META = {"*", "?", "["}


@dataclass
class RepoMapReport:
    """Structured data captured for repo_map.md."""

    top_dirs: List[str]
    imports_by_dir: Dict[str, Set[str]]
    http_usage: Dict[str, List[str]]
    url_report: Dict[str, List[Tuple[int, str]]]


def gather_top_level_dirs(root: Path, exclude: Set[str]) -> List[str]:
    """Return alphabetical top-level directories not filtered by `exclude`."""
    dirs = []
    for entry in sorted(root.iterdir()):
        if entry.name in exclude or not entry.is_dir():
            continue
        dirs.append(entry.name)
    return dirs


def collect_file_imports(path: Path) -> Tuple[Set[str], Set[str]]:
    """Return imports and detected HTTP clients from a Python module."""
    imports = set()
    http_used = set()
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (UnicodeDecodeError, SyntaxError):
        return imports, http_used
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root_name = alias.name.split(".", 1)[0]
                imports.add(root_name)
                if root_name in HTTP_LIBS:
                    http_used.add(root_name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module
            if module:
                root_name = module.split(".", 1)[0]
                imports.add(root_name)
                if root_name in HTTP_LIBS:
                    http_used.add(root_name)
    return imports, http_used


def collect_urls(path: Path) -> List[Tuple[int, str]]:
    """Gather literal URLs defined in a Python module."""
    urls = []
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (UnicodeDecodeError, SyntaxError):
        return urls
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            for match in URL_PATTERN.finditer(node.value):
                lineno = getattr(node, "lineno", None)
                urls.append((lineno or 0, match.group()))
    return urls


def aggregate_imports(root: Path, python_files: Iterable[Path]) -> Tuple[Dict[str, Set[str]], Dict[str, List[str]]]:
    """Group imports and HTTP usage by directory relative to `root`."""
    dir_imports: Dict[str, Set[str]] = {}
    http_usage: Dict[str, List[str]] = {lib: [] for lib in HTTP_LIBS}
    for path in python_files:
        rel_dir = path.parent.relative_to(root)
        key = str(rel_dir) if str(rel_dir) != "." else "."
        imports, http_libs = collect_file_imports(path)
        if not imports:
            continue
        dir_imports.setdefault(key, set()).update(sorted(imports))
        for lib in http_libs:
            http_usage.setdefault(lib, []).append(str(path.relative_to(root)))
    return dir_imports, http_usage


def find_python_files(root: Path, exclude: Set[str]) -> List[Path]:
    """Locate all Python files under `root` while skipping excluded components."""
    files = []
    for path in root.rglob("*.py"):
        rel_parts = path.relative_to(root).parts
        if any(part in exclude for part in rel_parts):
            continue
        files.append(path)
    return sorted(files)


def load_gitignore_excludes(root: Path) -> Set[str]:
    gitignore = root / ".gitignore"
    if not gitignore.exists():
        return set()
    excludes: Set[str] = set()
    for line in gitignore.read_text(encoding="utf-8").splitlines():
        entry = line.strip()
        if not entry or entry.startswith("#") or entry.startswith("!"):
            continue
        first = entry.split("/", 1)[0]
        if not first or any(char in first for char in _GITIGNORE_META):
            continue
        excludes.add(first.rstrip("/"))
    return excludes


def build_exclude_set(root: Path, extra: Iterable[str]) -> Set[str]:
    exclude = set(extra)
    exclude.update(DEFAULT_EXCLUDE)
    exclude.update(load_gitignore_excludes(root))
    return exclude


def generate_repo_report(root: Path, exclude: Set[str]) -> RepoMapReport:
    """Assemble a `RepoMapReport` for downstream consumers."""
    python_files = find_python_files(root, exclude)
    dir_imports, http_usage = aggregate_imports(root, python_files)
    url_report: Dict[str, List[Tuple[int, str]]] = {}
    for path in python_files:
        urls = collect_urls(path)
        if urls:
            url_report[str(path.relative_to(root))] = urls
    return RepoMapReport(
        top_dirs=gather_top_level_dirs(root, exclude),
        imports_by_dir=dir_imports,
        http_usage=http_usage,
        url_report=url_report,
    )


def render_repo_map(report: RepoMapReport, exclude: Set[str]) -> List[str]:
    """Turn a report into the markdown lines used for `repo_map.md`."""
    lines: List[str] = ["# Repository Map", "", f"## Top-level directories (excludes: {', '.join(sorted(exclude)) or '<none>'})", ""]
    if report.top_dirs:
        for name in report.top_dirs:
            lines.append(f"- {name}/")
    else:
        lines.append("- None besides excluded entries.")
    lines.extend(["", "## Imports by directory", ""])
    if report.imports_by_dir:
        for directory in sorted(report.imports_by_dir):
            imports = sorted(report.imports_by_dir[directory])
            lines.append(f"- `{directory}`: {', '.join(imports)}")
    else:
        lines.append("- No imports detected (no Python files parsed).")
    lines.extend(["", "## HTTP client usage", ""])
    for lib in sorted(HTTP_LIBS):
        uses = report.http_usage.get(lib, [])
        if uses:
            lines.append(f"- {lib}: used in {len(uses)} file(s)")
            for path in sorted(set(uses)):
                lines.append(f"  - {path}")
        else:
            lines.append(f"- {lib}: not imported in repository")
    lines.extend(["", "## Discovered URL literals", ""])
    if report.url_report:
        for path in sorted(report.url_report):
            lines.append(f"- {path}")
            for lineno, url in sorted(report.url_report[path]):
                line_info = f":{lineno}" if lineno else ""
                lines.append(f"  - {line_info} {url}")
    else:
        lines.append("- None found in parsed Python strings.")
    lines.append("")
    return lines
