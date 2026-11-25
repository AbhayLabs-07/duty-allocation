import pandas as pd
import re
from datetime import datetime, date

def parse_staff_list(excel_path='Staff List - 02.09.2026.xls'):
    df = pd.read_excel(excel_path, sheet_name='Teaching Staff', header=None)
    data_rows = df.iloc[3:].copy()

    records = []
    for _, r in data_rows.iterrows():
        sr_val = r[0]
        if pd.isna(sr_val):
            continue
        try:
            sr = int(float(str(sr_val).strip()))
        except:
            continue

        raw_name_cell = str(r[1]).strip() if pd.notna(r[1]) else ''
        raw_desig_cell = str(r[2]).strip() if pd.notna(r[2]) else ''
        dept = str(r[3]).strip() if pd.notna(r[3]) else ''

        # Extract DOJ / DOR
        doj_match = re.search(r'\(\s*(?:DOJ|DOR|Date of Joining)\s*[:=-]?\s*([^\)]+)\)', raw_name_cell, re.I)
        doj_str = doj_match.group(1).strip() if doj_match else None

        # Clean name by stripping the parenthetical DOJ
        name_clean = re.sub(r'\(\s*(?:DOJ|DOR|Date of Joining)\s*[:=-]?\s*[^\)]+\)', '', raw_name_cell).strip()
        name_clean = re.sub(r'\s+', ' ', name_clean)

        # Position / Designation cleanup
        desig_clean = re.sub(r'\s+', ' ', raw_desig_cell)
        desig_clean = desig_clean.replace('\n', ', ').strip(' ,;')

        # Title extraction (Dr., Prof., Mr., Ms., Mrs.)
        title = ""
        name_exact = name_clean
        title_match = re.match(r'^(Dr\.|Dr|Prof\.|Prof|Mr\.|Mr|Ms\.|Ms|Mrs\.|Mrs)\s*(.*)', name_clean, re.I)
        if title_match:
            t = title_match.group(1)
            if not t.endswith('.'):
                t = t + '.'
            title = t.capitalize()
            rest = title_match.group(2).strip()
            name_exact = f"{title} {rest}"
        else:
            title = "Prof."
            name_exact = f"Prof. {name_clean}"

        # Determine Role Category for Examination System:
        # HOD / Dy. HOD -> Senior Supervisor (SS) tracking
        desig_lower = desig_clean.lower()
        if 'principal' in desig_lower or 'dean' in desig_lower:
            role_category = "HOD" # Treated as Senior Administrative / SS
        elif 'hod' in desig_lower and 'dy' not in desig_lower and 'deputy' not in desig_lower:
            role_category = "HOD"
        elif 'dy.hod' in desig_lower or 'dy. hod' in desig_lower or 'deputy hod' in desig_lower or 'dy hod' in desig_lower:
            role_category = "Dy. HOD"
        else:
            role_category = "Faculty"

        # Standardize Designation for display
        if 'professor of practice' in desig_lower:
            designation = 'Professor of Practice'
        elif 'assistant professor' in desig_lower or 'assistant  professor' in desig_lower:
            designation = 'Assistant Professor'
        elif 'associate professor' in desig_lower:
            designation = 'Associate Professor'
        elif 'professor' in desig_lower and 'assistant' not in desig_lower and 'associate' not in desig_lower:
            designation = 'Professor'
        elif 'lecturer' in desig_lower or 'lecture' in desig_lower:
            designation = 'Lecturer'
        elif 'teaching assistant' in desig_lower:
            designation = 'Teaching Assistant'
        else:
            designation = desig_clean or 'Assistant Professor'

        # Parse DOJ to Python date if possible
        parsed_date = None
        if doj_str:
            # Common formats: DD.MM.YY, DD.MM.YYYY, DD/MM/YYYY
            clean_d = doj_str.replace('/', '.').replace('-', '.').strip()
            parts = clean_d.split('.')
            if len(parts) == 3:
                try:
                    d_day = int(parts[0])
                    d_month = int(parts[1])
                    d_year = int(parts[2])
                    if d_year < 100:
                        d_year = 2000 + d_year if d_year < 50 else 1900 + d_year
                    parsed_date = date(d_year, d_month, d_day)
                except:
                    pass

        records.append({
            'sr_no': sr,
            'title': title,
            'name': name_exact,
            'raw_name': name_clean,
            'position': desig_clean,
            'designation': designation,
            'role_category': role_category,
            'department': dept,
            'doj_str': doj_str,
            'joining_date': parsed_date
        })

    return records

if __name__ == '__main__':
    recs = parse_staff_list()
    print(f'Successfully extracted {len(recs)} faculty members from Staff List - 02.09.2026.xls')
    print('\nFirst 10 extracted faculty records:')
    for r in recs[:10]:
        print(f"#{r['sr_no']:03d} | Name: {r['name']:<30} | Pos: {r['position'][:35]:<35} | Dept: {r['department'][:30]:<30} | Role: {r['role_category']}")

    print('\nRole category summary:')
    from collections import Counter
    print(Counter(r['role_category'] for r in recs))
    print('\nDepartment summary:')
    print(Counter(r['department'] for r in recs))
