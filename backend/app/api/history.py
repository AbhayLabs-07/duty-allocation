from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.history import FacultyDutyHistory
from app.models.faculty import Faculty

router = APIRouter()

@router.get("")
def get_duty_history(
    faculty_id: Optional[int] = None,
    department_id: Optional[int] = None,
    role_served: Optional[str] = None,
    skip: int = 0,
    limit: int = 200,
    db: Session = Depends(get_db)
):
    query = db.query(FacultyDutyHistory).join(Faculty)
    if faculty_id:
        query = query.filter(FacultyDutyHistory.faculty_id == faculty_id)
    if department_id:
        query = query.filter(Faculty.department_id == department_id)
    if role_served:
        query = query.filter(FacultyDutyHistory.role_served == role_served)

    histories = query.order_by(FacultyDutyHistory.exam_date.desc()).offset(skip).limit(limit).all()
    results = []
    for h in histories:
        results.append({
            "id": h.id,
            "faculty_id": h.faculty_id,
            "faculty_name": h.faculty.name if h.faculty else "Unknown",
            "department_name": h.faculty.department.name if (h.faculty and h.faculty.department) else "Unknown",
            "exam_name": h.exam_name,
            "academic_year": h.academic_year,
            "semester": h.semester,
            "exam_date": str(h.exam_date),
            "shift_name": h.shift_name,
            "role_served": h.role_served,
            "block_or_room": h.block_or_room,
            "is_manual_override": h.is_manual_override,
            "recorded_at": h.recorded_at.isoformat() if h.recorded_at else None
        })
    return results
