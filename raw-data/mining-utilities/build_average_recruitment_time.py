"""
Downloads SCB table KV15RekTid07 (Average recruitment time, in months, Business
sector by industrial classification NACE Rev. 2, by quarter) and writes it to
minned_average_recruitment_time_by_industry.csv.

Source:
  https://www.statistikdatabasen.scb.se/pxweb/en/ssd/START__AM__AM0701__AM0701C/KV15RekTid07/

API endpoint (PXWeb v1):
  https://api.scb.se/OV0104/v1/doris/en/ssd/START/AM/AM0701/AM0701C/KV15RekTid07

KV15RekTid07 only covers 2015K2 onwards. The deprecated predecessor table
KVRekTid07 (AM0701D, "Old tables, not updated") covers 2009K1–2015K1 with the
same NACE Rev. 2 industry breakdown. Its JSON API path returns HTTP 400, but
the same data is published as a bulk CSV (TAB2127). We pull 2015K1 from that
bulk file to close the one-quarter gap right before KV15RekTid07 begins.
"""

import csv
import io
import json
import os
import urllib.request
import zipfile

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_PATH = os.path.join(OUT_DIR, "minned_average_recruitment_time_by_industry.csv")
API_URL = "https://api.scb.se/OV0104/v1/doris/en/ssd/START/AM/AM0701/AM0701C/KV15RekTid07"
OLD_BULK_URL = "https://www.statistikdatabasen.scb.se/Resources/PX/bulk/ssd/en/TAB2127_en.zip"

INDUSTRY_CODES = [
    "A-S", "A", "B+C", "D+E", "F", "G", "H",
    "I", "J", "K+L", "M", "N", "P+Q", "R+S",
]

QUERY = {
    "query": [
        {"code": "SNI2007", "selection": {"filter": "item", "values": INDUSTRY_CODES}},
        {"code": "ContentsCode", "selection": {"filter": "item", "values": ["000000HA", "000000H9"]}},
    ],
    "response": {"format": "json"},
}


def fetch():
    req = urllib.request.Request(
        API_URL,
        data=json.dumps(QUERY).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_2015k1_from_old_table():
    """Return {industry_code: (avg, moe)} for 2015K1 from the deprecated table.

    The bulk CSV has one row per (industry, quarter, observation_kind), where
    observation_kind is "Average recruitment" or "Margin of error". Industry
    labels look like "B+C mining, quarrying, manufacturing" — the first
    whitespace-separated token is the SNI2007 code we use elsewhere.
    """
    with urllib.request.urlopen(OLD_BULK_URL) as resp:
        zdata = resp.read()
    with zipfile.ZipFile(io.BytesIO(zdata)) as zf:
        text = zf.read(zf.namelist()[0]).decode("utf-8")
    reader = csv.DictReader(io.StringIO(text))
    value_col = "Average recruitment time, in months, private sector (KV)"
    out: dict[str, dict[str, str]] = {}
    for row in reader:
        if row["quarter"] != "2015K1":
            continue
        code = row["industrial classification (NACE Rev. 2)"].split(" ", 1)[0]
        entry = out.setdefault(code, {})
        if row["observations"] == "Average recruitment":
            entry["avg"] = row[value_col]
        elif row["observations"] == "Margin of error":
            entry["moe"] = row[value_col]
    return {code: (v.get("avg", ".."), v.get("moe", "..")) for code, v in out.items()}


def build():
    payload = fetch()

    # Map industry code -> English label from the metadata variable list.
    meta_req = urllib.request.Request(API_URL)
    with urllib.request.urlopen(meta_req) as r:
        meta = json.loads(r.read().decode("utf-8"))
    industry_labels = {}
    for var in meta["variables"]:
        if var["code"] == "SNI2007":
            industry_labels = dict(zip(var["values"], var["valueTexts"]))

    rows = []
    for entry in payload["data"]:
        industry_code, quarter = entry["key"]
        avg_recruitment, margin_of_error = entry["values"]
        rows.append({
            "industry_code": industry_code,
            "industry_label": industry_labels.get(industry_code, ""),
            "quarter": quarter,
            "average_recruitment_months": avg_recruitment,
            "margin_of_error": margin_of_error,
        })

    # Backfill 2015K1 from the deprecated predecessor table.
    old_2015k1 = fetch_2015k1_from_old_table()
    for industry_code in INDUSTRY_CODES:
        avg, moe = old_2015k1.get(industry_code, ("..", ".."))
        rows.append({
            "industry_code": industry_code,
            "industry_label": industry_labels.get(industry_code, ""),
            "quarter": "2015K1",
            "average_recruitment_months": avg,
            "margin_of_error": moe,
        })

    rows.sort(key=lambda row: (row["industry_code"], row["quarter"]))

    with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=[
            "industry_code",
            "industry_label",
            "quarter",
            "average_recruitment_months",
            "margin_of_error",
        ])
        w.writeheader()
        w.writerows(rows)

    print(f"Wrote {OUT_PATH} ({len(rows)} rows)")


if __name__ == "__main__":
    build()
