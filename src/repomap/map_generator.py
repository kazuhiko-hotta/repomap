"""Core helpers for assembling a repository map."""

import ast
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple

import pathspec

URL_PATTERN = re.compile(r"https?://[\w\-./?&=%+#,;:~$@!]+")
HTTP_LIBS = {"requests", "httpx", "aiohttp"}
DEFAULT_EXCLUDE = {".git", ".venv", "__pycache__", ".idea"}
_GITIGNORE_META = {"*", "?", "["}


class GitignoreRules:
    """Manages hierarchical .gitignore rules across the repository."""

    def __init__(self, root: Path):
        self.root = root
        self._specs: Dict[Path, pathspec.PathSpec] = {}
        self._load_all_gitignores()

    def _load_all_gitignores(self) -> None:
        """Load all .gitignore files recursively from root."""
        # Load root .gitignore first
        root_gitignore = self.root / ".gitignore"
        if root_gitignore.exists():
            self._load_gitignore(self.root)

        # Load all subdirectory .gitignore files
        for gitignore_path in self.root.rglob(".gitignore"):
            if gitignore_path != root_gitignore:
                dir_path = gitignore_path.parent
                self._load_gitignore(dir_path)

    def _load_gitignore(self, directory: Path) -> None:
        """Load .gitignore from a specific directory."""
        gitignore_path = directory / ".gitignore"
        if not gitignore_path.exists():
            return

        lines = gitignore_path.read_text(encoding="utf-8").splitlines()
        # pathspec expects lines without trailing newlines
        spec = pathspec.PathSpec.from_lines("gitignore", lines)
        self._specs[directory] = spec

    def is_ignored(self, file_path: Path) -> bool:
        """Check if a file is ignored by any applicable .gitignore rule."""
        # Get path relative to root
        try:
            rel_path = file_path.relative_to(self.root)
        except ValueError:
            return False

        # Convert to string with forward slashes for pathspec
        rel_path_str = str(rel_path).replace("\\", "/")

        # Collect all applicable .gitignore directories from root to file's parent
        applicable_dirs: List[Path] = []

        # Check root first
        if self.root in self._specs:
            applicable_dirs.append(self.root)

        # Check intermediate directories and file's parent
        current_dir = self.root
        for part in rel_path.parts[:-1]:  # Exclude the filename itself
            current_dir = current_dir / part
            if current_dir in self._specs:
                applicable_dirs.append(current_dir)

        # Collect all patterns from all applicable .gitignore files in order
        all_patterns = []
        for gitignore_dir in applicable_dirs:
            spec = self._specs[gitignore_dir]
            for pattern in spec.patterns:
                all_patterns.append((gitignore_dir, pattern))

        # Apply patterns in order
        # Last match wins (negation can override previous matches)
        ignored = False
        for gitignore_dir, pattern in all_patterns:
            # Calculate relative path from this .gitignore's directory
            try:
                path_from_gitignore = file_path.relative_to(gitignore_dir)
                path_str = str(path_from_gitignore).replace("\\", "/")
            except ValueError:
                continue

            # Check if pattern matches
            if pattern.match_file(path_str):
                # Negation pattern (starts with !) un-ignores
                if pattern.pattern.startswith("!"):
                    ignored = False
                else:
                    ignored = True

        return ignored


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


def aggregate_imports(
    root: Path, python_files: Iterable[Path]
) -> Tuple[Dict[str, Set[str]], Dict[str, List[str]]]:
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


def find_python_files(
    root: Path, exclude: Set[str], gitignore_rules: Optional[GitignoreRules] = None
) -> List[Path]:
    """Locate all Python files under `root` while skipping excluded components."""
    files = []
    for path in root.rglob("*.py"):
        rel_parts = path.relative_to(root).parts
        if any(part in exclude for part in rel_parts):
            continue
        # Check hierarchical .gitignore rules
        if gitignore_rules and gitignore_rules.is_ignored(path):
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


def build_exclude_set(
    root: Path, extra: Iterable[str]
) -> Tuple[Set[str], Optional[GitignoreRules]]:
    """Build exclude set and create GitignoreRules for hierarchical ignores."""
    exclude = set(extra)
    exclude.update(DEFAULT_EXCLUDE)
    # Load hierarchical .gitignore rules
    gitignore_rules = GitignoreRules(root)
    return exclude, gitignore_rules


def generate_repo_report(
    root: Path, exclude: Set[str], gitignore_rules: Optional[GitignoreRules] = None
) -> RepoMapReport:
    """Assemble a `RepoMapReport` for downstream consumers."""
    python_files = find_python_files(root, exclude, gitignore_rules)
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
    lines: List[str] = [
        "# Repository Map",
        "",
        f"## Top-level directories (excludes: {', '.join(sorted(exclude)) or '<none>'})",
        "",
    ]
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
