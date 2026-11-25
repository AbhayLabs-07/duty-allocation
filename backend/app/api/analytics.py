from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.models.faculty import Faculty
from app.models.department import Department
from app.models.examination import Examination, ExaminationShift
from app.models.allocation import DutyAllocation
from app.models.history import FacultyDutyHistory
from app.schemas.all_schemas import DashboardSummary

router = APIRouter()

def calculate_gini(values: List[float]) -> float:
    """Calculates Gini coefficient for duty distribution fairness (0.0 = perfect equity)."""
    if not values or len(values) == 0:
        return 0.0
    sorted_vals = sorted(values)
    n = len(values)
    cum_sum = 0
    total = sum(sorted_vals)
    if total == 0:
        return 0.0
    for i, val in enumerate(sorted_vals):
        cum_sum += (i + 1) * val
    return round((2 * cum_sum) / (n * total) - (n + 1) / n, 3)

@router.get("/summary", response_model=DashboardSummary)
def get_dashboard_summary(db: Session = Depends(get_db)):
    total_faculty = db.query(Faculty).count()
    total_depts = db.query(Department).count()
    upcoming_exams = db.query(Examination).filter(Examination.is_active == True).count()
    
    # Available blocks from upcoming scheduled shifts
    shifts = db.query(ExaminationShift).all()
    available_blocks = sum(s.block_count for s in shifts)

    # Historical and allocated counts
    total_js = db.query(func.sum(Faculty.previous_js_count)).scalar() or 0
    total_rel = db.query(func.sum(Faculty.previous_reliever_count)).scalar() or 0
    total_stb = db.query(func.sum(Faculty.previous_standby_count)).scalar() or 0
    total_ss = db.query(func.sum(Faculty.previous_ss_count)).scalar() or 0

    # Gini coefficient of total duties
    all_duties = [f.total_previous_duties for f in db.query(Faculty).all()]
    gini = calculate_gini([float(d) for d in all_duties])

    # Top faculty with highest JS count (candidates for Reliever/Standby priority)
    highest_js = db.query(Faculty).order_by(Faculty.previous_js_count.desc()).limit(8).all()
    high_js_list = [
        {
            "id": f.id,
            "faculty_id": f.faculty_id,
            "name": f.name,
            "department": f.department.name if f.department else "",
            "js_count": f.previous_js_count,
            "reliever_count": f.previous_reliever_count,
            "standby_count": f.previous_standby_count,
            "total_duties": f.total_previous_duties
        }
        for f in highest_js
    ]

    # Faculty with lowest Reliever count
    lowest_rel = db.query(Faculty).filter(Faculty.role_category == "Faculty").order_by(
        Faculty.previous_reliever_count.asc(), Faculty.previous_js_count.desc()
    ).limit(8).all()
    low_rel_list = [
        {
            "id": f.id,
            "faculty_id": f.faculty_id,
            "name": f.name,
            "department": f.department.name if f.department else "",
            "js_count": f.previous_js_count,
            "reliever_count": f.previous_reliever_count,
            "standby_count": f.previous_standby_count,
            "total_duties": f.total_previous_duties
        }
        for f in lowest_rel
    ]

    # Faculty with lowest Standby count
    lowest_stb = db.query(Faculty).filter(Faculty.role_category == "Faculty").order_by(
        Faculty.previous_standby_count.asc(), Faculty.previous_js_count.desc()
    ).limit(8).all()
    low_stb_list = [
        {
            "id": f.id,
            "faculty_id": f.faculty_id,
            "name": f.name,
            "department": f.department.name if f.department else "",
            "js_count": f.previous_js_count,
            "reliever_count": f.previous_reliever_count,
            "standby_count": f.previous_standby_count,
            "total_duties": f.total_previous_duties
        }
        for f in lowest_stb
    ]

    # Department-wise distribution
    dept_distribution = []
    departments = db.query(Department).all()
    for d in departments:
        f_list = db.query(Faculty).filter(Faculty.department_id == d.id).all()
        f_cnt = len(f_list)
        d_js = sum(f.previous_js_count for f in f_list)
        d_rel = sum(f.previous_reliever_count for f in f_list)
        d_stb = sum(f.previous_standby_count for f in f_list)
        d_ss = sum(f.previous_ss_count for f in f_list)
        d_tot = sum(f.total_previous_duties for f in f_list)
        dept_distribution.append({
            "department_code": d.code,
            "department_name": d.name,
            "faculty_count": f_cnt,
            "total_duties": d_tot,
            "js_count": d_js,
            "reliever_count": d_rel,
            "standby_count": d_stb,
            "ss_count": d_ss,
            "avg_duties_per_faculty": round(d_tot / max(1, f_cnt), 2)
        })

    # Recent proposed / approved allocations
    recent_allocs = db.query(DutyAllocation).order_by(DutyAllocation.id.desc()).limit(10).all()
    recent_list = [
        {
            "id": a.id,
            "faculty_name": a.faculty.name if a.faculty else "",
            "department": a.faculty.department.code if (a.faculty and a.faculty.department) else "",
            "assigned_role": a.assigned_role,
            "assigned_block": a.assigned_block,
            "status": a.status,
            "explainability_reason": a.explainability_reason
        }
        for a in recent_allocs
    ]

    return DashboardSummary(
        total_faculty=total_faculty,
        total_departments=total_depts,
        upcoming_examinations=upcoming_exams,
        available_blocks=available_blocks,
        total_js_assigned=total_js,
        total_reliever_assigned=total_rel,
        total_standby_assigned=total_stb,
        total_ss_assigned=total_ss,
        fairness_gini_coefficient=gini,
        faculty_highest_js=high_js_list,
        faculty_lowest_reliever=low_rel_list,
        faculty_lowest_standby=low_stb_list,
        department_distribution=dept_distribution,
        recent_allocations=recent_list
    )
