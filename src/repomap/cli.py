"""Command-line interface for the repomap helpers."""
from __future__ import annotations

import sys
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser, Namespace
from pathlib import Path
from typing import Iterable, List, Set, Sequence, Tuple

from . import DEFAULT_EXCLUDE, build_exclude_set, generate_repo_report, render_repo_map


def _format_excludes(exclude: Set[str]) -> str:
    return ", ".join(sorted(exclude)) or "<none>"


def _parse_args(argv: Sequence[str]) -> Tuple[ArgumentParser, Namespace]:
    parser = ArgumentParser(
        prog="repomap",
        description="Generate a repo_map.md summary for a Python project.",
        formatter_class=ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-r",
        "--root",
        default=".",
        help="Repository root to scan.",
    )
    parser.add_argument(
        "-e",
        "--exclude",
        action="append",
        default=[],
        metavar="DIR",
        help="Additional top-level directories to ignore.",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="repo_map.md",
        help="Target Markdown file (`-` prints to stdout).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Render the report but do not write any files.",
    )
    parser.add_argument(
        "--list-excludes",
        action="store_true",
        help="Print the list of directories that will be excluded.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress status messages after writing.",
    )
    parser.add_argument(
        "--show-defaults",
        action="store_true",
        help="Show the built-in default excludes before exiting.",
    )
    return parser, parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> int:
    resolved = list(argv) if argv is not None else list(sys.argv[1:])
    parser, args = _parse_args(resolved)

    if not resolved:
        parser.print_help()
        return 0

    root = Path(args.root).resolve()
    extra_excludes = [entry for entry in args.exclude if entry]
    exclude_set = build_exclude_set(root, extra_excludes)

    if args.show_defaults:
        print(f"Default excludes: {', '.join(sorted(DEFAULT_EXCLUDE))}")
        return 0

    if args.list_excludes:
        print(f"Combined excludes: {_format_excludes(exclude_set)}")
        print("Use --exclude to add entries beyond what Git and the defaults already ignore.")
        return 0

    report = generate_repo_report(root, exclude_set)
    lines = render_repo_map(report, exclude_set)
    output_text = "\n".join(lines).rstrip()

    if args.dry_run or args.output == "-":
        print(output_text)
        return 0

    try:
        Path(args.output).write_text(output_text + "\n", encoding="utf-8")
    except OSError as exc:
        print(f"Failed to write {args.output}: {exc}", file=sys.stderr)
        return 1

    if not args.quiet:
        print(f"Wrote repository map to {args.output} (scanned: {root})")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
