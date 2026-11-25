import sqlite3
import os
from datetime import datetime, timezone
from app.core.database import Base, engine, SessionLocal
from app.models.faculty import Faculty, FacultyUploadBatch, FacultyUploadBatchMember
from app.models.timetable import TimetableRecord
from app.models.history import FacultyDutyHistory

def migrate():
    # 1. Create all missing tables
    Base.metadata.create_all(bind=engine)
    print("Base metadata tables checked/created.")

    # 2. Add any missing columns to existing SQLite tables
    conn = sqlite3.connect("kam_bato.db")
    cursor = conn.cursor()

    columns_to_add = [
        ("faculty", "last_assigned_role", "TEXT"),
        ("faculty", "last_assigned_date", "DATE"),
        ("faculty", "current_cycle_duties", "INTEGER DEFAULT 0"),
        ("timetable_records", "shift_name", "TEXT DEFAULT 'Morning Shift'"),
        ("timetable_records", "duration", "TEXT DEFAULT '3 Hours'"),
        ("faculty_duty_history", "exam_timing", "TEXT"),
        ("faculty_duty_history", "status", "TEXT DEFAULT 'Approved'"),
    ]

    for table, col, col_type in columns_to_add:
        try:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_type};")
            print(f"Added column {col} to {table}")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                pass
            else:
                print(f"Notice on {table}.{col}: {e}")

    conn.commit()
    conn.close()

    # 3. Create initial active FacultyUploadBatch if none exists
    db = SessionLocal()
    existing_batch = db.query(FacultyUploadBatch).filter(FacultyUploadBatch.is_active == True).first()
    if not existing_batch:
        eligible_faculty = db.query(Faculty).filter(Faculty.role_category == "Faculty", Faculty.eligibility == True).all()
        batch = FacultyUploadBatch(
            batch_name="TCET Verified Faculty Roster (Initial Master)",
            filename="TCET_Faculty_List_AY2025_26.pdf",
            total_extracted=len(eligible_faculty),
            matched_existing_count=len(eligible_faculty),
            new_added_count=0,
            eligible_count=len(eligible_faculty),
            is_active=True
        )
        db.add(batch)
        db.flush()

        for f in eligible_faculty:
            bm = FacultyUploadBatchMember(
                batch_id=batch.id,
                faculty_id=f.id,
                is_eligible=True,
                notes="Verified Engineering Faculty Member"
            )
            db.add(bm)

        db.commit()
        print(f"Created initial active batch with {len(eligible_faculty)} eligible faculty.")
    else:
        print(f"Existing active batch already found: ID {existing_batch.id} ({existing_batch.total_extracted} members)")

    db.close()

if __name__ == "__main__":
    migrate()
