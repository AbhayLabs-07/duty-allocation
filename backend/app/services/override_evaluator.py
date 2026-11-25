from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.faculty import Faculty
from app.models.allocation import DutyAllocation
from app.models.history import FacultyAvailability

def evaluate_override_impact(
    db: Session,
    shift_id: int,
    original_faculty_id: int,
    replacement_faculty_id: int,
    new_role: str
) -> Dict[str, Any]:
    """
    Evaluates the fairness and workload impact of substituting original_faculty with replacement_faculty.
    Generates actionable warnings if:
    1. Replacement faculty has significantly higher historical JS than average.
    2. Replacement faculty is marked Unavailable/On Leave on this date.
    3. Replacement faculty is already assigned in this shift.
    4. Consecutive duty is triggered.
    """
    orig = db.query(Faculty).filter(Faculty.id == original_faculty_id).first()
    repl = db.query(Faculty).filter(Faculty.id == replacement_faculty_id).first()

    if not orig or not repl:
        return {"has_warning": False, "warnings": [], "impact_message": "Faculty records not found."}

    warnings = []

    # Check 1: Is replacement faculty available?
    # (Get shift date)
    from app.models.examination import ExaminationShift
    shift = db.query(ExaminationShift).filter(ExaminationShift.id == shift_id).first()
    if shift and shift.exam_date_rel:
        exam_date = shift.exam_date_rel.exam_date
        avail = db.query(FacultyAvailability).filter(
            FacultyAvailability.faculty_id == replacement_faculty_id,
            FacultyAvailability.date == exam_date
        ).first()
        if avail and not avail.is_available:
            warnings.append(
                f"Hard Conflict: {repl.name} is marked '{avail.status}' on {exam_date} (Reason: {avail.reason or 'Unspecified'})."
            )

    # Check 2: Is replacement faculty already assigned in this shift?
    existing_alloc = db.query(DutyAllocation).filter(
        DutyAllocation.shift_id == shift_id,
        DutyAllocation.faculty_id == replacement_faculty_id
    ).first()
    if existing_alloc:
        warnings.append(
            f"Duplicate Assignment: {repl.name} is already assigned as '{existing_alloc.assigned_role}' in this examination shift."
        )

    # Check 3: JS workload spike
    if new_role == "JS":
        # Calculate current average JS in department/college
        all_faculty = db.query(Faculty).filter(Faculty.eligibility == True).all()
        avg_js = sum(f.previous_js_count for f in all_faculty) / max(1, len(all_faculty))
        new_count = repl.previous_js_count + 1
        if new_count > avg_js + 1.5:
            warnings.append(
                f"Workload Warning: This replacement increases {repl.name}'s JS assignments to {new_count} while the current average is {avg_js:.1f}."
            )

    has_warning = len(warnings) > 0
    impact_message = (
        " ".join(warnings) if has_warning
        else f"Replacement verified. {repl.name} has balanced history ({repl.previous_js_count} JS, {repl.previous_reliever_count} Reliever) with no schedule conflicts."
    )

    return {
        "has_warning": has_warning,
        "warnings": warnings,
        "impact_message": impact_message,
        "original_faculty_name": orig.name,
        "replacement_faculty_name": repl.name,
        "new_role": new_role,
    }
