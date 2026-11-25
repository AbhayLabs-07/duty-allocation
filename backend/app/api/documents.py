import os
import shutil
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
from app.models.duty_chart import UploadedDutyChart, ExtractedDutyRecord
from app.models.faculty import Faculty
from app.models.department import Department
from app.models.history import FacultyDutyHistory
from app.schemas.all_schemas import UploadedChartOut, ExtractedRecordOut, ExtractedRecordUpdate
from app.services.document_parser import DocumentParser

router = APIRouter()

@router.post("/upload", response_model=UploadedChartOut)
def upload_duty_chart(
    file: UploadFile = File(...),
    exam_name: Optional[str] = Form(None),
    exam_year: Optional[str] = Form(None),
    semester: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    filename = file.filename
    ext = os.path.splitext(filename)[1].lower()
    
    file_type_map = {
        ".xlsx": "excel",
        ".xls": "excel",
        ".docx": "docx",
        ".pdf": "pdf",
        ".png": "image",
        ".jpg": "image",
        ".jpeg": "image",
        ".bmp": "image"
    }
    file_type = file_type_map.get(ext)
    if not file_type:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{ext}'. Allowed: .xlsx, .xls, .docx, .pdf, images (.png, .jpg)"
        )

    # Save file to disk
    save_path = os.path.join(settings.UPLOAD_DIR, filename)
    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Prepare faculty master list for fuzzy matching
    faculty_list = db.query(Faculty).join(Department).all()
    faculty_master_dicts = [
        {
            "id": f.id,
            "name": f.name,
            "department_id": f.department_id,
            "department_name": f.department.name if f.department else ""
        }
        for f in faculty_list
    ]

    parser = DocumentParser(faculty_master=faculty_master_dicts)
    try:
        parse_result = parser.parse_file(save_path, filename)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process document: {str(e)}")

    metadata = parse_result.get("metadata", {})
    records = parse_result.get("records", [])

    # Create Upload Record
    chart = UploadedDutyChart(
        filename=filename,
        file_type=file_type,
        file_path=save_path,
        status="Pending Verification",
        total_records_extracted=len(records),
        detected_exam_name=exam_name or metadata.get("detected_exam_name") or "Extracted Examination",
        detected_exam_year=exam_year or metadata.get("detected_exam_year") or "2025-2026",
        detected_semester=semester or metadata.get("detected_semester") or "Semester IV",
        detected_exam_date=metadata.get("detected_exam_date"),
        detected_shift=metadata.get("detected_shift"),
        detected_block_count=metadata.get("detected_block_count"),
        detected_rooms=metadata.get("detected_rooms")
    )
    db.add(chart)
    db.flush()

    for r in records:
        rec = ExtractedDutyRecord(
            upload_id=chart.id,
            raw_faculty_name=r["raw_faculty_name"],
            raw_department=r.get("raw_department"),
            raw_date=str(r.get("raw_date")) if r.get("raw_date") else None,
            raw_shift=r.get("raw_shift"),
            raw_duty_role=r.get("raw_duty_role"),
            raw_total_duty=r.get("raw_total_duty"),
            matched_faculty_id=r.get("matched_faculty_id"),
            matched_faculty_name=r.get("matched_faculty_name"),
            matched_department_id=r.get("matched_department_id"),
            verified_duty_role=r.get("verified_duty_role"),
            confidence_score=r.get("confidence_score", 100),
            is_verified=r.get("is_verified", False),
            verification_notes=f"Match Confidence: {r.get('confidence_score', 100)}%"
        )
        db.add(rec)

    db.commit()
    db.refresh(chart)
    return chart

@router.get("", response_model=List[UploadedChartOut])
def list_uploaded_charts(db: Session = Depends(get_db)):
    return db.query(UploadedDutyChart).order_by(UploadedDutyChart.uploaded_at.desc()).all()

@router.get("/{upload_id}", response_model=UploadedChartOut)
def get_uploaded_chart(upload_id: int, db: Session = Depends(get_db)):
    chart = db.query(UploadedDutyChart).filter(UploadedDutyChart.id == upload_id).first()
    if not chart:
        raise HTTPException(status_code=404, detail="Uploaded chart not found")
    return chart

@router.put("/records/{record_id}")
def update_extracted_record(record_id: int, update_in: ExtractedRecordUpdate, db: Session = Depends(get_db)):
    record = db.query(ExtractedDutyRecord).filter(ExtractedDutyRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Extracted duty record not found")
    
    if update_in.matched_faculty_id:
        fac = db.query(Faculty).filter(Faculty.id == update_in.matched_faculty_id).first()
        if fac:
            record.matched_faculty_id = fac.id
            record.matched_faculty_name = fac.name
            record.matched_department_id = fac.department_id
    
    if update_in.verified_duty_role:
        record.verified_duty_role = update_in.verified_duty_role
    
    record.is_verified = update_in.is_verified
    record.verification_notes = update_in.verification_notes or "Manually verified by administrator"
    db.commit()
    return {"status": "success", "record_id": record.id, "is_verified": record.is_verified}

@router.post("/{upload_id}/verify-and-save")
def verify_and_save_chart(upload_id: int, db: Session = Depends(get_db)):
    """
    Finalizes verification: saves verified historical records into FacultyDutyHistory
    and updates cached counters on Faculty Master.
    """
    chart = db.query(UploadedDutyChart).filter(UploadedDutyChart.id == upload_id).first()
    if not chart:
        raise HTTPException(status_code=404, detail="Upload not found")

    records = db.query(ExtractedDutyRecord).filter(ExtractedDutyRecord.upload_id == upload_id).all()
    committed_count = 0

    for r in records:
        fac_id = r.matched_faculty_id
        if not fac_id:
            continue
        
        fac = db.query(Faculty).filter(Faculty.id == fac_id).first()
        if not fac:
            continue

        role = r.verified_duty_role or r.raw_duty_role or "JS"
        
        # Save into history
        hist = FacultyDutyHistory(
            faculty_id=fac.id,
            exam_name=chart.detected_exam_name or "Historical Examination",
            academic_year=chart.detected_exam_year or "2025-2026",
            semester=chart.detected_semester or "Semester IV",
            exam_date=chart.detected_exam_date or chart.uploaded_at.date(),
            shift_name=r.raw_shift or chart.detected_shift or "Morning",
            role_served=role,
            block_or_room="Verified Document Record"
        )
        db.add(hist)

        # Increment faculty counter
        if role == "JS":
            fac.previous_js_count += 1
        elif role == "Reliever":
            fac.previous_reliever_count += 1
        elif role == "Standby":
            fac.previous_standby_count += 1
        elif role == "SS":
            fac.previous_ss_count += 1

        fac.total_previous_duties = fac.previous_js_count + fac.previous_reliever_count + fac.previous_standby_count + fac.previous_ss_count
        r.is_verified = True
        committed_count += 1

    chart.status = "Verified"
    db.commit()

    return {
        "status": "success",
        "message": f"Successfully verified and recorded {committed_count} historical duty entries.",
        "chart_status": chart.status
    }
