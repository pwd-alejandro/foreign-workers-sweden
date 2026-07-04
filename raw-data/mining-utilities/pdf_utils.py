"""Utilities for reading Migrationsverket annual-report PDFs (arsredovisning_YYYY.pdf).

Why this module exists
----------------------
The annual reports in ``raw-data/annual_reports_2001_2025/`` are the source for the
hand-keyed decision datasets (see ``build_work_permit_decisions.py`` and
``build_asylum_decisions.py``). Unlike the work-permit *xlsx* workbooks, these PDFs
are not machine-parsed into a table automatically — the figures are transcribed by
hand — but reliable *text* extraction makes that transcription fast and auditable.

Two gotchas this module handles for you:

1. **Encryption.** Every report is AES-encrypted with an *empty* owner password (no
   user password). pypdf opens them only if you call ``decrypt("")`` first, and only
   if the ``cryptography`` package is installed. ``open_report()`` does both.
2. **Layout drift.** Table numbers and page numbers move from year to year
   (asylum intake is "Tabell 3.1" on p20 in the 2025 report but numbered/paged
   differently in older ones). So never hard-code a page — use ``find_pages()`` /
   ``find_table()`` to locate a table by its caption text, then read that page.

Dependencies (install into the local venv)::

    migration-statistics/.venv/bin/python -m pip install pypdf cryptography

Typical use::

    from pdf_utils import open_report, find_table, page_text, parse_sv_int

    pages = find_table("arsredovisning_2025.pdf", "Inkomna asylärenden")
    print(page_text("arsredovisning_2025.pdf", pages[0]))
    n = parse_sv_int("6 741")   # -> 6741
"""
from __future__ import annotations

import re
from pathlib import Path
from functools import lru_cache

from pypdf import PdfReader

# Reports live two directories up from this file: <repo>/raw-data/annual_reports_2001_2025/
REPORTS_DIR = Path(__file__).resolve().parents[1] / "annual_reports_2001_2025"


def report_path(spec) -> Path:
    """Resolve a report reference to an absolute path.

    Accepts a full path, a bare filename ("arsredovisning_2025.pdf"), or a year
    (int or str, e.g. 2025 / "2025").
    """
    p = Path(str(spec))
    if p.is_absolute() and p.exists():
        return p
    s = str(spec)
    if re.fullmatch(r"(19|20)\d{2}", s):
        return REPORTS_DIR / f"arsredovisning_{s}.pdf"
    # bare filename
    cand = REPORTS_DIR / s
    return cand if cand.exists() else p


@lru_cache(maxsize=None)
def _reader(path_str: str) -> PdfReader:
    r = PdfReader(path_str)
    if r.is_encrypted:
        # Migrationsverket reports use an empty owner password.
        r.decrypt("")
    return r


def open_report(spec) -> PdfReader:
    """Return a decrypted ``PdfReader`` for a report (path / filename / year)."""
    return _reader(str(report_path(spec)))


def num_pages(spec) -> int:
    return len(open_report(spec).pages)


def page_text(spec, page_number: int) -> str:
    """Text of a single **1-indexed** page ('' if empty)."""
    return open_report(spec).pages[page_number - 1].extract_text() or ""


def extract_pages(spec, start: int, end: int) -> dict[int, str]:
    """{page_number: text} for the 1-indexed inclusive range ``start..end``."""
    r = open_report(spec)
    return {i: (r.pages[i - 1].extract_text() or "") for i in range(start, end + 1)}


def find_pages(spec, *keywords, case_sensitive: bool = True) -> dict[str, list[int]]:
    """Map each keyword to the 1-indexed pages whose text contains it."""
    r = open_report(spec)
    hits: dict[str, list[int]] = {k: [] for k in keywords}
    for i, page in enumerate(r.pages, start=1):
        t = page.extract_text() or ""
        hay = t if case_sensitive else t.casefold()
        for k in keywords:
            needle = k if case_sensitive else k.casefold()
            if needle in hay:
                hits[k].append(i)
    return hits


def find_table(spec, caption_substring: str, case_sensitive: bool = True) -> list[int]:
    """1-indexed pages containing ``caption_substring`` (e.g. a table caption)."""
    return find_pages(spec, caption_substring, case_sensitive=case_sensitive)[caption_substring]


# ---------------------------------------------------------------------------
# Value parsing helpers — Swedish number/percent formatting
# ---------------------------------------------------------------------------
def parse_sv_int(s):
    """Parse a Swedish-formatted integer. '6 741' / '6\xa0741' / '46 376' -> int.

    Returns None for blank / non-numeric input. Handles regular spaces, non-breaking
    spaces and thin spaces used as thousands separators.
    """
    if s is None:
        return None
    if isinstance(s, (int,)):
        return s
    if isinstance(s, float):
        return None if s != s else int(round(s))
    t = re.sub(r"[\s   ]", "", str(s))
    m = re.search(r"-?\d+", t)
    return int(m.group(0)) if m else None


def parse_sv_pct(s):
    """Parse a percentage token like '35%' / '35 %' / '35' -> 35.0 (float, 0-100).

    Returns None if no number is present.
    """
    if s is None:
        return None
    m = re.search(r"-?\d+(?:[.,]\d+)?", str(s))
    if not m:
        return None
    return float(m.group(0).replace(",", "."))


if __name__ == "__main__":
    # Smoke test / quick CLI: `python pdf_utils.py 2025 "Inkomna asylärenden"`
    import sys

    spec = sys.argv[1] if len(sys.argv) > 1 else "2025"
    print(f"{report_path(spec).name}: {num_pages(spec)} pages")
    if len(sys.argv) > 2:
        for pg in find_table(spec, sys.argv[2]):
            print(f"\n===== page {pg} =====\n{page_text(spec, pg)}")