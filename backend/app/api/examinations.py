from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.examination import Examination, ExaminationDate, ExaminationShift, ExaminationRoom
from app.models.faculty import Faculty
from app.schemas.all_schemas import ExaminationOut, ExaminationCreate, ShiftOut, RoomCreate, RoomOut

router = APIRouter()

@router.get("", response_model=List[ExaminationOut])
def list_examinations(is_active: Optional[bool] = None, db: Session = Depends(get_db)):
    query = db.query(Examination)
    if is_active is not None:
        query = query.filter(Examination.is_active == is_active)
    return query.order_by(Examination.start_date.desc()).all()

@router.get("/{exam_id}", response_model=ExaminationOut)
def get_examination(exam_id: int, db: Session = Depends(get_db)):
    exam = db.query(Examination).filter(Examination.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Examination not found")
    return exam

@router.post("", response_model=ExaminationOut)
def create_examination(exam_in: ExaminationCreate, db: Session = Depends(get_db)):
    exam = Examination(
        name=exam_in.name,
        academic_year=exam_in.academic_year,
        semester=exam_in.semester,
        exam_level=exam_in.exam_level,
        start_date=exam_in.start_date,
        end_date=exam_in.end_date,
        is_active=True
    )
    db.add(exam)
    db.flush()

    for d_in in exam_in.dates:
        exam_date = ExaminationDate(
            exam_id=exam.id,
            exam_date=d_in.exam_date,
            day_name=d_in.day_name or d_in.exam_date.strftime("%A")
        )
        db.add(exam_date)
        db.flush()

        for s_in in d_in.shifts:
            shift = ExaminationShift(
                exam_date_id=exam_date.id,
                shift_name=s_in.shift_name,
                start_time=s_in.start_time,
                end_time=s_in.end_time,
                block_count=s_in.block_count,
                room_list_str=s_in.room_list_str,
                status="Scheduled"
            )
            db.add(shift)
            db.flush()

            # Create individual rooms if room_list_str provided
            if s_in.room_list_str:
                room_names = [r.strip() for r in s_in.room_list_str.split(",") if r.strip()]
                for b_idx, r_name in enumerate(room_names, start=1):
                    rm = ExaminationRoom(
                        shift_id=shift.id,
                        block_number=b_idx,
                        room_number=r_name,
                        block_label=f"Block {b_idx} ({r_name})",
                        capacity=30
                    )
                    db.add(rm)

    db.commit()
    db.refresh(exam)
    return exam

@router.get("/shifts/{shift_id}")
def get_shift_details(shift_id: int, db: Session = Depends(get_db)):
    shift = db.query(ExaminationShift).filter(ExaminationShift.id == shift_id).first()
    if not shift:
        raise HTTPException(status_code=404, detail="Shift not found")
    
    exam_date = shift.exam_date_rel
    exam = exam_date.examination if exam_date else None
    rooms = db.query(ExaminationRoom).filter(ExaminationRoom.shift_id == shift_id).order_by(ExaminationRoom.block_number).all()
    
    # Calculate eligible faculty count
    eligible_count = db.query(Faculty).filter(Faculty.eligibility == True).count()

    return {
        "shift_id": shift.id,
        "shift_name": shift.shift_name,
        "start_time": shift.start_time,
        "end_time": shift.end_time,
        "status": shift.status,
        "block_count": shift.block_count,
        "room_list_str": shift.room_list_str,
        "exam_name": exam.name if exam else "General Exam",
        "exam_year": exam.academic_year if exam else "",
        "semester": exam.semester if exam else "",
        "exam_date": str(exam_date.exam_date) if exam_date else "",
        "day_name": exam_date.day_name if exam_date else "",
        "eligible_faculty_count": eligible_count,
        "rooms": [{"id": r.id, "block_number": r.block_number, "room_number": r.room_number, "label": r.block_label} for r in rooms]
    }

@router.put("/shifts/{shift_id}/blocks")
def update_shift_blocks(shift_id: int, block_count: int, room_list_str: Optional[str] = None, db: Session = Depends(get_db)):
    shift = db.query(ExaminationShift).filter(ExaminationShift.id == shift_id).first()
    if not shift:
        raise HTTPException(status_code=404, detail="Shift not found")
    
    shift.block_count = block_count
    if room_list_str:
        shift.room_list_str = room_list_str
        # Recreate rooms
        db.query(ExaminationRoom).filter(ExaminationRoom.shift_id == shift.id).delete()
        room_names = [r.strip() for r in room_list_str.split(",") if r.strip()]
        for b_idx in range(1, block_count + 1):
            r_name = room_names[b_idx - 1] if b_idx <= len(room_names) else f"R-{100 + b_idx}"
            rm = ExaminationRoom(
                shift_id=shift.id,
                block_number=b_idx,
                room_number=r_name,
                block_label=f"Block {b_idx} ({r_name})",
                capacity=30
            )
            db.add(rm)
    db.commit()
    return {"status": "success", "shift_id": shift.id, "block_count": shift.block_count}
