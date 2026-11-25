import os
import sys
import re
import random
from datetime import datetime, date, timedelta

# Ensure backend root is in sys.path
backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

import pandas as pd
from sqlalchemy.orm import Session
from app.core.database import Base, engine, SessionLocal
from app.models.department import Department
from app.models.faculty import Faculty
from app.models.user import User
from app.models.examination import Examination, ExaminationDate, ExaminationShift, ExaminationRoom
from app.models.allocation import AllocationConfiguration, AllocationAuditLog
from app.models.history import FacultyDutyHistory
from app.core.security import get_password_hash

DEPT_CODE_MAP = {
    'ELECTRONICS & TELECOMMUNICATION ENGINEERING': ('EXTC', 'Electronics & Telecommunication Engineering'),
    'COMPUTER ENGINEERING': ('COMP', 'Computer Engineering'),
    'ELECTRONICS and COMPUTER SCIENCE': ('ECS', 'Electronics & Computer Science'),
    'INFORMATION TECHNOLOGY': ('IT', 'Information Technology'),
    'MECHANICAL ENGINEERING': ('MECH', 'Mechanical Engineering'),
    'CIVIL ENGINEERING': ('CIVIL', 'Civil Engineering'),
    'Engineering Science & Humanities': ('ESH', 'Engineering Science & Humanities (H&S)'),
    'Artificial Intelligence & Data Science': ('AIDS', 'Artificial Intelligence & Data Science'),
    'Artificial Intelligence & Machine Learning': ('AIML', 'Artificial Intelligence & Machine Learning'),
    'Computer Science & Engineering (IoT)': ('CSE-IOT', 'Computer Science & Engineering (IoT)'),
    'Computer Science & Engineering (Cyber Security)': ('CSE-CS', 'Computer Science & Engineering (Cyber Security)'),
    'Mechanical & Mechatronics Engineering (Additive Manufacturing)': ('MME', 'Mechanical & Mechatronics Engineering (Additive Mfg)'),
    'BCA / MCA': ('BCA-MCA', 'BCA / MCA Department'),
    'BCA': ('BCA', 'Bachelor of Computer Applications (BCA)'),
    'MBA / BBA': ('MBA-BBA', 'Management Studies (MBA / BBA)'),
    'MBA': ('MBA', 'Master of Business Administration (MBA)'),
    'BBA': ('BBA', 'Bachelor of Business Administration (BBA)'),
    'B.Voc': ('BVOC', 'Bachelor of Vocation (B.Voc)')
}

def extract_faculty_from_excel(excel_path='Staff List - 02.09.2026.xls'):
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
        raw_dept_cell = str(r[3]).strip() if pd.notna(r[3]) else ''

        # Clean department name
        dept_key = re.sub(r'\s+', ' ', raw_dept_cell).strip()

        # Extract DOJ / DOR (handles both closed and unclosed parentheses like '(DOJ: 02.02.2026')
        doj_match = re.search(r'\(\s*(?:DOJ|DOR|Date of Joining)\s*[:=-]?\s*([^)\n]+)\)?', raw_name_cell, re.I)
        doj_str = doj_match.group(1).strip() if doj_match else None

        # Clean name: remove parenthetical DOJ/DOR
        name_clean = re.sub(r'\(\s*(?:DOJ|DOR|Date of Joining)\s*[:=-]?\s*[^)\n]+\)?', '', raw_name_cell).strip()
        name_clean = re.sub(r'\s+', ' ', name_clean)
        # Fix missing space after title dot: e.g. Dr.Priyanka -> Dr. Priyanka
        name_clean = re.sub(r'^(Dr|Prof|Mr|Ms|Mrs)\.([^\s])', r'\1. \2', name_clean, flags=re.I)

        # Exact Position / Designation
        position_exact = re.sub(r'\s+', ' ', raw_desig_cell).replace('\n', ', ').strip(' ,;')

        # Title extraction (Dr., Prof., Mr., Ms., Mrs.)
        title = ""
        name_with_title = name_clean
        title_match = re.match(r'^(Dr\.|Dr|Prof\.|Prof|Mr\.|Mr|Ms\.|Ms|Mrs\.|Mrs)\s*(.*)', name_clean, re.I)
        if title_match:
            t = title_match.group(1)
            if not t.endswith('.'):
                t = t + '.'
            title = t.capitalize()
            rest = title_match.group(2).strip()
            name_with_title = f"{title} {rest}"
        else:
            title = "Prof."
            name_with_title = f"Prof. {name_clean}"

        # Determine Role Category for Examination System
        desig_lower = position_exact.lower()
        if 'principal' in desig_lower or 'dean' in desig_lower:
            role_category = "HOD" # High admin role, treated as Senior Supervisor (SS)
        elif 'hod' in desig_lower and 'dy' not in desig_lower and 'deputy' not in desig_lower:
            role_category = "HOD"
        elif 'dy.hod' in desig_lower or 'dy. hod' in desig_lower or 'deputy hod' in desig_lower or 'dy hod' in desig_lower:
            role_category = "Dy. HOD"
        else:
            role_category = "Faculty"

        # Standard designation summary
        if 'professor of practice' in desig_lower:
            std_designation = 'Professor of Practice'
        elif 'assistant professor' in desig_lower:
            std_designation = 'Assistant Professor'
        elif 'associate professor' in desig_lower:
            std_designation = 'Associate Professor'
        elif 'professor' in desig_lower and 'assistant' not in desig_lower and 'associate' not in desig_lower:
            std_designation = 'Professor'
        elif 'lecturer' in desig_lower or 'lecture' in desig_lower:
            std_designation = 'Lecturer'
        elif 'teaching assistant' in desig_lower:
            std_designation = 'Teaching Assistant'
        else:
            std_designation = position_exact or 'Assistant Professor'

        # Parse joining date
        joining_date = None
        if doj_str:
            clean_d = doj_str.replace('/', '.').replace('-', '.').strip()
            parts = clean_d.split('.')
            if len(parts) == 3:
                try:
                    d_day = int(parts[0])
                    d_month = int(parts[1])
                    d_year = int(parts[2])
                    if d_year < 100:
                        d_year = 2000 + d_year if d_year < 50 else 1900 + d_year
                    joining_date = date(d_year, d_month, d_day)
                except:
                    pass

        records.append({
            'sr_no': sr,
            'title': title,
            'name': name_with_title,
            'raw_name': name_clean,
            'position_exact': position_exact,
            'designation': std_designation,
            'role_category': role_category,
            'department_raw': dept_key,
            'doj_str': doj_str,
            'joining_date': joining_date
        })

    return records

def populate_exact_staff():
    excel_path = os.path.join(os.path.dirname(backend_root), 'Staff List - 02.09.2026.xls')
    if not os.path.exists(excel_path):
        excel_path = 'Staff List - 02.09.2026.xls'

    records = extract_faculty_from_excel(excel_path)
    print(f"Extracted {len(records)} exact faculty records from {excel_path}")

    # Recreate tables cleanly
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db: Session = SessionLocal()
    try:
        # 1. Create all Departments from the Excel
        dept_db_map = {}
        for r in records:
            d_raw = r['department_raw']
            if d_raw not in dept_db_map:
                code, clean_name = DEPT_CODE_MAP.get(d_raw, (d_raw[:6].upper().replace(' ', ''), d_raw))
                # Check if code already used
                existing_codes = [d.code for d in dept_db_map.values()]
                if code in existing_codes:
                    code = f"{code}_{len(existing_codes)}"

                dept = Department(
                    code=code,
                    name=clean_name,
                    contact_email=f"hod.{code.lower()}@tcetmumbai.in"
                )
                db.add(dept)
                db.flush()
                dept_db_map[d_raw] = dept

        # Identify and assign HOD names to departments
        for r in records:
            if r['role_category'] == 'HOD' and 'principal' not in r['position_exact'].lower() and 'dean' not in r['position_exact'].lower():
                d_obj = dept_db_map.get(r['department_raw'])
                if d_obj and not d_obj.hod_name:
                    d_obj.hod_name = r['name']

        # 2. Add Standard Allocation Configuration
        config = AllocationConfiguration(
            name="TCET Examination Fairness Standard Policy",
            reliever_ratio=4,
            weight_prev_js=2.5,
            weight_prev_reliever=2.0,
            weight_prev_standby=1.5,
            weight_consecutive=2.0,
            weight_dept_equity=1.5,
            exclude_ss_from_fairness=True,
            is_active=True
        )
        db.add(config)
        db.flush()

        # 3. Create Users
        # Super Admin
        admin_user = User(
            username="admin",
            email="admin@tcetmumbai.in",
            hashed_password=get_password_hash("admin123"),
            full_name="Chief Examination Administrator",
            role="Super Admin",
            is_active=True
        )
        db.add(admin_user)

        # Controller of Examination (Dr. Sanjeev Chaudhari, Sr. 114)
        coe_record = next((r for r in records if 'controller of examination' in r['position_exact'].lower() and 'deputy' not in r['position_exact'].lower()), None)
        coe_name = coe_record['name'] if coe_record else "Dr. Sanjeev Chaudhari"
        controller_user = User(
            username="controller",
            email="coe@tcetmumbai.in",
            hashed_password=get_password_hash("controller123"),
            full_name=f"{coe_name} (Controller of Examinations)",
            role="Examination Controller",
            is_active=True
        )
        db.add(controller_user)

        # Principal (Dr. B. K. Mishra, Sr. 1)
        principal_record = next((r for r in records if 'principal' in r['position_exact'].lower() and 'vice' not in r['position_exact'].lower()), None)
        principal_name = principal_record['name'] if principal_record else "Dr. B. K. Mishra"
        principal_user = User(
            username="principal",
            email="principal@tcetmumbai.in",
            hashed_password=get_password_hash("principal123"),
            full_name=f"{principal_name} (Principal)",
            role="Super Admin",
            is_active=True
        )
        db.add(principal_user)

        db.flush()

        # 4. Insert all 368 Faculty Records with exact titles, names, positions, and departments
        all_faculty_objs = []
        for r in records:
            dept_obj = dept_db_map[r['department_raw']]
            fac_id_str = f"TCET-FAC-{r['sr_no']:03d}"

            # Calculate realistic baseline duty history for demonstration & fairness
            # Higher JS for some, lower for others, so the fairness solver balances them
            if r['role_category'] in ('HOD', 'Dy. HOD') or 'dean' in r['position_exact'].lower() or 'principal' in r['position_exact'].lower():
                prev_ss = random.randint(3, 8)
                prev_js = random.randint(0, 1) # Admins rarely get JS
                prev_rel = random.randint(0, 1)
                prev_stb = random.randint(0, 2)
            else:
                prev_ss = 0
                cluster = r['sr_no'] % 5
                if cluster == 0:
                    # High JS burden -> will receive priority for Reliever/Standby
                    prev_js = random.randint(7, 10)
                    prev_rel = random.randint(0, 1)
                    prev_stb = random.randint(0, 1)
                elif cluster == 1:
                    # Balanced
                    prev_js = random.randint(3, 5)
                    prev_rel = random.randint(2, 4)
                    prev_stb = random.randint(2, 4)
                elif cluster == 2:
                    # Low JS
                    prev_js = random.randint(1, 3)
                    prev_rel = random.randint(1, 2)
                    prev_stb = random.randint(0, 2)
                elif cluster == 3:
                    # High Standby
                    prev_js = random.randint(3, 5)
                    prev_rel = random.randint(1, 2)
                    prev_stb = random.randint(4, 6)
                else:
                    # High Reliever
                    prev_js = random.randint(4, 6)
                    prev_rel = random.randint(4, 6)
                    prev_stb = random.randint(1, 2)

            total_duties = prev_js + prev_rel + prev_stb + prev_ss

            # Email generation
            email_prefix = re.sub(r'[^a-z0-9]', '', r['raw_name'].lower().split()[-1] if r['raw_name'].split() else 'faculty')
            email_val = f"{email_prefix}.{r['sr_no']}@tcetmumbai.in"

            fac_obj = Faculty(
                faculty_id=fac_id_str,
                name=r['name'],
                department_id=dept_obj.id,
                designation=r['position_exact'], # Exact position as requested!
                role_category=r['role_category'],
                employment_status="Regular" if 'practice' not in r['position_exact'].lower() and 'assistant' not in r['position_exact'].lower() else "Regular",
                eligibility=True,
                joining_date=r['joining_date'] or (date.today() - timedelta(days=random.randint(500, 3000))),
                email=email_val,
                phone=f"+91 98{random.randint(10000000, 99999999)}",
                total_previous_duties=total_duties,
                previous_js_count=prev_js,
                previous_reliever_count=prev_rel,
                previous_standby_count=prev_stb,
                previous_ss_count=prev_ss
            )
            db.add(fac_obj)
            all_faculty_objs.append(fac_obj)

        db.flush()

        # Add HOD User accounts
        for d_raw, d_obj in dept_db_map.items():
            hod_fac = db.query(Faculty).filter(Faculty.department_id == d_obj.id, Faculty.role_category == "HOD").first()
            if hod_fac:
                u_name = f"hod_{d_obj.code.lower().replace('-', '_')}"
                if not db.query(User).filter(User.username == u_name).first():
                    hod_user = User(
                        username=u_name,
                        email=f"hod.{d_obj.code.lower()}@tcetmumbai.in",
                        hashed_password=get_password_hash("hod123"),
                        full_name=hod_fac.name,
                        role="Department HOD",
                        department_id=d_obj.id,
                        faculty_id=hod_fac.id,
                        is_active=True
                    )
                    db.add(hod_user)

        # 5. Create Active Examination with 32 Classrooms / Blocks
        exam = Examination(
            name="TCET Second Year Engineering Mid-Term Examination",
            academic_year="2025-2026",
            semester="Semester IV",
            exam_level="Second Year",
            start_date=date.today() + timedelta(days=1),
            end_date=date.today() + timedelta(days=7),
            is_active=True
        )
        db.add(exam)
        db.flush()

        exam_date_1 = ExaminationDate(
            exam_id=exam.id,
            exam_date=date.today() + timedelta(days=1),
            day_name=(date.today() + timedelta(days=1)).strftime("%A")
        )
        db.add(exam_date_1)
        db.flush()

        # 32 Classrooms / Blocks matching official TCET examination blocks
        room_numbers = [f"R-{100 + i}" if i <= 16 else f"R-{200 + (i - 16)}" for i in range(1, 33)]
        shift_1 = ExaminationShift(
            exam_date_id=exam_date_1.id,
            shift_name="Morning",
            start_time="10:00 AM",
            end_time="01:00 PM",
            block_count=32,
            room_list_str=", ".join(room_numbers),
            status="Scheduled"
        )
        db.add(shift_1)
        db.flush()

        for b_idx, r_no in enumerate(room_numbers, start=1):
            room = ExaminationRoom(
                shift_id=shift_1.id,
                block_number=b_idx,
                room_number=r_no,
                block_label=f"Block {b_idx} ({r_no})",
                capacity=30,
                floor="1st Floor" if b_idx <= 16 else "2nd Floor",
                building="Main Academic Wing"
            )
            db.add(room)

        # 6. Seed Historical Duty Logs for previous sessions
        past_dates = [date.today() - timedelta(days=d) for d in [28, 21, 14, 7]]
        for p_date in past_dates:
            for idx, f in enumerate(all_faculty_objs[:100]):
                if idx % 3 == 0:
                    role = "JS"
                elif idx % 6 == 1:
                    role = "Reliever"
                elif idx % 6 == 4:
                    role = "Standby"
                else:
                    continue

                hist = FacultyDutyHistory(
                    faculty_id=f.id,
                    exam_name="TCET First Year Engineering Winter 2025",
                    academic_year="2025-2026",
                    semester="Semester III",
                    exam_date=p_date,
                    shift_name="Morning",
                    role_served=role,
                    block_or_room=f"Block {(idx % 30) + 1}" if role == "JS" else None,
                    is_manual_override=False
                )
                db.add(hist)

        # Initial Audit Log
        audit = AllocationAuditLog(
            action="EXACT_STAFF_LIST_LOADED",
            entity_type="FacultyMaster",
            entity_id=0,
            performed_by="System Initializer",
            user_role="Super Admin",
            details=f"Loaded {len(records)} exact faculty records from 'Staff List - 02.09.2026.xls' with exact titles, names, positions, and departments.",
            timestamp=datetime.now()
        )
        db.add(audit)

        db.commit()
        print(f"Successfully loaded {len(all_faculty_objs)} faculty members into the database across {len(dept_db_map)} departments.")

    finally:
        db.close()

if __name__ == '__main__':
    populate_exact_staff()
