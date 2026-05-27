# Master CSVs — Migrationsverket work-permit statistics

Tidy long-format. Every Swedish label has a paired `_en` English column.
Counts are in `granted_count`. `year_month` is `YYYY-MM` for monthly rows or `YYYY` for annual-only rows. `is_year_total = True` flags the "Totalt" annual column (so you can sum without double-counting).

| File | Rows | Years | Dimensions |
|---|---:|---|---|
| `master_work_permits_by_occupation_field.csv` | 1,417 | 2021–2026 | year, month, permit_type (first-time / extension), occupation_field |
| `master_work_permits_by_occupation_group.csv` | 15,829 | 2015–2026 | + occupation_group (specific role, ~140) — 2015–2020 are annual first-time only, see methodology note below |
| `master_work_permits_by_citizenship.csv` | 11,930 | 2021–2026 | year, month, permit_type, citizenship (~110 countries) |
| `master_residence_permits_by_category.csv` | 2,483 | 2021–2026 | year, month, permit_basis (work/family/asylum/study/EU), sub_category |
| `master_residence_permits_by_gender.csv` | 474 | 2022–2026 | year, permit_basis, sub_category, gender |
| `master_residence_permits_by_persontype.csv` | 632 | 2022–2026 | year, permit_basis, sub_category, person_type (Adult / Child / Unaccompanied) |
| `master_historical_2005_2015.csv` | 283 | 2005–2015 | year, parent_category, sub_category — long-run trend, coarser categories |
| `master_work_permits_decisions.csv` | 8 | 2019–2026 | year, applications received, decisions made, granted, rejections, approval/rejection rate, open cases. Annual except 2026 (YTD). 2022 is sourced from the Årsredovisning rather than the monthly table — see scope column. |
| `decisions_metrics_dictionary.csv` | 8 | – | Swedish↔English column reference for the decisions file. |

Source files in `../granted-work-permits/`, `../granted-residence-permits-overview/`, `../historical/`. Build scripts: `../build_csv.py` (grants), `../scrape_decisions.py` (decisions via Wayback). Translation dictionaries: `../translations.py`.

## Gaps (relative to the original question set)
- **Rejection / decided counts** — now in `master_work_permits_decisions.csv`, scraped from Wayback Machine snapshots of Migrationsverket's `arbete.html` page (where the agency renders the table as HTML, not file). One row per reporting year. 2022 is sourced from the Årsredovisning 2022 (Figur 8.3, page 71) because Wayback has no snapshot in the Dec 2022 → Feb 2023 window where the table would have shown full-year 2022 totals; granted/rejection figures for that year are derived from the report's rounded bifallsandel (69%) and may differ from the true count by ±50. 2026 is YTD.
- **No age groups** beyond Adult / Child-in-family / Unaccompanied minor.
- **No cross-tabulation** between profession × citizenship × gender — only marginals.
- **Decisions only at total work-permit level** — Migrationsverket does NOT publish rejection/decision counts broken down by profession or nationality. So rejection-rate trends can only be analysed at the aggregate level.

## Notes on permit_type
- 2015–2020: source files explicitly state "Exklusive förlängningar" — only first-time permits are reported. The mined `_by_occupation` and `_by_category` tables therefore contain no extension rows for these years (rather than zero-filled rows).
- 2021: only first-time permits are reported (no extension column in source). The mined tables zero-fill the extension universe (every (field, group) seen in 2022–2025) for 2021 so the schema stays rectangular.
- 2022+: split into "förstagångs" (first-time) and "förlängning" (extension).

## Methodology — 2015–2020 backfill and the SSYK96 → SSYK 2012 transition

The 2015–2020 work-permit xlsx files (sourced from Migrationsverket via Wayback Machine snapshots: 2015–2018 from `20191212134328`, 2019–2020 from `20220126135742`) have a different layout from the modern 2021+ files. They report annual totals only (no monthly columns), first-time permits only (extensions are not published per occupation for these years), and a single combined sheet rather than the modern field/group/citizenship split. They are parsed by `_parse_occupation_group_legacy()` in `../build_csv.py`.

The bigger issue is that Migrationsverket migrated its occupational classification from **SSYK96** to **SSYK 2012** during this window:

- **2015**: pure SSYK96-era labels for skill-level fields (e.g. `Arbete inom jordbruk, trädgård, skogsbruk och fiske`, `Hantverksarbete inom byggverksamhet och tillverkning`, `Saknar SSYK`), interleaved with a few SSYK 2012-style field labels.
- **2016**: SSYK96 labels with an explicit `(SSYK96)` suffix, alongside SSYK 2012 labels for newly-classified grants.
- **2017**: mostly SSYK 2012 with a few residual `(SSYK96)` labels.
- **2018+**: pure SSYK 2012.

To preserve fidelity to the source we **keep the original Swedish occupation_field and occupation_group labels verbatim** in `master_work_permits_by_occupation_group.csv` (the `(SSYK96)` suffix is preserved when present). English translations for these legacy labels live in `../translations.py` under `YRKESOMRADE` and `YRKESGRUPP`. Because group identifiers differ across the SSYK transition, the same underlying role can appear in 2015 under one Swedish label and in 2022 under another — and the labels do not join cleanly.

The reconciliation happens at the **occupation_category** level (a coarser, 22-bucket clustering we define ourselves, see `../mined_datasets/add_occupation_category.py`). Every SSYK96 group and every transitional 2015–2017 label is mapped to the same category schema as the SSYK 2012 groups (e.g. both `Dataspecialister (SSYK96)` and `IT-arkitekter, systemutvecklare och testledare` roll up to `IT & software`). This means `minned_work_permits_granted_by_category.csv` is the recommended grain for any longitudinal analysis spanning the 2015 ↔ 2025 range; the finer `_by_occupation` grain is faithful to the source taxonomy but is not safe to join across the SSYK boundary without care.

## Workers ≠ all "Arbetsmarknad"
In the residence-permits files, basis "Arbetsmarknad" includes sub-categories like Arbetstagare (employees), Egen företagare (self-employed), Forskare (researchers), Anhörig (family of workers). For "work permits" in the strict sense, filter to `sub_category_sv == 'Arbetstagare'`.

## Sources for decision rates by year

Each reporting year is sourced from Migrationsverket's `arbete.html` page (monthly statistics table, captured by the Wayback Machine), except 2022 which uses the Årsredovisning PDF (no usable Wayback snapshot exists for full-year 2022).

  - 2019 — https://web.archive.org/web/20200203003251/https://www.migrationsverket.se/om-migrationsverket/statistik/arbete.html
  - 2020 — https://web.archive.org/web/20210203012023/https://www.migrationsverket.se/om-migrationsverket/statistik/arbete.html
  - 2021 — https://web.archive.org/web/20220126135742/https://www.migrationsverket.se/om-migrationsverket/statistik/arbete.html
  - 2022 (Årsredovisning, Figur 8.3 p. 71) — https://web.archive.org/web/20230311182425/https://www.migrationsverket.se/download/18.4cda87071866b3f3f2d24a/1677165402506/Migrationsverkets%20årsredovisning%202022.pdf
  - 2023 — https://web.archive.org/web/20240117091456/https://www.migrationsverket.se/om-migrationsverket/statistik/arbete.html
  - 2024 — https://web.archive.org/web/20250119120810/https://www.migrationsverket.se/om-migrationsverket/statistik/arbete.html
  - 2025 — https://web.archive.org/web/20260119010047/https://www.migrationsverket.se/om-migrationsverket/statistik/arbete.html
  - 2026 (YTD — live page) — https://www.migrationsverket.se/om-migrationsverket/statistik/arbete.html

## Migrationsverket Årsredovisning (annual report) PDFs, 2001–2025

Background source documents with detailed permit decision breakdowns (work-permit figures in Figur 8.3 of the 2022 report, equivalent figures in other years). 2001–2018 archives are sourced via the Wayback Machine because the live site only retains the most recent ~3 years. 2000 was not captured by Wayback. Note: scope/structure of reports changes substantially across the 25-year span (e.g. the agency was named "Statens Invandrarverk" before 2000 and the table layouts were progressively redesigned).

  - 2001 — https://web.archive.org/web/20030805235438/http://www.migrationsverket.se/pdffiler/arsredov/arr2001.pdf
  - 2002 — https://web.archive.org/web/20030517190652/http://www.migrationsverket.se/pdffiler/arsredov/arr2002.pdf
  - 2003 — https://web.archive.org/web/20050406224428/http://www.migrationsverket.se/infomaterial/om_verket/ek_redovisningar/arr2003.pdf
  - 2004 — https://web.archive.org/web/20050406231400/http://www.migrationsverket.se/infomaterial/om_verket/ek_redovisningar/arr2004.pdf
  - 2005 — https://web.archive.org/web/20060926071048/http://www.migrationsverket.se/infomaterial/om_verket/ek_redovisningar/arr2005.pdf
  - 2006 — https://web.archive.org/web/20070224151940/http://www.migrationsverket.se/infomaterial/om_verket/ek_redovisningar/arr_2006.pdf
  - 2007 — https://web.archive.org/web/20101207194135/http://www.migrationsverket.se/download/18.56e4f4801246221d25680001010/arr_2007.pdf
  - 2008 — https://web.archive.org/web/20100215055041/http://www.migrationsverket.se/download/18.56e4f4801246221d25680001007/arr_2008.pdf
  - 2009 — https://web.archive.org/web/20100331100729/http://www.migrationsverket.se/download/18.78fcf371269cd4cda980001324/arr2009.pdf
  - 2010 — https://web.archive.org/web/20170422033707/https://www.migrationsverket.se/download/18.5e83388f141c129ba63135f3/1485556231601/Årsredovisning_2010.pdf
  - 2011 — https://web.archive.org/web/20190715112523/https://www.migrationsverket.se/download/18.5e83388f141c129ba63129e8/1485556220956/Årsredovisning%202011.pdf
  - 2012 — https://web.archive.org/web/20190208185741/https://www.migrationsverket.se/download/18.5e83388f141c129ba6312e1c/1485556225850/Årsredovisning%202012.pdf
  - 2013 — https://web.archive.org/web/20190715112502/https://www.migrationsverket.se/download/18.7c00d8e6143101d166d29f5/1485556213873/Årsredovisning%202013.pdf
  - 2014 — https://web.archive.org/web/20190715112509/https://www.migrationsverket.se/download/18.39a9cd9514a346077212ead/1485556228297/Årsredovisning%202014.pdf
  - 2015 — https://web.archive.org/web/20190715112501/https://www.migrationsverket.se/download/18.2d998ffc151ac3871593f89/1485556210405/Årsredovisning%202015.pdf
  - 2016 — https://web.archive.org/web/20190715112513/https://www.migrationsverket.se/download/18.4100dc0b159d67dc6142a4e/1487775100129/Årsredovisning%202016.pdf
  - 2017 — https://web.archive.org/web/20190715112511/https://www.migrationsverket.se/download/18.4cb46070161462db1137cf/1519296859864/Migrationsverkets%20årsredovisning%202017.pdf
  - 2018 — https://web.archive.org/web/20190318133429/https://www.migrationsverket.se/download/18.748d859516793fb65f91654/1550847536193/Migrationsverket_Årsredovisning_2018.pdf
  - 2019 — https://web.archive.org/web/20201228175255/https://www.migrationsverket.se/download/18.2b2a286016dabb81a186962/1582201496682/Årsredovisning%202019.pdf
  - 2020 — https://web.archive.org/web/20220130184849/https://www.migrationsverket.se/download/18.2fa4056d1775f05c203633/1614757755760/Migrationsverket_ÅR_2020.pdf
  - 2021 — https://web.archive.org/web/20220228143107/https://www.migrationsverket.se/download/18.6b4387bd17dc72a9925fec/1645777608413/Migrationsverket_ÅR_2021.pdf
  - 2022 — https://web.archive.org/web/20230311182425/https://www.migrationsverket.se/download/18.4cda87071866b3f3f2d24a/1677165402506/Migrationsverkets%20årsredovisning%202022.pdf
  - 2023 — https://www.migrationsverket.se/download/18.2cd2e409193b84c506a2fb82/1738845281528/Migrationsverkets_arsredovisning_2023.pdf
  - 2024 — https://www.migrationsverket.se/download/18.2cd2e409193b84c506a346f2/1744638139545/Migrationsverkets_arsredovisning_2024.pdf
  - 2025 — https://www.migrationsverket.se/download/18.f09188f19bb7cf3a2ad60/1771595185205/Migrationsverkets_arsredovisning_2025.pdf
