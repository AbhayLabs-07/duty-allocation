from typing import Optional
from fastapi import APIRouter, Depends, Query, Response, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.faculty import Faculty
from app.models.department import Department
from app.models.allocation import DutyAllocation, AllocationAuditLog
from app.models.history import FacultyDutyHistory
from app.services.report_generator import ReportGenerator

router = APIRouter()

@router.get("/generate")
def get_report_data(
    report_type: str = Query(..., description="1 to 8 or report identifier"),
    format: str = Query("json", pattern="^(json|excel|pdf|html)$"),
    shift_id: Optional[int] = None,
    department_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    headers = []
    rows = []
    title = ""

    # 1. Daily Duty Allocation Report
    if report_type in ["1", "daily_duty", "daily"]:
        title = "Daily Duty Allocation Report"
        headers = ["Faculty Name", "Department", "Assigned Role", "Room / Block", "Fairness Reason", "Status"]
        query = db.query(DutyAllocation).join(Faculty)
        if shift_id:
            query = query.filter(DutyAllocation.shift_id == shift_id)
        allocations = query.all()
        for a in allocations:
            rows.append([
                a.faculty.name if a.faculty else "",
                a.faculty.department.name if (a.faculty and a.faculty.department) else "",
                a.assigned_role,
                a.assigned_block or "-",
                a.explainability_reason,
                a.status
            ])

    # 2. Faculty-wise Duty History
    elif report_type in ["2", "faculty_history"]:
        title = "Faculty-wise Comprehensive Duty History"
        headers = ["Faculty Name", "Department", "Examination", "Date", "Shift", "Role Served", "Block / Room"]
        query = db.query(FacultyDutyHistory).join(Faculty)
        if department_id:
            query = query.filter(Faculty.department_id == department_id)
        histories = query.order_by(FacultyDutyHistory.exam_date.desc()).all()
        for h in histories:
            rows.append([
                h.faculty.name if h.faculty else "",
                h.faculty.department.name if (h.faculty and h.faculty.department) else "",
                h.exam_name,
                str(h.exam_date),
                h.shift_name,
                h.role_served,
                h.block_or_room or "-"
            ])

    # 3. Department-wise Duty Report
    elif report_type in ["3", "department_report"]:
        title = "Department-wise Duty Allocation Equity Report"
        headers = ["Department Code", "Department Name", "Faculty Count", "Total JS", "Total Reliever", "Total Standby", "Total SS", "Total Duties", "Avg Per Faculty"]
        departments = db.query(Department).all()
        for d in departments:
            f_list = db.query(Faculty).filter(Faculty.department_id == d.id).all()
            cnt = len(f_list)
            js = sum(f.previous_js_count for f in f_list)
            rel = sum(f.previous_reliever_count for f in f_list)
            stb = sum(f.previous_standby_count for f in f_list)
            ss = sum(f.previous_ss_count for f in f_list)
            tot = sum(f.total_previous_duties for f in f_list)
            rows.append([
                d.code, d.name, cnt, js, rel, stb, ss, tot, round(tot / max(1, cnt), 2)
            ])

    # 4. JS Distribution Report
    elif report_type in ["4", "js_distribution"]:
        title = "Junior Supervisor (JS) Distribution & Burden Report"
        headers = ["Faculty ID", "Faculty Name", "Department", "Designation", "Total JS Duties", "Reliever Duties", "Total Duties"]
        faculty_list = db.query(Faculty).filter(Faculty.role_category == "Faculty").order_by(Faculty.previous_js_count.desc()).all()
        for f in faculty_list:
            rows.append([
                f.faculty_id, f.name, f.department.name if f.department else "",
                f.designation, f.previous_js_count, f.previous_reliever_count, f.total_previous_duties
            ])

    # 5. Reliever Distribution Report
    elif report_type in ["5", "reliever_distribution"]:
        title = "Reliever Opportunity Distribution Report"
        headers = ["Faculty ID", "Faculty Name", "Department", "Designation", "Reliever Duties", "JS Duties", "Total Duties"]
        faculty_list = db.query(Faculty).filter(Faculty.role_category == "Faculty").order_by(Faculty.previous_reliever_count.asc()).all()
        for f in faculty_list:
            rows.append([
                f.faculty_id, f.name, f.department.name if f.department else "",
                f.designation, f.previous_reliever_count, f.previous_js_count, f.total_previous_duties
            ])

    # 6. Standby Distribution Report
    elif report_type in ["6", "standby_distribution"]:
        title = "Standby Reserve Duty Distribution Report"
        headers = ["Faculty ID", "Faculty Name", "Department", "Designation", "Standby Duties", "JS Duties", "Total Duties"]
        faculty_list = db.query(Faculty).filter(Faculty.role_category == "Faculty").order_by(Faculty.previous_standby_count.asc()).all()
        for f in faculty_list:
            rows.append([
                f.faculty_id, f.name, f.department.name if f.department else "",
                f.designation, f.previous_standby_count, f.previous_js_count, f.total_previous_duties
            ])

    # 7. Fairness Analysis Report
    elif report_type in ["7", "fairness_analysis"]:
        title = "Algorithmic Fairness & Equity Index Analysis"
        headers = ["Faculty Name", "Department", "JS Count", "Reliever Count", "Standby Count", "Equity Balance Status"]
        all_faculty = db.query(Faculty).filter(Faculty.role_category == "Faculty").all()
        avg_js = sum(f.previous_js_count for f in all_faculty) / max(1, len(all_faculty))
        for f in all_faculty:
            status = "Equitable"
            if f.previous_js_count > avg_js + 3 and f.previous_reliever_count == 0:
                status = "Relief Candidate (High JS / No Reliever)"
            elif f.previous_js_count < avg_js - 2:
                status = "Classroom Under-Allocated"
            rows.append([
                f.name, f.department.name if f.department else "",
                f.previous_js_count, f.previous_reliever_count, f.previous_standby_count, status
            ])

    # 8. Manual Modification and Audit Report
    elif report_type in ["8", "audit_report"]:
        title = "Manual Duty Modification & Authorization Audit Trail"
        headers = ["Timestamp", "Action", "Faculty Name", "Authorized By", "Role", "Details"]
        logs = db.query(AllocationAuditLog).order_by(AllocationAuditLog.timestamp.desc()).all()
        for l in logs:
            rows.append([
                l.timestamp.strftime("%Y-%m-%d %H:%M:%S") if l.timestamp else "-",
                l.action,
                l.faculty_name or "-",
                l.performed_by,
                l.user_role,
                l.details
            ])
    else:
        raise HTTPException(status_code=400, detail="Invalid report_type. Valid values: 1 through 8.")

    # Return based on requested format
    if format == "json":
        return {
            "report_type": report_type,
            "title": title,
            "headers": headers,
            "total_rows": len(rows),
            "rows": rows
        }
    elif format == "excel":
        excel_io = ReportGenerator.generate_excel(f"Report_{report_type}", title, headers, rows)
        return Response(
            content=excel_io.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=Report_{report_type}.xlsx"}
        )
    elif format == "pdf":
        pdf_io = ReportGenerator.generate_pdf(title, headers, rows)
        return Response(
            content=pdf_io.getvalue(),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=Report_{report_type}.pdf"}
        )
    elif format == "html":
        html_str = ReportGenerator.generate_html(title, headers, rows)
        return Response(content=html_str, media_type="text/html")
