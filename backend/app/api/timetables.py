import os
import shutil
from typing import List, Optional
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.models.timetable import AcademicCodeMapping, TimetableUpload, TimetableRecord
from app.models.examination import Examination, ExaminationDate, ExaminationShift, ExaminationRoom
from app.services.timetable_parser import TimetableParser

router = APIRouter()

UPLOAD_DIR = os.path.join(os.getcwd(), "uploads", "timetables")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Pydantic Schemas
class CodeMappingCreate(BaseModel):
    code: str
    full_name: str
    category: str = "Year"
    description: Optional[str] = None

class TimetableRecordUpdate(BaseModel):
    department_name: Optional[str] = None
    programme: Optional[str] = None
    academic_year: Optional[str] = None
    semester: Optional[str] = None
    subject_name: Optional[str] = None
    subject_code: Optional[str] = None
    exam_date: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    confidence_score: Optional[int] = None

class TimetableRecordCreate(BaseModel):
    upload_id: Optional[int] = None
    exam_name: str
    department_name: str
    programme: Optional[str] = None
    academic_year: str
    semester: str
    subject_name: str
    subject_code: str
    exam_date: str
    start_time: str
    end_time: str
    confidence_score: int = 100
    notes: Optional[str] = "Manually added"

# ----------------- Academic Code Mappings -----------------

@router.get("/mappings")
def get_code_mappings(db: Session = Depends(get_db)):
    mappings = db.query(AcademicCodeMapping).all()
    if not mappings:
        # Seed standard defaults if empty
        defaults = [
            AcademicCodeMapping(code="SE", full_name="Second Year B.Tech", category="Year", description="Autonomous & University Curricula"),
            AcademicCodeMapping(code="TE", full_name="Third Year B.Tech", category="Year", description="Autonomous & University Curricula"),
            AcademicCodeMapping(code="BE", full_name="Final Year B.Tech", category="Year", description="Autonomous & University Curricula"),
            AcademicCodeMapping(code="FE", full_name="First Year B.Tech", category="Year", description="Common First Year Engineering"),
            AcademicCodeMapping(code="ST", full_name="Second Year (Autonomous Track)", category="Programme", description="Autonomous Curriculum Track"),
            AcademicCodeMapping(code="TT", full_name="Third Year (Autonomous Track)", category="Programme", description="Autonomous Curriculum Track"),
            AcademicCodeMapping(code="BT", full_name="Final Year (Autonomous Track)", category="Programme", description="Autonomous Curriculum Track"),
        ]
        db.add_all(defaults)
        db.commit()
        mappings = db.query(AcademicCodeMapping).all()

    return [
        {
            "id": m.id,
            "code": m.code,
            "full_name": m.full_name,
            "category": m.category,
            "description": m.description,
        }
        for m in mappings
    ]

@router.post("/mappings")
def create_code_mapping(data: CodeMappingCreate, db: Session = Depends(get_db)):
    existing = db.query(AcademicCodeMapping).filter(AcademicCodeMapping.code == data.code.strip().upper()).first()
    if existing:
        existing.full_name = data.full_name
        existing.category = data.category
        existing.description = data.description
        db.commit()
        return {"message": "Mapping updated successfully", "id": existing.id}
    
    mapping = AcademicCodeMapping(
        code=data.code.strip().upper(),
        full_name=data.full_name,
        category=data.category,
        description=data.description
    )
    db.add(mapping)
    db.commit()
    db.refresh(mapping)
    return {"message": "Mapping created successfully", "id": mapping.id}

@router.delete("/mappings/{mapping_id}")
def delete_code_mapping(mapping_id: int, db: Session = Depends(get_db)):
    m = db.query(AcademicCodeMapping).filter(AcademicCodeMapping.id == mapping_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Mapping not found")
    db.delete(m)
    db.commit()
    return {"message": "Mapping deleted"}

# ----------------- Timetable PDF Upload & Extraction -----------------

@router.post("/upload")
async def upload_timetable_pdf(
    file: UploadFile = File(...),
    exam_name: str = Form("End Semester Examination Winter 2026"),
    db: Session = Depends(get_db)
):
    """
    Asynchronous document extraction pipeline supporting native PDF & OCR fallback.
    Extracts exam timetable records with confidence scores.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF timetables are supported for this module.")

    timestamp = int(datetime.now().timestamp())
    saved_filename = f"timetable_{timestamp}_{file.filename}"
    saved_path = os.path.join(UPLOAD_DIR, saved_filename)

    with open(saved_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Load active custom academic code mappings from database
    mappings = db.query(AcademicCodeMapping).all()
    custom_map = {m.code: m.full_name for m in mappings}

    parser = TimetableParser(custom_mappings=custom_map)
    try:
        parsed_result = parser.parse_pdf_file(saved_path, default_exam_name=exam_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF parsing error: {str(e)}")

    upload_record = TimetableUpload(
        filename=file.filename,
        file_path=saved_path,
        total_pages=parsed_result["total_pages"],
        status="Reviewed",
        records_count=parsed_result["records_count"],
        processing_notes=f"Processed {parsed_result['total_pages']} pages. Extracted {parsed_result['records_count']} candidate examination entries."
    )
    db.add(upload_record)
    db.commit()
    db.refresh(upload_record)

    # Save extracted records for human review
    db_records = []
    for r in parsed_result["records"]:
        try:
            d_val = datetime.strptime(r["exam_date"], "%Y-%m-%d").date()
        except Exception:
            d_val = date(2026, 12, 12)

        rec = TimetableRecord(
            upload_id=upload_record.id,
            exam_name=r["exam_name"],
            department_name=r["department_name"],
            programme=r.get("programme"),
            academic_year=r["academic_year"],
            semester=r["semester"],
            subject_name=r["subject_name"],
            subject_code=r["subject_code"],
            exam_date=d_val,
            start_time=r["start_time"],
            end_time=r["end_time"],
            shift_name=r.get("shift_name") or parser._determine_shift(r["start_time"]),
            duration=r.get("duration") or parser.calculate_duration(r["start_time"], r["end_time"]),
            confidence_score=r["confidence_score"],
            is_confirmed=False,
            notes=r.get("notes")
        )
        db_records.append(rec)

    db.add_all(db_records)
    db.commit()

    return {
        "upload_id": upload_record.id,
        "filename": file.filename,
        "total_pages": parsed_result["total_pages"],
        "records_count": parsed_result["records_count"],
        "message": f"Successfully extracted {parsed_result['records_count']} examination schedule records across {parsed_result['total_pages']} pages. Please review."
    }

# ----------------- Review Extracted Timetable Screen -----------------

@router.get("/records")
def list_extracted_records(
    upload_id: Optional[int] = None,
    is_confirmed: Optional[bool] = None,
    exam_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(TimetableRecord)
    if upload_id is not None:
        query = query.filter(TimetableRecord.upload_id == upload_id)
    if is_confirmed is not None:
        query = query.filter(TimetableRecord.is_confirmed == is_confirmed)
    if exam_date:
        try:
            d = datetime.strptime(exam_date, "%Y-%m-%d").date()
            query = query.filter(TimetableRecord.exam_date == d)
        except Exception:
            pass

    records = query.order_by(TimetableRecord.exam_date.asc(), TimetableRecord.department_name.asc()).all()

    return [
        {
            "id": r.id,
            "upload_id": r.upload_id,
            "exam_name": r.exam_name,
            "department_name": r.department_name,
            "programme": r.programme,
            "academic_year": r.academic_year,
            "semester": r.semester,
            "subject_name": r.subject_name,
            "subject_code": r.subject_code,
            "exam_date": str(r.exam_date),
            "start_time": r.start_time,
            "end_time": r.end_time,
            "shift_name": r.shift_name or ("Morning Shift" if "AM" in (r.start_time or "").upper() else "Evening Shift"),
            "duration": r.duration or "3 Hours",
            "time_range": f"{r.start_time} - {r.end_time}",
            "confidence_score": r.confidence_score,
            "is_confirmed": r.is_confirmed,
            "notes": r.notes
        }
        for r in records
    ]

@router.put("/records/{record_id}")
def update_extracted_record(
    record_id: int,
    data: TimetableRecordUpdate,
    db: Session = Depends(get_db)
):
    rec = db.query(TimetableRecord).filter(TimetableRecord.id == record_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Record not found")

    if data.department_name: rec.department_name = data.department_name
    if data.programme: rec.programme = data.programme
    if data.academic_year: rec.academic_year = data.academic_year
    if data.semester: rec.semester = data.semester
    if data.subject_name: rec.subject_name = data.subject_name
    if data.subject_code: rec.subject_code = data.subject_code
    if data.exam_date:
        try:
            rec.exam_date = datetime.strptime(data.exam_date, "%Y-%m-%d").date()
        except Exception:
            pass
    if data.start_time: rec.start_time = data.start_time
    if data.end_time: rec.end_time = data.end_time
    if data.confidence_score is not None: rec.confidence_score = data.confidence_score

    rec.notes = "Manually corrected by Controller of Examination"
    db.commit()
    return {"message": "Record updated successfully"}

@router.post("/records")
def add_manual_timetable_record(
    data: TimetableRecordCreate,
    db: Session = Depends(get_db)
):
    try:
        d_val = datetime.strptime(data.exam_date, "%Y-%m-%d").date()
    except Exception:
        d_val = date(2026, 12, 12)

    rec = TimetableRecord(
        upload_id=data.upload_id,
        exam_name=data.exam_name,
        department_name=data.department_name,
        programme=data.programme or f"B.Tech {data.department_name}",
        academic_year=data.academic_year,
        semester=data.semester,
        subject_name=data.subject_name,
        subject_code=data.subject_code,
        exam_date=d_val,
        start_time=data.start_time,
        end_time=data.end_time,
        confidence_score=100,
        is_confirmed=False,
        notes=data.notes or "Manually entered"
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return {"message": "Record added successfully", "id": rec.id}

@router.delete("/records/{record_id}")
def delete_extracted_record(
    record_id: int,
    db: Session = Depends(get_db)
):
    rec = db.query(TimetableRecord).filter(TimetableRecord.id == record_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Record not found")
    db.delete(rec)
    db.commit()
    return {"message": "Record deleted"}

@router.post("/confirm")
def confirm_timetable_records(
    record_ids: Optional[List[int]] = None,
    upload_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Confirms reviewed records so they enter the main Examination Database.
    Automatically populates Examination, ExaminationDate, ExaminationShift, ExaminationRoom.
    """
    query = db.query(TimetableRecord)
    if record_ids:
        query = query.filter(TimetableRecord.id.in_(record_ids))
    elif upload_id:
        query = query.filter(TimetableRecord.upload_id == upload_id)
    else:
        query = query.filter(TimetableRecord.is_confirmed == False)

    records = query.all()
    if not records:
        return {"message": "No unconfirmed records to commit.", "confirmed_count": 0}

    # Mark as confirmed
    confirmed_count = 0
    for r in records:
        r.is_confirmed = True
        confirmed_count += 1

        # Check if Examination already exists or create
        exam = db.query(Examination).filter(Examination.name == r.exam_name).first()
        if not exam:
            exam = Examination(
                name=r.exam_name,
                academic_year="2026-2027",
                semester=r.semester,
                exam_level=r.academic_year,
                start_date=r.exam_date,
                end_date=r.exam_date,
                is_active=True
            )
            db.add(exam)
            db.flush()

        # Check if ExaminationDate exists
        ex_date = db.query(ExaminationDate).filter(
            ExaminationDate.exam_id == exam.id,
            ExaminationDate.exam_date == r.exam_date
        ).first()
        if not ex_date:
            ex_date = ExaminationDate(
                exam_id=exam.id,
                exam_date=r.exam_date,
                day_name=r.exam_date.strftime("%A")
            )
            db.add(ex_date)
            db.flush()

        # Check if ExaminationShift exists
        shift_name = "Morning" if "AM" in r.start_time.upper() else "Afternoon"
        shift = db.query(ExaminationShift).filter(
            ExaminationShift.exam_date_id == ex_date.id,
            ExaminationShift.shift_name == shift_name
        ).first()
        if not shift:
            shift = ExaminationShift(
                exam_date_id=ex_date.id,
                shift_name=shift_name,
                start_time=r.start_time,
                end_time=r.end_time,
                block_count=20, # Default classroom blocks
                status="Scheduled"
            )
            db.add(shift)
            db.flush()

    db.commit()

    return {
        "message": f"Successfully confirmed {confirmed_count} records into the main Examination database.",
        "confirmed_count": confirmed_count
    }
