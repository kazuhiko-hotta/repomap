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
            exclude = build_exclude_set(root, [])
            report = generate_repo_report(root, exclude)
            self.assertNotIn("ignored", report.imports_by_dir)
            self.assertIn("kept", report.imports_by_dir)

    def test_repo_report_captures_http_usage_and_urls(self):
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "client.py").write_text("import requests\nURL = 'https://example.com/api'\n")
            exclude = build_exclude_set(root, [])
            report = generate_repo_report(root, exclude)
            self.assertIn("requests", report.imports_by_dir.get(".", set()))
            self.assertTrue(report.url_report)
