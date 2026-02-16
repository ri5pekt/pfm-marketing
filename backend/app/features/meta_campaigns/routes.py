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
    ad_account_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all campaign rules, optionally filtered by ad account"""
    if ad_account_id:
        return service.get_rules_by_ad_account(db, ad_account_id)
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


@router.get("/logs")
def get_all_logs(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all rule execution logs across all ad accounts (for admin monitoring)"""
    return service.get_all_logs(db, limit=limit, offset=offset)


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


# ----------------------------
# Folder endpoints
# ----------------------------
@router.get("/folders", response_model=list[schemas.Folder])
def get_folders(
    ad_account_id: int = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all folders for an ad account"""
    return service.get_folders_by_ad_account(db, ad_account_id)


@router.post("/folders", response_model=schemas.Folder)
def create_folder(
    folder_data: schemas.FolderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new folder"""
    return service.create_folder(db, folder_data)


@router.put("/folders/{folder_id}", response_model=schemas.Folder)
def update_folder(
    folder_id: int,
    folder_data: schemas.FolderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update a folder (rename or reposition)"""
    folder = service.update_folder(db, folder_id, folder_data)
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    return folder


@router.delete("/folders/{folder_id}")
def delete_folder(
    folder_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a folder (rules move to root level)"""
    success = service.delete_folder(db, folder_id)
    if not success:
        raise HTTPException(status_code=404, detail="Folder not found")
    return {"message": "Folder deleted successfully"}


@router.get("/folders/{folder_id}/export")
def export_folder(
    folder_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Export folder structure with all rules as JSON"""
    try:
        export_data = service.export_folder_to_json(db, folder_id)
        return export_data
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export folder: {str(e)}")


@router.post("/folders/import")
def import_folder(
    request: schemas.FolderImportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Import folder structure with rules from JSON"""
    try:
        result = service.import_folder_from_json(db, request.ad_account_id, request.folder_json)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to import folder: {str(e)}")


@router.post("/folders/reorder")
def reorder_folders(
    request: schemas.FolderReorderRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Batch reorder folders"""
    service.reorder_folders(db, request.ad_account_id, request.items)
    return {"message": "Folders reordered successfully"}


@router.post("/rules/reorder")
def reorder_rules(
    request: schemas.RuleReorderRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Batch reorder rules and update folder assignments"""
    service.reorder_rules(db, request.ad_account_id, request.items)
    return {"message": "Rules reordered successfully"}

