"""
Downloads SCB table KV15RekochVakansgr07 (Recruitment and vacancy rate,
Business sector by industrial classification NACE Rev. 2, by quarter) and
writes it to minned_recruitment_and_vacancy_rate_by_industry.csv.

Source:
  https://www.statistikdatabasen.scb.se/pxweb/en/ssd/START__AM__AM0701__AM0701B/KV15RekochVakansgr07/

API endpoint (PXWeb v1):
  https://api.scb.se/OV0104/v1/doris/en/ssd/START/AM/AM0701/AM0701B/KV15RekochVakansgr07
"""

import csv
import json
import os
import urllib.request

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_PATH = os.path.join(OUT_DIR, "minned_recruitment_and_vacancy_rate_by_industry.csv")
API_URL = "https://api.scb.se/OV0104/v1/doris/en/ssd/START/AM/AM0701/AM0701B/KV15RekochVakansgr07"

INDUSTRY_CODES = [
    "A-S", "A", "B+C", "D+E", "F", "G", "H",
    "I", "J", "K+L", "M", "N", "P+Q", "R+S",
]

CONTENT_CODES = ["000000GV", "000000GW", "000000GX", "000000GY"]

QUERY = {
    "query": [
        {"code": "SNI2007", "selection": {"filter": "item", "values": INDUSTRY_CODES}},
        {"code": "ContentsCode", "selection": {"filter": "item", "values": CONTENT_CODES}},
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


def build():
    payload = fetch()

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
        recruitment_rate, recruitment_moe, vacancy_rate, vacancy_moe = entry["values"]
        rows.append({
            "industry_code": industry_code,
            "industry_label": industry_labels.get(industry_code, ""),
            "quarter": quarter,
            "recruitment_rate": recruitment_rate,
            "recruitment_margin_of_error": recruitment_moe,
            "vacancy_rate": vacancy_rate,
            "vacancy_margin_of_error": vacancy_moe,
        })

    rows.sort(key=lambda r: (r["industry_code"], r["quarter"]))

    with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=[
            "industry_code",
            "industry_label",
            "quarter",
            "recruitment_rate",
            "recruitment_margin_of_error",
            "vacancy_rate",
            "vacancy_margin_of_error",
        ])
        w.writeheader()
        w.writerows(rows)

    print(f"Wrote {OUT_PATH} ({len(rows)} rows)")


if __name__ == "__main__":
    build()
