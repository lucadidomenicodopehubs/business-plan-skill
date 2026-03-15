"""Export a markdown file to PDF and/or DOCX via Pandoc or wkhtmltopdf.

Graceful degradation chain:
1. Pandoc + XeLaTeX available → PDF + DOCX
2. Pandoc without XeLaTeX     → DOCX only (PDF skipped with warning)
3. Pandoc fails               → try wkhtmltopdf for PDF
4. No Pandoc at all           → exit code 2 with install instructions on stderr

Exit codes:
  0 — success (at least one export worked)
  1 — error (file not found, no args)
  2 — no export tools available (graceful, with install message)
"""

import shutil
import subprocess
import sys
from pathlib import Path


def _run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, **kwargs)


def export_with_pandoc(md_path: Path) -> int:
    """Try to export using pandoc. Returns exit code."""
    pandoc = shutil.which("pandoc")
    if not pandoc:
        return None  # signal: pandoc not found

    docx_path = md_path.with_suffix(".docx")
    pdf_path = md_path.with_suffix(".pdf")

    exported_any = False

    # Always try DOCX first — no extra deps needed
    result = _run([pandoc, str(md_path), "-o", str(docx_path)])
    if result.returncode == 0:
        print(f"DOCX written: {docx_path}", file=sys.stdout)
        exported_any = True
    else:
        print(f"WARNING: pandoc DOCX export failed: {result.stderr.strip()}", file=sys.stderr)

    # Try PDF via xelatex
    xelatex = shutil.which("xelatex")
    if xelatex:
        result = _run([pandoc, "--pdf-engine=xelatex", str(md_path), "-o", str(pdf_path)])
        if result.returncode == 0:
            print(f"PDF written:  {pdf_path}", file=sys.stdout)
            exported_any = True
        else:
            print(f"WARNING: pandoc PDF (xelatex) export failed: {result.stderr.strip()}", file=sys.stderr)
    else:
        print("WARNING: xelatex not found — skipping PDF export", file=sys.stderr)

    return 0 if exported_any else 1


def export_with_wkhtmltopdf(md_path: Path) -> int:
    """Fallback: convert markdown to HTML then PDF via wkhtmltopdf."""
    wk = shutil.which("wkhtmltopdf")
    if not wk:
        return None  # signal: not found

    # Write a minimal HTML wrapper
    html_path = md_path.with_suffix(".html")
    pdf_path = md_path.with_suffix(".pdf")
    content = md_path.read_text(encoding="utf-8")
    # Very basic markdown → HTML: just wrap in pre/body so it's readable
    html_content = (
        "<!DOCTYPE html><html><head>"
        '<meta charset="utf-8">'
        "<style>body{font-family:sans-serif;max-width:800px;margin:auto;padding:2em}"
        "pre{white-space:pre-wrap}</style>"
        f"</head><body><pre>{content}</pre></body></html>"
    )
    html_path.write_text(html_content, encoding="utf-8")

    try:
        result = _run([wk, str(html_path), str(pdf_path)])
        if result.returncode == 0:
            print(f"PDF written:  {pdf_path} (via wkhtmltopdf)", file=sys.stdout)
            return 0
        else:
            print(f"WARNING: wkhtmltopdf failed: {result.stderr.strip()}", file=sys.stderr)
            return 1
    finally:
        if html_path.exists():
            html_path.unlink()


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: export_doc.py <path_to_markdown_file>", file=sys.stderr)
        return 1

    md_path = Path(sys.argv[1])
    if not md_path.exists():
        print(f"Error: file not found: {md_path}", file=sys.stderr)
        return 1
    if not md_path.is_file():
        print(f"Error: not a file: {md_path}", file=sys.stderr)
        return 1

    # Step 1 & 2: try pandoc (handles both PDF+DOCX and DOCX-only internally)
    pandoc_result = export_with_pandoc(md_path)
    if pandoc_result is not None:
        # pandoc was found; return its result directly
        return pandoc_result

    # Step 3: pandoc not found — try wkhtmltopdf for PDF at least
    wk_result = export_with_wkhtmltopdf(md_path)
    if wk_result is not None:
        return wk_result

    # Step 4: nothing available
    print(
        "ERROR: No export tools found.\n"
        "To export your business plan, install one of:\n"
        "  • pandoc  — https://pandoc.org/installing.html\n"
        "    (also install texlive-xetex for PDF output)\n"
        "  • wkhtmltopdf — https://wkhtmltopdf.org/downloads.html\n"
        "\nOn Debian/Ubuntu:\n"
        "  sudo apt install pandoc texlive-xetex\n"
        "  # or: sudo apt install wkhtmltopdf",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
