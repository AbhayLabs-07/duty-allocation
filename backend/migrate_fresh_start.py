import sqlite3

def run_migration():
    conn = sqlite3.connect('kam_bato.db')
    c = conn.cursor()

    non_eng_depts = [
        'Engineering Science & Humanities (H&S)',
        'BCA / MCA Department',
        'Bachelor of Computer Applications (BCA)',
        'Management Studies (MBA / BBA)',
        'Master of Business Administration (MBA)',
        'Bachelor of Business Administration (BBA)',
        'Bachelor of Vocation (B.Voc)'
    ]

    placeholders = ','.join(['?']*len(non_eng_depts))

    c.execute(f'SELECT id FROM departments WHERE name IN ({placeholders})', non_eng_depts)
    non_eng_dept_ids = [r[0] for r in c.fetchall()]
    print('Non-eng dept IDs to remove:', non_eng_dept_ids)

    for dept_id in non_eng_dept_ids:
        c.execute('DELETE FROM faculty WHERE department_id = ?', (dept_id,))
        c.execute('DELETE FROM departments WHERE id = ?', (dept_id,))

    print('Deleted non-engineering departments and their faculty.')

    # Exclude leadership from examiner duties
    c.execute('''
    UPDATE faculty 
    SET eligibility = 'Exempted',
        employment_status = 'Leadership_Exempt',
        role_category = 'Leadership'
    WHERE LOWER(designation) LIKE '%principal%'
       OR LOWER(designation) LIKE '%dean%'
       OR LOWER(designation) LIKE '%hod%'
       OR LOWER(designation) LIKE '%controller%'
       OR LOWER(role_category) LIKE '%hod%'
       OR LOWER(role_category) LIKE '%dean%'
    ''')
    print('Updated leadership faculty to Exempted/Leadership_Exempt.')

    # Fresh start: zero out historical counts
    c.execute('''
    UPDATE faculty 
    SET total_previous_duties = 0,
        previous_js_count = 0,
        previous_reliever_count = 0,
        previous_standby_count = 0,
        previous_ss_count = 0
    ''')
    print('Reset all duty counts to 0 (fresh start).')

    # Find table names
    c.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in c.fetchall()]
    print('Existing tables:', tables)

    for tbl in ['duty_assignments', 'exam_rooms', 'exam_shifts', 'allocation_audit_logs', 'manual_override_records']:
        if tbl in tables:
            c.execute(f'DELETE FROM {tbl}')
            print(f'Cleared {tbl}')

    c.execute('SELECT count(*) FROM departments')
    print('Remaining departments count:', c.fetchone()[0])

    c.execute('SELECT d.name, count(f.id) FROM departments d LEFT JOIN faculty f ON f.department_id = d.id GROUP BY d.id')
    for row in c.fetchall():
        print(row)

    c.execute("SELECT count(*) FROM faculty WHERE eligibility = 'Eligible'")
    print('Eligible engineering faculty count:', c.fetchone()[0])

    c.execute("SELECT count(*) FROM faculty WHERE eligibility = 'Exempted'")
    print('Exempted leadership faculty count:', c.fetchone()[0])

    conn.commit()
    conn.close()
    print('Migration completed successfully!')

if __name__ == '__main__':
    run_migration()
