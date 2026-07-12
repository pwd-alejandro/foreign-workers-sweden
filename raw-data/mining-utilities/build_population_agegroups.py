"""
Derives migration-statistics/mined_datasets/minned_population_by_agegroup.csv from
the master table master_population_by_background.csv.

Changes vs. the master (per project spec):
  1. year and background pass through unchanged.
  2. sex (men / women) is collapsed — population is summed to a single total.
  3. an `age_group` categorical column is added next to `age`:
        young        = 0-19
        working_age  = 20-65
        elderly      = 66+   (66-99 and the '100+' aggregate)

Single-year `age` rows are preserved (one row per year x background x age); the
age_group is added beside them.

Output columns: year, background, age, age_group, population
"""

import csv
import os

SRC = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "..", "migration-statistics", "csv", "master_population_by_background.csv",
))
OUT = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "..", "migration-statistics", "mined_datasets", "minned_population_by_agegroup.csv",
))


def age_numeric(age):
    """'100+' -> 100; else int(age)."""
    return 100 if age == "100+" else int(age)


def age_group(age):
    a = age_numeric(age)
    if a <= 19:
        return "young"
    if a <= 65:
        return "working_age"
    return "elderly"


def build():
    # Sum population across sex, keyed by (year, background, age).
    totals = {}
    with open(SRC, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            key = (int(r["year"]), r["background"], r["age"])
            totals[key] = totals.get(key, 0) + int(r["population"])

    rows = [{
        "year": year,
        "background": background,
        "age": age,
        "age_group": age_group(age),
        "population": pop,
    } for (year, background, age), pop in totals.items()]

    rows.sort(key=lambda r: (r["year"], r["background"], age_numeric(r["age"])))

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["year", "background", "age", "age_group", "population"])
        w.writeheader()
        w.writerows(rows)

    print(f"Wrote {OUT} ({len(rows)} rows)")


if __name__ == "__main__":
    build()
