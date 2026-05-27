"""
Aggregates minned_work_permits_granted_by_occupation.csv up to the
occupation_category level and writes minned_work_permits_granted_by_category.csv.

Excludes the per-field "Total" pseudo-rows (occupation_category == 'Total')
so yearly sums reflect actual grants without double-counting.

Output is rectangular: every (year, permit_type, occupation_category)
combination gets a row, with 0 where the source has no entries (notably
2021 extension across all categories).

Output columns:
  year, permit_type, occupation_category, number_granted_applications
"""

import csv
import os
from collections import defaultdict

SRC = '/Users/alejandro.lozadacort/the-local/the-local/migration-statistics/mined_datasets/minned_work_permits_granted_by_occupation.csv'
OUT = '/Users/alejandro.lozadacort/the-local/the-local/migration-statistics/mined_datasets/minned_work_permits_granted_by_category.csv'


def main():
    with open(SRC, newline='', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))

    # Aggregate, excluding "Total" pseudo-rows
    agg = defaultdict(int)
    years = set()
    permit_types = set()
    categories = set()
    for r in rows:
        cat = r['occupation_category']
        if cat == 'Total':
            continue
        year = int(r['year'])
        ptype = r['permit_type']
        years.add(year)
        permit_types.add(ptype)
        categories.add(cat)
        agg[(year, ptype, cat)] += int(r['number_granted_applications'])

    # Rectangular fill
    out_rows = []
    for year in sorted(years):
        for ptype in sorted(permit_types):
            for cat in sorted(categories):
                out_rows.append({
                    'year': year,
                    'permit_type': ptype,
                    'occupation_category': cat,
                    'number_granted_applications': agg.get((year, ptype, cat), 0),
                })

    # permit_type sort: first-time before extension
    out_rows.sort(key=lambda x: (
        x['year'],
        0 if x['permit_type'] == 'first-time' else 1,
        x['occupation_category'],
    ))

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=[
            'year', 'permit_type', 'occupation_category', 'number_granted_applications',
        ])
        w.writeheader()
        w.writerows(out_rows)

    print(f'Wrote {OUT}')
    print(f'  rows: {len(out_rows)} ({len(years)} years × {len(permit_types)} types × {len(categories)} categories)')

    # Sanity: yearly totals per permit_type
    totals = defaultdict(int)
    for r in out_rows:
        totals[(r['year'], r['permit_type'])] += r['number_granted_applications']
    print('\n  yearly sums (matches granular sums in source):')
    for k, v in sorted(totals.items()):
        print(f'    {k}: {v}')


if __name__ == '__main__':
    main()
