from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.core.database import get_db
from app.models.allocation import AllocationConfiguration, AllocationAuditLog

router = APIRouter()

class SystemRulesUpdate(BaseModel):
    js_per_classroom: Optional[int] = None
    reliever_ratio: Optional[int] = None
    standby_ratio_or_count: Optional[int] = None
    disallow_same_department_js: Optional[bool] = None
    disallow_same_subject_js: Optional[bool] = None
    weight_prev_js: Optional[float] = None
    weight_prev_reliever: Optional[float] = None
    weight_prev_standby: Optional[float] = None
    weight_consecutive: Optional[float] = None
    weight_dept_equity: Optional[float] = None
    exclude_ss_from_fairness: Optional[bool] = None

@router.get("")
def get_system_rules(db: Session = Depends(get_db)):
    config = db.query(AllocationConfiguration).filter(AllocationConfiguration.is_active == True).first()
    if not config:
        config = AllocationConfiguration(
            name="Institutional Rules",
            js_per_classroom=1,
            reliever_ratio=4,
            standby_ratio_or_count=2,
            disallow_same_department_js=False,
            disallow_same_subject_js=False,
            weight_prev_js=2.5,
            weight_prev_reliever=2.0,
            weight_prev_standby=1.5,
            weight_consecutive=2.0,
            weight_dept_equity=1.5,
            exclude_ss_from_fairness=True
        )
        db.add(config)
        db.commit()
        db.refresh(config)

    return {
        "id": config.id,
        "name": config.name,
        "js_per_classroom": config.js_per_classroom,
        "reliever_ratio": config.reliever_ratio,
        "standby_ratio_or_count": config.standby_ratio_or_count,
        "disallow_same_department_js": config.disallow_same_department_js,
        "disallow_same_subject_js": config.disallow_same_subject_js,
        "weight_prev_js": config.weight_prev_js,
        "weight_prev_reliever": config.weight_prev_reliever,
        "weight_prev_standby": config.weight_prev_standby,
        "weight_consecutive": config.weight_consecutive,
        "weight_dept_equity": config.weight_dept_equity,
        "exclude_ss_from_fairness": config.exclude_ss_from_fairness,
        "updated_at": config.updated_at
    }

@router.put("")
def update_system_rules(rules_in: SystemRulesUpdate, db: Session = Depends(get_db)):
    config = db.query(AllocationConfiguration).filter(AllocationConfiguration.is_active == True).first()
    if not config:
        config = AllocationConfiguration(name="Institutional Rules")
        db.add(config)

    if rules_in.js_per_classroom is not None:
        config.js_per_classroom = rules_in.js_per_classroom
    if rules_in.reliever_ratio is not None:
        config.reliever_ratio = rules_in.reliever_ratio
    if rules_in.standby_ratio_or_count is not None:
        config.standby_ratio_or_count = rules_in.standby_ratio_or_count
    if rules_in.disallow_same_department_js is not None:
        config.disallow_same_department_js = rules_in.disallow_same_department_js
    if rules_in.disallow_same_subject_js is not None:
        config.disallow_same_subject_js = rules_in.disallow_same_subject_js
    if rules_in.weight_prev_js is not None:
        config.weight_prev_js = rules_in.weight_prev_js
    if rules_in.weight_prev_reliever is not None:
        config.weight_prev_reliever = rules_in.weight_prev_reliever
    if rules_in.weight_prev_standby is not None:
        config.weight_prev_standby = rules_in.weight_prev_standby
    if rules_in.weight_consecutive is not None:
        config.weight_consecutive = rules_in.weight_consecutive
    if rules_in.weight_dept_equity is not None:
        config.weight_dept_equity = rules_in.weight_dept_equity
    if rules_in.exclude_ss_from_fairness is not None:
        config.exclude_ss_from_fairness = rules_in.exclude_ss_from_fairness

    audit = AllocationAuditLog(
        action="RULES_CONFIGURATION_UPDATED",
        entity_type="AllocationConfiguration",
        entity_id=config.id,
        performed_by="Controller of Examination",
        user_role="Controller of Examination",
        details="Updated institutional rules: classroom staffing ratios, same-department conflict policies, and solver weights."
    )
    db.add(audit)
    db.commit()

    return {"message": "Institutional system rules successfully updated and logged to audit trail."}
