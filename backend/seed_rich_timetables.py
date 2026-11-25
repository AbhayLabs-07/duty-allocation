import os
from datetime import date
from app.core.database import SessionLocal
from app.models.timetable import TimetableRecord
from app.models.examination import ExaminationDate, ExaminationShift, Examination

def seed_rich_timetables():
    db = SessionLocal()
    # Remove older demo records so we have clean, non-duplicate records
    db.query(TimetableRecord).delete()
    db.commit()

    sample_records = [
        # 2026-12-12 Morning Shift (Various Durations: 2 hrs, 1.5 hrs, 3 hrs)
        {
            "exam_name": "End Semester Examination Winter 2026",
            "department_name": "AI&DS",
            "programme": "B.Tech Artificial Intelligence & Data Science",
            "academic_year": "ST",
            "semester": "Semester IV",
            "subject_name": "Database Management Systems",
            "subject_code": "AID301",
            "exam_date": date(2026, 12, 12),
            "start_time": "10:30 AM",
            "end_time": "12:30 PM",
            "shift_name": "Morning Shift",
            "duration": "2 Hours",
            "confidence_score": 96,
            "is_confirmed": True,
            "notes": "Verified extracted record"
        },
        {
            "exam_name": "End Semester Examination Winter 2026",
            "department_name": "IT",
            "programme": "B.Tech Information Technology",
            "academic_year": "SE",
            "semester": "Semester IV",
            "subject_name": "Engineering Mathematics IV",
            "subject_code": "IT401",
            "exam_date": date(2026, 12, 12),
            "start_time": "10:30 AM",
            "end_time": "12:00 PM",
            "shift_name": "Morning Shift",
            "duration": "1.5 Hours",
            "confidence_score": 94,
            "is_confirmed": True,
            "notes": "Verified extracted record"
        },
        {
            "exam_name": "End Semester Examination Winter 2026",
            "department_name": "COMP",
            "programme": "B.Tech Computer Engineering",
            "academic_year": "BE",
            "semester": "Semester VIII",
            "subject_name": "Machine Learning & Distributed Systems",
            "subject_code": "CS501",
            "exam_date": date(2026, 12, 12),
            "start_time": "10:30 AM",
            "end_time": "01:30 PM",
            "shift_name": "Morning Shift",
            "duration": "3 Hours",
            "confidence_score": 98,
            "is_confirmed": True,
            "notes": "Verified extracted record"
        },
        # 2026-12-12 Evening Shift (Various Durations: 1.5 hrs, 2 hrs, 3 hrs)
        {
            "exam_name": "End Semester Examination Winter 2026",
            "department_name": "IT",
            "programme": "B.Tech Information Technology",
            "academic_year": "TT",
            "semester": "Semester VI",
            "subject_name": "Web Architecture & Microservices",
            "subject_code": "IT503",
            "exam_date": date(2026, 12, 12),
            "start_time": "02:30 PM",
            "end_time": "04:00 PM",
            "shift_name": "Evening Shift",
            "duration": "1.5 Hours",
            "confidence_score": 95,
            "is_confirmed": True,
            "notes": "Verified extracted record"
        },
        {
            "exam_name": "End Semester Examination Winter 2026",
            "department_name": "COMP",
            "programme": "B.Tech Computer Engineering",
            "academic_year": "TE",
            "semester": "Semester VI",
            "subject_name": "Computer Networks & Cryptography",
            "subject_code": "CS402",
            "exam_date": date(2026, 12, 12),
            "start_time": "02:30 PM",
            "end_time": "04:30 PM",
            "shift_name": "Evening Shift",
            "duration": "2 Hours",
            "confidence_score": 94,
            "is_confirmed": True,
            "notes": "Verified extracted record"
        },
        {
            "exam_name": "End Semester Examination Winter 2026",
            "department_name": "MECH",
            "programme": "B.Tech Mechanical Engineering",
            "academic_year": "BT",
            "semester": "Semester VIII",
            "subject_name": "Fluid Mechanics & Thermal Dynamics",
            "subject_code": "ME302",
            "exam_date": date(2026, 12, 12),
            "start_time": "02:30 PM",
            "end_time": "05:30 PM",
            "shift_name": "Evening Shift",
            "duration": "3 Hours",
            "confidence_score": 92,
            "is_confirmed": True,
            "notes": "Verified extracted record"
        },
        # 2026-12-14 Morning Shift
        {
            "exam_name": "End Semester Examination Winter 2026",
            "department_name": "CIVIL",
            "programme": "B.Tech Civil Engineering",
            "academic_year": "TE",
            "semester": "Semester VI",
            "subject_name": "Structural Analysis & Concrete Technology",
            "subject_code": "CE403",
            "exam_date": date(2026, 12, 14),
            "start_time": "10:30 AM",
            "end_time": "01:30 PM",
            "shift_name": "Morning Shift",
            "duration": "3 Hours",
            "confidence_score": 93,
            "is_confirmed": True,
            "notes": "Verified extracted record"
        },
        # 2026-12-14 Evening Shift
        {
            "exam_name": "End Semester Examination Winter 2026",
            "department_name": "E&TC",
            "programme": "B.Tech Electronics & Telecommunication",
            "academic_year": "SE",
            "semester": "Semester IV",
            "subject_name": "Signals and Linear Systems",
            "subject_code": "ETC401",
            "exam_date": date(2026, 12, 14),
            "start_time": "02:30 PM",
            "end_time": "04:30 PM",
            "shift_name": "Evening Shift",
            "duration": "2 Hours",
            "confidence_score": 91,
            "is_confirmed": True,
            "notes": "Verified extracted record"
        },
    ]

    for rec_data in sample_records:
        r = TimetableRecord(**rec_data)
        db.add(r)
    db.commit()

    # Ensure ExaminationDate and ExaminationShift records exist for 2026-12-12 and 2026-12-14
    exam = db.query(Examination).first()
    if not exam:
        exam = Examination(
            name="End Semester Examination Winter 2026",
            academic_year="2026-2027",
            semester="Semester IV",
            exam_level="SE/TE/BE",
            start_date=date(2026, 12, 12),
            end_date=date(2026, 12, 16),
            is_active=True
        )
        db.add(exam)
        db.flush()

    for d_val in [date(2026, 12, 12), date(2026, 12, 14)]:
        ex_d = db.query(ExaminationDate).filter(ExaminationDate.exam_date == d_val).first()
        if not ex_d:
            ex_d = ExaminationDate(
                exam_id=exam.id,
                exam_date=d_val,
                day_name=d_val.strftime("%A")
            )
            db.add(ex_d)
            db.flush()

        for s_name, s_start, s_end in [("Morning Shift", "10:30 AM", "01:30 PM"), ("Evening Shift", "02:30 PM", "05:30 PM")]:
            ex_s = db.query(ExaminationShift).filter(
                ExaminationShift.exam_date_id == ex_d.id,
                ExaminationShift.shift_name == s_name
            ).first()
            if not ex_s:
                ex_s = ExaminationShift(
                    exam_date_id=ex_d.id,
                    shift_name=s_name,
                    start_time=s_start,
                    end_time=s_end,
                    block_count=24,
                    status="Scheduled"
                )
                db.add(ex_s)
    db.commit()
    print("Successfully populated verified timetable records and shifts.")
    db.close()

if __name__ == "__main__":
    seed_rich_timetables()
