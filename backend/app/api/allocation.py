import math
import re
from typing import List, Optional, Dict, Any
from datetime import date, datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Response, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.examination import ExaminationShift, ExaminationRoom, ExaminationDate, Examination
from app.models.faculty import Faculty, FacultyUploadBatch, FacultyUploadBatchMember
from app.models.department import Department
from app.models.allocation import DutyAllocation, AllocationConfiguration, AllocationAuditLog, ManualOverrideRecord
from app.models.history import FacultyDutyHistory, FacultyAvailability
from app.models.timetable import TimetableRecord
from app.schemas.all_schemas import (
    AllocationRunRequest, AllocationSummary, DutyAllocationOut,
    ManualOverrideRequest, ImpactCheckRequest, ReplaceFacultyRequest,
    RequirementCalculationRequest
)
from app.services.optimizer import FairnessOptimizer, ShortageError
from app.services.override_evaluator import evaluate_override_impact
from app.services.report_generator import ReportGenerator

router = APIRouter()

# ----------------- Date & Dynamic Timings Retrieval -----------------

@router.get("/date-exams")
def get_date_examinations(
    date_str: str = Query(..., alias="date"),
    shift_name: Optional[str] = Query(None, alias="shift"),
    timing_str: Optional[str] = Query(None, alias="timing"),
    db: Session = Depends(get_db)
):
    """
    Retrieves all verified examination records, academic years, departments,
    subjects, and dynamic examination timings occurring on the selected date.
    """
    try:
        t_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

    tt_query = db.query(TimetableRecord).filter(TimetableRecord.exam_date == t_date)
    tt_records = tt_query.all()

    # Also search examination dates
    ex_dates = db.query(ExaminationDate).filter(ExaminationDate.exam_date == t_date).all()

    all_exams_list = []
    seen = set()

    # Group timings chronologically by shift
    timings_by_shift = {
        "Morning Shift": set(),
        "Evening Shift": set()
    }

    for r in tt_records:
        r_shift = r.shift_name or ("Morning Shift" if "AM" in (r.start_time or "").upper() else "Evening Shift")
        t_range = f"{r.start_time} - {r.end_time}"
        
        if r_shift in timings_by_shift:
            timings_by_shift[r_shift].add(t_range)
        else:
            timings_by_shift["Morning Shift"].add(t_range)

        key = f"{r.department_name}-{r.academic_year}-{r.subject_code}-{r.start_time}"
        if key not in seen:
            seen.add(key)
            all_exams_list.append({
                "id": r.id,
                "exam_name": r.exam_name,
                "department": r.department_name,
                "programme": r.programme or f"B.Tech {r.department_name}",
                "academic_year": r.academic_year,
                "semester": r.semester,
                "subject_name": r.subject_name,
                "subject_code": r.subject_code,
                "start_time": r.start_time,
                "end_time": r.end_time,
                "time": t_range,
                "time_range": t_range,
                "shift": r_shift,
                "shift_name": r_shift,
                "duration": r.duration or "3 Hours",
                "source": "Timetable Record"
            })

    # If no timetable records, query ExaminationDates
    if not all_exams_list:
        for ed in ex_dates:
            exam_obj = ed.examination
            for s in ed.shifts:
                s_shift = "Morning Shift" if "morning" in s.shift_name.lower() else "Evening Shift"
                t_range = f"{s.start_time or '10:30 AM'} - {s.end_time or '01:30 PM'}"
                timings_by_shift[s_shift].add(t_range)
                all_exams_list.append({
                    "id": s.id,
                    "exam_name": exam_obj.name,
                    "department": "Engineering All Departments",
                    "programme": f"B.Tech ({exam_obj.exam_level})",
                    "academic_year": exam_obj.exam_level or "SE",
                    "semester": exam_obj.semester or "Semester IV",
                    "subject_name": f"{exam_obj.name} - {s.shift_name}",
                    "subject_code": f"EXAM-{exam_obj.id}",
                    "start_time": s.start_time or "10:30 AM",
                    "end_time": s.end_time or "01:30 PM",
                    "time": t_range,
                    "time_range": t_range,
                    "shift": s_shift,
                    "shift_name": s_shift,
                    "duration": "3 Hours",
                    "source": "Scheduled Session"
                })

    # Chronologically sort timings in each shift (start time, then end time)
    def parse_time_key(t_val: str):
        try:
            parts = t_val.split("-")
            s_clean = re.sub(r"\s+", " ", parts[0].strip().upper())
            e_clean = re.sub(r"\s+", " ", parts[1].strip().upper()) if len(parts) > 1 else s_clean
            t1 = datetime.strptime(s_clean, "%I:%M %p")
            t2 = datetime.strptime(e_clean, "%I:%M %p")
            return (t1, t2)
        except Exception:
            return (datetime.min, datetime.min)

    sorted_timings_by_shift = {
        s: sorted(list(t_set), key=parse_time_key)
        for s, t_set in timings_by_shift.items()
    }

    # Filter by shift if requested
    filtered_exams = all_exams_list
    if shift_name:
        filtered_exams = [e for e in filtered_exams if e.get("shift_name") == shift_name]
    if timing_str:
        filtered_exams = [e for e in filtered_exams if e.get("time_range") == timing_str or e.get("time") == timing_str]

    # Active shifts for this date
    shifts = []
    for ed in ex_dates:
        for s in ed.shifts:
            shifts.append({
                "shift_id": s.id,
                "shift_name": s.shift_name,
                "time": f"{s.start_time} - {s.end_time}",
                "block_count": s.block_count,
                "status": s.status
            })

    is_verified = len(all_exams_list) > 0
    detected_years = sorted(list(set(e.get("academic_year") for e in all_exams_list if e.get("academic_year"))))
    
    # Active shifts list that actually have exams
    available_shift_names = [s for s, t_list in sorted_timings_by_shift.items() if len(t_list) > 0]
    if not available_shift_names:
        available_shift_names = ["Morning Shift", "Evening Shift"]

    suggested_shift = available_shift_names[0] if available_shift_names else "Morning Shift"

    return {
        "date": str(t_date),
        "is_verified_in_pdf": is_verified,
        "verification_message": (
            f"Verified in Timetable PDF ({len(all_exams_list)} course{'s' if len(all_exams_list)>1 else ''} running on this date)"
            if is_verified else "Notice: Date not found in the uploaded timetable PDF."
        ),
        "total_examinations": len(all_exams_list),
        "detected_years": detected_years,
        "suggested_shift": suggested_shift,
        "available_shift_names": available_shift_names,
        "timings_by_shift": sorted_timings_by_shift,
        "examinations": filtered_exams,
        "all_examinations": all_exams_list,
        "available_shifts": shifts
    }

@router.get("/timings")
def get_timings(
    date_str: str = Query(..., alias="date"),
    shift_name: Optional[str] = Query(None, alias="shift"),
    db: Session = Depends(get_db)
):
    """
    Returns dynamically extracted examination timings for the selected date and shift.
    Chronologically sorted with duplicate options eliminated.
    """
    try:
        t_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

    query = db.query(TimetableRecord).filter(TimetableRecord.exam_date == t_date)
    if shift_name:
        query = query.filter(TimetableRecord.shift_name == shift_name)

    records = query.all()
    timing_map: Dict[str, List[Dict[str, Any]]] = {}

    for r in records:
        t_range = f"{r.start_time} - {r.end_time}"
        timing_map.setdefault(t_range, []).append({
            "id": r.id,
            "department": r.department_name,
            "programme": r.programme,
            "academic_year": r.academic_year,
            "semester": r.semester,
            "subject_name": r.subject_name,
            "subject_code": r.subject_code,
            "start_time": r.start_time,
            "end_time": r.end_time,
            "duration": r.duration or "3 Hours",
            "shift_name": r.shift_name
        })

    def parse_time(t: str):
        try:
            parts = t.split("-")
            s_clean = re.sub(r"\s+", " ", parts[0].strip().upper())
            e_clean = re.sub(r"\s+", " ", parts[1].strip().upper()) if len(parts) > 1 else s_clean
            t1 = datetime.strptime(s_clean, "%I:%M %p")
            t2 = datetime.strptime(e_clean, "%I:%M %p")
            return (t1, t2)
        except Exception:
            return (datetime.min, datetime.min)

    sorted_timings = sorted(list(timing_map.keys()), key=parse_time)

    return {
        "date": str(t_date),
        "shift": shift_name,
        "timings": sorted_timings,
        "examinations_by_timing": timing_map
    }

# ----------------- Requirement Calculation & Strict Batch Scoping -----------------

@router.post("/calculate-requirements")
def calculate_staffing_requirements(
    req: RequirementCalculationRequest,
    db: Session = Depends(get_db)
):
    """
    Calculates required Junior Supervisors, Relievers, and Standby personnel.
    CRITICAL RULE: Restricts available faculty strictly to the latest verified
    Faculty Upload Batch. Never falls back to the full faculty master.
    """
    num_blocks = req.num_classrooms
    if num_blocks <= 0:
        raise HTTPException(status_code=422, detail="Number of examination blocks must be greater than zero.")

    js_per_room = req.js_per_classroom or 1
    rel_ratio = req.reliever_ratio or 4

    required_js = num_blocks * js_per_room
    required_rel = max(1, math.ceil(num_blocks / rel_ratio))
    required_stb = req.standby_count if req.standby_count is not None else 6

    total_required = required_js + required_rel + required_stb

    # Locate the active or requested faculty upload batch
    target_batch = None
    if req.batch_id:
        target_batch = db.query(FacultyUploadBatch).filter(FacultyUploadBatch.id == req.batch_id).first()
    if not target_batch:
        target_batch = db.query(FacultyUploadBatch).filter(FacultyUploadBatch.is_active == True).order_by(FacultyUploadBatch.id.desc()).first()

    if not target_batch:
        return {
            "num_classrooms": num_blocks,
            "js_per_classroom": js_per_room,
            "required_js": required_js,
            "required_relievers": required_rel,
            "required_standby": required_stb,
            "total_required": total_required,
            "eligible_faculty_available": 0,
            "shortage": total_required,
            "can_allocate": False,
            "batch_id": None,
            "batch_name": None,
            "shortage_message": "No faculty list uploaded for current allocation. Please upload the verified faculty list PDF first."
        }

    # Query strictly the eligible members of this verified batch
    batch_faculty_ids = [
        bm.faculty_id for bm in db.query(FacultyUploadBatchMember).filter(
            FacultyUploadBatchMember.batch_id == target_batch.id,
            FacultyUploadBatchMember.is_eligible == True
        ).all()
    ]

    eligible_count = db.query(Faculty).filter(
        Faculty.id.in_(batch_faculty_ids),
        Faculty.eligibility == True,
        Faculty.role_category == "Faculty"
    ).count()

    shortage = max(0, total_required - eligible_count)

    return {
        "num_classrooms": num_blocks,
        "js_per_classroom": js_per_room,
        "required_js": required_js,
        "required_relievers": required_rel,
        "required_standby": required_stb,
        "total_required": total_required,
        "eligible_faculty_available": eligible_count,
        "shortage": shortage,
        "can_allocate": (shortage == 0),
        "batch_id": target_batch.id,
        "batch_name": target_batch.batch_name,
        "batch_filename": target_batch.filename,
        "shortage_message": (
            f"Shortage detected: Required {total_required} faculty members, but the verified faculty list contains only {eligible_count} eligible faculty (Shortage: {shortage})."
            if shortage > 0 else f"Staffing requirements satisfied ({total_required} required from {eligible_count} verified faculty in current list)."
        )
    }

# ----------------- Run Allocation Engine (Google OR-Tools CP-SAT) -----------------

@router.post("/run", response_model=AllocationSummary)
def run_allocation(req: AllocationRunRequest, db: Session = Depends(get_db)):
    shift = db.query(ExaminationShift).filter(ExaminationShift.id == req.shift_id).first()
    if not shift:
        raise HTTPException(status_code=404, detail="Examination shift not found")

    num_blocks = req.block_count if req.block_count is not None and req.block_count > 0 else shift.block_count
    if not num_blocks or num_blocks <= 0:
        raise HTTPException(
            status_code=422,
            detail="Classroom block count is missing. Please enter the number of examination classrooms being used."
        )

    if req.block_count and req.block_count != shift.block_count:
        shift.block_count = req.block_count
        db.flush()

    config = db.query(AllocationConfiguration).filter(AllocationConfiguration.is_active == True).first()
    reliever_ratio = req.reliever_ratio or (config.reliever_ratio if config else 4)
    js_per_classroom = req.js_per_classroom or (config.js_per_classroom if config else 1)
    disallow_same_dept = req.disallow_same_department_js if req.disallow_same_department_js is not None else (config.disallow_same_department_js if config else False)

    # Fetch room list
    rooms = db.query(ExaminationRoom).filter(ExaminationRoom.shift_id == shift.id).order_by(ExaminationRoom.block_number).all()
    rooms_list = [r.block_label or f"Classroom {r.room_number}" for r in rooms]
    if len(rooms_list) < num_blocks:
        for b in range(len(rooms_list) + 1, num_blocks + 1):
            rooms_list.append(f"Classroom {100 + b}")

    # CRITICAL RULE: Restrict strictly to the verified faculty list batch
    target_batch = None
    if req.batch_id:
        target_batch = db.query(FacultyUploadBatch).filter(FacultyUploadBatch.id == req.batch_id).first()
    if not target_batch:
        target_batch = db.query(FacultyUploadBatch).filter(FacultyUploadBatch.is_active == True).order_by(FacultyUploadBatch.id.desc()).first()

    if not target_batch:
        raise HTTPException(
            status_code=400,
            detail="No verified faculty upload list found. Please upload the faculty list PDF first."
        )

    batch_member_faculty_ids = [
        bm.faculty_id for bm in db.query(FacultyUploadBatchMember).filter(
            FacultyUploadBatchMember.batch_id == target_batch.id,
            FacultyUploadBatchMember.is_eligible == True
        ).all()
    ]

    # Query strictly from verified batch members
    fac_query = db.query(Faculty).join(Department).filter(
        Faculty.id.in_(batch_member_faculty_ids),
        Faculty.eligibility == True
    )
    if config and config.exclude_ss_from_fairness:
        fac_query = fac_query.filter(Faculty.role_category == "Faculty")

    if req.department_filter:
        fac_query = fac_query.filter(Faculty.department_id.in_(req.department_filter))

    if req.faculty_ids:
        fac_query = fac_query.filter(Faculty.id.in_(req.faculty_ids))

    candidate_faculty = fac_query.all()
    
    # Check date exclusions / unavailability
    exam_date = shift.exam_date_rel.exam_date if shift.exam_date_rel else date.today()
    unavail_records = db.query(FacultyAvailability.faculty_id).filter(
        FacultyAvailability.date == exam_date,
        FacultyAvailability.is_available == False
    ).all()
    unavail_ids = {u[0] for u in unavail_records}

    # Filter out unavailable faculty (Hard Constraint)
    active_faculty_pool = [f for f in candidate_faculty if f.id not in unavail_ids]

    # Detect consecutive duty
    prev_day = exam_date - timedelta(days=1)
    consecutive_histories = db.query(FacultyDutyHistory.faculty_id).filter(
        FacultyDutyHistory.exam_date == prev_day
    ).all()
    consecutive_ids = {h[0] for h in consecutive_histories}

    # Detect exam department IDs on this date (for same-department conflict checking)
    tt_depts = db.query(TimetableRecord.department_name).filter(TimetableRecord.exam_date == exam_date).all()
    tt_dept_names = {t[0].lower() for t in tt_depts}
    exam_dept_ids = [d.id for d in db.query(Department).all() if d.name.lower() in tt_dept_names or d.code.lower() in tt_dept_names]

    # Prepare faculty data for optimizer
    faculty_input = [
        {
            "id": f.id,
            "faculty_id": f.faculty_id,
            "name": f.name,
            "department_id": f.department_id,
            "department_name": f.department.name if f.department else "Unknown",
            "designation": f.designation,
            "previous_js_count": f.previous_js_count,
            "previous_reliever_count": f.previous_reliever_count,
            "previous_standby_count": f.previous_standby_count,
            "total_previous_duties": f.total_previous_duties,
            "last_assigned_role": f.last_assigned_role,
            "last_assigned_date": str(f.last_assigned_date) if f.last_assigned_date else None,
            "current_cycle_duties": f.current_cycle_duties or 0
        }
        for f in active_faculty_pool
    ]

    optimizer = FairnessOptimizer(
        weight_prev_js=config.weight_prev_js if config else 2.5,
        weight_prev_reliever=config.weight_prev_reliever if config else 2.0,
        weight_prev_standby=config.weight_prev_standby if config else 1.5,
        weight_consecutive=config.weight_consecutive if config else 2.0,
        weight_dept_equity=config.weight_dept_equity if config else 1.5,
        reliever_ratio=reliever_ratio,
        js_per_classroom=js_per_classroom,
        disallow_same_department_js=disallow_same_dept
    )

    try:
        opt_result = optimizer.solve(
            eligible_faculty=faculty_input,
            num_blocks=num_blocks,
            requested_reliever_count=req.reliever_count,
            requested_standby_count=req.standby_count,
            consecutive_faculty_ids=consecutive_ids,
            rooms_list=rooms_list,
            exam_department_ids=exam_dept_ids
        )
    except ShortageError as se:
        raise HTTPException(
            status_code=422,
            detail={
                "status": "SHORTAGE",
                "required": se.required,
                "available": se.available,
                "shortage": se.shortage,
                "message": f"Allocation cannot be completed. Required: {se.required}, Available: {se.available}, Shortage: {se.shortage}"
            }
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))

    # Clean old proposed allocations for this shift
    db.query(DutyAllocation).filter(DutyAllocation.shift_id == shift.id).delete()
    db.flush()

    saved_allocations = []
    for a in opt_result["allocations"]:
        allocation = DutyAllocation(
            shift_id=shift.id,
            faculty_id=a["faculty_id"],
            assigned_role=a["assigned_role"],
            assigned_block=a["assigned_block"],
            status="Proposed",
            fairness_score=a["fairness_score"],
            prev_js_snapshot=a["prev_js_snapshot"],
            prev_reliever_snapshot=a["prev_reliever_snapshot"],
            prev_standby_snapshot=a["prev_standby_snapshot"],
            prev_total_snapshot=a["prev_total_snapshot"],
            explainability_reason=a["explainability_reason"],
            is_manual_override=False
        )
        db.add(allocation)
        db.flush()
        
        saved_allocations.append(DutyAllocationOut(
            id=allocation.id,
            shift_id=shift.id,
            faculty_id=a["faculty_id"],
            faculty_name=a["faculty_name"],
            department_name=a["department_name"],
            designation=a.get("designation", "Assistant Professor"),
            assigned_role=a["assigned_role"],
            assigned_block=a["assigned_block"],
            status="Proposed",
            fairness_score=a["fairness_score"],
            prev_js_snapshot=a["prev_js_snapshot"],
            prev_reliever_snapshot=a["prev_reliever_snapshot"],
            prev_standby_snapshot=a["prev_standby_snapshot"],
            prev_total_snapshot=a["prev_total_snapshot"],
            previous_role=a.get("previous_role", "JS"),
            explainability_reason=a["explainability_reason"],
            is_manual_override=False
        ))

    shift.status = "Allocated"
    db.commit()

    exam_rel = shift.exam_date_rel.examination if shift.exam_date_rel else None

    return AllocationSummary(
        shift_id=shift.id,
        exam_name=exam_rel.name if exam_rel else "Engineering Examination",
        exam_date=str(exam_date),
        shift_name=shift.shift_name,
        total_eligible_faculty=opt_result["total_eligible_faculty"],
        required_js=opt_result["required_js"],
        required_relievers=opt_result["required_relievers"],
        required_standby=opt_result["required_standby"],
        required_ss=0,
        overall_fairness_score=opt_result.get("overall_fairness_score", 95.0),
        shortage=0,
        allocations=saved_allocations,
        solver_status=opt_result["solver_status"],
        execution_time_seconds=opt_result["execution_time_seconds"],
        fairness_variance_score=opt_result["fairness_variance_score"]
    )

# ----------------- Shift Allocation Retrieval -----------------

@router.get("/shift/{shift_id}", response_model=AllocationSummary)
def get_shift_allocations(shift_id: int, db: Session = Depends(get_db)):
    shift = db.query(ExaminationShift).filter(ExaminationShift.id == shift_id).first()
    if not shift:
        raise HTTPException(status_code=404, detail="Examination shift not found")

    allocations = db.query(DutyAllocation).filter(DutyAllocation.shift_id == shift_id).all()
    exam_date = shift.exam_date_rel.exam_date if shift.exam_date_rel else date.today()
    exam_rel = shift.exam_date_rel.examination if shift.exam_date_rel else None

    out_list = []
    js_c = sum(1 for a in allocations if a.assigned_role == "JS")
    rel_c = sum(1 for a in allocations if a.assigned_role == "Reliever")
    stb_c = sum(1 for a in allocations if a.assigned_role == "Standby")

    for a in allocations:
        out_list.append(DutyAllocationOut(
            id=a.id,
            shift_id=a.shift_id,
            faculty_id=a.faculty_id,
            faculty_name=a.faculty.name if a.faculty else "Unknown",
            department_name=a.faculty.department.name if (a.faculty and a.faculty.department) else "Unknown",
            designation=a.faculty.designation if a.faculty else "Assistant Professor",
            assigned_role=a.assigned_role,
            assigned_block=a.assigned_block,
            status=a.status,
            fairness_score=a.fairness_score,
            prev_js_snapshot=a.prev_js_snapshot,
            prev_reliever_snapshot=a.prev_reliever_snapshot,
            prev_standby_snapshot=a.prev_standby_snapshot,
            prev_total_snapshot=a.prev_total_snapshot,
            previous_role="Reliever" if a.prev_reliever_snapshot > a.prev_js_snapshot else "JS",
            explainability_reason=a.explainability_reason,
            is_manual_override=a.is_manual_override,
            original_role=a.original_role,
            override_reason=a.override_reason,
            override_by_user=a.override_by_user
        ))

    return AllocationSummary(
        shift_id=shift.id,
        exam_name=exam_rel.name if exam_rel else "Engineering Examination",
        exam_date=str(exam_date),
        shift_name=shift.shift_name,
        total_eligible_faculty=len(out_list),
        required_js=js_c,
        required_relievers=rel_c,
        required_standby=stb_c,
        required_ss=0,
        overall_fairness_score=94.5,
        shortage=0,
        allocations=out_list,
        solver_status="Saved Allocation",
        execution_time_seconds=0.0,
        fairness_variance_score=0.0
    )

# ----------------- Manual Override with Impact Evaluation -----------------

@router.post("/override/impact-check")
def check_override_impact(req: ImpactCheckRequest, db: Session = Depends(get_db)):
    """
    Evaluates replacement impact before committing, giving warning such as:
    'Warning: This replacement increases Faculty B's JS assignments to 5 while current average is 2.7.'
    """
    return evaluate_override_impact(
        db=db,
        shift_id=req.shift_id,
        original_faculty_id=req.original_faculty_id,
        replacement_faculty_id=req.replacement_faculty_id,
        new_role=req.new_role
    )

@router.post("/override/replace")
def replace_faculty_override(req: ReplaceFacultyRequest, db: Session = Depends(get_db)):
    """
    Substitutes an assigned faculty member with an authorized replacement faculty.
    Evaluates impact warning and permanently records in the audit trail.
    """
    allocation = db.query(DutyAllocation).filter(DutyAllocation.id == req.allocation_id).first()
    if not allocation:
        raise HTTPException(status_code=404, detail="Allocation record not found")

    orig_fac_id = allocation.faculty_id
    orig_fac = allocation.faculty
    repl_fac = db.query(Faculty).filter(Faculty.id == req.replacement_faculty_id).first()
    if not repl_fac:
        raise HTTPException(status_code=404, detail="Replacement faculty not found")

    new_role = req.new_role or allocation.assigned_role

    # Run impact evaluation
    eval_res = evaluate_override_impact(
        db=db,
        shift_id=allocation.shift_id,
        original_faculty_id=orig_fac_id,
        replacement_faculty_id=req.replacement_faculty_id,
        new_role=new_role
    )

    # Apply override
    old_role = allocation.assigned_role
    allocation.original_role = f"{orig_fac.name} ({old_role})"
    allocation.faculty_id = repl_fac.id
    allocation.assigned_role = new_role
    allocation.is_manual_override = True
    allocation.override_reason = req.override_reason
    allocation.override_by_user = req.performed_by or "Controller of Examination"
    allocation.prev_js_snapshot = repl_fac.previous_js_count
    allocation.prev_reliever_snapshot = repl_fac.previous_reliever_count
    allocation.prev_standby_snapshot = repl_fac.previous_standby_count
    allocation.prev_total_snapshot = repl_fac.total_previous_duties
    allocation.explainability_reason = f"Manual override: Replaced {orig_fac.name} with {repl_fac.name} ({new_role}). Reason: {req.override_reason}"

    # Record in ManualOverrideRecord
    override_rec = ManualOverrideRecord(
        shift_id=allocation.shift_id,
        original_faculty_id=orig_fac_id,
        replacement_faculty_id=repl_fac.id,
        original_role=old_role,
        new_role=new_role,
        override_reason=req.override_reason,
        impact_warning=eval_res["impact_message"],
        performed_by=req.performed_by or "Controller of Examination"
    )
    db.add(override_rec)

    # Record in AllocationAuditLog
    audit = AllocationAuditLog(
        action="MANUAL_FACULTY_REPLACEMENT",
        entity_type="DutyAllocation",
        entity_id=allocation.id,
        faculty_name=f"{orig_fac.name} -> {repl_fac.name}",
        performed_by=req.performed_by or "Controller of Examination",
        user_role="Controller of Examination",
        details=f"Manual replacement: {orig_fac.name} replaced by {repl_fac.name} as {new_role}. Reason: {req.override_reason}. Warning: {eval_res['impact_message']}"
    )
    db.add(audit)
    db.commit()

    return {
        "status": "success",
        "message": f"Successfully substituted {orig_fac.name} with {repl_fac.name}.",
        "has_warning": eval_res["has_warning"],
        "warning_text": eval_res["impact_message"]
    }

# ----------------- Approve & Finalize Allocation -----------------

@router.post("/shift/{shift_id}/approve")
def approve_allocation(shift_id: int, db: Session = Depends(get_db)):
    shift = db.query(ExaminationShift).filter(ExaminationShift.id == shift_id).first()
    if not shift:
        raise HTTPException(status_code=404, detail="Shift not found")

    allocations = db.query(DutyAllocation).filter(DutyAllocation.shift_id == shift_id).all()
    if not allocations:
        raise HTTPException(status_code=400, detail="No duty allocations exist to approve")

    exam_date = shift.exam_date_rel.exam_date if shift.exam_date_rel else date.today()
    exam_rel = shift.exam_date_rel.examination if shift.exam_date_rel else None

    for a in allocations:
        a.status = "Published"
        fac = a.faculty
        if fac:
            hist = FacultyDutyHistory(
                faculty_id=fac.id,
                exam_name=exam_rel.name if exam_rel else "Official Examination",
                academic_year=exam_rel.academic_year if exam_rel else "2026-2027",
                semester=exam_rel.semester if exam_rel else "Semester IV",
                exam_date=exam_date,
                shift_name=shift.shift_name,
                exam_timing=f"{shift.start_time or '10:30 AM'} - {shift.end_time or '01:30 PM'}",
                role_served=a.assigned_role,
                block_or_room=a.assigned_block,
                is_manual_override=a.is_manual_override,
                status="Approved"
            )
            db.add(hist)

            if a.assigned_role == "JS":
                fac.previous_js_count += 1
            elif a.assigned_role == "Reliever":
                fac.previous_reliever_count += 1
            elif a.assigned_role == "Standby":
                fac.previous_standby_count += 1
            elif a.assigned_role == "SS":
                fac.previous_ss_count += 1
            fac.total_previous_duties = fac.previous_js_count + fac.previous_reliever_count + fac.previous_standby_count + fac.previous_ss_count
            fac.last_assigned_role = a.assigned_role
            fac.last_assigned_date = exam_date
            fac.current_cycle_duties = (fac.current_cycle_duties or 0) + 1

    shift.status = "Published"
    
    audit = AllocationAuditLog(
        action="ALLOCATION_APPROVED_PUBLISHED",
        entity_type="ExaminationShift",
        entity_id=shift.id,
        performed_by="Controller of Examination",
        user_role="Controller of Examination",
        details=f"Approved and published duty chart for shift {shift.id} ({len(allocations)} faculty members)."
    )
    db.add(audit)
    db.commit()

    return {"status": "success", "message": f"Successfully approved and published {len(allocations)} duty assignments."}

# ----------------- Final Export System (Excel, PDF, CSV) -----------------

@router.get("/export/{shift_id}/excel")
def export_allocation_excel(shift_id: int, db: Session = Depends(get_db)):
    shift = db.query(ExaminationShift).filter(ExaminationShift.id == shift_id).first()
    if not shift:
        raise HTTPException(status_code=404, detail="Shift not found")

    allocations = db.query(DutyAllocation).filter(DutyAllocation.shift_id == shift_id).all()
    headers = [
        "Faculty Name", "Department", "Designation", "Assigned Duty Role",
        "Assigned Classroom / Block", "Previous Duties", "Fairness Rationale"
    ]
    rows = []
    for a in allocations:
        rows.append([
            a.faculty.name if a.faculty else "",
            a.faculty.department.name if (a.faculty and a.faculty.department) else "",
            a.faculty.designation if a.faculty else "Assistant Professor",
            a.assigned_role,
            a.assigned_block or "-",
            f"JS: {a.prev_js_snapshot}, Rel: {a.prev_reliever_snapshot}, Stb: {a.prev_standby_snapshot}",
            a.explainability_reason
        ])
    excel_stream = ReportGenerator.generate_excel("Duty_Allocation_Chart", f"Official Duty Chart - Shift {shift.shift_name}", headers, rows)
    return Response(
        content=excel_stream.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=Duty_Allocation_Shift_{shift_id}.xlsx"}
    )

@router.get("/export/{shift_id}/csv")
def export_allocation_csv(shift_id: int, db: Session = Depends(get_db)):
    shift = db.query(ExaminationShift).filter(ExaminationShift.id == shift_id).first()
    if not shift:
        raise HTTPException(status_code=404, detail="Shift not found")

    allocations = db.query(DutyAllocation).filter(DutyAllocation.shift_id == shift_id).all()
    lines = ["Faculty Name,Department,Designation,Assigned Role,Assigned Block,Explainability Reason\n"]
    for a in allocations:
        f_name = f'"{a.faculty.name}"' if a.faculty else '""'
        d_name = f'"{a.faculty.department.name}"' if (a.faculty and a.faculty.department) else '""'
        desig = f'"{a.faculty.designation}"' if a.faculty else '"Assistant Professor"'
        block = f'"{a.assigned_block or "-"}"'
        reason = f'"{a.explainability_reason.replace(chr(34), chr(39))}"'
        lines.append(f"{f_name},{d_name},{desig},{a.assigned_role},{block},{reason}\n")

    return Response(
        content="".join(lines),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=Duty_Allocation_Shift_{shift_id}.csv"}
    )
