"""
Builds the asylum decisions-by-type CSV from the Migrationsverket annual reports:

  ../../migration-statistics/mined_datasets/minned_asylum_decisions_by_type.csv

This is the asylum parallel of `build_work_permit_decisions.py`. Scope: "Asylärenden"
(asylum cases) as reported by Migrationsverket, Totalt (women + men), incl. unaccompanied
minors where the source folds them in. Every figure is hand-keyed from a specific
report/table/page; provenance and caveats live in each row's `notes`.

Sourcing convention (see AGENTS.md):
  - Canonical value for year Y = Y's OWN arsredovisning_Y.pdf. Each report prints a 3-year
    window; overlaps were used to cross-check keying (they agree, modulo minor restatement).
  - Table/page numbers drift every year, so each ROW records where it was read from.

═══════════════════════════════════════════════════════════════════════════════════════
METHODOLOGY — read before analysing. Three era-breaks make some columns non-comparable:

1. permit_type: `first-time` is a UNIFORM, COMPARABLE series for the whole 2001-2025 span;
   `extension` is a separate series that only begins meaningfully in 2017.
   Rationale (evidence-backed): the extension category is a structural artifact of Sweden's
   July 2016 temporary-residence-permit law (time-limited permits: 3 yr refugees / 13 mo
   subsidiary), made permanent by the 20 Jul 2021 Aliens Act. Before that, protection meant
   PERMANENT residence, so there was almost nothing to renew — extension applications were
   ~0 (13 received in 2011, 7 in 2012, ~40 in 2015-2016). Reports also confirm the identity
   total == first-time + extension exactly wherever both are printed (2018-2025 + the 2016
   annex). Therefore, to make the whole history comparable WITHOUT inflating the modern era
   by a category that did not historically exist:
     - 2001-2016: extensions ≈ 0 and were not split out, so the reported total IS first-time;
       these rows are emitted as `first-time`. For 2013-2016 (where the source does break out
       a few extension decisions) we use the FIRST-TIME-ONLY decided figure, not the sum.
     - 2017-2025: `first-time` and `extension` are emitted as separate rows.
   Do NOT reconstruct a first-time+extension "total" and chart it against pre-2017 figures —
   that compares a first-time-only past against a first-time+extension present.

2. approval_rate BASIS changes across eras — DO NOT plot as one continuous line:
     - 2017-2025: `bifallsandel (mot avslag)` = grants ÷ (grants + rejections), excluding
       Dublin transfers and withdrawn cases. This is the modern, cleanest measure.
     - 2012-2016: computed here from published granted/rejected COUNTS (grants ÷ (g+r)).
     - 2008-2011: `andel bifall` = share of ASYLUM SEEKERS granted (a different denominator
       — applicants, not merit-decided cases). Higher-level, not directly comparable.
     - 2001-2007: raw first-instance grant/rejection COUNTS where published (persons, not
       cases); several years give only a garbled % → approval_rate left blank.
   Each row's `notes` states the exact basis.

3. number_granted_applications:
     - split years (2017+): derived as round((decisions − Dublin) × approval_rate), i.e.
       Dublin transfers removed first so grants reflect only cases Sweden decided on the
       merits for Sweden (per project decision). Where the report published a Bifall COUNT
       directly (2017), that count is used verbatim instead of deriving.
     - pre-2017 first-time rows: the report's published granted/rejected counts are used
       as-is (approximate "cirka" figures flagged in notes); never derived from the era's
       non-comparable rate.

RELIABLE ACROSS THE WHOLE 2001-2025 SPAN: number_applications_received and
number_decisions_made (asylum CASES received / decided). These are clean table figures and
are the recommended backbone for longitudinal application/decision trends.
═══════════════════════════════════════════════════════════════════════════════════════

Note on 2015: it is the European refugee-crisis PEAK (162,877 first-time applications
received; the ~112,000 decisions in 2016 are that backlog being processed). Treat 2015-2016
as outliers, not a baseline.
"""

import csv
import os

from pdf_utils import report_path

OUT = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "..", "migration-statistics", "mined_datasets",
    "minned_asylum_decisions_by_type.csv",
))

# Per-row fields:
#   year, permit_type, src_year, src_page, src_table,
#   received, decided, dublin,           # case counts (Dublin = subset of decided)
#   bifall_pct,                          # published approval %, if any
#   granted_pub, rejected_pub,           # published grant/reject COUNTS, if any
#   derive_from_rate (bool),             # compute counts from rate (split years only)
#   note
# Any missing field defaults to None / False.
def R(**kw):
    kw.setdefault("dublin", None)
    kw.setdefault("bifall_pct", None)
    kw.setdefault("granted_pub", None)
    kw.setdefault("rejected_pub", None)
    kw.setdefault("derive_from_rate", False)
    kw.setdefault("note", "")
    return kw


ROWS = [
    # ═══════════════ SPLIT YEARS (first-time + extension), 2017-2025 ═══════════════
    R(year=2025, permit_type="first-time", src_year=2025, src_page=21, src_table="Tabell 3.2",
      received=6741, decided=8385, dublin=667, bifall_pct=35, derive_from_rate=True,
      note="Received from Tabell 3.1 (p20); decided+bifallsandel(mot avslag)+Dublin from Tabell 3.2 (p21)."),
    R(year=2025, permit_type="extension", src_year=2025, src_page=21, src_table="Tabell 3.2",
      received=22815, decided=20603, bifall_pct=96, derive_from_rate=True,
      note="Extensions have no Dublin transfers."),

    R(year=2024, permit_type="first-time", src_year=2024, src_page=53, src_table="Tabell 6.2",
      received=9588, decided=10617, dublin=789, bifall_pct=34, derive_from_rate=True,
      note="Combined table (report not yet restructured). Cross-check: 2025 report restates 2024 "
           "first-time received 9588->9927 (+3.5%), decided 10617~10615, bifall 34%~33%. Canonical=own."),
    R(year=2024, permit_type="extension", src_year=2024, src_page=53, src_table="Tabell 6.2",
      received=21388, decided=31458, bifall_pct=97, derive_from_rate=True),

    R(year=2023, permit_type="first-time", src_year=2023, src_page=51, src_table="Figur 6.2",
      received=12498, decided=15907, dublin=1057, bifall_pct=34, derive_from_rate=True,
      note="SCOPE: 2023 report folds Ukraine/mass-flight cases into the asylum table for all years "
           "(2020-2022 reports exclude them); may inflate vs neighbouring reports."),
    R(year=2023, permit_type="extension", src_year=2023, src_page=51, src_table="Figur 6.2",
      received=32990, decided=33782, bifall_pct=97, derive_from_rate=True),

    R(year=2022, permit_type="first-time", src_year=2022, src_page=52, src_table="Figur 6.2",
      received=14816, decided=13178, dublin=1153, bifall_pct=37, derive_from_rate=True,
      note="SCOPE: excludes mass-flight-directive (Ukraine) cases and Ukrainian applications after "
           "24 Feb 2022, per report note."),
    R(year=2022, permit_type="extension", src_year=2022, src_page=52, src_table="Figur 6.2",
      received=28312, decided=29910, bifall_pct=97, derive_from_rate=True),

    R(year=2021, permit_type="first-time", src_year=2021, src_page=55, src_table="Figur 8.2",
      received=11414, decided=12802, dublin=707, bifall_pct=32, derive_from_rate=True),
    R(year=2021, permit_type="extension", src_year=2021, src_page=55, src_table="Figur 8.2",
      received=32007, decided=27799, bifall_pct=97, derive_from_rate=True),

    R(year=2020, permit_type="first-time", src_year=2020, src_page=39, src_table="Figur 6.1",
      received=12991, decided=20980, dublin=1159, bifall_pct=29, derive_from_rate=True,
      note="Decided > received: crisis-era backlog still being cleared."),
    R(year=2020, permit_type="extension", src_year=2020, src_page=39, src_table="Figur 6.1",
      received=27520, decided=29032, bifall_pct=97, derive_from_rate=True),

    R(year=2019, permit_type="first-time", src_year=2019, src_page=47, src_table="Figur 6.1",
      received=21958, decided=24569, dublin=1945, bifall_pct=35, derive_from_rate=True),
    R(year=2019, permit_type="extension", src_year=2019, src_page=47, src_table="Figur 6.1",
      received=36610, decided=19951, bifall_pct=98, derive_from_rate=True),

    R(year=2018, permit_type="first-time", src_year=2018, src_page=56, src_table="Figur 7.2",
      received=21502, decided=35512, dublin=1929, bifall_pct=39, derive_from_rate=True),
    R(year=2018, permit_type="extension", src_year=2018, src_page=56, src_table="Figur 7.2",
      received=7457, decided=11445, bifall_pct=100, derive_from_rate=True),

    R(year=2017, permit_type="first-time", src_year=2017, src_page=40, src_table="Figur 26",
      received=25666, decided=66301, dublin=2690, bifall_pct=47, granted_pub=27205,
      note="Own report gives Bifall COUNTS not a %; granted_pub=27205 used verbatim. "
           "approval_rate 47% (mot avslag) taken from the 2018/2019 reports (agree). "
           "rejected count not published for 2017."),
    R(year=2017, permit_type="extension", src_year=2017, src_page=40, src_table="Figur 26",
      received=18154, decided=12624, bifall_pct=100, granted_pub=11807,
      note="granted_pub=11807 (own report Bifall count); approval_rate 100% from 2018/2019 reports."),

    # ═══════════════ PRE-2017 FIRST-TIME ROWS (relabeled from totals), 2001-2016 ═══════════════
    # Asylum was not split first-time/extension before 2017; extensions were ~0 (permanent
    # residence regime), so the reported total IS first-time. For 2013-2016, where the source
    # breaks out a few extension DECISIONS, we use the first-time-only decided figure (not the sum)
    # so `first-time` stays a clean, uniform series across the whole span.
    R(year=2016, permit_type="first-time", src_year=2016, src_page=148, src_table="Bilaga 14",
      received=28939, decided=111979, dublin=9901, granted_pub=67258, rejected_pub=30423,
      note="Crisis backlog: 111,979 first-time decisions (peak). Extensions negligible (~47 received, "
           "40 decided) and excluded. granted/rejected = first-time beviljade/avslag from the statistical "
           "annex; övriga (withdrawn) excluded. approval_rate computed from counts (mot-avslag basis "
           "differs from the 77% the 2018 report cites)."),
    R(year=2015, permit_type="first-time", src_year=2015, src_page=16, src_table="Figur 4 + Figur 114",
      received=162877, decided=58802, dublin=5790, granted_pub=32631, rejected_pub=16821,
      note="PEAK YEAR: 162,877 first-time applications received (European refugee crisis) — outlier, "
           "not a baseline. First-time decided 58,802 (40 extension decisions excluded). granted 32,631 "
           "from Figur 114; rejected 16,821 cross-sourced from the 2016 annex first-time avslag."),
    R(year=2014, permit_type="first-time", src_year=2014, src_page=73, src_table="Tabell 23",
      received=81301, decided=53503, dublin=6424, granted_pub=32500, rejected_pub=9400,
      note="First-time decided 53,503 (1,785 extension decisions excluded). granted/rejected are 'cirka' "
           "prose (p74); the 2016 annex reports a higher first-time rejection count (17,299) on a wider basis."),
    R(year=2013, permit_type="first-time", src_year=2013, src_page=50, src_table="Tabell 16",
      received=54264, decided=49870, dublin=8645, granted_pub=30800, rejected_pub=12100,
      note="First-time received = Inkomna asylärenden förstagångs (54,264). First report to break out "
           "extensions (8,544 received / 6,853 decided) — excluded to keep first-time comparable. "
           "granted/rejected 'cirka' prose (p51)."),
    R(year=2012, permit_type="first-time", src_year=2012, src_page=29, src_table="Figur 10",
      received=43907, decided=36526, dublin=5981, granted_pub=12500, rejected_pub=13000,
      note="No extension category yet (7 extension applications in 2012) → reported total is first-time. "
           "granted/rejected 'cirka' prose (p31)."),
    R(year=2011, permit_type="first-time", src_year=2011, src_page=24, src_table="Figur 12",
      received=29670, decided=30404, dublin=2717, bifall_pct=30, granted_pub=9000, rejected_pub=18000,
      note="No extension category (13 in 2011) → total is first-time. approval_rate 30% = 'andel "
           "asylsökande som fick bifall' (share of applicants — different basis from modern mot-avslag). "
           "granted 'drygt 9 000' / rejected 'cirka 18 000' (approx, p26)."),
    R(year=2010, permit_type="first-time", src_year=2010, src_page=22, src_table="Figur 6",
      received=31905, decided=31256, dublin=3932, bifall_pct=28, granted_pub=8724,
      note="Total is first-time (no extension category). approval_rate 28% = share of applicants granted "
           "(p23). granted 8,724 (prose); rejected not published."),
    R(year=2009, permit_type="first-time", src_year=2009, src_page=24, src_table="Tabell 3",
      received=24232, decided=27394, dublin=3604, bifall_pct=27,
      note="Total is first-time (no extension category). approval_rate 27% = share of applicants granted "
           "(prose). No grant/reject counts published; counts left blank (era rate not comparable to base)."),
    R(year=2008, permit_type="first-time", src_year=2008, src_page=18, src_table="Tabell 3",
      received=24860, decided=33845, dublin=3414, bifall_pct=24,
      note="Total is first-time (no extension category). approval_rate 24% = share of applicants granted "
           "(prose). Dublin=varav Dublinärenden (p19). No grant/reject counts published."),
    R(year=2007, permit_type="first-time", src_year=2007, src_page=14, src_table="Tabell 3",
      received=38347, decided=32492, dublin=3414, bifall_pct=48, granted_pub=15639,
      note="Total is first-time. granted 15,639 persons (48% of applicants, first-instance) from prose. "
           "rejected not published. approval basis = applicant share."),
    R(year=2006, permit_type="first-time", src_year=2006, src_page=10, src_table="Tabell 4",
      received=27224, decided=18838, dublin=2267, bifall_pct=42, granted_pub=7940,
      note="Total is first-time. granted 7,940 persons (42%) cross-sourced from the 2007 report (own gives "
           "% only). Dublin 2,267 from 2008 report. approval basis = applicant share."),
    R(year=2005, permit_type="first-time", src_year=2005, src_page=11, src_table="Tabell 4",
      received=17662, decided=21325,
      note="Total is first-time. Grant rate given only as a font-garbled % in prose; approval_rate/counts "
           "left blank. Received/decided are clean table figures. Old 2-instance system "
           "(Migrationsverket + Utlänningsnämnden)."),
    R(year=2004, permit_type="first-time", src_year=2004, src_page=14, src_table="Tabell 6",
      received=23941, decided=35308,
      note="Total is first-time. 'grundärenden' terminology. Prose cites 3,399 first-instance grants only "
           "(not a comparable total-grant measure) → granted left blank. Received/decided clean."),
    R(year=2003, permit_type="first-time", src_year=2003, src_page=10, src_table="Tabell 3",
      received=33853, decided=31334,
      note="Total is first-time. 'grundärenden'. Grant given only as a % in prose → approval_rate/counts blank."),
    R(year=2002, permit_type="first-time", src_year=2002, src_page=12, src_table="Tabell 3",
      received=33168, decided=27157, granted_pub=5514, rejected_pub=18497,
      note="Total is first-time. granted/rejected = first-instance persons (5,514 positive / 18,497 negative, "
           "prose p9). Persons-basis, not case-basis; 'grundärenden'. approval computed from counts."),
    R(year=2001, permit_type="first-time", src_year=2001, src_page=14, src_table="Tabell 5",
      received=23730, decided=16860, granted_pub=4650, rejected_pub=10600,
      note="Total is first-time. granted/rejected = 'cirka' first-instance persons (~4,650 / ~10,600, "
           "prose p13). Approximate, persons-basis. 'grundärenden'. Earliest own report."),
]


def derive(r):
    """Return (approval_rate, rejection_rate, granted, rejected, calc_note)."""
    decided = r["decided"]
    dublin = r["dublin"] or 0
    bifall = r["bifall_pct"]
    g_pub, r_pub = r["granted_pub"], r["rejected_pub"]

    # approval_rate: published % first, else from published counts
    if bifall is not None:
        approval = round(bifall / 100, 4)
    elif g_pub is not None and r_pub is not None and (g_pub + r_pub) > 0:
        approval = round(g_pub / (g_pub + r_pub), 4)
    else:
        approval = None
    rejection = round(1 - approval, 4) if approval is not None else None

    # counts
    if g_pub is not None:
        granted, rejected = g_pub, r_pub
        calc = f"granted={g_pub} (published){'' if r_pub is None else f', rejected={r_pub} (published)'}"
    elif r["derive_from_rate"] and approval is not None and decided is not None:
        substantive = decided - dublin
        granted = round(substantive * approval)
        rejected = substantive - granted
        calc = (f"substantive = decided - Dublin = {decided} - {dublin} = {substantive}; "
                f"granted = round({substantive} * {approval}) = {granted}; rejected = {rejected} "
                f"(Dublin excluded — not decided in Sweden on the merits)")
    else:
        granted = rejected = None
        calc = "grant/reject counts not derived (era rate not comparable to decided base)"
    return approval, rejection, granted, rejected, calc


def build_rows():
    out = []
    for r in ROWS:
        approval, rejection, granted, rejected, calc = derive(r)
        src = f"arsredovisning_{r['src_year']}.pdf"
        notes = [f"source: {src} p{r['src_page']} ({r['src_table']})", calc]
        if approval is not None:
            notes.append(f"approval_rate={approval}, rejection_rate={rejection}")
        if r["note"]:
            notes.append(r["note"])
        out.append({
            "year": r["year"],
            "permit_type": r["permit_type"],
            "number_applications_received": r["received"],
            "number_decisions_made": r["decided"],
            "number_dublin_transfers": r["dublin"],
            "number_granted_applications": granted,
            "number_rejected_applications": rejected,
            "approval_rate": approval,
            "rejection_rate": rejection,
            "source_page": f"{src}#{r['src_page']}",
            "notes": " | ".join(notes),
        })
    order = {"first-time": 0, "extension": 1, "total": 2}
    out.sort(key=lambda x: (x["year"], order[x["permit_type"]]))
    return out


def main():
    for r in ROWS:
        p = report_path(r["src_year"])
        if not p.exists():
            raise FileNotFoundError(f"missing source report: {p}")

    rows = build_rows()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=[
            "year", "permit_type",
            "number_applications_received", "number_decisions_made",
            "number_dublin_transfers",
            "number_granted_applications", "number_rejected_applications",
            "approval_rate", "rejection_rate", "source_page", "notes",
        ])
        w.writeheader()
        w.writerows(rows)

    print(f"Wrote {OUT} ({len(rows)} rows)")
    for r in rows:
        g = r["number_granted_applications"]
        print(f"  {r['year']} {r['permit_type']:10s} recv={str(r['number_applications_received']):>7} "
              f"dec={str(r['number_decisions_made']):>7} granted={str(g):>7} "
              f"approval={r['approval_rate']}")


if __name__ == "__main__":
    main()
