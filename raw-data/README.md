# raw-data

Raw source data and the scripts that turn it into the workable datasets used by
the analysis (`../migration-statistics/migration-analysis.ipynb`). 

```
raw-data/
├── annual_reports_2001_2025/   raw — Migrationsverket annual reports (PDF)
├── granted_permits_2015_2025/  raw — yearly work-permits-granted workbooks
└── mining-utilities/           code that turns the raw data into the master / derived CSVs
```

## Where the raw data comes from

All raw data originates from **Migrationsverket** (the Swedish Migration Agency).
One derived dataset also pulls from the **Statistics Sweden (SCB)** open API
(recruitment-time series). Older files are sourced via the **Internet Archive
Wayback Machine** because the live site only retains the most recent few years.

| Folder | Contents | Source |
| --- | --- | --- |
| `annual_reports_2001_2025/` | `arsredovisning_YYYY.pdf` — Migrationsverket's annual reports (Årsredovisning), 2001–2025. Used as the source for the hand-keyed work-permit decision figures. | Migrationsverket (older years via Wayback — see URL list at the bottom) |
| `granted_permits_2015_2025/` | `Beviljade arbetstillstånd YYYY` — work permits granted, broken down by occupation field/group. One `.xls`/`.xlsx` per year, 2015–2025. | Migrationsverket (2015–2018 via Wayback snapshot `20191212134328`, 2019–2020 via `20220126135742`, 2021+ from the live site) |

## How it becomes the analysis datasets

The scripts in `mining-utilities/` run in two stages. Stage 1 reads the raw
workbooks and writes the one master CSV; stage 2 reads that master (plus the
annual-report figures and the SCB API) to build the small derived datasets the
notebook actually loads.

### Stage 1 — raw → master CSV (`../migration-statistics/csv/`)

- **`translations.py`** — Swedish→English label dictionaries (`YRKESOMRADE`,
  `YRKESGRUPP`, `PERMIT_TYPE`). Not run on its own; imported by `build_csv.py` so
  every Swedish label gets a paired English column.
- **`build_csv.py`** — reads the `.xls`/`.xlsx` workbooks from
  `granted_permits_2015_2025/` and writes the long-format master table
  `master_work_permits_by_occupation_group.csv` (handles both the 2015–2020
  legacy layout and the 2021+ modern layout; see that folder's `README.md` for
  the SSYK96 → SSYK 2012 methodology).

### Stage 2 — master + reports + SCB API → derived datasets (`../migration-statistics/mined_datasets/`)

- **`build_granted_by_occupation.py`** — `master_work_permits_by_occupation_group.csv`
  → `minned_work_permits_granted_by_occupation.csv`.
- **`add_occupation_category.py`** — adds a coarser `occupation_category` column to
  `minned_work_permits_granted_by_occupation.csv` (edits it in place); this is what
  makes the data joinable across the SSYK classification change.
- **`build_granted_by_category.py`** — `minned_work_permits_granted_by_occupation.csv`
  → **`minned_work_permits_granted_by_category.csv`**.
- **`build_work_permit_decisions.py`** — hand-keyed from each year's own
  `arsredovisning_YYYY.pdf` (see `annual_reports_2001_2025/`); writes
  **`minned_work_permit_decisions_by_type.csv`** (first-time vs. extension
  decisions, approval/rejection rates).
- **`build_average_recruitment_time.py`** — pulls from the SCB open API; writes
  **`minned_average_recruitment_time_by_industry.csv`**.

The three datasets in **bold** are the ones loaded by
`../migration-statistics/migration-analysis.ipynb`;
`minned_work_permits_granted_by_occupation.csv` is an intermediate feeding the
`_by_category` build.

> **Note on paths:** these scripts were written with hard-coded absolute paths
> pointing at the original layout (`migration-statistics/...`). They are kept here
> for provenance and reproducibility; after this reorganization their input/output
> paths will need updating before they can be re-run.

## Source URLs — Migrationsverket Årsredovisning (annual report) PDFs, 2001–2025

The live site only retains the most recent ~3 years, so 2001–2018 are sourced via
the Wayback Machine. 2000 was not captured. Note that report scope and table
layout change substantially across the 25-year span (the agency was named
"Statens Invandrarverk" before 2000, and the tables were progressively redesigned).

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
