"""
Downloads SCB table UtlSvBakgGrov (Number of persons by region, foreign/Swedish
background, age, sex and year) and writes the long-format master table
migration-statistics/csv/master_population_by_background.csv.

Source (PXWeb v1 API):
  https://api.scb.se/OV0104/v1/doris/en/ssd/START/BE/BE0101/BE0101Q/UtlSvBakgGrov

Scope: whole of Sweden only (Region == "00"); no regional split.
Covers 2002-2024, single years of age 0-99 plus the aggregate "100+", both
backgrounds (foreign / Swedish) and both sexes (men / women).

Output columns: year, background, age, sex, population
  - background: 'foreign' | 'Swedish'   (SCB UtlBakgrund 1 / 2)
  - age:        '0'..'99' | '100+'       (verbatim SCB Alder codes; '100+' is 100 and older)
  - sex:        'men' | 'women'          (SCB Kon 1 / 2)
  - population: integer headcount
"""

import csv
import json
import os
import urllib.request

API_URL = "https://api.scb.se/OV0104/v1/doris/en/ssd/START/BE/BE0101/BE0101Q/UtlSvBakgGrov"

OUT = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "..", "migration-statistics", "csv", "master_population_by_background.csv",
))

BACKGROUND = {"1": "foreign", "2": "Swedish"}
SEX = {"1": "men", "2": "women"}


def _get(url, data=None):
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8") if data is not None else None,
        headers={"Content-Type": "application/json"},
        method="POST" if data is not None else "GET",
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def age_sort_key(age):
    """'100+' sorts after '99'; everything else numerically."""
    return 100 if age == "100+" else int(age)


def build():
    meta = _get(API_URL)
    var = {v["code"]: v for v in meta["variables"]}
    ages = var["Alder"]["values"]           # ['0'..'99','100+']
    years = var["Tid"]["values"]            # ['2002'..'2024']

    query = {
        "query": [
            {"code": "Region", "selection": {"filter": "item", "values": ["00"]}},
            {"code": "UtlBakgrund", "selection": {"filter": "item", "values": ["1", "2"]}},
            {"code": "Alder", "selection": {"filter": "item", "values": ages}},
            {"code": "Kon", "selection": {"filter": "item", "values": ["1", "2"]}},
            {"code": "Tid", "selection": {"filter": "item", "values": years}},
        ],
        "response": {"format": "json"},
    }
    payload = _get(API_URL, query)

    rows = []
    for entry in payload["data"]:
        region, bg, age, sex, year = entry["key"]
        (pop,) = entry["values"]
        rows.append({
            "year": int(year),
            "background": BACKGROUND[bg],
            "age": age,
            "sex": SEX[sex],
            "population": int(pop),
        })

    rows.sort(key=lambda r: (r["year"], r["background"], r["sex"], age_sort_key(r["age"])))

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["year", "background", "age", "sex", "population"])
        w.writeheader()
        w.writerows(rows)

    print(f"Wrote {OUT} ({len(rows)} rows; years {rows[0]['year']}-{rows[-1]['year']})")


if __name__ == "__main__":
    build()
