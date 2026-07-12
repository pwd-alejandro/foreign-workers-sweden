"""
Derives migration-statistics/mined_datasets/minned_employment_by_industry_birth.csv
from the master table master_employment_by_industry_birth.csv.

Pivots the long master (two rows per industry: born-in-Sweden / foreign-born) into
one row per industry and adds the shares the unit-chart plots need. Every industry
present in the master is carried through; the plotting layer decides which to show.

Changes vs. the master:
  1. the two region-of-birth rows are pivoted into columns
        born_in_sweden, foreign_born
  2. total = born_in_sweden + foreign_born  (sum of the two reported parts)
  3. share columns are added:
        pct_born_in_sweden = born_in_sweden / total * 100
        pct_foreign_born   = foreign_born   / total * 100
  4. rows are sorted by total, largest first, ties broken by higher Swedish-born
     share (the same order the plot uses).

Note: SCB disclosure protection means the 'Total' industry (A-U+US) is not exactly
the sum of the individual industries; every industry's `total` here is the sum of
its own two reported parts, not a recomputation of the aggregate.

Output columns: year, industry_code, industry_name, born_in_sweden, foreign_born,
                total, pct_born_in_sweden, pct_foreign_born
"""

import csv
import os

SRC = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "..", "migration-statistics", "csv", "master_employment_by_industry_birth.csv",
))
OUT = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "..", "migration-statistics", "mined_datasets",
    "minned_employment_by_industry_birth.csv",
))


def build():
    # Collect the two parts per industry, keyed by code (name/year carried along).
    ind = {}
    with open(SRC, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            code = r["industry_code"]
            d = ind.setdefault(code, {
                "year": int(r["year"]),
                "industry_code": code,
                "industry_name": r["industry_name"],
                "born_in_sweden": 0,
                "foreign_born": 0,
            })
            d[r["region_of_birth"]] += int(r["employed"])

    rows = []
    for d in ind.values():
        total = d["born_in_sweden"] + d["foreign_born"]
        d["total"] = total
        d["pct_born_in_sweden"] = round(100 * d["born_in_sweden"] / total, 1) if total else 0.0
        d["pct_foreign_born"] = round(100 * d["foreign_born"] / total, 1) if total else 0.0
        rows.append(d)

    # Largest first; ties -> higher Swedish-born share (matches the plot's sort).
    rows.sort(key=lambda d: (-d["total"], -d["pct_born_in_sweden"]))

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=[
            "year", "industry_code", "industry_name", "born_in_sweden",
            "foreign_born", "total", "pct_born_in_sweden", "pct_foreign_born"])
        w.writeheader()
        w.writerows(rows)

    print(f"Wrote {OUT} ({len(rows)} rows)")


if __name__ == "__main__":
    build()
