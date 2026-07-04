# SKILLS.md — reusable tooling in mining-utilities

Catalog of the helpers here and the recipes for using them. For the *why* and the
data caveats, see `AGENTS.md`.

## `pdf_utils.py` — read Migrationsverket annual-report PDFs

Handles the two things that otherwise trip you up: the reports are AES-encrypted with
an empty owner password, and every report paginates its tables differently.

Prereqs (once): `../../migration-statistics/.venv/bin/python -m pip install pypdf cryptography`

### API

| Function | Returns | Purpose |
|---|---|---|
| `open_report(spec)` | `PdfReader` | Decrypted reader. `spec` = year (`2025`), filename, or path. Cached. |
| `num_pages(spec)` | `int` | Page count. |
| `page_text(spec, n)` | `str` | Text of **1-indexed** page `n`. |
| `extract_pages(spec, a, b)` | `{n: str}` | Text for 1-indexed inclusive range `a..b`. |
| `find_pages(spec, *kw, case_sensitive=True)` | `{kw: [pages]}` | Pages containing each keyword. |
| `find_table(spec, caption, case_sensitive=True)` | `[pages]` | Pages containing a caption substring. |
| `report_path(spec)` | `Path` | Resolve year/filename → absolute path. |
| `parse_sv_int(s)` | `int \| None` | `"6 741"` / `"46\xa0376"` → `6741`. Handles NBSP/thin-space separators. |
| `parse_sv_pct(s)` | `float \| None` | `"35 %"` → `35.0` (0–100 scale). |

`spec` is flexible everywhere: an `int` year, `"2025"`, `"arsredovisning_2025.pdf"`,
or a full path all resolve to the same report.

### Recipe — locate and read a table (never hard-code pages)

```python
from pdf_utils import find_table, page_text, parse_sv_int

# Table captions drift year to year — search for the caption, then read the page.
for pg in find_table(2025, "Inkomna asylärenden"):
    print(page_text(2025, pg))

# When the caption itself changed (2024 uses "Asylärenden 2022–2024"), search a stable
# fragment or scan for a section keyword instead:
find_table(2024, "Asylärenden")          # -> [53]
```

### Recipe — find where a section moved across years

```python
from pdf_utils import find_pages
for year in range(2025, 2020, -1):
    print(year, find_pages(year, "Asylärenden", "Arbetsmarknadsärenden"))
```

### CLI smoke test

```
../../migration-statistics/.venv/bin/python pdf_utils.py 2025 "Inkomna asylärenden"
```

## Workflow — hand-keying a decision dataset from the PDFs

The reports aren't reliably auto-parseable into tables, so the extraction is
manual-but-audited. Standard loop (see `build_asylum_decisions.py` as the template):

1. **Locate.** `find_table(year, "<caption fragment>")` → page number.
2. **Read.** `page_text(year, pg)` and identify the Totalt columns for first-time /
   extension: received, decided, approval rate.
3. **Key.** Add a `dict(...)` entry to the script's `ROWS` list with `src_pdf_page`,
   `src_table`, and the raw published figures.
4. **Cross-anchor.** Compare the overlap with the adjacent report's window; record any
   material discrepancy in `notes` (see gotcha #2/#3 in `AGENTS.md`).
5. **Build & verify.** Run the script, eyeball the printed yearly sums, and sanity-check
   monotonic/known trends before committing.

Work backwards from the newest report; each report's 3-year window lets you validate the
prior year you already keyed.
