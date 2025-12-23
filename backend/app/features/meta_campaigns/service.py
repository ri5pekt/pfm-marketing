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
# Rule CRUD Operations
# ----------------------------
def get_all_rules(db: Session):
    return db.query(models.CampaignRule).all()


def get_rules_by_ad_account(db: Session, ad_account_id: int):
    return db.query(models.CampaignRule).filter(
        models.CampaignRule.ad_account_id == ad_account_id
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
    rule = get_rule(db, rule_id)
    if not rule:
        raise ValueError("Rule not found")

    if not rule.enabled:
        create_rule_log(db, rule_id, "skipped", "Rule is disabled", {})
        return {"message": "Rule is disabled", "rule_id": rule_id}

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
    scope_filters = {k: v for k, v in conditions.items() if k in ["name_contains", "ids", "campaign_ids", "campaign_name_contains"]}
    time_range = conditions.get("time_range", {})
    rule_conditions = conditions.get("conditions", [])

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
        "evaluations": []
    }

    total_start_time = time.time()
    logger.info(f"[TIMING] === Starting rule execution: rule_id={rule_id} (rule: {rule.name}) ===")

    # Helper function to create a hashable key from time range dict
    def time_range_key(tr):
        """Create a hashable key from time range dict"""
        if not tr:
            return None
        return (
            tr.get("unit"),
            tr.get("amount"),
            tr.get("exclude_today", True)
        )

    try:
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
            tr_key = time_range_key(condition_time_range)

            if tr_key not in condition_groups:
                condition_groups[tr_key] = {
                    "time_range": condition_time_range,
                    "condition_indices": []
                }
            condition_groups[tr_key]["condition_indices"].append(idx)

        # Check if any condition uses cpp_winning_days (requires daily insights)
        has_cpp_winning_days = any(
            cond.get("field") == "cpp_winning_days" for cond in rule_conditions
        )

        # Fetch insights for each unique time range
        insights_by_time_range = {}
        daily_insights_by_time_range = {}  # For cpp_winning_days
        total_insights_fetched = 0
        for tr_key, group in condition_groups.items():
            group_time_range = group["time_range"]
            group_indices = group["condition_indices"]
            logger.info(f"[TIMING] Fetching insights for {len(group_indices)} condition(s) with time range: {group_time_range}")

            group_insights = fetch_insights(account_id, access_token, rule_level, filtered_ids, group_time_range)
            insights_by_time_range[tr_key] = group_insights
            total_insights_fetched += len(group_insights)

            # If any condition in this group uses cpp_winning_days, also fetch daily insights
            group_has_cpp_winning_days = any(
                rule_conditions[idx].get("field") == "cpp_winning_days" for idx in group_indices
            )
            if group_has_cpp_winning_days:
                logger.info(f"[TIMING] Fetching daily insights for CPP Winning Days calculation with time range: {group_time_range}")
                group_daily_insights = fetch_daily_insights(account_id, access_token, rule_level, filtered_ids, group_time_range)
                daily_insights_by_time_range[tr_key] = group_daily_insights

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

        # Step 4: Pre-fetch campaign statuses if needed (for ad/ad_set levels with campaign_status conditions)
        step_start_time = time.time()
        logger.info(f"[TIMING] Step 4 - Pre-fetching campaign statuses...")
        campaign_status_cache = {}
        has_campaign_status_condition = any(
            cond.get("field") == "campaign_status" for cond in rule_conditions
        )

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
        step_elapsed = time.time() - step_start_time
        logger.info(f"[TIMING] Step 4 completed in {step_elapsed:.2f} seconds - Campaign statuses cached: {len(campaign_status_cache)} campaigns")

        # Step 5: Evaluate conditions for each item
        step_start_time = time.time()
        logger.info(f"[TIMING] Step 5 - Evaluating conditions for {len(filtered_data)} items...")
        items_meeting_conditions = []

        for item in filtered_data:
            item_id = item.get("id")

            item_evaluation = {
                "item_id": item_id,
                "item_name": item.get("name"),
                "conditions_evaluated": [],
                "all_conditions_met": False
            }

            # Evaluate all conditions
            all_passed = True
            for condition in rule_conditions:
                # Get the time range for this condition (fallback to global)
                condition_time_range = condition.get("time_range") or time_range
                tr_key = time_range_key(condition_time_range)

                # Get insights for this condition's time range
                condition_insights = insights_by_time_range.get(tr_key, {}).get(item_id, {})

                # Initialize variables for CPP winning days breakdown
                cpp_winning_days_breakdown = []
                cpp_winning_days_total_days = 0

                # Handle CPP Winning Days - calculate from daily insights
                if condition.get("field") == "cpp_winning_days":
                    threshold = condition.get("threshold")
                    if threshold is None:
                        logger.warning(f"CPP Winning Days condition missing threshold, skipping")
                        item_evaluation["conditions_evaluated"].append({
                            "field": "cpp_winning_days",
                            "operator": condition.get("operator"),
                            "expected_value": condition.get("value"),
                            "actual_value": None,
                            "passed": False,
                            "error": "Threshold not specified"
                        })
                        all_passed = False
                        continue

                    # Get daily insights for this time range
                    daily_insights_list = daily_insights_by_time_range.get(tr_key, {}).get(item_id, [])

                    # Calculate winning days (days where CPP < threshold)
                    # A "winning day" is a day where CPP was below the threshold
                    winning_days = 0
                    daily_cpp_breakdown = []  # For detailed logging and UI display
                    for daily_insight in daily_insights_list:
                        # Calculate CPP for this day
                        daily_cpp = calculate_metric_from_insights(daily_insight, "cpp")
                        date_start = daily_insight.get("date_start", "unknown")
                        spend = daily_insight.get("spend", 0)
                        actions = daily_insight.get("actions", [])
                        cost_per_action_type = daily_insight.get("cost_per_action_type", [])

                        # Count days where CPP is calculated (not None), greater than 0 (has purchases), and less than threshold
                        # If CPP is 0 or None, it means no purchases occurred, so skip that day
                        # Only count days with actual purchases (CPP > 0) that are below the threshold
                        is_winning = False
                        if daily_cpp is not None and daily_cpp > 0 and daily_cpp < threshold:
                            winning_days += 1
                            is_winning = True

                        # Store detailed breakdown for logging and evaluation
                        daily_cpp_breakdown.append({
                            "date": date_start,
                            "cpp": daily_cpp,
                            "spend": spend,
                            "is_winning": is_winning,
                            "actions": actions,
                            "cost_per_action_type": cost_per_action_type
                        })

                    # Add winning days count to insights as a synthetic metric
                    if not condition_insights:
                        condition_insights = {}
                    condition_insights["cpp_winning_days"] = winning_days

                    # Log detailed breakdown
                    breakdown_parts = []
                    for d in daily_cpp_breakdown:
                        cpp_str = f"${d['cpp']:.2f}" if d['cpp'] is not None else "N/A"
                        winning_str = " (WINNING)" if d['is_winning'] else ""
                        breakdown_parts.append(f"{d['date']}: CPP={cpp_str}{winning_str}")
                    breakdown_str = ", ".join(breakdown_parts)
                    logger.info(f"Item {item_id}: Calculated {winning_days} winning days (CPP < {threshold}) from {len(daily_insights_list)} daily insights")
                    logger.info(f"Item {item_id} daily CPP breakdown: {breakdown_str}")

                    # Store breakdown for later use in evaluation
                    cpp_winning_days_breakdown = daily_cpp_breakdown
                    cpp_winning_days_total_days = len(daily_insights_list)

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
                evaluation_context = {
                    "time_range_used": time_range_used,
                    "time_range_key": str(tr_key) if tr_key else "global"
                }

                passed, evaluation = evaluate_condition(item, condition_insights, condition, campaign_status_cache)
                evaluation["time_range_used"] = time_range_used

                # Add CPP winning days breakdown to evaluation if this was a cpp_winning_days condition
                if condition.get("field") == "cpp_winning_days":
                    evaluation["cpp_winning_days_breakdown"] = cpp_winning_days_breakdown
                    evaluation["cpp_winning_days_total_days"] = cpp_winning_days_total_days
                item_evaluation["conditions_evaluated"].append(evaluation)
                if not passed:
                    all_passed = False

            item_evaluation["all_conditions_met"] = all_passed
            log_details["evaluations"].append(item_evaluation)

            if all_passed:
                items_meeting_conditions.append(item)
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
                    rule_name=rule.name
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

        total_elapsed = time.time() - total_start_time
        logger.info(f"[TIMING] === Rule execution completed in {total_elapsed:.2f} seconds total ===")

        create_rule_log(db, rule_id, status, message, log_details)

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
