"""
Builds two CSVs from the Migrationsverket annual reports (2001-2025):

  - minned_work_permit_decisions.csv         (totals: one row per year)
  - minned_work_permit_decisions_by_type.csv (one row per year per permit_type)

Scope: "Arbetsmarknadsärenden" (labour-market cases) as reported by Migrationsverket.
This category includes work permits (arbetstagare) plus their relatives (anhöriga),
own-business owners (egna företagare), guest researchers, and international exchange.
Pre-2008 (before the Dec 2008 labour migration reform) the category was narrower
and scope/labels are not directly comparable - notes flag that on each row.

Each year is sourced from THAT year's own arsredovisning_YYYY.pdf wherever the
own report provides the breakdown; for a few years where the own report lacks
first-time/extension/bifallsandel detail, the next year's report (which carries
three years of history) is used and noted.

Derived columns:
  - number_granted_applications  = round(decisions * approval_rate) when bifallsandel given
  - number_rejected_applications = decisions - granted
  - approval_rate                = granted / decisions when computed from counts
  - rejection_rate               = 1 - approval_rate
Every calculation is recorded in `notes`.
"""

import csv
import os

OUT_DIR = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------------
# Source records. Each entry is (year, source_page_pdf, first_*, ext_*, total_*, scope_note)
# Values mined from the per-year reports unless `src` notes otherwise.
# bifall is given as published rounded percentage (or computed from beviljade/avgjorda).
# Where a field is None it could not be read from the indicated table.
# ---------------------------------------------------------------------------

# Format per year: dict with keys:
#   src_year, src_pdf_page, src_table (label),
#   first_in, first_dec, first_bifall_pct,
#   ext_in,   ext_dec,   ext_bifall_pct,
#   total_in, total_dec,
#   scope_note (str)
ROWS = [
    dict(year=2025, src_year=2025, src_pdf_page=30, src_table="Table 3.15 + 3.16",
         first_in=33463, first_dec=38041, first_bifall_pct=58,
         ext_in=39175, ext_dec=45984, ext_bifall_pct=80,
         total_in=72638, total_dec=84025,
         scope_note=""),
    dict(year=2024, src_year=2024, src_pdf_page=76, src_table="Table 8.3",
         first_in=36881, first_dec=44261, first_bifall_pct=55,
         ext_in=42711, ext_dec=47070, ext_bifall_pct=83,
         total_in=79592, total_dec=91331,
         scope_note=""),
    dict(year=2023, src_year=2023, src_pdf_page=67, src_table="Figure 8.3",
         first_in=47160, first_dec=55187, first_bifall_pct=63,
         ext_in=44415, ext_dec=53774, ext_bifall_pct=86,
         total_in=91575, total_dec=108961,
         scope_note=""),
    dict(year=2022, src_year=2022, src_pdf_page=71, src_table="Figure 8.3",
         first_in=64915, first_dec=58704, first_bifall_pct=69,
         ext_in=39176, ext_dec=30213, ext_bifall_pct=87,
         total_in=104091, total_dec=88917,
         scope_note=""),
    dict(year=2021, src_year=2021, src_pdf_page=68, src_table="Figure 9.3",
         first_in=56095, first_dec=52655, first_bifall_pct=73,
         ext_in=39771, ext_dec=32059, ext_bifall_pct=89,
         total_in=95866, total_dec=84714,
         scope_note=""),
    dict(year=2020, src_year=2020, src_pdf_page=66, src_table="Figure 7.3",
         first_in=46351, first_dec=45719, first_bifall_pct=68,
         ext_in=38609, ext_dec=33748, ext_bifall_pct=89,
         total_in=84960, total_dec=79467,
         scope_note=""),
    dict(year=2019, src_year=2019, src_pdf_page=92, src_table="Figure 7.1",
         first_in=59307, first_dec=52547, first_bifall_pct=80,
         ext_in=31890, ext_dec=30208, ext_bifall_pct=87,
         total_in=91197, total_dec=82755,
         scope_note=""),
    dict(year=2018, src_year=2018, src_pdf_page=100, src_table="Figure 8.2",
         first_in=49079, first_dec=51455, first_bifall_pct=78,
         ext_in=23749, ext_dec=27201, ext_bifall_pct=87,
         total_in=72828, total_dec=78656,
         scope_note=""),
    dict(year=2017, src_year=2017, src_pdf_page=69, src_table="Figure 68",
         first_in=38395, first_dec=41588, first_bifall_pct=75,
         ext_in=20339, ext_dec=26395, ext_bifall_pct=78,
         total_in=58734, total_dec=67983,
         scope_note=""),
    dict(year=2016, src_year=2016, src_pdf_page=56, src_table="Figure 68",
         first_in=32885, first_dec=32172, first_bifall_pct=75,
         ext_in=20458, ext_dec=15012, ext_bifall_pct=86,
         total_in=53343, total_dec=47184,
         scope_note=""),
    dict(year=2015, src_year=2015, src_pdf_page=69, src_table="Figure 74",
         first_in=37163, first_dec=35297, first_bifall_pct=74,  # bifall from 2016 report Fig 68
         ext_in=21558, ext_dec=19025, ext_bifall_pct=89,         # bifall from 2016 report Fig 68
         total_in=58721, total_dec=54322,
         scope_note="bifallsandel sourced from arsredovisning_2016.pdf p56 Figure 68 (the 2015 own report omits bifallsandel in its main labour-market table)"),
    dict(year=2014, src_year=2014, src_pdf_page=116, src_table="Figure 73",
         first_in=32546, first_dec=32846, first_bifall_pct=75,  # first/ext split + bifall from 2016 Fig 68
         ext_in=19979, ext_dec=18967, ext_bifall_pct=89,
         total_in=52525, total_dec=51813,
         scope_note="first-time/extension split and bifallsandel sourced from arsredovisning_2016.pdf p56 Figure 68 (2014 own report only gives totals)"),
    dict(year=2013, src_year=2013, src_pdf_page=92, src_table="Figure 60",
         first_in=37367, first_dec=36135, first_bifall_pct=None,   # bifall not in own table
         ext_in=19336, ext_dec=16887, ext_bifall_pct=None,
         total_in=56703, total_dec=53022,
         scope_note="first-time/extension split sourced from arsredovisning_2015.pdf p69 Figure 74 (2013 own report only gives totals). bifallsandel not separately published for the broad category in either year."),
    dict(year=2012, src_year=2012, src_pdf_page=66, src_table="Figure 47",
         first_in=None, first_dec=None, first_bifall_pct=None,
         ext_in=None, ext_dec=None, ext_bifall_pct=None,
         total_in=49327, total_dec=49257,
         scope_note="own report gives only Arbetsmarknadsärenden totals. Prose states ~35,000 förstagångs for arbetstagare (workers only, excluding anhöriga) so a full first-time/extension split cannot be reconstructed."),
    dict(year=2011, src_year=2011, src_pdf_page=51, src_table="Figure 42",
         first_in=None, first_dec=None, first_bifall_pct=None,
         ext_in=None, ext_dec=None, ext_bifall_pct=None,
         total_in=46334, total_dec=39319,
         scope_note="own report gives only Arbetsmarknadsärenden totals. Prose: ~77% of decisions were förstagångs but bifallsandel only stated for narrow sub-categories."),
    dict(year=2010, src_year=2010, src_pdf_page=51, src_table="Figure 37 + Figure 40",
         first_in=26346, first_dec=23357, first_bifall_pct=None,  # beviljade=20777 -> bifall computed in build step
         ext_in=None, ext_dec=None, ext_bifall_pct=None,
         total_in=32575, total_dec=28638,
         scope_note="first-time inkomna/avgjorda/beviljade from Figure 40 p52 (beviljade=20777); first-time bifall computed as 20777/23357. Extension figures derivable as totals minus first-time (inkomna ~6229, avgjorda ~5281) but not published, so left blank."),
    dict(year=2009, src_year=2009, src_pdf_page=55, src_table="Arbetstillståndsärenden row",
         first_in=17230, first_dec=16302, first_bifall_pct=None,  # beviljade=13877 from 2010 Fig 40 -> compute
         ext_in=None, ext_dec=None, ext_bifall_pct=None,
         total_in=22438, total_dec=21399,
         scope_note="first-time inkomna/avgjorda from arsredovisning_2010.pdf p52 Figure 40 (own report does not split). first-time beviljade=13877 (2010 Fig 40), bifall computed."),
    dict(year=2008, src_year=2008, src_pdf_page=52, src_table="Arbetstillståndsärenden row",
         first_in=12794, first_dec=12895, first_bifall_pct=None,  # beviljade=11032 -> compute
         ext_in=4663, ext_dec=4711, ext_bifall_pct=None,
         total_in=17457, total_dec=17606,
         scope_note="first-time inkomna from p53 prose (12,794); förlängning inkomna=4,663 and avgjorda=4,711 from p61 prose; first-time beviljade=11,032 from 2010 Fig 40; first-time bifall computed as 11032/12895. Labour migration reform of 15 Dec 2008 fundamentally widened scope after this year."),
    dict(year=2007, src_year=2007, src_pdf_page=45, src_table="Tabell 31",
         first_in=None, first_dec=None, first_bifall_pct=None,
         ext_in=None, ext_dec=None, ext_bifall_pct=None,
         total_in=14371, total_dec=13454,
         scope_note="Pre-2008 reform: 'Arbetstillståndsärenden' refers to a narrower work-permit category (no first-time/extension split published in own report). 2008 beviljade column gives 2006/2007/2008 = 7102/8632/11032; 2007 bifall ≈ 8632/13454 = 64% if applied to total, but interpretation differs from post-2010 'Arbetsmarknadsärenden'."),
    dict(year=2006, src_year=2006, src_pdf_page=25, src_table="Tabell 19",
         first_in=None, first_dec=None, first_bifall_pct=None,
         ext_in=None, ext_dec=None, ext_bifall_pct=None,
         total_in=11967, total_dec=12077,
         scope_note="Pre-2008 reform; narrow Arbetstillstånd category, no first-time/extension split. 2008 report lists 2006 beviljade=7102 (bifall ~59% of 12077)."),
    dict(year=2005, src_year=2005, src_pdf_page=23, src_table="Tabell 15",
         first_in=None, first_dec=None, first_bifall_pct=None,
         ext_in=None, ext_dec=None, ext_bifall_pct=None,
         total_in=11888, total_dec=11744,
         scope_note="Pre-2008 reform; narrow Arbetstillstånd category."),
    dict(year=2004, src_year=2004, src_pdf_page=41, src_table="Tabell 27",
         first_in=9620, first_dec=9998, first_bifall_pct=None,  # 2004 first beviljade not isolated; total beviljade=11992
         ext_in=3941, ext_dec=4134, ext_bifall_pct=None,
         total_in=13561, total_dec=14132,
         scope_note="Pre-2008 reform: first-time = total-extension (inkomna 13561-3941=9620; avgjorda 14132-4134=9998). Total beviljade=11992; total bifall = 11992/14132 = 84.9% computed in build step. Per-type bifall not published."),
    dict(year=2003, src_year=2003, src_pdf_page=31, src_table="Tabell 17 + 2004 Tabell 27",
         first_in=12971, first_dec=13411, first_bifall_pct=None,  # 2003 own gives first avgjorda; ext from 2004 Tabell 27
         ext_in=5506, ext_dec=6079, ext_bifall_pct=None,
         total_in=18477, total_dec=19490,
         scope_note="Pre-2008 reform: 2003 own report Tabell 17 gives 'varav arbetsmarknadsärenden 13,411' under förstagångs avgjorda. Total inkomna/avgjorda and extension breakdown from arsredovisning_2004.pdf p41 Tabell 27. Total beviljade 2003=16,034; total bifall 16034/19490 = 82.3% computed in build step."),
    dict(year=2002, src_year=2002, src_pdf_page=23, src_table="Tabell 9 + 2004 Tabell 27",
         first_in=12946, first_dec=14700, first_bifall_pct=None,
         ext_in=5815, ext_dec=5368, ext_bifall_pct=None,
         total_in=18761, total_dec=20068,
         scope_note="Pre-2008 reform: 2002 own report Tabell 9 gives 'varav arbetsmarknadsärenden 14,700' under förstagångs avgjorda. Total inkomna/avgjorda and extension breakdown from arsredovisning_2004.pdf p41 Tabell 27. Total beviljade 2002=16,732; total bifall 16732/20068 = 83.4% computed in build step."),
    dict(year=2001, src_year=2001, src_pdf_page=7, src_table="Tabell 1",
         first_in=None, first_dec=13393, first_bifall_pct=None,
         ext_in=None, ext_dec=None, ext_bifall_pct=None,
         total_in=None, total_dec=None,
         scope_note="Pre-2008 reform; 2001 own report (Tabell 1) gives 'varav arbetsmarknadsärenden 13,393' under förstagångs avgjorda (sökts vid ambassad). Total Arbetsmarknadsärenden inkomna/avgjorda not separately published; not comparable to later years."),
]

# 2008 beviljade for 2008 = 11,032 (from 2008 report p60 'Beviljade arbetstillstånd 7 102 8 632 11 032' = 2006/2007/2008)
# We attach as separately-known beviljade where useful
TOTAL_BEVILJADE = {
    2002: 16732,
    2003: 16034,
    2004: 11992,
}


def calc_first_bifall_pct(row):
    """Compute first-time bifall% from known beviljade where the report exposes it."""
    beviljade_by_year_2010_fig40 = {2008: 11032, 2009: 13877, 2010: 20777}
    if row["first_bifall_pct"] is None and row["year"] in beviljade_by_year_2010_fig40:
        b = beviljade_by_year_2010_fig40[row["year"]]
        d = row["first_dec"]
        if d:
            return round(b / d * 100, 1), f"first_bifall computed as {b}/{d} = {b/d*100:.1f}% (beviljade from arsredovisning_2010.pdf p52 Figure 40)"
    return row["first_bifall_pct"], ""


def build_csvs():
    # by-type rows: first-time and extension
    by_type_path = os.path.join(OUT_DIR, "minned_work_permit_decisions_by_type.csv")
    totals_path = os.path.join(OUT_DIR, "minned_work_permit_decisions.csv")

    by_type_rows = []
    totals_rows = []

    for r in ROWS:
        year = r["year"]
        src_filename = f"arsredovisning_{r['src_year']}.pdf"
        page = r["src_pdf_page"]
        table = r["src_table"]
        base_src = f"{src_filename} p{page} ({table})"
        scope_note = r["scope_note"]

        # Recompute first_bifall_pct from 2010-Fig40 beviljade where possible
        fb_pct, fb_note = calc_first_bifall_pct(r)

        # ----------------- by-type: first-time -----------------
        notes = []
        first_in = r["first_in"]
        first_dec = r["first_dec"]
        first_granted = first_rejected = None
        first_app = first_rej = None
        if first_dec is not None and fb_pct is not None:
            first_granted = round(first_dec * fb_pct / 100)
            first_rejected = first_dec - first_granted
            first_app = round(fb_pct / 100, 4)
            first_rej = round(1 - first_app, 4)
            notes.append(f"granted = round(decisions * bifallsandel) = round({first_dec} * {fb_pct}%) = {first_granted}")
            notes.append(f"rejected = decisions - granted = {first_dec} - {first_granted} = {first_rejected}")
            notes.append(f"approval_rate = {fb_pct}/100 = {first_app}; rejection_rate = 1 - approval_rate = {first_rej}")
            if fb_note:
                notes.append(fb_note)
        if scope_note:
            notes.append(scope_note)
        by_type_rows.append({
            "year": year,
            "permit_type": "first-time",
            "number_applications_received": first_in,
            "number_decisions_made": first_dec,
            "number_granted_applications": first_granted,
            "number_rejected_applications": first_rejected,
            "approval_rate": first_app,
            "rejection_rate": first_rej,
            "source_page": f"{src_filename}#{page}",
            "notes": " | ".join(notes),
        })

        # ----------------- by-type: extension -----------------
        notes = []
        ext_in = r["ext_in"]
        ext_dec = r["ext_dec"]
        eb_pct = r["ext_bifall_pct"]
        ext_granted = ext_rejected = ext_app = ext_rej = None
        if ext_dec is not None and eb_pct is not None:
            ext_granted = round(ext_dec * eb_pct / 100)
            ext_rejected = ext_dec - ext_granted
            ext_app = round(eb_pct / 100, 4)
            ext_rej = round(1 - ext_app, 4)
            notes.append(f"granted = round(decisions * bifallsandel) = round({ext_dec} * {eb_pct}%) = {ext_granted}")
            notes.append(f"rejected = decisions - granted = {ext_dec} - {ext_granted} = {ext_rejected}")
            notes.append(f"approval_rate = {eb_pct}/100 = {ext_app}; rejection_rate = 1 - approval_rate = {ext_rej}")
        if scope_note:
            notes.append(scope_note)
        by_type_rows.append({
            "year": year,
            "permit_type": "extension",
            "number_applications_received": ext_in,
            "number_decisions_made": ext_dec,
            "number_granted_applications": ext_granted,
            "number_rejected_applications": ext_rejected,
            "approval_rate": ext_app,
            "rejection_rate": ext_rej,
            "source_page": f"{src_filename}#{page}",
            "notes": " | ".join(notes),
        })

        # ----------------- totals -----------------
        notes = []
        total_in = r["total_in"]
        total_dec = r["total_dec"]
        # Prefer to sum first+extension granted to compute total granted (more accurate than weighted avg).
        total_granted = total_rejected = total_app = total_rej = None
        if first_granted is not None and ext_granted is not None:
            total_granted = first_granted + ext_granted
            notes.append(f"granted = first-time granted + extension granted = {first_granted} + {ext_granted} = {total_granted}")
            if total_dec:
                total_rejected = total_dec - total_granted
                total_app = round(total_granted / total_dec, 4)
                total_rej = round(1 - total_app, 4)
                notes.append(f"rejected = decisions - granted = {total_dec} - {total_granted} = {total_rejected}")
                notes.append(f"approval_rate = granted / decisions = {total_granted}/{total_dec} = {total_app}")
                notes.append(f"rejection_rate = 1 - approval_rate = {total_rej}")
        elif year in TOTAL_BEVILJADE and total_dec:
            # pre-2010 reports give total beviljade directly
            total_granted = TOTAL_BEVILJADE[year]
            total_rejected = total_dec - total_granted
            total_app = round(total_granted / total_dec, 4)
            total_rej = round(1 - total_app, 4)
            notes.append(f"granted = published total beviljade (arsredovisning_2004.pdf p41 Tabell 27) = {total_granted}")
            notes.append(f"rejected = decisions - granted = {total_dec} - {total_granted} = {total_rejected}")
            notes.append(f"approval_rate = granted / decisions = {total_granted}/{total_dec} = {total_app}")
            notes.append(f"rejection_rate = 1 - approval_rate = {total_rej}")
        if scope_note:
            notes.append(scope_note)
        totals_rows.append({
            "year": year,
            "number_applications_received": total_in,
            "number_decisions_made": total_dec,
            "number_granted_applications": total_granted,
            "number_rejected_applications": total_rejected,
            "approval_rate": total_app,
            "rejection_rate": total_rej,
            "source_page": f"{src_filename}#{page}",
            "notes": " | ".join(notes),
        })

    # Write totals CSV
    totals_rows.sort(key=lambda x: x["year"])
    with open(totals_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=[
            "year",
            "number_applications_received",
            "number_decisions_made",
            "number_granted_applications",
            "number_rejected_applications",
            "approval_rate",
            "rejection_rate",
            "source_page",
            "notes",
        ])
        w.writeheader()
        w.writerows(totals_rows)

    # Write by-type CSV
    by_type_rows.sort(key=lambda x: (x["year"], 0 if x["permit_type"] == "first-time" else 1))
    with open(by_type_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=[
            "year",
            "permit_type",
            "number_applications_received",
            "number_decisions_made",
            "number_granted_applications",
            "number_rejected_applications",
            "approval_rate",
            "rejection_rate",
            "source_page",
            "notes",
        ])
        w.writeheader()
        w.writerows(by_type_rows)

    print(f"Wrote {totals_path} ({len(totals_rows)} rows)")
    print(f"Wrote {by_type_path} ({len(by_type_rows)} rows)")


if __name__ == "__main__":
    build_csvs()
