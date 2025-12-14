from sqlalchemy.orm import Session
from app.features.meta_campaigns import models, schemas
from datetime import datetime, timedelta
import requests
import logging
import time
import json
from typing import Dict, List, Any, Tuple
from urllib.parse import quote, urlparse, parse_qs, urlencode, urlunparse

logger = logging.getLogger(__name__)

# API call delays to prevent rate limiting
READ_DELAY = 0.3  # Delay between read API calls (300ms)
WRITE_DELAY = 0.7  # Delay between write API calls (700ms)
INSIGHTS_DELAY = 1.0  # Delay between insights API calls (1s)

# Rate limit tracking - store last N readings per account
_rate_limit_history = {}  # {account_id: [{"timestamp": time, "usage": {...}}, ...]}
_MAX_HISTORY = 10  # Keep last 10 readings per account


def track_rate_limit_usage(account_id: str, rate_limit_headers: dict, api_type: str = "read"):
    """
    Track rate limit usage over time to understand call frequency and avoid blocking.

    Args:
        account_id: Ad account ID for tracking
        rate_limit_headers: Dict of rate limit headers
        api_type: Type of API call
    """
    global _rate_limit_history

    if not account_id:
        return

    current_time = time.time()
    current_usage = {}

    # Extract key metrics from headers
    for header_name, header_value in rate_limit_headers.items():
        if header_value:
            try:
                usage_data = json.loads(header_value)
                if isinstance(usage_data, dict):
                    # Extract key metrics
                    metrics = {
                        "call_count": usage_data.get("call_count", 0),
                        "total_time": usage_data.get("total_time", 0),
                        "total_cputime": usage_data.get("total_cputime", 0),
                        "acc_id_util_pct": usage_data.get("acc_id_util_pct", None),
                        "reset_time_duration": usage_data.get("reset_time_duration", None),
                        "ads_api_access_tier": usage_data.get("ads_api_access_tier", None)
                    }
                    current_usage[header_name] = metrics
            except (json.JSONDecodeError, ValueError):
                pass

    if not current_usage:
        return

    # Initialize history for this account if needed
    if account_id not in _rate_limit_history:
        _rate_limit_history[account_id] = []

    # Add current reading
    _rate_limit_history[account_id].append({
        "timestamp": current_time,
        "usage": current_usage
    })

    # Keep only last N readings
    if len(_rate_limit_history[account_id]) > _MAX_HISTORY:
        _rate_limit_history[account_id] = _rate_limit_history[account_id][-_MAX_HISTORY:]

    # Analyze trends if we have at least 2 readings
    history = _rate_limit_history[account_id]
    if len(history) >= 2:
        prev_reading = history[-2]
        curr_reading = history[-1]
        time_diff = curr_reading["timestamp"] - prev_reading["timestamp"]

        if time_diff > 0:
            # Analyze each header
            for header_name in current_usage:
                if header_name in prev_reading["usage"]:
                    prev_metrics = prev_reading["usage"][header_name]
                    curr_metrics = curr_reading["usage"][header_name]

                    # Track call_count increase rate
                    prev_calls = prev_metrics.get("call_count", 0)
                    curr_calls = curr_metrics.get("call_count", 0)
                    if curr_calls > prev_calls:
                        calls_per_second = (curr_calls - prev_calls) / time_diff
                        logger.info(f"[RATE_LIMIT_TRACK] {header_name} - Call count: {prev_calls} → {curr_calls} (+{curr_calls - prev_calls}) in {time_diff:.2f}s = {calls_per_second:.2f} calls/sec")

                    # Track total_time increase rate
                    prev_time = prev_metrics.get("total_time", 0)
                    curr_time = curr_metrics.get("total_time", 0)
                    if curr_time > prev_time:
                        time_per_second = (curr_time - prev_time) / time_diff
                        logger.info(f"[RATE_LIMIT_TRACK] {header_name} - Total time: {prev_time} → {curr_time} (+{curr_time - prev_time}) in {time_diff:.2f}s = {time_per_second:.2f} time units/sec")

                    # Track acc_id_util_pct if available
                    prev_pct = prev_metrics.get("acc_id_util_pct")
                    curr_pct = curr_metrics.get("acc_id_util_pct")
                    if prev_pct is not None and curr_pct is not None:
                        pct_change = curr_pct - prev_pct
                        pct_per_second = pct_change / time_diff if time_diff > 0 else 0
                        logger.info(f"[RATE_LIMIT_TRACK] {header_name} - Usage %: {prev_pct}% → {curr_pct}% ({pct_change:+.1f}%) in {time_diff:.2f}s = {pct_per_second:.2f}%/sec")

                        # Calculate time until 100% if trend continues
                        if pct_per_second > 0 and curr_pct < 100:
                            time_to_limit = (100 - curr_pct) / pct_per_second
                            logger.warning(f"[RATE_LIMIT_TRACK] ⚠️ {header_name} - At current rate ({pct_per_second:.2f}%/sec), will hit 100% in {time_to_limit:.1f} seconds ({time_to_limit/60:.1f} minutes)")

                        # Warn if approaching limits
                        if curr_pct >= 90:
                            logger.error(f"[RATE_LIMIT_TRACK] 🚨 {header_name} - CRITICAL: Usage at {curr_pct}% - Very close to limit!")
                        elif curr_pct >= 80:
                            logger.warning(f"[RATE_LIMIT_TRACK] ⚠️ {header_name} - WARNING: Usage at {curr_pct}% - Approaching limit")

                    # Check reset_time_duration if available
                    reset_duration = curr_metrics.get("reset_time_duration")
                    if reset_duration and reset_duration > 0:
                        logger.info(f"[RATE_LIMIT_TRACK] {header_name} - Reset time duration: {reset_duration} seconds ({reset_duration/60:.1f} minutes)")


def check_rate_limit_headers(response: requests.Response, api_type: str = "read", account_id: str = None):
    """
    Check and log Meta API rate limiting headers to monitor usage.

    Meta API provides these headers:
    - X-App-Usage: App-level rate limiting
    - X-Ad-Account-Usage: Ad account-level rate limiting
    - X-Business-Use-Case-Usage: Business use case rate limiting

    Each header contains JSON like: {"call_count": 100, "total_time": 20, "total_cputime": 20}

    Args:
        response: requests.Response object from Meta API
        api_type: Type of API call ("read", "write", "insights")
        account_id: Optional account ID for tracking trends
    """
    rate_limit_headers = {
        "X-App-Usage": response.headers.get("X-App-Usage"),
        "X-Ad-Account-Usage": response.headers.get("X-Ad-Account-Usage"),
        "X-Business-Use-Case-Usage": response.headers.get("X-Business-Use-Case-Usage")
    }

    # Track usage trends if account_id provided
    if account_id:
        track_rate_limit_usage(account_id, rate_limit_headers, api_type)

    # Only log if we have rate limit headers
    if any(rate_limit_headers.values()):
        usage_info = {}
        for header_name, header_value in rate_limit_headers.items():
            if header_value:
                try:
                    usage_data = json.loads(header_value)
                    usage_info[header_name] = usage_data
                except (json.JSONDecodeError, ValueError):
                    usage_info[header_name] = header_value

        # Check if we're getting close to limits (usually 80%+ is concerning)
        warnings = []
        for header_name, usage_data in usage_info.items():
            if isinstance(usage_data, dict):
                # Meta API typically uses call_count and total_time
                call_count = usage_data.get("call_count", 0)
                total_time = usage_data.get("total_time", 0)

                # Check for acc_id_util_pct in X-Ad-Account-Usage (percentage usage, 0-100)
                util_pct = usage_data.get("acc_id_util_pct", 0)

                # Handle X-Business-Use-Case-Usage which has nested structure
                if header_name == "X-Business-Use-Case-Usage" and isinstance(usage_data, dict):
                    # This header has account IDs as keys, with arrays of usage data
                    for account_id_key, usage_list in usage_data.items():
                        if isinstance(usage_list, list) and len(usage_list) > 0:
                            for usage_item in usage_list:
                                if isinstance(usage_item, dict):
                                    bc_call_count = usage_item.get("call_count", 0)
                                    bc_total_time = usage_item.get("total_time", 0)

                                    # Warn if usage is high
                                    if bc_call_count > 80 or bc_total_time > 80:
                                        warnings.append(f"{header_name} ({account_id_key}): call_count={bc_call_count}, total_time={bc_total_time}")

                # Warn if usage seems high
                # Meta API typically has limits around 100 for call_count/total_time
                # For acc_id_util_pct, 80%+ is concerning
                if util_pct > 0 and util_pct >= 80:
                    warnings.append(f"{header_name}: acc_id_util_pct={util_pct}%")
                elif call_count > 80 or total_time > 80:
                    warnings.append(f"{header_name}: call_count={call_count}, total_time={total_time}")

        if warnings:
            logger.warning(f"[RATE_LIMIT] ⚠️ HIGH USAGE WARNING ({api_type}): {'; '.join(warnings)}")

    return rate_limit_headers


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


def fetch_facebook_data(account_id: str, access_token: str, rule_level: str, limit: int = None, scope_filters: Dict[str, Any] = None):
    """
    Fetch all campaigns, adsets, or ads from Facebook API with pagination support.
    Loads all items across multiple pages, not just the first page.
    This is critical for rules to ensure they can filter/execute on all items, not just the first page.

    Args:
        account_id: Meta Ad Account ID (e.g., "act_123456789")
        access_token: Meta Access Token
        rule_level: Level to fetch - "campaign", "ad_set", or "ad"
        limit: Number of items per page (None = use defaults: 3000 for ads, 2000 for others)
        scope_filters: Optional scope filters to apply at API level (e.g., campaign_ids)

    Returns:
        List of all items (campaigns, ad sets, or ads)
    """
    base_url = "https://graph.facebook.com/v21.0"

    # Ensure account_id has 'act_' prefix
    if not account_id.startswith("act_"):
        account_id = f"act_{account_id}"

    # Use higher limit for ads (3000) to reduce number of API calls
    if limit is None:
        if rule_level == "ad":
            limit = 3000
        else:
            limit = 2000

    if rule_level == "ad":
        endpoint = f"{base_url}/{account_id}/ads"
        # Reduced fields to avoid "Please reduce the amount of data" error from Facebook API
        # Only include fields actually used in rule evaluation and filtering
        fields = "id,name,adset_id,campaign_id,status,effective_status"
        # Filter out archived and deleted ads, but keep paused ads (needed for reactivation rules)
        # Using effective_status to filter out ARCHIVED and DELETED, but keep ACTIVE, PAUSED, etc.
        filtering = '[{"field":"effective_status","operator":"NOT_IN","value":["ARCHIVED","DELETED"]}]'
    elif rule_level == "ad_set":
        endpoint = f"{base_url}/{account_id}/adsets"
        fields = "id,name,campaign_id,status,effective_status,daily_budget,lifetime_budget"
        # Filter out archived and deleted ad sets, but keep paused
        filtering = '[{"field":"effective_status","operator":"NOT_IN","value":["ARCHIVED","DELETED"]}]'
    else:  # campaign
        endpoint = f"{base_url}/{account_id}/campaigns"
        fields = "id,name,status,effective_status"
        # Filter out archived and deleted campaigns, but keep paused
        filtering = '[{"field":"effective_status","operator":"NOT_IN","value":["ARCHIVED","DELETED"]}]'

    # Add campaign_ids filter to API request if provided in scope_filters
    if scope_filters and "campaign_ids" in scope_filters and scope_filters["campaign_ids"]:
        campaign_ids = scope_filters["campaign_ids"]
        # Convert string to list if needed
        if isinstance(campaign_ids, str):
            campaign_ids = [id_val.strip() for id_val in campaign_ids.replace("\n", ",").split(",") if id_val.strip()]

        if isinstance(campaign_ids, list) and campaign_ids:
            # Parse existing filtering JSON
            try:
                filter_list = json.loads(filtering)
            except json.JSONDecodeError:
                filter_list = []

            # Determine the field name based on rule level
            if rule_level == "campaign":
                # For campaigns, filter by id field
                filter_field = "id"
            else:
                # For ads and ad sets, filter by campaign.id field
                filter_field = "campaign.id"

            # Add campaign_ids filter
            campaign_filter = {
                "field": filter_field,
                "operator": "IN",
                "value": campaign_ids
            }
            filter_list.append(campaign_filter)

            # Convert back to JSON string
            filtering = json.dumps(filter_list)
            logger.info(f"[FETCH] Added campaign_ids filter to API request: {len(campaign_ids)} campaign(s) - {campaign_ids[:5]}{'...' if len(campaign_ids) > 5 else ''}")

    all_items = []
    # Add filtering parameter to exclude archived/deleted items (URL-encode the JSON filter)
    filtering_encoded = quote(filtering)
    url = f"{endpoint}?fields={fields}&limit={limit}&filtering={filtering_encoded}&access_token={access_token}"

    try:
        page_count = 0
        start_time = time.time()
        logger.info(f"[FETCH] Starting to fetch {rule_level} data for account {account_id} with limit={limit} (excluding ARCHIVED and DELETED)")

        while True:
            page_count += 1
            page_start_time = time.time()
            logger.info(f"[FETCH] Fetching {rule_level} page {page_count} for account {account_id}... (URL: {endpoint})")

            response = requests.get(url, timeout=30)
            request_time = time.time() - page_start_time

            # Check for rate limiting errors before raising
            if response.status_code == 400:
                try:
                    error_data = response.json()
                    error_info = error_data.get("error", {})
                    error_code = error_info.get("code")
                    error_subcode = error_info.get("error_subcode")
                    error_message = error_info.get("message", "")
                    error_type = error_info.get("type", "")

                    logger.error(f"[FETCH] Facebook API error - Code: {error_code}, Subcode: {error_subcode}, Type: {error_type}, Message: {error_message}")

                    # Check if it's a rate limit error (code 17 or subcode 2446079)
                    if error_code == 17 or error_subcode == 2446079 or "too many" in error_message.lower() or "rate limit" in error_message.lower():
                        logger.error(f"[FETCH] Rate limit detected! Total pages fetched before error: {page_count - 1}, Total items: {len(all_items)}")
                        raise Exception(f"Facebook API rate limit reached: {error_message}. Please wait a few minutes and try again.")
                except (ValueError, KeyError):
                    pass  # If we can't parse the error, let raise_for_status handle it

            response.raise_for_status()

            # Check and log rate limit headers in detail
            rate_limit_headers = {
                "X-App-Usage": response.headers.get("X-App-Usage"),
                "X-Ad-Account-Usage": response.headers.get("X-Ad-Account-Usage"),
                "X-Business-Use-Case-Usage": response.headers.get("X-Business-Use-Case-Usage")
            }

            # Log rate limit headers if present
            if any(rate_limit_headers.values()):
                logger.info(f"[FETCH] Rate limit headers received for page {page_count}:")
                for header_name, header_value in rate_limit_headers.items():
                    if header_value:
                        try:
                            usage_data = json.loads(header_value)
                            logger.info(f"[FETCH]   {header_name}: {json.dumps(usage_data, indent=2)}")

                            # Extract and log key metrics
                            if isinstance(usage_data, dict):
                                call_count = usage_data.get("call_count", 0)
                                total_time = usage_data.get("total_time", 0)
                                total_cputime = usage_data.get("total_cputime", 0)
                                acc_id_util_pct = usage_data.get("acc_id_util_pct", None)

                                if acc_id_util_pct is not None:
                                    logger.info(f"[FETCH]     → Ad Account Usage: {acc_id_util_pct}%")
                                if call_count > 0:
                                    logger.info(f"[FETCH]     → Call Count: {call_count}")
                                if total_time > 0:
                                    logger.info(f"[FETCH]     → Total Time: {total_time}")
                                if total_cputime > 0:
                                    logger.info(f"[FETCH]     → Total CPU Time: {total_cputime}")

                                # Special handling for X-Business-Use-Case-Usage
                                if header_name == "X-Business-Use-Case-Usage":
                                    for account_id, usage_list in usage_data.items():
                                        if isinstance(usage_list, list):
                                            logger.info(f"[FETCH]     → Business Use Case Usage for {account_id}:")
                                            for idx, usage_item in enumerate(usage_list):
                                                if isinstance(usage_item, dict):
                                                    logger.info(f"[FETCH]       [{idx}] {json.dumps(usage_item, indent=2)}")
                        except (json.JSONDecodeError, ValueError):
                            logger.info(f"[FETCH]   {header_name}: {header_value} (raw)")
                    else:
                        logger.debug(f"[FETCH]   {header_name}: not present")

            # Also call the existing check function for warnings and tracking
            check_rate_limit_headers(response, "read", account_id=account_id)

            data = response.json()
            page_items = data.get("data", [])
            all_items.extend(page_items)

            page_elapsed = time.time() - page_start_time
            logger.info(f"[FETCH] Page {page_count} completed in {page_elapsed:.2f}s - Fetched {len(page_items)} items (total: {len(all_items)})")

            paging = data.get("paging", {})
            next_url = paging.get("next")

            if not next_url:
                logger.info(f"[FETCH] No more pages - reached end of data")
                break

            # Ensure filtering parameter is preserved in next_url
            # Facebook's next_url might not include our filtering parameter
            try:
                parsed = urlparse(next_url)
                query_params = parse_qs(parsed.query)

                # Check if filtering is already in the URL
                if 'filtering' not in query_params:
                    # Add our filtering parameter to preserve it across pagination
                    query_params['filtering'] = [filtering_encoded]
                    # Reconstruct the URL with filtering
                    new_query = urlencode(query_params, doseq=True)
                    next_url = urlunparse((
                        parsed.scheme,
                        parsed.netloc,
                        parsed.path,
                        parsed.params,
                        new_query,
                        parsed.fragment
                    ))
                    logger.debug(f"[FETCH] Added filtering parameter to next_url for page {page_count + 1}")
            except Exception as e:
                logger.warning(f"[FETCH] Could not parse/modify next_url: {e}. Using next_url as-is.")
                # If parsing fails, try to append filtering manually
                separator = '&' if '?' in next_url else '?'
                next_url = f"{next_url}{separator}filtering={filtering_encoded}"

            url = next_url

            # Use 0.5s delay for all rule levels
            delay = 0.5
            logger.info(f"[FETCH] Waiting {delay:.2f}s before fetching next {rule_level} page to avoid rate limiting...")
            time.sleep(delay)

        total_elapsed = time.time() - start_time
        logger.info(f"[FETCH] Completed fetching {rule_level} data for account {account_id}: {len(all_items)} total items across {page_count} page(s) in {total_elapsed:.2f}s")
        if all_items and len(all_items) > 0:
            # Log sample item to verify fields are present
            sample_item = all_items[0]
            logger.info(f"[FETCH] Sample {rule_level} item fields: {list(sample_item.keys())}")
            if rule_level == "ad":
                logger.info(f"[FETCH] Sample ad - id: {sample_item.get('id')}, name: {sample_item.get('name')}")
            # Log sample names for debugging
            sample_names = [item.get("name", "N/A") for item in all_items[:10]]
            logger.info(f"[FETCH] Sample {rule_level} names (first 10): {sample_names}")
        else:
            logger.warning(f"[FETCH] No {rule_level} items found for account {account_id}")
        return all_items
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching Facebook data: {str(e)}")
        if hasattr(e, 'response') and e.response is not None and hasattr(e.response, 'text'):
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
    total_batches = (len(ids) + batch_size - 1) // batch_size
    insights_start_time = time.time()
    logger.info(f"[TIMING] Fetching insights for {len(ids)} IDs in {total_batches} batch(es)...")

    for i in range(0, len(ids), batch_size):
        batch_ids = ids[i:i + batch_size]
        batch_num = (i // batch_size) + 1
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
        logger.info(f"[TIMING] Fetching insights batch {batch_num}/{total_batches}: level={level}, time_range={time_range_str}, batch_size={len(batch_ids)}")

        try:
            batch_start_time = time.time()
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            check_rate_limit_headers(response, "insights", account_id=account_id)
            data = response.json()
            batch_elapsed = time.time() - batch_start_time
            logger.info(f"[TIMING] Insights batch {batch_num}/{total_batches} completed in {batch_elapsed:.2f} seconds - {len(batch_ids)} IDs, got {len(data.get('data', []))} insights")
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

            # Add delay between batches (except after the last batch)
            if batch_num < total_batches:
                time.sleep(INSIGHTS_DELAY)
                logger.debug(f"Waiting {INSIGHTS_DELAY}s before fetching next insights batch to avoid rate limiting")
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching insights batch: {str(e)}")
            if hasattr(e, 'response') and e.response is not None and hasattr(e.response, 'text'):
                logger.error(f"Response: {e.response.text}")
            # Mark all batch items as having no insights
            for obj_id in batch_ids:
                if obj_id not in insights_data:
                    insights_data[obj_id] = {}

    total_elapsed = time.time() - insights_start_time
    logger.info(f"[TIMING] Total insights fetch completed in {total_elapsed:.2f} seconds for {len(ids)} IDs across {total_batches} batch(es)")

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
                logger.info(f"Applying campaign_name_contains filter at campaign level: {len(filtered_data)} items before filter")
                filtered_data = [
                    item for item in filtered_data
                    if any(keyword.lower() in item.get("name", "").lower() for keyword in keywords)
                ]
                logger.info(f"After campaign_name_contains filter: {len(filtered_data)} items remaining")
                if filtered_data:
                    sample_names = [item.get("name", "N/A") for item in filtered_data[:5]]
                    logger.info(f"Sample matching campaign names: {sample_names}")
            else:
                # For ad/adset level, fetch campaigns by name, then filter by campaign_id
                if account_id and access_token:
                    try:
                        filter_start_time = time.time()
                        logger.info(f"Fetching campaigns for campaign_name_contains filter (keywords: {keywords})...")
                        # Fetch campaigns and filter by name with pagination
                        base_url = "https://graph.facebook.com/v21.0"
                        if not account_id.startswith("act_"):
                            account_id_formatted = f"act_{account_id}"
                        else:
                            account_id_formatted = account_id

                        all_campaigns = []
                        url = f"{base_url}/{account_id_formatted}/campaigns"
                        params = {
                            "fields": "id,name",
                            "limit": 2000,  # Use 2000 to minimize API calls
                            "access_token": access_token
                        }
                        using_next_url = False
                        page_count = 0
                        while True:
                            page_count += 1
                            if using_next_url:
                                response = requests.get(url, timeout=30)
                            else:
                                response = requests.get(url, params=params, timeout=30)
                            response.raise_for_status()
                            check_rate_limit_headers(response, "read", account_id=account_id)

                            data = response.json()
                            page_campaigns = data.get("data", [])
                            all_campaigns.extend(page_campaigns)

                            paging = data.get("paging", {})
                            next_url = paging.get("next")

                            if not next_url:
                                break

                            url = next_url
                            using_next_url = True
                            time.sleep(READ_DELAY)

                        filter_elapsed = time.time() - filter_start_time
                        logger.info(f"[TIMING] Campaign fetch for campaign_name_contains filter took {filter_elapsed:.2f} seconds")
                        logger.info(f"Fetched all campaigns: {len(all_campaigns)} total across {page_count} page(s)")

                        # Filter campaigns by name keywords
                        matching_campaign_ids = [
                            str(campaign.get("id"))
                            for campaign in all_campaigns
                            if any(keyword.lower() in campaign.get("name", "").lower() for keyword in keywords)
                        ]
                        logger.info(f"Found {len(matching_campaign_ids)} campaigns matching campaign_name_contains (keywords: {keywords})")
                        if matching_campaign_ids:
                            logger.debug(f"Matching campaign IDs: {matching_campaign_ids[:10]}")  # Log first 10

                        # Filter ads/adsets by matching campaign IDs
                        logger.info(f"Filtering {rule_level} items by campaign_id: {len(filtered_data)} items before filter")
                        if matching_campaign_ids:
                            filtered_data = [
                                item for item in filtered_data
                                if str(item.get("campaign_id", "")) in matching_campaign_ids
                            ]
                            logger.info(f"After campaign_name_contains filter: {len(filtered_data)} items remaining")
                            if filtered_data:
                                sample_names = [item.get("name", "N/A") for item in filtered_data[:5]]
                                logger.info(f"Sample matching {rule_level} names: {sample_names}")
                        else:
                            # No campaigns match, so no ads/adsets match
                            logger.info("No campaigns match, so no ads/adsets match")
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
                check_rate_limit_headers(response, "write", account_id=account_id)
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
                    check_rate_limit_headers(get_response, "read", account_id=account_id)
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
                            check_rate_limit_headers(response, "write")
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
                            check_rate_limit_headers(response, "write")
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
            time.sleep(WRITE_DELAY)
            logger.debug(f"Waiting {WRITE_DELAY}s before processing next item to avoid rate limiting")

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

    total_start_time = time.time()
    logger.info(f"[TIMING] === Starting rule execution: rule_id={rule_id} (rule: {rule.name}) ===")

    try:
        # Step 1: Fetch data from Facebook API
        step_start_time = time.time()
        logger.info(f"[TIMING] Step 1 - Fetching {rule_level} data for rule {rule_id} (rule: {rule.name})")
        all_data = fetch_facebook_data(account_id, access_token, rule_level, scope_filters=scope_filters)
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

        # Step 3: Fetch insights for filtered items
        step_start_time = time.time()
        logger.info(f"[TIMING] Step 3 - Fetching insights for {len(filtered_data)} filtered {rule_level} items")
        filtered_ids = [item.get("id") for item in filtered_data]
        logger.info(f"Fetching insights for {len(filtered_ids)} filtered {rule_level} items")
        insights_data = fetch_insights(account_id, access_token, rule_level, filtered_ids, time_range)
        step_elapsed = time.time() - step_start_time
        # Log insights summary
        insights_with_data = sum(1 for v in insights_data.values() if v and len(v) > 0)
        logger.info(f"[TIMING] Step 3 completed in {step_elapsed:.2f} seconds - Insights fetched: {insights_with_data} items have data out of {len(insights_data)} total")
        log_details["insights_summary"] = {
            "total_items": len(insights_data),
            "items_with_data": insights_with_data,
            "sample_insights": {k: v for k, v in list(insights_data.items())[:3]}  # First 3 for debugging
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

