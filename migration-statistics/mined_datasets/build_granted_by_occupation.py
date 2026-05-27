"""
Reshapes csv/master_work_permits_by_occupation_group.csv into
mined_datasets/minned_work_permits_granted_by_occupation.csv.

Output columns:
  year, permit_type, occupation_field, occupation_group, number_granted_applications

Rules:
- Only yearly totals (source rows where is_year_total='True').
- English labels for permit_type, occupation_field, occupation_group.
- 2021 extension has no data in the source: emit zero rows for every
  (occupation_field, occupation_group) tuple seen in any extension year (2022-2025).
- All other rows pass through as-is from the source year-total rows.
- All occupation_field values are kept (incl. 'Unknown', 'Occupation missing', 'Military').
"""

import csv
import os

SRC = '/Users/alejandro.lozadacort/the-local/the-local/migration-statistics/csv/master_work_permits_by_occupation_group.csv'
OUT = '/Users/alejandro.lozadacort/the-local/the-local/migration-statistics/mined_datasets/minned_work_permits_granted_by_occupation.csv'


def main():
    with open(SRC, newline='', encoding='utf-8') as f:
        src_rows = [r for r in csv.DictReader(f) if r['is_year_total'] == 'True']

    out_rows = []
    extension_universe = set()  # (field_en, group_en) seen in any extension year

    for r in src_rows:
        if r['permit_type_en'] == 'extension':
            extension_universe.add((r['occupation_field_en'], r['occupation_group_en']))
        out_rows.append({
            'year': int(r['year']),
            'permit_type': r['permit_type_en'],
            'occupation_field': r['occupation_field_en'],
            'occupation_group': r['occupation_group_en'],
            'number_granted_applications': int(r['granted_count']),
        })

    # 2021 extension zero-fill
    for field, group in extension_universe:
        out_rows.append({
            'year': 2021,
            'permit_type': 'extension',
            'occupation_field': field,
            'occupation_group': group,
            'number_granted_applications': 0,
        })

    out_rows.sort(key=lambda x: (
        x['year'],
        0 if x['permit_type'] == 'first-time' else 1,
        x['occupation_field'],
        x['occupation_group'],
    ))

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=[
            'year', 'permit_type', 'occupation_field', 'occupation_group',
            'number_granted_applications',
        ])
        w.writeheader()
        w.writerows(out_rows)

    print(f'Wrote {OUT}')
    print(f'  rows: {len(out_rows)}')
    print(f'  extension universe size: {len(extension_universe)}')

    # Quick sanity: yearly totals per permit_type
    from collections import defaultdict
    totals = defaultdict(int)
    for r in out_rows:
        totals[(r['year'], r['permit_type'])] += r['number_granted_applications']
    print('  yearly sums:')
    for k, v in sorted(totals.items()):
        print(f'    {k}: {v}')


if __name__ == '__main__':
    main()
