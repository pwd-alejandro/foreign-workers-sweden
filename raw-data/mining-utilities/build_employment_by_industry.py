"""
Downloads SCB table TAB3204 (Employed 15-74 years by region of work, by region,
sex, industrial classification NACE Rev. 2 and region of birth) and writes the
long-format master table
migration-statistics/csv/master_employment_by_industry_birth.csv.

Source (PXWeb v2beta API, JSON-stat2):
  https://api.scb.se/OV0104/v2beta/api/v2/tables/TAB3204/data

Scope: whole of Sweden only (Region == "00"), both sexes combined (Kon == "1+2"),
latest year (2024), employed by region of work (ContentsCode 000002XH), split by
region of birth into born-in-Sweden ("in") vs foreign born ("ut").

ALL SNI2007 industries are downloaded (both the single-letter sections and the
aggregates such as 'D+E', 'M+N', 'A-U+US'); choosing which ones to show is left to
the plotting layer. A handful of codes get a shorter English title via
SIMPLIFIED_NAMES; every other industry keeps the verbatim SCB label.

  A        Agriculture, forestry & fishing
  D+E      Energy & environment
  M+N      Professional, scientific & tech
  P        Education
  Q        Health & social work
  A-U+US   Total   (SCB disclosure protection means this is NOT exactly the sum of
                    the parts -- treat as reported, not computed)

Output columns: year, industry_code, industry_name, region_of_birth, employed
  - industry_code:   verbatim SCB SNI2007 code (may aggregate, e.g. 'D+E')
  - industry_name:   simplified English title where known, else the SCB label
  - region_of_birth: 'born_in_sweden' | 'foreign_born'   (SCB Fodelseregion in / ut)
  - employed:        integer headcount
"""

import csv
import json
import os
import urllib.parse
import urllib.request

API_URL = "https://api.scb.se/OV0104/v2beta/api/v2/tables/TAB3204/data"

# Bracketed keys are kept literal; only the values are percent-encoded (mirrors a
# curl --data-urlencode call, which the SCB v2 API accepts). '*' selects every
# SNI2007 value (filtering to specific industries happens at the plotting layer).
QUERY_PARAMS = [
    ("lang", "en"),
    ("valueCodes[Region]", "00"),
    ("valueCodes[Kon]", "1+2"),
    ("valueCodes[SNI2007]", "*"),
    ("valueCodes[Fodelseregion]", "in,ut"),
    ("valueCodes[ContentsCode]", "000002XH"),
    ("valueCodes[Tid]", "2024"),
    ("outputFormat", "json-stat2"),
]

OUT = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "..", "migration-statistics", "csv", "master_employment_by_industry_birth.csv",
))

# Shorter English titles for the SCB SNI2007 codes we tend to plot; any code not
# listed here keeps its verbatim SCB label.
SIMPLIFIED_NAMES = {
    "A": "Agriculture, forestry & fishing",
    "D+E": "Energy & environment",
    "I": "Hospitality",
    "M+N": "Professional, scientific & tech",
    "P": "Education",
    "Q": "Health & social work",
    "A-U+US": "Total",
}
REGION_OF_BIRTH = {"in": "born_in_sweden", "ut": "foreign_born"}


def _get(url):
    req = urllib.request.Request(url, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _strides(size):
    """Row-major strides for a JSON-stat2 flat value array of the given shape."""
    strides = [1] * len(size)
    for i in range(len(size) - 2, -1, -1):
        strides[i] = strides[i + 1] * size[i + 1]
    return strides


def build():
    # safe='*' keeps the SNI2007 wildcard literal while still encoding '+' and ',' .
    query = "&".join(
        f"{k}={urllib.parse.quote(v, safe='*')}" for k, v in QUERY_PARAMS
    )
    ds = _get(f"{API_URL}?{query}")

    dims = ds["id"]                       # dimension order of the flat value array
    strides = _strides(ds["size"])
    values = ds["value"]

    sni_cat = ds["dimension"]["SNI2007"]["category"]
    sni_index = sni_cat["index"]                                       # code -> pos
    sni_label = sni_cat["label"]                                       # code -> SCB name
    birth_index = ds["dimension"]["Fodelseregion"]["category"]["index"]
    (year,) = ds["dimension"]["Tid"]["category"]["index"].keys()      # single year

    def value_at(sni_code, birth_code):
        coords = {d: 0 for d in dims}     # size-1 dims (Region/Kon/Contents/Tid) -> 0
        coords["SNI2007"] = sni_index[sni_code]
        coords["Fodelseregion"] = birth_index[birth_code]
        flat = sum(coords[dims[i]] * strides[i] for i in range(len(dims)))
        return int(values[flat])

    rows = []
    for sni_code in sni_index:            # preserves API/request order
        for birth_code in birth_index:
            rows.append({
                "year": int(year),
                "industry_code": sni_code,
                "industry_name": SIMPLIFIED_NAMES.get(sni_code, sni_label[sni_code]),
                "region_of_birth": REGION_OF_BIRTH[birth_code],
                "employed": value_at(sni_code, birth_code),
            })

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f, fieldnames=["year", "industry_code", "industry_name",
                           "region_of_birth", "employed"])
        w.writeheader()
        w.writerows(rows)

    print(f"Wrote {OUT} ({len(rows)} rows; year {year})")


if __name__ == "__main__":
    build()
