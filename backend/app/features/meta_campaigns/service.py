from sqlalchemy.orm import Session
from app.features.meta_campaigns import models, schemas
from datetime import datetime, timedelta
import requests
import logging
import time
from typing import Dict, List, Any, Tuple

logger = logging.getLogger(__name__)


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


def fetch_facebook_data(account_id: str, access_token: str, rule_level: str, limit: int = 100):
    """Fetch campaigns, adsets, or ads from Facebook API"""
    base_url = "https://graph.facebook.com/v21.0"

    # Ensure account_id has 'act_' prefix
    if not account_id.startswith("act_"):
        account_id = f"act_{account_id}"

    if rule_level == "ad":
        endpoint = f"{base_url}/{account_id}/ads"
        fields = "id,name,account_id,adset_id,campaign_id,status,configured_status,effective_status,bid_amount,conversion_domain,created_time,last_updated_by_app_id,issues_info,preview_shareable_link,recommendations,tracking_specs,creative{id,name,object_story_spec,thumbnail_url,asset_feed_spec}"
    elif rule_level == "ad_set":
        endpoint = f"{base_url}/{account_id}/adsets"
        fields = "id,name,campaign_id,status,effective_status,daily_budget,lifetime_budget"
    else:  # campaign
        endpoint = f"{base_url}/{account_id}/campaigns"
        fields = "id,name,status,effective_status"

    url = f"{endpoint}?fields={fields}&limit={limit}&access_token={access_token}"

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        items = data.get("data", [])
        logger.info(f"Fetched {len(items)} {rule_level} items from Facebook API")
        if items and len(items) > 0:
            # Log sample item to verify fields are present
            sample_item = items[0]
            logger.debug(f"Sample {rule_level} item fields: {list(sample_item.keys())}")
            if rule_level == "ad":
                logger.debug(f"Sample ad - id: {sample_item.get('id')}, name: {sample_item.get('name')}, bid_amount: {sample_item.get('bid_amount')}")
        return items
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching Facebook data: {str(e)}")
        if hasattr(e.response, 'text'):
            logger.error(f"Response: {e.response.text}")
        raise


def fetch_insights(account_id: str, access_token: str, rule_level: str, ids: List[str], time_range: Dict[str, Any]):
    """Fetch insights for the given IDs and time range"""
    base_url = "https://graph.facebook.com/v21.0"

    # Ensure account_id has 'act_' prefix
    if not account_id.startswith("act_"):
        account_id = f"act_{account_id}"

    # Build time range string
    time_range_str = build_time_range_string(time_range)

    # Fields to fetch
    fields = "campaign_id,adset_id,ad_id,spend,impressions,clicks,cpc,cpm,ctr,actions,cost_per_action_type"

    if rule_level == "ad":
        level = "ad"
    elif rule_level == "ad_set":
        level = "adset"
    else:
        level = "campaign"

    endpoint = f"{base_url}/{account_id}/insights"
    insights_data = {}

    # Fetch insights in batches (Facebook API supports up to 50 IDs per request)
    batch_size = 50
    for i in range(0, len(ids), batch_size):
        batch_ids = ids[i:i + batch_size]
        ids_str = ",".join(batch_ids)

        # Build filtering JSON string
        # Facebook API v21.0+ requires specific filter fields for each level
        if level == "ad":
            filter_field = "ad.id"
        elif level == "adset":
            filter_field = "adset.id"
        else:  # campaign
            filter_field = "campaign.id"
        filtering = f"[{{\"field\":\"{filter_field}\",\"operator\":\"IN\",\"value\":[{','.join([f'\"{id_val}\"' for id_val in batch_ids])}]}}]"

        # Add action_breakdowns parameter to get cost_per_action_type properly populated
        url = f"{endpoint}?level={level}&fields={fields}&time_range={time_range_str}&filtering={filtering}&action_breakdowns=action_type&access_token={access_token}"
        logger.info(f"Fetching insights: level={level}, time_range={time_range_str}, batch_size={len(batch_ids)}")

        try:
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            data = response.json()
            logger.info(f"Insights API response for batch: {len(batch_ids)} IDs, got {len(data.get('data', []))} insights")
            if data.get("data") and len(data["data"]) > 0:
                # Log first insight to see structure
                first_insight = data["data"][0]
                logger.info(f"Sample insight structure: {list(first_insight.keys())}, spend={first_insight.get('spend')}, impressions={first_insight.get('impressions')}")
                # Log cost_per_action_type if present
                if "cost_per_action_type" in first_insight:
                    logger.info(f"cost_per_action_type sample: {first_insight.get('cost_per_action_type')}")
                else:
                    logger.warning(f"cost_per_action_type not found in insights response. Available fields: {list(first_insight.keys())}")
            if data.get("data"):
                for insight in data["data"]:
                    obj_id = insight.get(f"{level}_id") or insight.get("id")
                    if obj_id:
                        insights_data[obj_id] = insight
                        # Log sample insight data for debugging
                        logger.debug(f"Insight for {obj_id}: spend={insight.get('spend')}, impressions={insight.get('impressions')}, clicks={insight.get('clicks')}")
            # Mark items without insights
            for obj_id in batch_ids:
                if obj_id not in insights_data:
                    insights_data[obj_id] = {}
                    logger.debug(f"No insights data found for {obj_id}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching insights batch: {str(e)}")
            if hasattr(e.response, 'text'):
                logger.error(f"Response: {e.response.text}")
            # Mark all batch items as having no insights
            for obj_id in batch_ids:
                if obj_id not in insights_data:
                    insights_data[obj_id] = {}

    return insights_data


def build_time_range_string(time_range: Dict[str, Any]) -> str:
    """Build Facebook API time_range parameter

    Note: Facebook API includes both start and end dates, so for N days we subtract (N-1) days
    to get exactly N days of data.
    """
    unit = time_range.get("unit", "days")
    amount = time_range.get("amount", 1)
    exclude_today = time_range.get("exclude_today", True)

    end_time = datetime.now()
    if exclude_today and unit == "days":
        end_time = end_time.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
        end_time = end_time.replace(hour=23, minute=59, second=59)

    if unit == "minutes":
        # For minutes/hours, we want exactly that duration, so subtract full amount
        start_time = end_time - timedelta(minutes=amount)
    elif unit == "hours":
        start_time = end_time - timedelta(hours=amount)
    else:  # days
        # For days, Facebook API includes both start and end dates, so subtract (amount - 1)
        # to get exactly 'amount' days of data
        start_time = end_time - timedelta(days=amount - 1)

    # Format as JSON string for Facebook API
    logger.debug(f"Time range: {start_time.strftime('%Y-%m-%d')} to {end_time.strftime('%Y-%m-%d')} ({amount} {unit})")
    return f"{{\"since\":\"{start_time.strftime('%Y-%m-%d')}\",\"until\":\"{end_time.strftime('%Y-%m-%d')}\"}}"


def apply_scope_filters(data: List[Dict], scope_filters: Dict[str, Any], rule_level: str = "ad", account_id: str = None, access_token: str = None) -> List[Dict]:
    """Apply scope filters to the data

    Args:
        data: List of items to filter
        scope_filters: Dictionary of scope filters
        rule_level: The rule level (campaign, ad_set, or ad) to determine filter behavior
        account_id: Account ID for fetching campaign data (needed for campaign_name_contains)
        access_token: Access token for fetching campaign data (needed for campaign_name_contains)
    """
    filtered_data = data.copy()

    # Name contains filter (for ad/adset level - filters by item name)
    if "name_contains" in scope_filters and scope_filters["name_contains"]:
        keywords = scope_filters["name_contains"]
        if isinstance(keywords, list):
            filtered_data = [
                item for item in filtered_data
                if any(keyword.lower() in item.get("name", "").lower() for keyword in keywords)
            ]

    # IDs filter (for ad/adset level - filters by item id)
    if "ids" in scope_filters and scope_filters["ids"]:
        ids = scope_filters["ids"]
        if isinstance(ids, list):
            filtered_data = [
                item for item in filtered_data
                if str(item.get("id", "")) in [str(id_val) for id_val in ids]
            ]
        elif isinstance(ids, str):
            # Handle comma-separated or newline-separated IDs
            ids_list = [id_val.strip() for id_val in ids.replace("\n", ",").split(",") if id_val.strip()]
            filtered_data = [
                item for item in filtered_data
                if str(item.get("id", "")) in [str(id_val) for id_val in ids_list]
            ]

    # Campaign Name contains filter
    if "campaign_name_contains" in scope_filters and scope_filters["campaign_name_contains"]:
        keywords = scope_filters["campaign_name_contains"]
        if isinstance(keywords, list) and keywords:
            if rule_level == "campaign":
                # For campaign level, filter by campaign name directly
                filtered_data = [
                    item for item in filtered_data
                    if any(keyword.lower() in item.get("name", "").lower() for keyword in keywords)
                ]
            else:
                # For ad/adset level, fetch campaigns by name, then filter by campaign_id
                if account_id and access_token:
                    try:
                        # Fetch campaigns and filter by name
                        base_url = "https://graph.facebook.com/v21.0"
                        if not account_id.startswith("act_"):
                            account_id = f"act_{account_id}"

                        url = f"{base_url}/{account_id}/campaigns"
                        params = {
                            "fields": "id,name",
                            "limit": 500,
                            "access_token": access_token
                        }
                        response = requests.get(url, params=params, timeout=30)
                        if response.status_code == 200:
                            campaigns_data = response.json().get("data", [])
                            # Filter campaigns by name keywords
                            matching_campaign_ids = [
                                str(campaign.get("id"))
                                for campaign in campaigns_data
                                if any(keyword.lower() in campaign.get("name", "").lower() for keyword in keywords)
                            ]
                            # Filter ads/adsets by matching campaign IDs
                            if matching_campaign_ids:
                                filtered_data = [
                                    item for item in filtered_data
                                    if str(item.get("campaign_id", "")) in matching_campaign_ids
                                ]
                            else:
                                # No campaigns match, so no ads/adsets match
                                filtered_data = []
                    except Exception as e:
                        logger.warning(f"Error fetching campaigns for campaign_name_contains filter: {str(e)}")
                        # If we can't fetch campaigns, we can't filter, so keep all data

    # Campaign IDs filter
    if "campaign_ids" in scope_filters and scope_filters["campaign_ids"]:
        campaign_ids = scope_filters["campaign_ids"]
        # Convert string to list if needed
        if isinstance(campaign_ids, str):
            campaign_ids = [id_val.strip() for id_val in campaign_ids.replace("\n", ",").split(",") if id_val.strip()]

        if isinstance(campaign_ids, list) and campaign_ids:
            if rule_level == "campaign":
                # For campaign level, filter by campaign id (item id)
                filtered_data = [
                    item for item in filtered_data
                    if str(item.get("id", "")) in [str(id_val) for id_val in campaign_ids]
                ]
            else:
                # For ad/adset level, filter by campaign_id field
                filtered_data = [
                    item for item in filtered_data
                    if str(item.get("campaign_id", "")) in [str(id_val) for id_val in campaign_ids]
                ]

    return filtered_data


def calculate_metric_from_insights(insights: Dict, field: str) -> float:
    """Calculate a metric value from insights data"""
    if not insights or len(insights) == 0:
        logger.debug(f"No insights data available for field '{field}'")
        return 0

    # Helper to safely convert to float, handling strings and None
    def safe_float(value, default=0):
        if value is None or value == "":
            return default
        try:
            return float(str(value).replace(",", ""))  # Remove commas from formatted numbers
        except (ValueError, TypeError):
            return default

    if field == "cpp":
        # Try to extract cost_per_purchase from cost_per_action_type array first
        cost_per_action_type = insights.get("cost_per_action_type", [])
        logger.debug(f"cost_per_action_type for cpp: {cost_per_action_type}, type: {type(cost_per_action_type)}")

        if cost_per_action_type:
            # Find the purchase action in the array
            # Facebook API can return various purchase action types: "purchase", "offsite_conversion.fb_pixel_purchase",
            # "onsite_web_purchase", "omni_purchase", "web_in_store_purchase", etc.
            purchase_action_types = ["purchase", "offsite_conversion.fb_pixel_purchase", "onsite_web_purchase",
                                   "omni_purchase", "web_in_store_purchase", "web_app_in_store_purchase"]
            for action_cost in cost_per_action_type:
                if isinstance(action_cost, dict):
                    action_type = action_cost.get("action_type", "")
                    logger.debug(f"Checking action_type: {action_type}, action_cost: {action_cost}")
                    # Check for any purchase action type
                    if action_type in purchase_action_types or "purchase" in action_type.lower():
                        cpp_value = action_cost.get("value")
                        logger.debug(f"Found purchase action ({action_type}), value: {cpp_value}")
                        if cpp_value:
                            # cost_per_action_type value might come as a string with currency or as a number
                            cpp_str = str(cpp_value).replace("$", "").replace(",", "")
                            result = safe_float(cpp_str, 0)
                            logger.debug(f"Calculated CPP from cost_per_action_type: {result}")
                            return result

        # Fallback: Try cost_per_result if available (for purchase-optimized campaigns)
        cost_per_result = insights.get("cost_per_result", [])
        if cost_per_result and isinstance(cost_per_result, list):
            for result_item in cost_per_result:
                if isinstance(result_item, dict):
                    indicator = result_item.get("indicator", "")
                    # Check if it's a purchase-related result
                    if "purchase" in indicator.lower():
                        values = result_item.get("values", [])
                        if values and isinstance(values, list) and len(values) > 0:
                            cpp_value = values[0].get("value")
                            if cpp_value:
                                cpp_str = str(cpp_value).replace("$", "").replace(",", "")
                                result = safe_float(cpp_str, 0)
                                logger.debug(f"Calculated CPP from cost_per_result: {result}")
                                return result

        # Fallback: Calculate from spend and purchase actions if cost_per_action_type is not available
        logger.debug(f"cost_per_action_type not available, falling back to calculation from spend and actions")
        spend = safe_float(insights.get("spend"), 0)
        actions = insights.get("actions", [])
        purchases = 0
        if actions:
            for action in actions:
                if isinstance(action, dict) and action.get("action_type") == "purchase":
                    purchases += safe_float(action.get("value"), 0)

        if purchases > 0:
            result = spend / purchases
            logger.debug(f"Calculated CPP from spend/purchases: spend={spend}, purchases={purchases}, cpp={result}")
            return result
        else:
            logger.debug(f"No purchases found. spend={spend}, actions={actions}")
            return 0
    elif field == "spend":
        return safe_float(insights.get("spend"), 0)
    elif field == "conversions":
        actions = insights.get("actions", [])
        conversions = 0
        if actions:
            for action in actions:
                if isinstance(action, dict) and action.get("action_type") in ["purchase", "complete_registration", "lead"]:
                    conversions += safe_float(action.get("value"), 0)
        return conversions
    elif field == "ctr":
        ctr_value = insights.get("ctr")
        if ctr_value:
            # CTR might come as percentage string like "1.23%" or as decimal
            ctr_str = str(ctr_value).replace("%", "")
            return safe_float(ctr_str, 0)
        return 0
    elif field == "cpc":
        return safe_float(insights.get("cpc"), 0)
    elif field == "cpm":
        return safe_float(insights.get("cpm"), 0)
    elif field == "roas":
        spend = safe_float(insights.get("spend"), 0)
        actions = insights.get("actions", [])
        revenue = 0
        if actions:
            for action in actions:
                if isinstance(action, dict) and action.get("action_type") == "purchase":
                    revenue += safe_float(action.get("value"), 0)
        return revenue / spend if spend > 0 else 0
    elif field == "daily_budget":
        # This comes from the object data, not insights
        return None
    return None


def evaluate_condition(item: Dict, insights: Dict, condition: Dict, campaign_status_cache: Dict[str, str] = None) -> Tuple[bool, Dict]:
    """Evaluate a single condition against an item

    Args:
        item: The item (ad, adset, or campaign) to evaluate
        insights: Insights data for the item
        condition: The condition to evaluate
        campaign_status_cache: Optional dict mapping campaign_id to campaign status
    """
    field = condition.get("field")
    operator = condition.get("operator")
    expected_value = condition.get("value")

    evaluation = {
        "field": field,
        "operator": operator,
        "expected_value": expected_value,
        "actual_value": None,
        "passed": False
    }

    # Handle status field (from object data)
    if field == "status":
        actual_value = item.get("status") or item.get("effective_status")
        evaluation["actual_value"] = actual_value
        if operator == "=":
            evaluation["passed"] = str(actual_value) == str(expected_value)
        elif operator == "!=":
            evaluation["passed"] = str(actual_value) != str(expected_value)

    # Handle campaign_status field (from campaign data)
    elif field == "campaign_status":
        campaign_id = item.get("campaign_id")
        if campaign_id and campaign_status_cache:
            actual_value = campaign_status_cache.get(str(campaign_id))
            evaluation["actual_value"] = actual_value
            if actual_value is not None:
                if operator == "=":
                    evaluation["passed"] = str(actual_value) == str(expected_value)
                elif operator == "!=":
                    evaluation["passed"] = str(actual_value) != str(expected_value)
            else:
                # Campaign status not found in cache, condition fails
                evaluation["passed"] = False
        else:
            # No campaign_id or no cache available, condition fails
            evaluation["actual_value"] = None
            evaluation["passed"] = False

    # Handle name_contains field (from object data)
    elif field == "name_contains":
        actual_value = item.get("name", "")
        evaluation["actual_value"] = actual_value
        if operator == "=":
            evaluation["passed"] = str(expected_value).lower() in actual_value.lower()
        elif operator == "!=":
            evaluation["passed"] = str(expected_value).lower() not in actual_value.lower()

    # Handle daily_budget (from object data)
    elif field == "daily_budget":
        actual_value = item.get("daily_budget")
        if actual_value is not None:
            actual_value = float(actual_value) / 100  # Convert cents to dollars
            evaluation["actual_value"] = actual_value  # Store converted value (in dollars) for display
            expected_value = float(expected_value)
            if operator == ">":
                evaluation["passed"] = actual_value > expected_value
            elif operator == ">=":
                evaluation["passed"] = actual_value >= expected_value
            elif operator == "<":
                evaluation["passed"] = actual_value < expected_value
            elif operator == "<=":
                evaluation["passed"] = actual_value <= expected_value
            elif operator == "=":
                evaluation["passed"] = actual_value == expected_value
            elif operator == "!=":
                evaluation["passed"] = actual_value != expected_value
        else:
            evaluation["actual_value"] = None

    # Handle metrics from insights
    else:
        actual_value = calculate_metric_from_insights(insights, field)
        evaluation["actual_value"] = actual_value

        # Log for debugging when actual_value is 0 or None
        if actual_value == 0 or actual_value is None:
            logger.debug(f"Field '{field}' evaluation - actual_value: {actual_value}, insights keys: {list(insights.keys()) if insights else 'empty'}")
            if insights:
                logger.debug(f"Insights data for field '{field}': spend={insights.get('spend')}, impressions={insights.get('impressions')}, clicks={insights.get('clicks')}, actions={insights.get('actions')}")

        if actual_value is not None:
            expected_value = float(expected_value)
            if operator == ">":
                evaluation["passed"] = actual_value > expected_value
            elif operator == ">=":
                evaluation["passed"] = actual_value >= expected_value
            elif operator == "<":
                evaluation["passed"] = actual_value < expected_value
            elif operator == "<=":
                evaluation["passed"] = actual_value <= expected_value
            elif operator == "=":
                evaluation["passed"] = abs(actual_value - expected_value) < 0.01  # Float comparison
            elif operator == "!=":
                evaluation["passed"] = abs(actual_value - expected_value) >= 0.01

    return evaluation["passed"], evaluation


def send_slack_notification(webhook_url: str, rule_name: str, action_type: str, result: Dict) -> bool:
    """
    Send a Slack notification about an action execution result.

    Args:
        webhook_url: Slack webhook URL
        rule_name: Name of the rule that triggered the action
        action_type: Type of action (set_status, adjust_daily_budget)
        result: Action result dictionary with success, message, item_name, etc.

    Returns:
        bool: True if notification was sent successfully, False otherwise
    """
    if not webhook_url:
        return False

    try:
        # Determine color based on success
        color = "good" if result.get("success") else "danger"

        # Build message text
        status_emoji = "✅" if result.get("success") else "❌"
        item_name = result.get("item_name", "Unknown")
        message = result.get("message", "")

        # Format action type for display
        action_display = action_type.replace("_", " ").title()
        if action_type == "set_status":
            action_display = f"Set Status: {result.get('message', '')}"
        elif action_type == "adjust_daily_budget":
            old_budget = result.get("old_budget")
            new_budget = result.get("new_budget")
            if old_budget is not None and new_budget is not None:
                action_display = f"Budget Adjusted: ${old_budget:.2f} → ${new_budget:.2f}"
        elif action_type == "send_notification":
            action_display = "Notification: Rule conditions met"

        # Create Slack message payload
        payload = {
            "attachments": [
                {
                    "color": color,
                    "title": f"{status_emoji} Rule Action Executed: {rule_name}",
                    "fields": [
                        {
                            "title": "Item",
                            "value": item_name,
                            "short": True
                        },
                        {
                            "title": "Item ID",
                            "value": result.get("item_id", "N/A"),
                            "short": True
                        },
                        {
                            "title": "Action",
                            "value": action_display,
                            "short": False
                        },
                        {
                            "title": "Status",
                            "value": "Success" if result.get("success") else "Failed",
                            "short": True
                        }
                    ],
                    "footer": "PFM Marketing Automation",
                    "ts": int(time.time())
                }
            ]
        }

        # Add error field if action failed
        if not result.get("success") and result.get("error"):
            payload["attachments"][0]["fields"].append({
                "title": "Error",
                "value": result.get("error", "Unknown error")[:500],  # Limit error length
                "short": False
            })

        # Send to Slack
        response = requests.post(webhook_url, json=payload, timeout=10)
        response.raise_for_status()
        logger.info(f"Slack notification sent successfully for action on {item_name}")
        return True

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send Slack notification: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending Slack notification: {str(e)}", exc_info=True)
        return False


def execute_action(account_id: str, access_token: str, rule_level: str, items: List[Dict], action: Dict, slack_webhook_url: str = None, rule_name: str = None) -> List[Dict]:
    """
    Execute an action on items via Meta API.
    Returns a list of action results with success/failure status.
    """
    action_type = action.get("type")
    results = []
    base_url = "https://graph.facebook.com/v21.0"

    for index, item in enumerate(items):
        item_id = item.get("id")
        item_name = item.get("name", "Unknown")
        result = {
            "item_id": item_id,
            "item_name": item_name,
            "action_type": action_type,
            "success": False,
            "message": "",
            "error": None
        }

        try:
            if action_type == "set_status":
                status = action.get("status", "PAUSED")
                url = f"{base_url}/{item_id}"
                params = {
                    "status": status,
                    "access_token": access_token
                }
                response = requests.post(url, params=params, timeout=30)
                response.raise_for_status()
                result["success"] = True
                result["message"] = f"Status set to {status}"
                logger.info(f"Successfully set status to {status} for {rule_level} {item_id}")

            elif action_type == "adjust_daily_budget":
                # Get current budget first
                if rule_level == "ad_set":
                    # Fetch current adset to get daily_budget
                    url = f"{base_url}/{item_id}"
                    params = {"fields": "daily_budget", "access_token": access_token}
                    get_response = requests.get(url, params=params, timeout=30)
                    get_response.raise_for_status()
                    adset_data = get_response.json()
                    current_budget = float(adset_data.get("daily_budget", 0)) / 100  # Convert cents to dollars

                    # Calculate new budget
                    direction = action.get("direction", "increase")
                    percent = float(action.get("percent", 0))
                    min_cap = action.get("min_cap")
                    max_cap = action.get("max_cap")

                    if direction == "increase":
                        new_budget = current_budget * (1 + percent / 100)
                        # Check if increase would exceed max cap - if so, skip the action
                        if max_cap is not None and new_budget > float(max_cap):
                            result["success"] = False
                            result["message"] = f"Budget increase would exceed max cap (${max_cap:.2f}). Current: ${current_budget:.2f}, Would be: ${new_budget:.2f}. Action skipped."
                            result["old_budget"] = current_budget
                            result["new_budget"] = current_budget
                            logger.info(f"Skipping budget increase for adset {item_id}: would exceed max cap ${max_cap:.2f} (current: ${current_budget:.2f}, would be: ${new_budget:.2f})")
                        else:
                            # Update budget (in cents)
                            url = f"{base_url}/{item_id}"
                            params = {
                                "daily_budget": int(new_budget * 100),
                                "access_token": access_token
                            }
                            response = requests.post(url, params=params, timeout=30)
                            response.raise_for_status()
                            result["success"] = True
                            result["message"] = f"Budget adjusted from ${current_budget:.2f} to ${new_budget:.2f}"
                            result["old_budget"] = current_budget
                            result["new_budget"] = new_budget
                            logger.info(f"Successfully adjusted budget for adset {item_id}: ${current_budget:.2f} -> ${new_budget:.2f}")
                    else:  # decrease
                        new_budget = current_budget * (1 - percent / 100)
                        # Check if decrease would go below min cap - if so, skip the action
                        if min_cap is not None and new_budget < float(min_cap):
                            result["success"] = False
                            result["message"] = f"Budget decrease would go below min cap (${min_cap:.2f}). Current: ${current_budget:.2f}, Would be: ${new_budget:.2f}. Action skipped."
                            result["old_budget"] = current_budget
                            result["new_budget"] = current_budget
                            logger.info(f"Skipping budget decrease for adset {item_id}: would go below min cap ${min_cap:.2f} (current: ${current_budget:.2f}, would be: ${new_budget:.2f})")
                        else:
                            # Update budget (in cents)
                            url = f"{base_url}/{item_id}"
                            params = {
                                "daily_budget": int(new_budget * 100),
                                "access_token": access_token
                            }
                            response = requests.post(url, params=params, timeout=30)
                            response.raise_for_status()
                            result["success"] = True
                            result["message"] = f"Budget adjusted from ${current_budget:.2f} to ${new_budget:.2f}"
                            result["old_budget"] = current_budget
                            result["new_budget"] = new_budget
                            logger.info(f"Successfully adjusted budget for adset {item_id}: ${current_budget:.2f} -> ${new_budget:.2f}")
                else:
                    result["success"] = False
                    result["message"] = "Budget adjustment only available for ad sets"
                    result["error"] = "Invalid rule level for budget adjustment"
                    logger.warning(f"Budget adjustment attempted on {rule_level} {item_id}, but only ad sets support budget adjustment")

            elif action_type == "send_notification":
                # Send notification action - no API call, just notification
                result["success"] = True
                result["message"] = "Notification sent (no changes made)"
                logger.info(f"Send notification action for {rule_level} {item_id}: {item_name}")

            else:
                result["success"] = False
                result["message"] = f"Unknown action type: {action_type}"
                result["error"] = f"Unsupported action type: {action_type}"
                logger.warning(f"Unknown action type: {action_type}")

        except requests.exceptions.RequestException as e:
            result["success"] = False
            error_msg = str(e)
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    error_msg = error_data.get("error", {}).get("message", error_msg)
                except:
                    error_msg = e.response.text or error_msg
            result["error"] = error_msg
            result["message"] = f"Failed to execute action: {error_msg}"
            logger.error(f"Error executing action {action_type} on {rule_level} {item_id}: {error_msg}")
        except Exception as e:
            result["success"] = False
            result["error"] = str(e)
            result["message"] = f"Unexpected error: {str(e)}"
            logger.error(f"Unexpected error executing action {action_type} on {rule_level} {item_id}: {str(e)}", exc_info=True)

        results.append(result)

        # Send Slack notification if enabled and webhook URL is provided
        send_notification = action.get("send_slack_notification", True)  # Default to True if not specified
        if send_notification and slack_webhook_url and rule_name:
            # For send_notification action, customize the message
            if action_type == "send_notification":
                # Create a custom result for notification-only actions
                notification_result = result.copy()
                notification_result["message"] = f"Rule conditions met for {item_name}"
                send_slack_notification(slack_webhook_url, rule_name, action_type, notification_result)
            else:
                send_slack_notification(slack_webhook_url, rule_name, action_type, result)

        # Add delay between API calls to avoid rate limiting (except after the last item)
        if index < len(items) - 1:
            time.sleep(1.0)  # 1 second delay between calls to prevent rate limiting
            logger.debug(f"Waiting 1 second before processing next item to avoid rate limiting")

    return results


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

    try:
        # Step 1: Fetch data from Facebook API
        logger.info(f"Fetching {rule_level} data for rule {rule_id}")
        all_data = fetch_facebook_data(account_id, access_token, rule_level)
        log_details["data_fetch"] = {
            "total_items": len(all_data),
            "items": all_data[:10]  # Log first 10 for reference
        }

        # Step 2: Apply scope filters
        filtered_data = apply_scope_filters(all_data, scope_filters, rule_level, account_id, access_token)
        log_details["filtered_data"] = [
            {
                "id": item.get("id"),
                "name": item.get("name"),
                "status": item.get("status"),
                "effective_status": item.get("effective_status")
            }
            for item in filtered_data
        ]

        # Step 3: Fetch insights for filtered items
        filtered_ids = [item.get("id") for item in filtered_data]
        logger.info(f"Fetching insights for {len(filtered_ids)} filtered {rule_level} items")
        insights_data = fetch_insights(account_id, access_token, rule_level, filtered_ids, time_range)
        # Log insights summary
        insights_with_data = sum(1 for v in insights_data.values() if v and len(v) > 0)
        logger.info(f"Insights fetched: {insights_with_data} items have data out of {len(insights_data)} total")
        log_details["insights_summary"] = {
            "total_items": len(insights_data),
            "items_with_data": insights_with_data,
            "sample_insights": {k: v for k, v in list(insights_data.items())[:3]}  # First 3 for debugging
        }

        # Step 4: Pre-fetch campaign statuses if needed (for ad/ad_set levels with campaign_status conditions)
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

        # Step 5: Evaluate conditions for each item
        items_meeting_conditions = []

        for item in filtered_data:
            item_id = item.get("id")
            insights = insights_data.get(item_id, {})

            item_evaluation = {
                "item_id": item_id,
                "item_name": item.get("name"),
                "conditions_evaluated": [],
                "all_conditions_met": False
            }

            # Evaluate all conditions
            all_passed = True
            for condition in rule_conditions:
                passed, evaluation = evaluate_condition(item, insights, condition, campaign_status_cache)
                item_evaluation["conditions_evaluated"].append(evaluation)
                if not passed:
                    all_passed = False

            item_evaluation["all_conditions_met"] = all_passed
            log_details["evaluations"].append(item_evaluation)

            if all_passed:
                items_meeting_conditions.append(item)

        # Step 6: Determine decision
        decision = "proceed" if len(items_meeting_conditions) > 0 else "skip"
        log_details["decision"] = decision
        log_details["items_meeting_conditions_count"] = len(items_meeting_conditions)
        log_details["items_meeting_conditions"] = [
            {"id": item.get("id"), "name": item.get("name")}
            for item in items_meeting_conditions
        ]

        # Step 7: Execute actions if conditions are met
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

        log_details["actions_executed"] = actions_executed

        # Step 7: Log results
        if actions_executed:
            success_count = sum(1 for a in actions_executed if a.get("success", False))
            message = f"Executed actions on {success_count}/{len(actions_executed)} item(s). {len(items_meeting_conditions)} item(s) met all conditions."
        else:
            message = f"Test completed: {len(items_meeting_conditions)} item(s) meet all conditions"
        status = "success" if decision == "proceed" else "skipped"

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

