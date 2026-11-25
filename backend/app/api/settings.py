from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.allocation import AllocationConfiguration, AllocationAuditLog
from app.schemas.all_schemas import ConfigurationUpdate

router = APIRouter()

@router.get("/fairness-config")
def get_fairness_config(db: Session = Depends(get_db)):
    config = db.query(AllocationConfiguration).filter(AllocationConfiguration.is_active == True).first()
    if not config:
        config = AllocationConfiguration(
            name="Standard Fairness Configuration",
            reliever_ratio=4,
            weight_prev_js=2.5,
            weight_prev_reliever=2.0,
            weight_prev_standby=1.5,
            weight_consecutive=2.0,
            weight_dept_equity=1.5,
            exclude_ss_from_fairness=True,
            is_active=True
        )
        db.add(config)
        db.commit()
        db.refresh(config)
    return config

@router.put("/fairness-config")
def update_fairness_config(update_in: ConfigurationUpdate, db: Session = Depends(get_db)):
    config = db.query(AllocationConfiguration).filter(AllocationConfiguration.is_active == True).first()
    if not config:
        raise HTTPException(status_code=404, detail="Active configuration not found")

    changes = []
    update_data = update_in.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        old_v = getattr(config, k)
        if old_v != v:
            changes.append(f"{k}: {old_v} -> {v}")
            setattr(config, k, v)

    if changes:
        audit = AllocationAuditLog(
            action="CONFIGURATION_UPDATED",
            entity_type="AllocationConfiguration",
            entity_id=config.id,
            performed_by="Super Admin",
            user_role="Super Admin",
            details=f"Updated fairness parameters: {'; '.join(changes)}"
        )
        db.add(audit)

    db.commit()
    db.refresh(config)
    return {"status": "success", "config": config, "changes": changes}
