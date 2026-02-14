"""Unit tests for the repomap helpers."""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from repomap import build_exclude_set, generate_repo_report


class MapGeneratorTests(unittest.TestCase):
    def test_generate_repo_report_respects_gitignore(self):
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "ignored").mkdir()
            (root / "ignored" / "module.py").write_text("print('skip')\n")
            (root / ".gitignore").write_text("ignored/\n")
            (root / "kept").mkdir()
            (root / "kept" / "module.py").write_text("import os\n")
            exclude, gitignore_rules = build_exclude_set(root, [])
            report = generate_repo_report(root, exclude, gitignore_rules)
            self.assertNotIn("ignored", report.imports_by_dir)
            self.assertIn("kept", report.imports_by_dir)

    def test_repo_report_captures_http_usage_and_urls(self):
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "client.py").write_text(
                "import requests\nURL = 'https://example.com/api'\n"
            )
            exclude, gitignore_rules = build_exclude_set(root, [])
            report = generate_repo_report(root, exclude, gitignore_rules)
            self.assertIn("requests", report.imports_by_dir.get(".", set()))
            self.assertTrue(report.url_report)

    def test_hierarchical_gitignore_is_respected(self):
        """Test that subdirectory .gitignore files are respected."""
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            # Create nested structure
            subdir = root / "subdir"
            subdir.mkdir()
            (subdir / ".gitignore").write_text("ignored_in_subdir.py\n")
            (subdir / "ignored_in_subdir.py").write_text("import os\n")
            (subdir / "kept.py").write_text("import sys\n")
            # Create file at root
            (root / "root_file.py").write_text("import json\n")

            exclude, gitignore_rules = build_exclude_set(root, [])
            report = generate_repo_report(root, exclude, gitignore_rules)

            # subdir/ignored_in_subdir.py should be excluded
            self.assertNotIn("subdir/ignored_in_subdir.py", str(report.imports_by_dir))
            # subdir/kept.py should be included
            self.assertIn("subdir", report.imports_by_dir)
            # root_file.py should be included
            self.assertIn(".", report.imports_by_dir)

    def test_nested_gitignore_with_negation(self):
        """Test that negation patterns (!) in .gitignore work correctly."""
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            # Root ignores all .py files
            (root / ".gitignore").write_text("*.py\n")
            # Subdir un-ignores specific files
            subdir = root / "subdir"
            subdir.mkdir()
            (subdir / ".gitignore").write_text("!kept.py\n")
            (subdir / "ignored.py").write_text("import os\n")
            (subdir / "kept.py").write_text("import sys\n")

            exclude, gitignore_rules = build_exclude_set(root, [])
            report = generate_repo_report(root, exclude, gitignore_rules)

            # ignored.py should be excluded by root .gitignore
            # kept.py should be included due to negation in subdir/.gitignore
            self.assertIn("subdir", report.imports_by_dir)
            imports = report.imports_by_dir.get("subdir", set())
            self.assertNotIn("os", imports)  # from ignored.py
            self.assertIn("sys", imports)  # from kept.py
