from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.dependencies import get_current_active_user
from app.auth.models import User
from app.features.meta_campaigns import schemas, service
from app.features.meta_campaigns.scheduler_service import schedule_rule, unschedule_rule
from typing import Optional

router = APIRouter(prefix="/meta-campaigns", tags=["meta-campaigns"])


@router.get("/rules", response_model=list[schemas.Rule])
def get_rules(
    business_account_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all campaign rules, optionally filtered by business account"""
    if business_account_id:
        return service.get_rules_by_business_account(db, business_account_id)
    return service.get_all_rules(db)


@router.post("/rules", response_model=schemas.Rule)
def create_rule(
    rule_data: schemas.RuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new campaign rule"""
    rule = service.create_rule(db, rule_data)
    # Schedule the rule if it's enabled and has a schedule
    if rule.enabled and rule.schedule_cron:
        schedule_rule(rule)
    return rule


@router.get("/rules/{rule_id}", response_model=schemas.Rule)
def get_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific rule"""
    rule = service.get_rule(db, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return rule


@router.put("/rules/{rule_id}", response_model=schemas.Rule)
def update_rule(
    rule_id: int,
    rule_data: schemas.RuleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update a campaign rule"""
    # Unschedule the old rule first
    unschedule_rule(rule_id)

    rule = service.update_rule(db, rule_id, rule_data)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    # If schedule_cron is null/empty, clear next_run_at and ensure it's unscheduled
    if not rule.schedule_cron:
        rule.next_run_at = None
        db.commit()
        db.refresh(rule)
    # Reschedule the rule if it's enabled and has a schedule
    elif rule.enabled and rule.schedule_cron:
        schedule_rule(rule)

    return rule


@router.delete("/rules/{rule_id}")
def delete_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a campaign rule"""
    # Unschedule the rule first
    unschedule_rule(rule_id)

    success = service.delete_rule(db, rule_id)
    if not success:
        raise HTTPException(status_code=404, detail="Rule not found")
    return {"message": "Rule deleted successfully"}


@router.get("/rules/{rule_id}/logs", response_model=list[schemas.RuleLog])
def get_rule_logs(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get logs for a specific rule"""
    return service.get_rule_logs(db, rule_id)


@router.post("/rules/{rule_id}/test")
def test_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Manually trigger a rule check"""
    return service.test_rule(db, rule_id)


@router.delete("/rules/{rule_id}/logs/{log_id}")
def delete_rule_log(
    rule_id: int,
    log_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a specific rule log entry"""
    success = service.delete_rule_log(db, log_id)
    if not success:
        raise HTTPException(status_code=404, detail="Log entry not found")
    return {"message": "Log entry deleted successfully"}

