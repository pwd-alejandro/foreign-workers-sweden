# AGENTS.md — mining-utilities

Operating context for anyone (human or agent) turning Migrationsverket raw data
into the analysis CSVs. Read this before touching a build script or a PDF.

## What lives here

Two independent data lineages feed `../../migration-statistics/`:

| Lineage | Raw source | Extraction | Build script |
|---|---|---|---|
| **A. Work permits** (by occupation) | `../granted_permits_2015_2025/*.xls[x]` | **Automated** (openpyxl/xlrd) | `build_csv.py` → derived by `build_granted_by_*` / `add_occupation_category.py` |
| **B. Decisions by case type** (asylum, labour-market, …) | `../annual_reports_2001_2025/arsredovisning_YYYY.pdf` | **Hand-keyed** from PDF tables | `build_work_permit_decisions.py`, `build_asylum_decisions.py` |
| **C. Recruitment time** | SCB open API | API pull | `build_average_recruitment_time.py` |

The Excel workbooks contain **work permits only** — no asylum, family, student, or
other migration types. Every other migration category comes from the annual-report
PDFs (lineage B).

## Reading the annual-report PDFs

Use **`pdf_utils.py`** — never re-implement PDF opening. The reports are AES-encrypted
with an *empty* owner password; `pdf_utils.open_report()` decrypts them (requires the
`cryptography` package). See `SKILLS.md` for the function catalog and recipes.

Install deps into the local venv once:

```
../../migration-statistics/.venv/bin/python -m pip install pypdf cryptography
```

Run scripts with that interpreter (the venv has stale shebangs, so call the binary
directly rather than activating):

```
../../migration-statistics/.venv/bin/python build_asylum_decisions.py
```

### Structure of the reports

Section **3 "Prövning av ärenden" (Examination of cases)** in modern reports breaks
decisions out by case type, each with parallel intake/decision/pending tables:

| § (2025) | Swedish | English | Notes |
|---|---|---|---|
| 3.1 | Asylärenden | Asylum | core refugee flow |
| 3.2 | Tillfälligt skydd (massflyktsdirektivet) | Temporary protection (Ukraine/mass-influx) | from 2022 |
| 3.3 | Vidarebosättningsärenden | Resettlement / quota refugees | annual quota (900 in 2025) |
| 3.4 | Anknytningsärenden | Family reunification | |
| 3.5 | Arbetsmarknadsärenden | Labour-market (work) | mined by `build_work_permit_decisions.py` |
| 3.6 | EES-ärenden | EEA | |
| 3.7 | Studerandeärenden | Students | |
| 3.8 / 3.9 | Viserings- / Besöksärenden | Visas / visits | |
| 3.10 | Medborgarskapsärenden | Citizenship | |

## ⚠️ Gotchas — read before keying any year

1. **Layout drift — never hard-code a page or table number.** Section, table, and page
   numbers move every year. The 2025 report was explicitly restructured ("Ny uppbyggnad
   av årsredovisningen"): asylum intake/decisions are split across `Tabell 3.1`/`3.2`.
   The 2024 report puts the same data in one combined `Tabell 6.2 Asylärenden 2022–2024`.
   Older reports differ again. **Always `find_table()` by caption text**, then read.

2. **3-year overlapping windows → cross-anchor, don't blindly trust.** Each report prints
   the target year plus the two prior. Use the overlap to validate keying: e.g. the 2025
   report's "2024" column should roughly match the 2024 report's "2024" column.

3. **Reports restate prior years.** The overlap is *close, not identical*. Observed for
   asylum first-time **received**: 2024 = 9,588 (2024 report) vs 9,927 (2025 report),
   a ~3.5% restatement; **decisions** barely move (10,617 vs 10,615). Intake figures are
   more volatile than decision figures. **Convention: the canonical value for year Y is
   Y's own report**; adjacent reports are used only to cross-check, and material
   discrepancies get recorded in the row's `notes`.

4. **`Bifallsandel (mot avslag)` is a grant-vs-reject rate, NOT grant-vs-all-decisions.**
   Its denominator is (grants + rejections) only — it *excludes* Dublin transfers,
   immediate-enforcement, and withdrawn/written-off cases, which are part of "Totalt
   avgjorda". So `granted ≈ decisions × approval_rate` (as done for work permits) is only
   an approximation for asylum and slightly overstates grants. Whichever derivation is
   used, state it explicitly in `notes`. (This is a live methodology question — see the
   header of `build_asylum_decisions.py`.)

5. **Gender splits.** Asylum tables report Kvinnor / Män / Totalt. The mined CSVs
   currently keep only Totalt; the gendered figures are available if needed later.

6. **Pre-2008 scope break.** The 15 Dec 2008 labour-migration reform (and earlier agency
   renamings — "Statens Invandrarverk" before 2000) changed category scope and labels.
   Pre-2008 figures are not directly comparable; flag every such row in `notes`. See the
   extensive per-year `scope_note`s in `build_work_permit_decisions.py` for the pattern.

## Glossary (Swedish → English)

| Swedish | English |
|---|---|
| Inkomna (ärenden) | Received / incoming (cases) |
| Avgjorda (ärenden) | Decided / determined (cases) |
| Öppna ärenden | Open / pending cases |
| Förstagångsärenden | First-time cases |
| Förlängningsärenden | Extension / renewal cases |
| Beviljade | Granted |
| Avslag | Rejection / refusal |
| Bifallsandel (mot avslag) | Approval rate (grants ÷ (grants+rejections)) |
| Genomsnittlig handläggningstid | Average processing time |
| Genomsnittlig kötid | Average queue/waiting time |
| Dublinöverföringar | Dublin transfers |
| Barn utan vårdnadshavare (BUV) | Unaccompanied minors |
| Preskriberat avlägsnandebeslut | Time-barred removal order |

## Output conventions for the hand-keyed decision CSVs (lineage B)

- One row per (year, permit_type) where permit_type ∈ {`first-time`, `extension`}.
- Columns mirror `minned_work_permit_decisions_by_type.csv`:
  `year, permit_type, number_applications_received, number_decisions_made,
  number_granted_applications, number_rejected_applications, approval_rate,
  rejection_rate, source_page, notes`.
- `source_page` = `arsredovisning_YYYY.pdf#<page>`; `notes` records every computation,
  every cross-report discrepancy, and every scope caveat. Full provenance is the point.
- Prefer **relative paths** (resolved from `__file__`) so scripts run in the current
  repo layout. (The older `build_*` scripts still carry hard-coded absolute paths from
  before the reorg — fix on touch.)
