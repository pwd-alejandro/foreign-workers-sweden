# Master CSV — Migrationsverket work-permit statistics

Tidy long-format. Every Swedish label has a paired `_en` English column.
Counts are in `granted_count`. `year_month` is `YYYY-MM` for monthly rows or `YYYY` for annual-only rows. `is_year_total = True` flags the "Totalt" annual column (so you can sum without double-counting).

| File | Rows | Years | Dimensions |
|---|---:|---|---|
| `master_work_permits_by_occupation_group.csv` | ~15,800 | 2015–2026 | year, month, permit_type (first-time / extension), occupation_field, occupation_group (specific role, ~140) — 2015–2020 are annual first-time only, see methodology note below |

Source files in `../../raw-data/granted_permits_2015_2025/`. Build script: `../../raw-data/mining-utilities/build_csv.py`. Translation dictionaries: `../../raw-data/mining-utilities/translations.py`.

This master is the input to the derived datasets in `../mined_datasets/` (via `build_granted_by_occupation.py` → `add_occupation_category.py` → `build_granted_by_category.py`).

## Notes on permit_type
- 2015–2020: source files explicitly state "Exklusive förlängningar" — only first-time permits are reported. The mined `_by_occupation` and `_by_category` tables therefore contain no extension rows for these years (rather than zero-filled rows).
- 2021: only first-time permits are reported (no extension column in source). The mined tables zero-fill the extension universe (every (field, group) seen in 2022–2025) for 2021 so the schema stays rectangular.
- 2022+: split into "förstagångs" (first-time) and "förlängning" (extension).

## Methodology — 2015–2020 backfill and the SSYK96 → SSYK 2012 transition

The 2015–2020 work-permit xlsx files (sourced from Migrationsverket via Wayback Machine snapshots: 2015–2018 from `20191212134328`, 2019–2020 from `20220126135742`) have a different layout from the modern 2021+ files. They report annual totals only (no monthly columns), first-time permits only (extensions are not published per occupation for these years), and a single combined sheet rather than the modern field/group split. They are parsed by `_parse_occupation_group_legacy()` in `../../raw-data/mining-utilities/build_csv.py`.

The bigger issue is that Migrationsverket migrated its occupational classification from **SSYK96** to **SSYK 2012** during this window:

- **2015**: pure SSYK96-era labels for skill-level fields (e.g. `Arbete inom jordbruk, trädgård, skogsbruk och fiske`, `Hantverksarbete inom byggverksamhet och tillverkning`, `Saknar SSYK`), interleaved with a few SSYK 2012-style field labels.
- **2016**: SSYK96 labels with an explicit `(SSYK96)` suffix, alongside SSYK 2012 labels for newly-classified grants.
- **2017**: mostly SSYK 2012 with a few residual `(SSYK96)` labels.
- **2018+**: pure SSYK 2012.

To preserve fidelity to the source we **keep the original Swedish occupation_field and occupation_group labels verbatim** in `master_work_permits_by_occupation_group.csv` (the `(SSYK96)` suffix is preserved when present). English translations for these legacy labels live in `../../raw-data/mining-utilities/translations.py` under `YRKESOMRADE` and `YRKESGRUPP`. Because group identifiers differ across the SSYK transition, the same underlying role can appear in 2015 under one Swedish label and in 2022 under another — and the labels do not join cleanly.

The reconciliation happens at the **occupation_category** level (a coarser, 22-bucket clustering we define ourselves, see `../../raw-data/mining-utilities/add_occupation_category.py`). Every SSYK96 group and every transitional 2015–2017 label is mapped to the same category schema as the SSYK 2012 groups (e.g. both `Dataspecialister (SSYK96)` and `IT-arkitekter, systemutvecklare och testledare` roll up to `IT & software`). This means `../mined_datasets/minned_work_permits_granted_by_category.csv` is the recommended grain for any longitudinal analysis spanning the 2015 ↔ 2025 range; the finer `_by_occupation` grain is faithful to the source taxonomy but is not safe to join across the SSYK boundary without care.
