from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.models.department import Department
from app.models.faculty import Faculty
from app.schemas.all_schemas import DepartmentOut, DepartmentCreate, DepartmentUpdate

router = APIRouter()

@router.get("", response_model=List[DepartmentOut])
def list_departments(db: Session = Depends(get_db)):
    departments = db.query(Department).all()
    results = []
    for d in departments:
        count = db.query(Faculty).filter(Faculty.department_id == d.id).count()
        results.append(DepartmentOut(
            id=d.id,
            code=d.code,
            name=d.name,
            hod_name=d.hod_name,
            contact_email=d.contact_email,
            faculty_count=count
        ))
    return results

@router.get("/{department_id}", response_model=DepartmentOut)
def get_department(department_id: int, db: Session = Depends(get_db)):
    d = db.query(Department).filter(Department.id == department_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Department not found")
    count = db.query(Faculty).filter(Faculty.department_id == d.id).count()
    return DepartmentOut(
        id=d.id,
        code=d.code,
        name=d.name,
        hod_name=d.hod_name,
        contact_email=d.contact_email,
        faculty_count=count
    )

@router.post("", response_model=DepartmentOut)
def create_department(dept_in: DepartmentCreate, db: Session = Depends(get_db)):
    existing = db.query(Department).filter(
        (Department.code == dept_in.code) | (Department.name == dept_in.name)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Department with this code or name already exists")
    
    dept = Department(
        code=dept_in.code.upper(),
        name=dept_in.name,
        hod_name=dept_in.hod_name,
        contact_email=dept_in.contact_email
    )
    db.add(dept)
    db.commit()
    db.refresh(dept)
    return DepartmentOut(
        id=dept.id,
        code=dept.code,
        name=dept.name,
        hod_name=dept.hod_name,
        contact_email=dept.contact_email,
        faculty_count=0
    )

@router.put("/{department_id}", response_model=DepartmentOut)
def update_department(department_id: int, dept_in: DepartmentUpdate, db: Session = Depends(get_db)):
    dept = db.query(Department).filter(Department.id == department_id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")
    
    update_data = dept_in.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(dept, field, val)

    db.commit()
    db.refresh(dept)
    count = db.query(Faculty).filter(Faculty.department_id == dept.id).count()
    return DepartmentOut(
        id=dept.id,
        code=dept.code,
        name=dept.name,
        hod_name=dept.hod_name,
        contact_email=dept.contact_email,
        faculty_count=count
    )

@router.delete("/{department_id}")
def delete_department(department_id: int, db: Session = Depends(get_db)):
    dept = db.query(Department).filter(Department.id == department_id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")
    db.delete(dept)
    db.commit()
    return {"status": "success", "message": f"Department {dept.name} deleted"}

@router.get("/{department_id}/equity-stats")
def get_department_equity_stats(department_id: int, db: Session = Depends(get_db)):
    dept = db.query(Department).filter(Department.id == department_id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")
    
    faculty_list = db.query(Faculty).filter(Faculty.department_id == department_id).all()
    count = len(faculty_list)
    if count == 0:
        return {"department": dept.name, "faculty_count": 0, "avg_js": 0, "avg_reliever": 0, "avg_standby": 0}
    
    total_js = sum(f.previous_js_count for f in faculty_list)
    total_rel = sum(f.previous_reliever_count for f in faculty_list)
    total_stb = sum(f.previous_standby_count for f in faculty_list)

    return {
        "department": dept.name,
        "faculty_count": count,
        "total_js": total_js,
        "avg_js": round(total_js / count, 2),
        "total_reliever": total_rel,
        "avg_reliever": round(total_rel / count, 2),
        "total_standby": total_stb,
        "avg_standby": round(total_stb / count, 2)
    }
