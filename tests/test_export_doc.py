"""Tests for export_doc.py"""
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).parent.parent / "scripts"


def run_export(md_path, *extra_args):
    return subprocess.run(
        [sys.executable, str(SCRIPTS / "export_doc.py"), md_path, *extra_args],
        capture_output=True, text=True,
    )


class TestExportBasics:
    def test_nonexistent_file_fails(self):
        result = run_export("/tmp/nonexistent.md")
        assert result.returncode == 1

    def test_no_args_fails(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / "export_doc.py")],
            capture_output=True, text=True,
        )
        assert result.returncode == 1

    def test_markdown_file_accepted(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("# Test\nSome content")
            f.flush()
            result = run_export(f.name)
            # Exit 0 = success, Exit 2 = pandoc not found (graceful)
            assert result.returncode in (0, 2)


class TestExportDegradation:
    def test_exit_code_2_when_no_pandoc(self):
        import os
        env = os.environ.copy()
        env["PATH"] = ""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("# Test\nContent")
            f.flush()
            result = subprocess.run(
                [sys.executable, str(SCRIPTS / "export_doc.py"), f.name],
                capture_output=True, text=True, env=env,
            )
            assert result.returncode == 2
            assert "pandoc" in result.stderr.lower() or "install" in result.stderr.lower()

    def test_docx_generated_when_pandoc_available(self):
        import shutil
        if not shutil.which("pandoc"):
            pytest.skip("pandoc not installed")
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, dir="/tmp") as f:
            f.write("# Business Plan Test\n\n## Executive Summary\nTest content.")
            f.flush()
            result = run_export(f.name)
            assert result.returncode == 0
            docx_path = Path(f.name).with_suffix(".docx")
            assert docx_path.exists()
            docx_path.unlink()
