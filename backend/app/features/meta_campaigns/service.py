from sqlalchemy.orm import Session
from app.features.meta_campaigns import models, schemas
from datetime import datetime
import requests
import logging
import time
import json
from typing import Dict, List, Any

# Import from refactored modules
from app.features.meta_campaigns.facebook_api_client import fetch_facebook_data, fetch_insights, fetch_daily_insights, build_time_range_string, fetch_ads_for_item
from app.features.meta_campaigns.data_filtering import apply_scope_filters
from app.features.meta_campaigns.condition_evaluator import calculate_metric_from_insights, evaluate_condition
from app.features.meta_campaigns.action_executor import execute_action, send_slack_notification
from app.features.meta_campaigns.rate_limit_tracker import check_rate_limit_headers

logger = logging.getLogger(__name__)


# ----------------------------
# Folder CRUD Operations
# ----------------------------
def get_folders_by_ad_account(db: Session, ad_account_id: int):
    """Get all folders for an ad account, ordered by position"""
    return db.query(models.RuleFolder).filter(
        models.RuleFolder.ad_account_id == ad_account_id
    ).order_by(models.RuleFolder.position).all()


def create_folder(db: Session, folder_data: schemas.FolderCreate):
    """Create a new folder with auto-assigned position"""
    # Get the max position for this ad account
    max_position = db.query(models.RuleFolder).filter(
        models.RuleFolder.ad_account_id == folder_data.ad_account_id
    ).count()

    folder_dict = folder_data.model_dump()
    folder_dict['position'] = max_position

    folder = models.RuleFolder(**folder_dict)
    db.add(folder)
    db.commit()
    db.refresh(folder)
    return folder


def update_folder(db: Session, folder_id: int, folder_data: schemas.FolderUpdate):
    """Update a folder (rename or reposition)"""
    folder = db.query(models.RuleFolder).filter(models.RuleFolder.id == folder_id).first()
    if not folder:
        return None

    update_data = folder_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(folder, field, value)

    db.commit()
    db.refresh(folder)
    return folder


def delete_folder(db: Session, folder_id: int):
    """Delete a folder and move its rules to root level"""
    folder = db.query(models.RuleFolder).filter(models.RuleFolder.id == folder_id).first()
    if not folder:
        return False

    # Move all rules in this folder to root level (folder_id = null)
    db.query(models.CampaignRule).filter(
        models.CampaignRule.folder_id == folder_id
    ).update({"folder_id": None})

    db.delete(folder)
    db.commit()
    return True


def reorder_folders(db: Session, ad_account_id: int, reorder_items: List[schemas.FolderReorderItem]):
    """Batch update folder positions"""
    for item in reorder_items:
        db.query(models.RuleFolder).filter(
            models.RuleFolder.id == item.id,
            models.RuleFolder.ad_account_id == ad_account_id
        ).update({"position": item.position})

    db.commit()
    return True


def _generate_unique_folder_name(db: Session, ad_account_id: int, base_name: str) -> str:
    """Generate a unique folder name by appending (copy) or (copy N) if needed"""
    # Get all existing folder names for this account
    existing_folders = db.query(models.RuleFolder.name).filter(
        models.RuleFolder.ad_account_id == ad_account_id
    ).all()
    existing_names = {folder.name for folder in existing_folders}
    
    # If base name doesn't exist, use it
    if base_name not in existing_names:
        return base_name
    
    # Try "name (copy)"
    copy_name = f"{base_name} (copy)"
    if copy_name not in existing_names:
        return copy_name
    
    # Try "name (copy 2)", "name (copy 3)", etc.
    counter = 2
    while True:
        numbered_name = f"{base_name} (copy {counter})"
        if numbered_name not in existing_names:
            return numbered_name
        counter += 1
        # Safety limit to prevent infinite loop
        if counter > 100:
            raise ValueError("Too many folders with similar names")


def export_folder_to_json(db: Session, folder_id: int):
    """Export folder and its rules to a portable JSON format"""
    # Get folder
    folder = db.query(models.RuleFolder).filter(models.RuleFolder.id == folder_id).first()
    if not folder:
        raise ValueError("Folder not found")
    
    # Get all rules in folder
    rules = db.query(models.CampaignRule).filter(
        models.CampaignRule.folder_id == folder_id
    ).order_by(models.CampaignRule.position).all()
    
    # Build export structure (excluding IDs and account-specific data)
    export_data = {
        "folder": {
            "name": folder.name,
        },
        "rules": [
            {
                "name": rule.name,
                "description": rule.description or "",
                "enabled": rule.enabled,
                "position": rule.position,
                "schedule_cron": rule.schedule_cron or "",
                "conditions": rule.conditions,  # JSON field
                "actions": rule.actions,  # JSON field
            }
            for rule in rules
        ],
        "export_timestamp": datetime.now().isoformat(),
        "version": "1.0",  # For future compatibility
        "rules_count": len(rules),
    }
    
    return export_data


def import_folder_from_json(db: Session, ad_account_id: int, folder_json: dict):
    """Import folder and rules from JSON"""
    # Validate version compatibility
    if folder_json.get("version") != "1.0":
        raise ValueError("Unsupported JSON version")
    
    # Validate structure
    if "folder" not in folder_json or "rules" not in folder_json:
        raise ValueError("Invalid JSON structure: missing 'folder' or 'rules'")
    
    # Get max position for new folder
    max_position = db.query(models.RuleFolder).filter(
        models.RuleFolder.ad_account_id == ad_account_id
    ).count()
    
    # Generate unique folder name
    base_name = folder_json["folder"]["name"]
    unique_name = _generate_unique_folder_name(db, ad_account_id, base_name)
    
    # Create folder
    folder = models.RuleFolder(
        ad_account_id=ad_account_id,
        name=unique_name,
        position=max_position,
    )
    db.add(folder)
    db.flush()  # Get folder.id without committing
    
    # Create rules (import as DISABLED by default for safety)
    rules_imported = 0
    for rule_data in folder_json["rules"]:
        try:
            rule = models.CampaignRule(
                ad_account_id=ad_account_id,
                folder_id=folder.id,
                name=rule_data["name"],
                description=rule_data.get("description", ""),
                enabled=False,  # Always import as disabled for safety
                position=rule_data.get("position", 0),
                schedule_cron=rule_data.get("schedule_cron") or None,
                conditions=rule_data["conditions"],
                actions=rule_data["actions"],
            )
            db.add(rule)
            rules_imported += 1
        except Exception as e:
            # Log error but continue with other rules
            print(f"Failed to import rule '{rule_data.get('name', 'unknown')}': {str(e)}")
    
    db.commit()
    db.refresh(folder)
    
    return {
        "folder_id": folder.id,
        "folder_name": folder.name,
        "rules_imported": rules_imported,
        "rules_total": len(folder_json["rules"]),
    }


def reorder_rules(db: Session, ad_account_id: int, reorder_items: List[schemas.RuleReorderItem]):
    """Batch update rule positions and folder assignments"""
    for item in reorder_items:
        db.query(models.CampaignRule).filter(
            models.CampaignRule.id == item.id,
            models.CampaignRule.ad_account_id == ad_account_id
        ).update({
            "folder_id": item.folder_id,
            "position": item.position
        })

    db.commit()
    return True


# ----------------------------
# Rule CRUD Operations
# ----------------------------
def get_all_rules(db: Session):
    return db.query(models.CampaignRule).all()


def get_rules_by_ad_account(db: Session, ad_account_id: int):
    return db.query(models.CampaignRule).filter(
        models.CampaignRule.ad_account_id == ad_account_id
    ).order_by(
        models.CampaignRule.folder_id.nullslast(),
        models.CampaignRule.position
    ).all()


def get_rule(db: Session, rule_id: int):
    return db.query(models.CampaignRule).filter(models.CampaignRule.id == rule_id).first()


def create_rule(db: Session, rule_data: schemas.RuleCreate):
    rule = models.CampaignRule(**rule_data.model_dump())
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


def update_rule(db: Session, rule_id: int, rule_data: schemas.RuleUpdate):
    rule = db.query(models.CampaignRule).filter(models.CampaignRule.id == rule_id).first()
    if not rule:
        return None

    update_data = rule_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(rule, field, value)

    db.commit()
    db.refresh(rule)
    return rule


def delete_rule(db: Session, rule_id: int):
    rule = db.query(models.CampaignRule).filter(models.CampaignRule.id == rule_id).first()
    if not rule:
        return False

    db.delete(rule)
    db.commit()
    return True


def get_all_logs(db: Session, limit: int = 100, offset: int = 0):
    """Get all rule execution logs across all ad accounts with rule and account info"""
    from sqlalchemy import desc
    
    logs = db.query(
        models.RuleLog,
        models.CampaignRule.name.label('rule_name'),
        models.CampaignRule.ad_account_id,
        models.AdAccount.name.label('ad_account_name')
    ).join(
        models.CampaignRule,
        models.RuleLog.rule_id == models.CampaignRule.id
    ).join(
        models.AdAccount,
        models.CampaignRule.ad_account_id == models.AdAccount.id
    ).order_by(
        desc(models.RuleLog.created_at)
    ).limit(limit).offset(offset).all()
    
    # Format the results
    result = []
    for log, rule_name, ad_account_id, ad_account_name in logs:
        result.append({
            "id": log.id,
            "rule_id": log.rule_id,
            "rule_name": rule_name,
            "ad_account_id": ad_account_id,
            "ad_account_name": ad_account_name,
            "status": log.status,
            "message": log.message,
            "details": log.details,
            "created_at": log.created_at
        })
    
    return result


def get_rule_logs(db: Session, rule_id: int, limit: int = 100):
    return db.query(models.RuleLog).filter(
        models.RuleLog.rule_id == rule_id
    ).order_by(models.RuleLog.created_at.desc()).limit(limit).all()


def delete_rule_log(db: Session, log_id: int):
    """Delete a rule log entry"""
    log = db.query(models.RuleLog).filter(models.RuleLog.id == log_id).first()
    if not log:
        return False

    db.delete(log)
    db.commit()
    return True


def create_rule_log(db: Session, rule_id: int, status: str, message: str, details: dict = None):
    log = models.RuleLog(
        rule_id=rule_id,
        status=status,
        message=message,
        details=details
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


# ----------------------------
# Rule Testing Orchestrator
# ----------------------------
def test_rule(db: Session, rule_id: int):
    """Test a rule by fetching data, applying filters, and evaluating conditions"""
    try:
        rule = get_rule(db, rule_id)
        if not rule:
            raise ValueError("Rule not found")

        if not rule.enabled:
            create_rule_log(db, rule_id, "skipped", "Rule is disabled", {})
            return {"message": "Rule is disabled", "rule_id": rule_id}
    except TypeError as e:
        error_msg = f"TypeError in test_rule setup: {str(e)}"
        logger.error(error_msg)
        logger.error(f"Rule ID: {rule_id}")
        create_rule_log(db, rule_id, "error", error_msg, {"error": str(e)})
        raise
    except Exception as e:
        error_msg = f"Unexpected error in test_rule: {str(e)}"
        logger.error(error_msg)
        create_rule_log(db, rule_id, "error", error_msg, {"error": str(e)})
        raise

    # Get ad account for credentials
    from app.features.meta_campaigns.models import AdAccount
    ad_account = db.query(AdAccount).filter(
        AdAccount.id == rule.ad_account_id
    ).first()

    if not ad_account:
        create_rule_log(db, rule_id, "error", "Ad account not found", {})
        raise ValueError("Ad account not found")

    account_id = rule.meta_account_id or ad_account.meta_account_id
    access_token = rule.meta_access_token or ad_account.meta_access_token
    slack_webhook_url = ad_account.slack_webhook_url

    if not account_id or not access_token:
        create_rule_log(db, rule_id, "error", "Meta account ID or access token missing", {})
        raise ValueError("Meta account ID or access token missing")

    # Parse rule conditions
    conditions = rule.conditions
    rule_level = conditions.get("rule_level", "ad")
    # Include campaign-level scope filters
    scope_filters = {k: v for k, v in conditions.items() if k in ["name_contains", "ids", "campaign_ids", "campaign_name_contains", "campaign_name_doesnt_contain"]}
    time_range = conditions.get("time_range", {})
    
    # Extract flat list of conditions from groups (backward compatible with old format)
    if "condition_groups" in conditions:
        # New format: flatten all conditions from all groups
        rule_conditions = []
        for group in conditions.get("condition_groups", []):
            rule_conditions.extend(group.get("conditions", []))
    else:
        # Old format: flat conditions array
        rule_conditions = conditions.get("conditions", [])

    # API call counter to track performance
    api_call_counter = {
        "total": 0,
        "fetch_items": 0,
        "fetch_insights": 0,
        "actions": 0
    }

    log_details = {
        "timestamp": datetime.now().isoformat(),
        "rule_level": rule_level,
        "scope_filters": scope_filters,
        "time_range": time_range,
        "conditions": rule_conditions,
        # Also include individual scope filter keys for easier access
        "name_contains": conditions.get("name_contains"),
        "ids": conditions.get("ids"),
        "campaign_ids": conditions.get("campaign_ids"),
        "data_fetch": {},
        "filtered_data": [],
        "evaluations": [],
        "api_calls": api_call_counter
    }

    total_start_time = time.time()
    logger.info(f"[TIMING] === Starting rule execution: rule_id={rule_id} (rule: {rule.name}) ===")

    # Helper function to create a hashable key from time range dict
    def time_range_key(tr):
        """Create a hashable key from time range dict"""
        if not tr:
            return None
        
        # Get values and ensure they're hashable (not lists)
        unit = tr.get("unit")
        amount = tr.get("amount")
        exclude_today = tr.get("exclude_today", True)
        
        # Convert lists to tuples or take first element (defensive programming)
        if isinstance(unit, list):
            unit = unit[0] if unit else None
        if isinstance(amount, list):
            amount = amount[0] if amount else None
        if isinstance(exclude_today, list):
            exclude_today = exclude_today[0] if exclude_today else True
            
        return (unit, amount, exclude_today)

    try:
        # Step 0.5: Pre-resolve campaign name filters (contains/doesn't contain) to campaign_ids for API-level filtering
        # This dramatically reduces API calls by filtering at the source
        has_campaign_name_contains = "campaign_name_contains" in scope_filters and scope_filters["campaign_name_contains"]
        has_campaign_name_doesnt_contain = "campaign_name_doesnt_contain" in scope_filters and scope_filters["campaign_name_doesnt_contain"]
        
        if (has_campaign_name_contains or has_campaign_name_doesnt_contain) and rule_level in ["ad", "ad_set"]:
            step_start_time = time.time()
            logger.info(f"[TIMING] Step 0.5 - Pre-resolving campaign name filters for API optimization")
            try:
                # Fetch campaigns matching name pattern
                base_url = "https://graph.facebook.com/v21.0"
                account_id_formatted = f"act_{account_id}" if not account_id.startswith("act_") else account_id
                
                # Build filtering for existing campaign_ids if present
                campaign_filtering = None
                if "campaign_ids" in scope_filters and scope_filters["campaign_ids"]:
                    existing_campaign_ids = scope_filters["campaign_ids"]
                    if isinstance(existing_campaign_ids, str):
                        existing_campaign_ids = [id_val.strip() for id_val in existing_campaign_ids.replace("\n", ",").split(",") if id_val.strip()]
                    if isinstance(existing_campaign_ids, list) and existing_campaign_ids:
                        campaign_filtering = json.dumps([{
                            "field": "id",
                            "operator": "IN",
                            "value": existing_campaign_ids
                        }])
                        logger.info(f"Pre-filtering campaigns by existing campaign_ids: {len(existing_campaign_ids)} campaigns")
                
                all_campaigns = []
                url = f"{base_url}/{account_id_formatted}/campaigns"
                params = {
                    "fields": "id,name",
                    "limit": 2000,
                    "access_token": access_token
                }
                if campaign_filtering:
                    from urllib.parse import quote
                    params["filtering"] = quote(campaign_filtering)
                
                while True:
                    response = requests.get(url, params=params, timeout=30)
                    response.raise_for_status()
                    data = response.json()
                    all_campaigns.extend(data.get("data", []))
                    
                    next_url = data.get("paging", {}).get("next")
                    if not next_url:
                        break
                    url = next_url
                    params = {}  # next_url already has all params
                    time.sleep(0.3)
                
                # Start with all campaigns
                matching_campaign_ids = [str(campaign.get("id")) for campaign in all_campaigns]
                
                # Apply positive filter (contains)
                if has_campaign_name_contains:
                    keywords_contains = scope_filters["campaign_name_contains"]
                    if isinstance(keywords_contains, list) and keywords_contains:
                        matching_campaign_ids = [
                            str(campaign.get("id"))
                            for campaign in all_campaigns
                            if any(keyword.lower() in campaign.get("name", "").lower() for keyword in keywords_contains)
                        ]
                        logger.info(f"After campaign_name_contains: {len(matching_campaign_ids)} campaigns match (keywords: {keywords_contains})")
                
                # Apply negative filter (doesn't contain)
                if has_campaign_name_doesnt_contain:
                    keywords_doesnt_contain = scope_filters["campaign_name_doesnt_contain"]
                    if isinstance(keywords_doesnt_contain, list) and keywords_doesnt_contain:
                        # Filter OUT campaigns that contain any of these keywords
                        matching_campaign_ids = [
                            cid for cid in matching_campaign_ids
                            if not any(
                                keyword.lower() in next(
                                    (c.get("name", "") for c in all_campaigns if str(c.get("id")) == cid),
                                    ""
                                ).lower()
                                for keyword in keywords_doesnt_contain
                            )
                        ]
                        logger.info(f"After campaign_name_doesnt_contain: {len(matching_campaign_ids)} campaigns remain (excluded keywords: {keywords_doesnt_contain})")
                
                step_elapsed = time.time() - step_start_time
                logger.info(f"[TIMING] Step 0.5 completed in {step_elapsed:.2f} seconds - Resolved to {len(matching_campaign_ids)} campaigns (from {len(all_campaigns)} total)")
                
                if matching_campaign_ids:
                    # Add resolved campaign IDs to scope_filters for API-level filtering
                    scope_filters["campaign_ids"] = matching_campaign_ids
                    logger.info(f"[OPTIMIZATION] Campaign name filters resolved to campaign_ids - will fetch only from {len(matching_campaign_ids)} campaigns")
                    # Remove campaign_name filters to avoid re-processing
                    if "campaign_name_contains" in scope_filters:
                        del scope_filters["campaign_name_contains"]
                    if "campaign_name_doesnt_contain" in scope_filters:
                        del scope_filters["campaign_name_doesnt_contain"]
                else:
                    # No campaigns match, so result will be empty
                    logger.info(f"[OPTIMIZATION] No campaigns match name filters - skipping data fetch")
                    log_details["data_fetch"] = {"total_items": 0, "items": []}
                    log_details["filtered_data"] = []
                    log_details["evaluations"] = []
                    log_details["decision"] = "skip"
                    log_details["items_meeting_conditions_count"] = 0
                    create_rule_log(db, rule_id, "skipped", "No campaigns match name filters", log_details)
                    return {
                        "message": "No campaigns match name filters",
                        "rule_id": rule_id,
                        "decision": "skip",
                        "items_checked": 0,
                        "items_meeting_conditions": 0,
                        "log_details": log_details
                    }
            except Exception as e:
                logger.warning(f"Error pre-resolving campaign name filters: {str(e)}. Falling back to post-fetch filtering.")
        
        # Step 0.6: Pre-resolve parent status conditions to IDs for API-level filtering
        # This dramatically reduces API calls by only fetching items with active parents
        has_campaign_status_condition = False
        campaign_status_value = None
        has_adset_status_condition = False
        adset_status_value = None
        
        for cond in rule_conditions:
            if cond.get("field") == "campaign_status" and cond.get("operator") == "=":
                has_campaign_status_condition = True
                campaign_status_value = cond.get("value")
            elif cond.get("field") == "adset_status" and cond.get("operator") == "=":
                has_adset_status_condition = True
                adset_status_value = cond.get("value")
        
        if has_campaign_status_condition and campaign_status_value and rule_level in ["ad", "ad_set"]:
            step_start_time = time.time()
            logger.info(f"[TIMING] Step 0.6a - Pre-resolving campaign_status={campaign_status_value} to campaign_ids for API optimization")
            base_url = "https://graph.facebook.com/v21.0"
            account_id_formatted = f"act_{account_id}" if not account_id.startswith("act_") else account_id
            
            # Build filtering for campaign status
            campaign_filtering = json.dumps([{
                "field": "effective_status",
                "operator": "IN",
                "value": [campaign_status_value]
            }])
            
            # If campaign_ids already set, filter by those too
            if "campaign_ids" in scope_filters and scope_filters["campaign_ids"]:
                existing_campaign_ids = scope_filters["campaign_ids"]
                campaign_filtering = json.dumps([
                    {"field": "effective_status", "operator": "IN", "value": [campaign_status_value]},
                    {"field": "id", "operator": "IN", "value": existing_campaign_ids}
                ])
            
            all_campaigns = []
            url = f"{base_url}/{account_id_formatted}/campaigns"
            params = {
                "fields": "id",
                "filtering": campaign_filtering,
                "limit": 2000,
                "access_token": access_token
            }
            
            while True:
                response = requests.get(url, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()
                all_campaigns.extend(data.get("data", []))
                next_url = data.get("paging", {}).get("next")
                if not next_url:
                    break
                url = next_url
                params = {}
                time.sleep(0.3)
            
            matching_campaign_ids = [str(c.get("id")) for c in all_campaigns]
            step_elapsed = time.time() - step_start_time
            logger.info(f"[TIMING] Step 0.6a completed in {step_elapsed:.2f} seconds - Found {len(matching_campaign_ids)} campaigns with status={campaign_status_value}")
            
            if matching_campaign_ids:
                scope_filters["campaign_ids"] = matching_campaign_ids
                logger.info(f"[OPTIMIZATION] campaign_status condition resolved to campaign_ids - will fetch only from {len(matching_campaign_ids)} campaigns")
            else:
                logger.info(f"[OPTIMIZATION] No campaigns with status={campaign_status_value} - skipping data fetch")
                log_details["data_fetch"] = {"total_items": 0, "items": []}
                log_details["filtered_data"] = []
                log_details["evaluations"] = []
                log_details["decision"] = "skip"
                log_details["items_meeting_conditions_count"] = 0
                create_rule_log(db, rule_id, "skipped", f"No campaigns with status={campaign_status_value}", log_details)
                return {
                    "message": f"No campaigns with status={campaign_status_value}",
                    "rule_id": rule_id,
                    "decision": "skip",
                    "items_checked": 0,
                    "items_meeting_conditions": 0,
                    "log_details": log_details
                }
        
        if has_adset_status_condition and adset_status_value and rule_level == "ad":
            step_start_time = time.time()
            logger.info(f"[TIMING] Step 0.6b - Pre-resolving adset_status={adset_status_value} for API optimization")
            base_url = "https://graph.facebook.com/v21.0"
            account_id_formatted = f"act_{account_id}" if not account_id.startswith("act_") else account_id
            
            # Build filtering for adset status
            adset_filtering = json.dumps([{
                "field": "effective_status",
                "operator": "IN",
                "value": [adset_status_value]
            }])
            
            # If campaign_ids already set, filter by those too
            if "campaign_ids" in scope_filters and scope_filters["campaign_ids"]:
                existing_campaign_ids = scope_filters["campaign_ids"]
                adset_filtering = json.dumps([
                    {"field": "effective_status", "operator": "IN", "value": [adset_status_value]},
                    {"field": "campaign.id", "operator": "IN", "value": existing_campaign_ids}
                ])
            
            all_adsets = []
            url = f"{base_url}/{account_id_formatted}/adsets"
            params = {
                "fields": "id,campaign_id",
                "filtering": adset_filtering,
                "limit": 2000,
                "access_token": access_token
            }
            
            while True:
                response = requests.get(url, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()
                all_adsets.extend(data.get("data", []))
                next_url = data.get("paging", {}).get("next")
                if not next_url:
                    break
                url = next_url
                params = {}
                time.sleep(0.3)
            
            matching_adset_ids = [str(a.get("id")) for a in all_adsets]
            step_elapsed = time.time() - step_start_time
            logger.info(f"[TIMING] Step 0.6b completed in {step_elapsed:.2f} seconds - Found {len(matching_adset_ids)} adsets with status={adset_status_value}")
            
            if matching_adset_ids:
                # For ads, we need to filter by adset_id, which we'll pass to the fetch function
                # Store in scope_filters so it can be applied
                scope_filters["adset_ids"] = matching_adset_ids
                logger.info(f"[OPTIMIZATION] adset_status condition resolved to adset_ids - will fetch only from {len(matching_adset_ids)} adsets")
            else:
                logger.info(f"[OPTIMIZATION] No adsets with status={adset_status_value} - skipping data fetch")
                log_details["data_fetch"] = {"total_items": 0, "items": []}
                log_details["filtered_data"] = []
                log_details["evaluations"] = []
                log_details["decision"] = "skip"
                log_details["items_meeting_conditions_count"] = 0
                create_rule_log(db, rule_id, "skipped", f"No adsets with status={adset_status_value}", log_details)
                return {
                    "message": f"No adsets with status={adset_status_value}",
                    "rule_id": rule_id,
                    "decision": "skip",
                    "items_checked": 0,
                    "items_meeting_conditions": 0,
                    "log_details": log_details
                }
        
        # Step 1: Fetch data from Facebook API
        step_start_time = time.time()
        logger.info(f"[TIMING] Step 1 - Fetching {rule_level} data for rule {rule_id} (rule: {rule.name})")
        # Optimization: if the rule has an explicit status condition like status = ACTIVE/PAUSED,
        # apply it at API level via effective_status IN [...]
        status_in = None
        try:
            status_values = []
            for cond in rule_conditions:
                if cond.get("field") == "status" and cond.get("operator") == "=":
                    v = cond.get("value")
                    if isinstance(v, str) and v:
                        status_values.append(v)
            if status_values:
                status_in = sorted(set(status_values))
        except Exception:
            status_in = None

        all_data = fetch_facebook_data(
            account_id,
            access_token,
            rule_level,
            scope_filters=scope_filters,
            effective_status_in=status_in,
            api_call_counter=api_call_counter,
        )
        step_elapsed = time.time() - step_start_time
        logger.info(f"[TIMING] Step 1 completed in {step_elapsed:.2f} seconds - Fetched {len(all_data)} total {rule_level} items from Facebook API")
        log_details["data_fetch"] = {
            "total_items": len(all_data),
            "items": all_data[:10]  # Log first 10 for reference
        }

        # Step 2: Apply scope filters
        step_start_time = time.time()
        logger.info(f"[TIMING] Step 2 - Applying scope filters for rule {rule_id}...")
        logger.info(f"Applying scope filters for {rule_level} level. Starting with {len(all_data)} items.")
        logger.info(f"Scope filters: {scope_filters}")
        filtered_data = apply_scope_filters(all_data, scope_filters, rule_level, account_id, access_token)
        step_elapsed = time.time() - step_start_time
        logger.info(f"[TIMING] Step 2 completed in {step_elapsed:.2f} seconds - After scope filtering: {len(filtered_data)} items remaining (from {len(all_data)} total)")
        log_details["filtered_data"] = [
            {
                "id": item.get("id"),
                "name": item.get("name"),
                "status": item.get("status"),
                "effective_status": item.get("effective_status")
            }
            for item in filtered_data
        ]

        # Step 3: Group conditions by time range and fetch insights
        step_start_time = time.time()
        logger.info(f"[TIMING] Step 3 - Grouping conditions by time range and fetching insights")
        filtered_ids = [item.get("id") for item in filtered_data]

        # Group conditions by their time range (or use global if not specified)
        condition_groups = {}
        for idx, condition in enumerate(rule_conditions):
            # Get time range for this condition (fallback to global)
            condition_time_range = condition.get("time_range") or time_range
            
            try:
                tr_key = time_range_key(condition_time_range)
            except TypeError as e:
                logger.error(f"Error creating time_range_key for condition {idx}: {e}")
                logger.error(f"Condition time_range: {condition_time_range}")
                logger.error(f"Time range type: {type(condition_time_range)}")
                raise

            if tr_key not in condition_groups:
                condition_groups[tr_key] = {
                    "time_range": condition_time_range,
                    "condition_indices": []
                }
            condition_groups[tr_key]["condition_indices"].append(idx)

        # Fetch insights for each unique time range
        insights_by_time_range = {}
        total_insights_fetched = 0
        for tr_key, group in condition_groups.items():
            group_time_range = group["time_range"]
            group_indices = group["condition_indices"]
            logger.info(f"[TIMING] Fetching insights for {len(group_indices)} condition(s) with time range: {group_time_range}")

            group_insights = fetch_insights(account_id, access_token, rule_level, filtered_ids, group_time_range, api_call_counter)
            insights_by_time_range[tr_key] = group_insights
            total_insights_fetched += len(group_insights)

            # Log insights summary for this time range
            insights_with_data = sum(1 for v in group_insights.values() if v and len(v) > 0)
            logger.info(f"[TIMING] Time range {group_time_range}: {insights_with_data} items have data out of {len(group_insights)} total")

        step_elapsed = time.time() - step_start_time
        logger.info(f"[TIMING] Step 3 completed in {step_elapsed:.2f} seconds - Fetched insights for {len(condition_groups)} unique time range(s)")
        log_details["insights_summary"] = {
            "unique_time_ranges": len(condition_groups),
            "time_range_groups": {
                str(k): {
                    "time_range": v["time_range"],
                    "condition_count": len(v["condition_indices"])
                }
                for k, v in condition_groups.items()
            },
            "total_insights_fetched": total_insights_fetched
        }

        # Step 4: Pre-fetch parent object statuses if needed
        step_start_time = time.time()
        logger.info(f"[TIMING] Step 4 - Pre-fetching parent object statuses...")
        campaign_status_cache = {}
        adset_status_cache = {}
        
        has_campaign_status_condition = any(
            cond.get("field") == "campaign_status" for cond in rule_conditions
        )
        has_adset_status_condition = any(
            cond.get("field") == "adset_status" for cond in rule_conditions
        )

        # Pre-fetch campaign statuses if needed (for ad/ad_set levels with campaign_status conditions)
        if has_campaign_status_condition and rule_level in ["ad", "ad_set"]:
            # Collect unique campaign IDs from filtered items
            campaign_ids = set()
            for item in filtered_data:
                campaign_id = item.get("campaign_id")
                if campaign_id:
                    campaign_ids.add(str(campaign_id))

            # Fetch campaign statuses if we have campaign IDs
            if campaign_ids:
                try:
                    base_url = "https://graph.facebook.com/v21.0"
                    if not account_id.startswith("act_"):
                        account_id_formatted = f"act_{account_id}"
                    else:
                        account_id_formatted = account_id

                    # Fetch campaigns in batches using filtering (Facebook API supports up to 50 IDs per filter)
                    batch_size = 50
                    campaign_ids_list = list(campaign_ids)
                    for i in range(0, len(campaign_ids_list), batch_size):
                        batch_ids = campaign_ids_list[i:i + batch_size]
                        # Build filtering JSON string for campaign IDs
                        filtering = f"[{{\"field\":\"campaign.id\",\"operator\":\"IN\",\"value\":[{','.join([f'\"{id_val}\"' for id_val in batch_ids])}]}}]"

                        url = f"{base_url}/{account_id_formatted}/campaigns"
                        params = {
                            "fields": "id,status,effective_status",
                            "filtering": filtering,
                            "limit": batch_size,
                            "access_token": access_token
                        }
                        response = requests.get(url, params=params, timeout=30)
                        if response.status_code == 200:
                            data = response.json()
                            campaigns_data = data.get("data", [])
                            for campaign in campaigns_data:
                                campaign_id = str(campaign.get("id"))
                                status = campaign.get("status") or campaign.get("effective_status")
                                campaign_status_cache[campaign_id] = status
                        else:
                            logger.warning(f"Error fetching campaign statuses: {response.status_code} - {response.text}")
                except Exception as e:
                    logger.warning(f"Error fetching campaign statuses: {str(e)}")
                    # Continue without campaign status cache - conditions will fail gracefully
        
        # Pre-fetch ad set statuses if needed (for ad-level rules with adset_status conditions)
        if has_adset_status_condition and rule_level == "ad":
            # Collect unique ad set IDs from filtered items
            adset_ids = set()
            for item in filtered_data:
                adset_id = item.get("adset_id")
                if adset_id:
                    adset_ids.add(str(adset_id))

            # Fetch ad set statuses if we have ad set IDs
            if adset_ids:
                try:
                    base_url = "https://graph.facebook.com/v21.0"
                    if not account_id.startswith("act_"):
                        account_id_formatted = f"act_{account_id}"
                    else:
                        account_id_formatted = account_id

                    # Fetch ad sets in batches using filtering (Facebook API supports up to 50 IDs per filter)
                    batch_size = 50
                    adset_ids_list = list(adset_ids)
                    for i in range(0, len(adset_ids_list), batch_size):
                        batch_ids = adset_ids_list[i:i + batch_size]
                        # Build filtering JSON string for ad set IDs
                        filtering = f"[{{\"field\":\"adset.id\",\"operator\":\"IN\",\"value\":[{','.join([f'\"{id_val}\"' for id_val in batch_ids])}]}}]"

                        url = f"{base_url}/{account_id_formatted}/adsets"
                        params = {
                            "fields": "id,status,effective_status",
                            "filtering": filtering,
                            "limit": batch_size,
                            "access_token": access_token
                        }
                        response = requests.get(url, params=params, timeout=30)
                        if response.status_code == 200:
                            data = response.json()
                            adsets_data = data.get("data", [])
                            for adset in adsets_data:
                                adset_id = str(adset.get("id"))
                                status = adset.get("status") or adset.get("effective_status")
                                adset_status_cache[adset_id] = status
                        else:
                            logger.warning(f"Error fetching ad set statuses: {response.status_code} - {response.text}")
                except Exception as e:
                    logger.warning(f"Error fetching ad set statuses: {str(e)}")
                    # Continue without ad set status cache - conditions will fail gracefully
        
        step_elapsed = time.time() - step_start_time
        logger.info(f"[TIMING] Step 4 completed in {step_elapsed:.2f} seconds - Campaign statuses cached: {len(campaign_status_cache)} campaigns, Adset statuses cached: {len(adset_status_cache)} ad sets")

        # Helper function to normalize conditions to groups format
        def normalize_conditions_to_groups(conditions_data):
            """
            Normalize conditions to condition_groups format.
            Handles both old (flat) and new (grouped) formats.
            """
            # If already in new format
            if "condition_groups" in conditions_data:
                groups = conditions_data["condition_groups"]
                # Generate simple indexed group_ids for logging
                for idx, group in enumerate(groups):
                    group["group_id"] = f"group_{idx + 1}"
                return groups
            
            # If old format, wrap in single group
            if "conditions" in conditions_data:
                return [{
                    "group_id": "group_1",
                    "conditions": conditions_data["conditions"]
                }]
            
            return []

        # Step 5: Evaluate conditions for each item
        step_start_time = time.time()
        logger.info(f"[TIMING] Step 5 - Evaluating conditions for {len(filtered_data)} items...")
        items_meeting_conditions = []

        # Normalize conditions to groups
        condition_groups = normalize_conditions_to_groups(rule.conditions)
        logger.info(f"[EVAL] Evaluating {len(condition_groups)} condition group(s) with OR logic between groups")

        for item in filtered_data:
            item_id = item.get("id")

            item_evaluation = {
                "item_id": item_id,
                "item_name": item.get("name"),
                "condition_groups": [],
                "any_group_passed": False,
                "passed_group_ids": []
            }

            # Evaluate each group (OR logic between groups)
            any_group_passed = False
            passed_group_ids = []

            for group_idx, group in enumerate(condition_groups):
                group_id = group.get("group_id", f"group_{group_idx + 1}")
                group_conditions = group.get("conditions", [])
                
                group_evaluation = {
                    "group_id": group_id,
                    "conditions_evaluated": [],
                    "all_conditions_passed": True
                }
                
                logger.debug(f"[EVAL] Evaluating group {group_id} with {len(group_conditions)} condition(s)")
                
                # Evaluate all conditions in this group (AND logic)
                for condition in group_conditions:
                    # Get the time range for this condition (fallback to global)
                    condition_time_range = condition.get("time_range") or time_range
                    
                    try:
                        tr_key = time_range_key(condition_time_range)
                    except TypeError as e:
                        logger.error(f"Error creating time_range_key in evaluation: {e}")
                        logger.error(f"Condition time_range: {condition_time_range}")
                        raise

                    # Get insights for this condition's time range
                    condition_insights = insights_by_time_range.get(tr_key, {}).get(item_id, {})

                    # Handle Amount of Active Ads - fetch and count active ads
                    if condition.get("field") == "amount_of_active_ads":
                        # Determine what to count based on rule level
                        if rule_level == "campaign":
                            # Count ads in this campaign
                            ads = fetch_ads_for_item(account_id, access_token, item_id, "campaign")
                        elif rule_level == "ad_set":
                            # Count ads in this adset
                            ads = fetch_ads_for_item(account_id, access_token, item_id, "adset")
                        elif rule_level == "ad":
                            # Count ads in the parent adset
                            adset_id = item.get("adset_id")
                            if adset_id:
                                ads = fetch_ads_for_item(account_id, access_token, adset_id, "adset")
                            else:
                                logger.warning(f"Ad {item_id} has no adset_id, cannot count active ads")
                                ads = []
                        else:
                            ads = []

                        # Count ads with ACTIVE status
                        active_ads_count = 0
                        for ad in ads:
                            status = ad.get("status") or ad.get("effective_status")
                            if status == "ACTIVE":
                                active_ads_count += 1

                        # Add count to insights as a synthetic metric
                        if not condition_insights:
                            condition_insights = {}
                        condition_insights["amount_of_active_ads"] = active_ads_count
                        logger.info(f"Item {item_id}: Counted {active_ads_count} active ads out of {len(ads)} total ads")

                    # Log which time range was used for this condition
                    time_range_used = condition_time_range if condition.get("time_range") else "global"

                    passed, evaluation = evaluate_condition(item, condition_insights, condition, campaign_status_cache, adset_status_cache)
                    evaluation["time_range_used"] = time_range_used

                    group_evaluation["conditions_evaluated"].append(evaluation)
                    if not passed:
                        group_evaluation["all_conditions_passed"] = False
                
                item_evaluation["condition_groups"].append(group_evaluation)
                
                # If this group passed, mark it (OR logic)
                if group_evaluation["all_conditions_passed"]:
                    any_group_passed = True
                    passed_group_ids.append(group_id)
                    logger.debug(f"[EVAL] Group {group_id} PASSED for item {item_id}")
                    # Performance optimization: break early since we only need one group to pass
                    break
                else:
                    logger.debug(f"[EVAL] Group {group_id} FAILED for item {item_id}")

            item_evaluation["any_group_passed"] = any_group_passed
            item_evaluation["passed_group_ids"] = passed_group_ids
            log_details["evaluations"].append(item_evaluation)

            if any_group_passed:
                items_meeting_conditions.append(item)
                logger.info(f"[EVAL] Item {item_id} ({item.get('name')}) met conditions via group(s): {passed_group_ids}")
        step_elapsed = time.time() - step_start_time
        logger.info(f"[TIMING] Step 5 completed in {step_elapsed:.2f} seconds - {len(items_meeting_conditions)} item(s) met all conditions out of {len(filtered_data)} evaluated")

        # Step 6: Determine decision
        decision = "proceed" if len(items_meeting_conditions) > 0 else "skip"
        log_details["decision"] = decision
        log_details["items_meeting_conditions_count"] = len(items_meeting_conditions)
        log_details["items_meeting_conditions"] = [
            {"id": item.get("id"), "name": item.get("name")}
            for item in items_meeting_conditions
        ]

        # Step 7: Execute actions if conditions are met
        step_start_time = time.time()
        logger.info(f"[TIMING] Step 7 - Executing actions on {len(items_meeting_conditions)} items...")
        actions_executed = []
        if decision == "proceed" and len(items_meeting_conditions) > 0:
            rule_actions = rule.actions.get("actions", [])
            for action in rule_actions:
                action_results = execute_action(
                    account_id, access_token, rule_level,
                    items_meeting_conditions, action,
                    slack_webhook_url=slack_webhook_url,
                    rule_name=rule.name,
                    api_call_counter=api_call_counter
                )
                actions_executed.extend(action_results)
        step_elapsed = time.time() - step_start_time
        logger.info(f"[TIMING] Step 7 completed in {step_elapsed:.2f} seconds - Executed {len(actions_executed)} action(s)")

        log_details["actions_executed"] = actions_executed

        # Step 8: Log results
        if actions_executed:
            success_count = sum(1 for a in actions_executed if a.get("success", False))
            message = f"Executed actions on {success_count}/{len(actions_executed)} item(s). {len(items_meeting_conditions)} item(s) met all conditions."
        else:
            message = f"Test completed: {len(items_meeting_conditions)} item(s) meet all conditions"
        status = "success" if decision == "proceed" else "skipped"

        # Add items_checked to log_details so it's persisted in the database
        log_details["items_checked"] = len(filtered_data)

        total_elapsed = time.time() - total_start_time
        logger.info(f"[TIMING] === Rule execution completed in {total_elapsed:.2f} seconds total ===")
        logger.info(f"[API CALLS] Total: {api_call_counter['total']}, Fetch Items: {api_call_counter['fetch_items']}, Fetch Insights: {api_call_counter['fetch_insights']}, Actions: {api_call_counter['actions']}")
        logger.info(f"[DEBUG] log_details keys: {log_details.keys()}")
        logger.info(f"[DEBUG] api_calls in log_details: {log_details.get('api_calls')}")

        create_rule_log(db, rule_id, status, message, log_details)

        # Update last_run_at timestamp for manual test runs
        rule.last_run_at = datetime.now()
        db.commit()

        return {
            "message": message,
            "rule_id": rule_id,
            "decision": decision,
            "items_checked": len(filtered_data),
            "items_meeting_conditions": len(items_meeting_conditions),
            "log_details": log_details
        }

    except Exception as e:
        logger.error(f"Error testing rule {rule_id}: {str(e)}", exc_info=True)
        log_details["error"] = str(e)
        create_rule_log(db, rule_id, "error", f"Error testing rule: {str(e)}", log_details)
        raise
