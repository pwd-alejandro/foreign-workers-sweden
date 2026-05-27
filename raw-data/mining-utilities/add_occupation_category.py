"""
Adds an `occupation_category` column to
mined_datasets/minned_work_permits_granted_by_occupation.csv.

The new column slots between `occupation_field` and `occupation_group` and
collapses the ~150 atomic occupation groups into 22 role-specific clusters
that crosscut occupation_field (e.g., 'IT managers', 'IT architects' and
'IT support' all land in 'IT & software', regardless of skill-level field).

"Total" pseudo-groups (one per occupation_field) are mapped to 'Total' so
they remain identifiable and filterable.

Idempotent: rewrites the file in place. Errors out if an occupation_group
in the source is unmapped (so the schema stays exhaustive).
"""

import csv
import sys

CSV_PATH = '/Users/alejandro.lozadacort/the-local/the-local/migration-statistics/mined_datasets/minned_work_permits_granted_by_occupation.csv'

# ---------------------------------------------------------------------------
# Mapping: occupation_group (English label) -> occupation_category
# ---------------------------------------------------------------------------
GROUP_TO_CATEGORY = {
    # ---- IT & software ------------------------------------------------------
    'IT architects, developers and test leads': 'IT & software',
    'IT operations, support and network technicians': 'IT & software',
    'IT managers': 'IT & software',

    # ---- Engineering professionals -----------------------------------------
    'Engineering professionals': 'Engineering professionals',
    'Engineers and technicians': 'Engineering professionals',
    'Architects and surveyors': 'Engineering professionals',
    'Managers in architecture and engineering': 'Engineering professionals',
    'R&D managers': 'Engineering professionals',
    'Production managers in manufacturing': 'Engineering professionals',
    'Operations managers in construction and mining': 'Engineering professionals',
    'Operations technicians and process supervisors': 'Engineering professionals',
    'Supervisors in construction and manufacturing': 'Engineering professionals',

    # ---- Doctors & dentists -------------------------------------------------
    'Doctors / physicians': 'Doctors & dentists',
    'Dentists': 'Doctors & dentists',
    'Veterinarians': 'Doctors & dentists',

    # ---- Nurses & allied health --------------------------------------------
    'Nurses': 'Nurses & allied health',
    'Nurses (continued)': 'Nurses & allied health',
    'Other health specialists': 'Nurses & allied health',
    'Naprapaths, physiotherapists and occupational therapists': 'Nurses & allied health',
    'Biomedical analysts, dental technicians and lab engineers': 'Nurses & allied health',
    'Dental hygienists': 'Nurses & allied health',
    'Veterinary assistants': 'Nurses & allied health',
    'Alternative medicine therapists': 'Nurses & allied health',
    'Psychologists and psychotherapists': 'Nurses & allied health',

    # ---- Care & nursing aides ----------------------------------------------
    'Care workers and personal assistants': 'Care & nursing aides',
    'Assistant nurses': 'Care & nursing aides',
    'Nursing aides': 'Care & nursing aides',
    'Dental nurses': 'Care & nursing aides',
    'Managers in healthcare': 'Care & nursing aides',
    'Managers in elderly care': 'Care & nursing aides',

    # ---- Hospitality & food service ----------------------------------------
    'Cooks and cold-buffet chefs': 'Hospitality & food service',
    'Head chefs and sous chefs': 'Hospitality & food service',
    'Head waiters, waiters and bartenders': 'Hospitality & food service',
    'Fast food, kitchen and restaurant helpers': 'Hospitality & food service',
    'Restaurant and kitchen managers': 'Hospitality & food service',
    'Hotel and conference managers': 'Hospitality & food service',

    # ---- Agriculture, forestry & fisheries ---------------------------------
    'Berry pickers and planters': 'Agriculture, forestry & fisheries',
    'Crop growers, agriculture and horticulture': 'Agriculture, forestry & fisheries',
    'Forestry workers': 'Agriculture, forestry & fisheries',
    'Animal breeders and keepers': 'Agriculture, forestry & fisheries',
    'Mixed crop and animal producers': 'Agriculture, forestry & fisheries',
    'Fish farmers and fishers': 'Agriculture, forestry & fisheries',
    'Forestry and agriculture managers': 'Agriculture, forestry & fisheries',

    # ---- Construction trades -----------------------------------------------
    'Carpenters, masons and construction workers': 'Construction trades',
    'Painters, lacquerers and chimney sweeps': 'Construction trades',
    'Installation and industrial electricians': 'Construction trades',
    'Roofers, floor layers and plumbers': 'Construction trades',
    'Casters, welders and sheet-metal workers': 'Construction trades',
    'Surface finishers and furniture makers': 'Construction trades',
    'Construction labourers': 'Construction trades',
    'Heavy equipment operators': 'Construction trades',

    # ---- Manufacturing & factory work --------------------------------------
    'Butchers, bakers and food processors': 'Manufacturing & factory work',
    'Blacksmiths and toolmakers': 'Manufacturing & factory work',
    'Tailors, upholsterers and leather workers': 'Manufacturing & factory work',
    'Prepress technicians, printers and bookbinders': 'Manufacturing & factory work',
    'Hand packers and other factory workers': 'Manufacturing & factory work',
    'Assemblers': 'Manufacturing & factory work',
    'Machine operators, food industry': 'Manufacturing & factory work',
    'Machine operators, rubber/plastic/paper': 'Manufacturing & factory work',
    'Machine operators, textile/laundry/leather': 'Manufacturing & factory work',
    'Machine operators, chemical and pharma products': 'Manufacturing & factory work',
    'Process and machine operators, steel and metal works': 'Manufacturing & factory work',
    'Process operators, wood and paper industry': 'Manufacturing & factory work',
    'Other process and machine operators': 'Manufacturing & factory work',
    'Ore processing and well drillers': 'Manufacturing & factory work',

    # ---- Vehicle & equipment mechanics -------------------------------------
    'Vehicle mechanics and repairers': 'Vehicle & equipment mechanics',
    'Electronics and communications repairers': 'Vehicle & equipment mechanics',
    'Precision mechanics and craft workers': 'Vehicle & equipment mechanics',

    # ---- Transport & logistics ---------------------------------------------
    'Warehouse and transport staff': 'Transport & logistics',
    'Car, motorcycle and bicycle drivers': 'Transport & logistics',
    'Lorry and bus drivers': 'Transport & logistics',
    'Pilots and ship/engine officers': 'Transport & logistics',
    'Sailors and deckhands': 'Transport & logistics',
    'Postal carriers and sorting workers': 'Transport & logistics',
    'Dockworkers and ramp staff': 'Transport & logistics',
    'Cabin crew, conductors and guides': 'Transport & logistics',
    'Purchasing, logistics and transport managers': 'Transport & logistics',

    # ---- Cleaning & building maintenance -----------------------------------
    'Cleaners and domestic helpers': 'Cleaning & building maintenance',
    'Launderers, window cleaners and other cleaners': 'Cleaning & building maintenance',
    'Cleaning supervisors and building caretakers': 'Cleaning & building maintenance',
    'Newspaper carriers, janitors and other service workers': 'Cleaning & building maintenance',
    'Recycling workers': 'Cleaning & building maintenance',

    # ---- Sales, retail & marketing -----------------------------------------
    'Shop sales staff': 'Sales, retail & marketing',
    'Cashiers': 'Sales, retail & marketing',
    'Marketers and communicators': 'Sales, retail & marketing',
    'Sales and marketing managers': 'Sales, retail & marketing',
    'Insurance advisors, business sales and buyers': 'Sales, retail & marketing',
    'Brokers and agents': 'Sales, retail & marketing',
    'Event and telephone salespersons': 'Sales, retail & marketing',
    'Market sellers': 'Sales, retail & marketing',
    'Travel agents, customer service and receptionists': 'Sales, retail & marketing',
    'Communications and PR managers': 'Sales, retail & marketing',
    'Managers in retail and wholesale': 'Sales, retail & marketing',

    # ---- Business, finance & legal -----------------------------------------
    'Auditors, financial analysts and fund managers': 'Business, finance & legal',
    'Organisational developers, analysts and HR specialists': 'Business, finance & legal',
    'Lawyers': 'Business, finance & legal',
    'Bank tellers and accounting clerks': 'Business, finance & legal',
    'Office assistants and secretaries': 'Business, finance & legal',
    'Legal and executive secretaries': 'Business, finance & legal',
    'Tax and social-insurance officers': 'Business, finance & legal',
    'Finance managers': 'Business, finance & legal',
    'HR managers': 'Business, finance & legal',
    'Administration and planning managers': 'Business, finance & legal',
    'Property and administration managers': 'Business, finance & legal',
    'Managers in banking, finance and insurance': 'Business, finance & legal',
    'Mathematicians, actuaries and statisticians': 'Business, finance & legal',

    # ---- General management ------------------------------------------------
    'CEOs and managing directors': 'General management',
    'Other administration and service managers': 'General management',
    'Managers in other service industries': 'General management',
    'Politicians and senior civil servants': 'General management',
    'Other managers in public services': 'General management',
    'Elected officials': 'General management',

    # ---- Education ---------------------------------------------------------
    'University and college teachers': 'Education',
    'Primary, after-school and preschool teachers': 'Education',
    'Secondary education teachers': 'Education',
    'Vocational teachers': 'Education',
    'Other teaching professionals': 'Education',
    'Driving instructors': 'Education',
    'Childcare workers and teaching assistants': 'Education',
    'Managers in primary, secondary and adult education': 'Education',
    'Other managers in education': 'Education',

    # ---- Arts, media & culture ---------------------------------------------
    'Designers': 'Arts, media & culture',
    'Authors, journalists and interpreters': 'Arts, media & culture',
    'Artists, musicians and actors': 'Arts, media & culture',
    'Photographers, decorators and entertainers': 'Arts, media & culture',
    'Image, sound and lighting technicians': 'Arts, media & culture',
    'Curators and librarians': 'Arts, media & culture',
    'Library and archive assistants': 'Arts, media & culture',

    # ---- Natural sciences (research) ---------------------------------------
    'Biologists, pharmacologists and agriculture/forestry specialists': 'Natural sciences (research)',
    'Physicists and chemists': 'Natural sciences (research)',
    'Environmental and health protection specialists': 'Natural sciences (research)',

    # ---- Personal services & sports ----------------------------------------
    'Beauticians and body therapists': 'Personal services & sports',
    'Athletes and recreation leaders': 'Personal services & sports',
    'Managers in wellness, sports and leisure': 'Personal services & sports',

    # ---- Religion & social work --------------------------------------------
    'Priests and deacons': 'Religion & social work',
    'Religious community leaders': 'Religion & social work',
    'Social workers and counsellors': 'Religion & social work',
    'Treatment assistants and clergy': 'Religion & social work',

    # ---- Military & security -----------------------------------------------
    'Soldiers': 'Military & security',
    'Officers': 'Military & security',
    'Specialist officers': 'Military & security',
    'Other security and protective service workers': 'Military & security',

    # ---- Unknown / other ---------------------------------------------------
    'Other': 'Unknown / other',
    'Other service staff': 'Unknown / other',
    'Unknown': 'Unknown / other',
    'Occupation missing': 'Unknown / other',
    'Croupiers and debt collectors': 'Unknown / other',

    # ---- Total (pseudo-group, kept for filtering) --------------------------
    'Total': 'Total',

    # ------------------------------------------------------------------------
    # Legacy SSYK96 / transitional 2015-2017 occupation_group labels.
    # Mapped to the same 22-category schema so 2015-2020 data joins cleanly
    # with the 2018+ taxonomy at the category level. SSYK96 groups carry the
    # "(SSYK96)" suffix; "transitional" labels appear only in 2017.
    # ------------------------------------------------------------------------
    'Computing professionals (SSYK96)': 'IT & software',

    'Engineering professionals, architects etc. (SSYK96)': 'Engineering professionals',
    'Physicists and chemists (SSYK96)': 'Natural sciences (research)',
    'Specialists in biology, agriculture and forestry (SSYK96)': 'Natural sciences (research)',

    'Health-care specialists (SSYK96)': 'Doctors & dentists',
    'Care and nursing personnel (SSYK96)': 'Care & nursing aides',

    'Catering and restaurant staff (SSYK96)': 'Hospitality & food service',
    'Kitchen and restaurant helpers (SSYK96)': 'Hospitality & food service',

    'Forestry workers (SSYK96)': 'Agriculture, forestry & fisheries',
    'Agriculture, horticulture, forestry and fisheries helpers (SSYK96)': 'Agriculture, forestry & fisheries',

    'Construction and civil-engineering workers (SSYK96)': 'Construction trades',
    'Construction and civil-engineering occupations (SSYK96)': 'Construction trades',
    'Construction craft workers (SSYK96)': 'Construction trades',
    'Casters, welders and sheet-metal workers (SSYK96)': 'Construction trades',
    'Painters, lacquerers and chimney sweeps (SSYK96)': 'Construction trades',

    'Blacksmiths and toolmakers (SSYK96)': 'Manufacturing & factory work',
    'Butchers, bakers and pastry chefs (SSYK96)': 'Manufacturing & factory work',
    'Tailors, cutters and upholsterers (SSYK96)': 'Manufacturing & factory work',
    'Tanners, hide processors and shoemakers (SSYK96)': 'Manufacturing & factory work',
    'Machine operators, food industry (SSYK96)': 'Manufacturing & factory work',
    'Machine operators, chemical-technical industry (SSYK96)': 'Manufacturing & factory work',
    'Mining, quarrying and stone-cutting workers (SSYK96)': 'Manufacturing & factory work',

    'Machine and engine mechanics (SSYK96)': 'Vehicle & equipment mechanics',

    'Vehicle drivers (SSYK96)': 'Transport & logistics',
    'Train drivers and railway-yard staff (SSYK96)': 'Transport & logistics',
    'Postal carriers (SSYK96)': 'Transport & logistics',
    'Goods handlers and couriers (SSYK96)': 'Transport & logistics',
    'Warehouse and transport assistants (SSYK96)': 'Transport & logistics',

    'Cleaners (SSYK96)': 'Cleaning & building maintenance',
    'Cleaning occupations (transitional)': 'Cleaning & building maintenance',
    'Sanitation and recycling workers (SSYK96)': 'Cleaning & building maintenance',
    'Newspaper carriers and janitors (SSYK96)': 'Cleaning & building maintenance',

    'Retail salespersons and demonstrators (SSYK96)': 'Sales, retail & marketing',
    'Salespersons, buyers and brokers (SSYK96)': 'Sales, retail & marketing',
    'Cashiers (SSYK96)': 'Sales, retail & marketing',
    'Customer-service clerks (SSYK96)': 'Sales, retail & marketing',

    'Bookkeeping and accounting assistants (SSYK96)': 'Business, finance & legal',
    'Accounting and administrative assistants (SSYK96)': 'Business, finance & legal',
    'Business economists, marketers and HR officers (SSYK96)': 'Business, finance & legal',
    'Other office staff (SSYK96)': 'Business, finance & legal',

    'Preschool and after-school teachers (SSYK96)': 'Education',

    'Journalists, artists and actors (SSYK96)': 'Arts, media & culture',
    'Designers, entertainers and professional athletes (SSYK96)': 'Arts, media & culture',

    'Hairdressers and other personal-service staff (SSYK96)': 'Personal services & sports',

    'Military personnel (SSYK96)': 'Military & security',
    'Security personnel (SSYK96)': 'Military & security',

    'Other service workers (SSYK96)': 'Unknown / other',
    'Service occupations (transitional)': 'Unknown / other',
    'SSYK missing': 'Unknown / other',
}


def main():
    with open(CSV_PATH, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        original_fieldnames = reader.fieldnames
        rows = list(reader)

    # Detect already-added column (idempotency)
    if 'occupation_category' in original_fieldnames:
        print('occupation_category already present; will overwrite values.')
        new_fieldnames = original_fieldnames
    else:
        # Insert between occupation_field and occupation_group
        new_fieldnames = []
        for col in original_fieldnames:
            new_fieldnames.append(col)
            if col == 'occupation_field':
                new_fieldnames.append('occupation_category')

    # Verify all groups in source are mapped
    unmapped = sorted({r['occupation_group'] for r in rows
                       if r['occupation_group'] not in GROUP_TO_CATEGORY})
    if unmapped:
        print('ERROR: unmapped occupation_group values found:', file=sys.stderr)
        for g in unmapped:
            print(f'  - {g!r}', file=sys.stderr)
        sys.exit(1)

    # Inject category
    for r in rows:
        r['occupation_category'] = GROUP_TO_CATEGORY[r['occupation_group']]

    # Write back
    with open(CSV_PATH, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=new_fieldnames)
        w.writeheader()
        w.writerows(rows)

    # Report
    from collections import defaultdict
    cat_totals = defaultdict(int)
    cat_groups = defaultdict(set)
    for r in rows:
        if r['occupation_category'] == 'Total':
            continue
        cat_totals[r['occupation_category']] += int(r['number_granted_applications'])
        cat_groups[r['occupation_category']].add(r['occupation_group'])

    print(f'\nWrote {CSV_PATH} ({len(rows)} rows, new fieldnames: {new_fieldnames})')
    print(f'\nGrants per category (excluding "Total" rows), sorted by volume:')
    for cat, total in sorted(cat_totals.items(), key=lambda x: -x[1]):
        print(f'  {total:>7}  ({len(cat_groups[cat]):>2} groups)  {cat}')

    # Sanity: total across categories vs sum of all "Total" pseudo-rows
    real_sum = sum(cat_totals.values())
    total_pseudo = sum(int(r['number_granted_applications']) for r in rows
                       if r['occupation_category'] == 'Total')
    print(f'\nSum across category rows (excl Total): {real_sum}')
    print(f'Sum across "Total" pseudo rows         : {total_pseudo}')
    print(f'(These should be equal.)' if real_sum == total_pseudo
          else f'WARNING: discrepancy of {real_sum - total_pseudo}')


if __name__ == '__main__':
    main()
