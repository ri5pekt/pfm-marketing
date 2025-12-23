import requests
import logging
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any
from urllib.parse import quote, urlparse, parse_qs, urlencode, urlunparse
from app.features.meta_campaigns.rate_limit_tracker import check_rate_limit_headers

logger = logging.getLogger(__name__)

# API call delays to prevent rate limiting
READ_DELAY = 0.3  # Delay between read API calls (300ms)
WRITE_DELAY = 0.7  # Delay between write API calls (700ms)
INSIGHTS_DELAY = 1.0  # Delay between insights API calls (1s)


def _safe_float_any(value, default=0.0) -> float:
    if value is None or value == "":
        return default
    try:
        return float(str(value).replace(",", "").replace("$", ""))
    except (ValueError, TypeError):
        return default


def _pick_canonical_purchase_action_value(items, preferred_types):
    """
    Meta often returns multiple overlapping purchase action_type variants.
    This helper returns (value, chosen_action_type, by_type_dict) considering only action_types containing 'purchase'.
    """
    by_type = {}
    if isinstance(items, list):
        for it in items:
            if isinstance(it, dict):
                at = it.get("action_type")
                if not at:
                    continue
                at_str = str(at)
                if "purchase" not in at_str.lower():
                    continue
                by_type[at_str] = _safe_float_any(it.get("value"), 0.0)

    for t in preferred_types:
        if t in by_type:
            return by_type[t], t, by_type
    if by_type:
        first_key = sorted(by_type.keys())[0]
        return by_type[first_key], first_key, by_type
    return 0.0, "none", by_type


def fetch_facebook_data(
    account_id: str,
    access_token: str,
    rule_level: str,
    limit: int = None,
    scope_filters: Dict[str, Any] = None,
    effective_status_in: List[str] | None = None,
):
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

    # If rule conditions include an explicit status filter, apply it at API level to reduce payload.
    # We use effective_status because it is filterable and matches the statuses used in the UI (ACTIVE/PAUSED/etc.).
    if effective_status_in:
        try:
            filter_list = json.loads(filtering)
        except json.JSONDecodeError:
            filter_list = []
        status_filter = {
            "field": "effective_status",
            "operator": "IN",
            "value": [str(s) for s in effective_status_in if s],
        }
        if status_filter["value"]:
            filter_list.append(status_filter)
            filtering = json.dumps(filter_list)
            logger.info(f"[FETCH] Added effective_status IN filter to API request: {status_filter['value']}")

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
    # NOTE:
    # - Meta does not provide a direct "AOV" metric; we derive it when needed from purchase value / purchase count.
    # - For "Media Margin Volume" we need both purchase count and purchase value.
    # - Use action_values (purchase) to derive purchase value. (Meta may show "purchase conversion value" in UI,
    #   but it is not a valid Insights field to request directly in v21.0.)
    fields = "campaign_id,adset_id,ad_id,spend,impressions,clicks,cpc,cpm,ctr,actions,action_values,cost_per_action_type"

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
        filtering_obj = [{"field": filter_field, "operator": "IN", "value": batch_ids}]

        # IMPORTANT: pass JSON params via requests params so they're properly URL-encoded
        params = {
            "level": level,
            "fields": fields,
            "time_range": time_range_str,
            "filtering": json.dumps(filtering_obj),
            # Add action_breakdowns parameter to get cost_per_action_type properly populated
            "action_breakdowns": "action_type",
            "access_token": access_token,
        }

        logger.info(
            f"[TIMING] Fetching insights batch {batch_num}/{total_batches}: level={level}, time_range={time_range_str}, batch_size={len(batch_ids)}"
        )

        try:
            batch_start_time = time.time()
            response = requests.get(endpoint, params=params, timeout=60)
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
                # Log purchase-related fields for debugging ROAS/revenue signals
                av = first_insight.get("action_values") or []
                purchase_value_dbg = 0
                if isinstance(av, list):
                    for x in av:
                        if isinstance(x, dict) and "purchase" in (x.get("action_type") or "").lower():
                            purchase_value_dbg += float(str(x.get("value", 0)).replace(",", "").replace("$", "") or 0)
                logger.info(f"Purchase value (from action_values purchase sum): {purchase_value_dbg}")
                # Log cost_per_action_type if present
                if "cost_per_action_type" in first_insight:
                    logger.info(f"cost_per_action_type sample: {first_insight.get('cost_per_action_type')}")
                else:
                    logger.warning(f"cost_per_action_type not found in insights response. Available fields: {list(first_insight.keys())}")
                # Log actions array for purchase data
                if "actions" in first_insight:
                    purchase_actions = [a for a in first_insight.get("actions", []) if isinstance(a, dict) and "purchase" in a.get("action_type", "").lower()]
                    if purchase_actions:
                        logger.info(f"Purchase actions found: {purchase_actions}")
                    else:
                        logger.info(f"Actions array: {first_insight.get('actions')}")
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


def fetch_daily_insights(account_id: str, access_token: str, rule_level: str, ids: List[str], time_range: Dict[str, Any]):
    """Fetch daily insights (broken down by day) for the given IDs and time range

    This is used for metrics that need day-by-day data, like CPP Winning Days.
    """
    base_url = "https://graph.facebook.com/v21.0"

    # Ensure account_id has 'act_' prefix
    if not account_id.startswith("act_"):
        account_id = f"act_{account_id}"

    # Build time range string
    time_range_str = build_time_range_string(time_range)

    # Fields to fetch - same as regular insights but we'll break down by day
    fields = "campaign_id,adset_id,ad_id,spend,impressions,clicks,actions,action_values,cost_per_action_type,date_start,date_stop"

    if rule_level == "ad":
        level = "ad"
    elif rule_level == "ad_set":
        level = "adset"
    else:
        level = "campaign"

    endpoint = f"{base_url}/{account_id}/insights"
    daily_insights_data = {}

    # Fetch insights in batches (Facebook API supports up to 50 IDs per request)
    batch_size = 50
    total_batches = (len(ids) + batch_size - 1) // batch_size
    logger.info(f"[TIMING] Fetching daily insights for {len(ids)} IDs in {total_batches} batch(es)...")

    for i in range(0, len(ids), batch_size):
        batch_ids = ids[i:i + batch_size]
        batch_num = (i // batch_size) + 1

        # Build filtering JSON string
        if level == "ad":
            filter_field = "ad.id"
        elif level == "adset":
            filter_field = "adset.id"
        else:  # campaign
            filter_field = "campaign.id"
        filtering_obj = [{"field": filter_field, "operator": "IN", "value": batch_ids}]

        # IMPORTANT: Add time_increment=1 to get daily breakdown
        params = {
            "level": level,
            "fields": fields,
            "time_range": time_range_str,
            "time_increment": "1",  # Daily breakdown
            "filtering": json.dumps(filtering_obj),
            "action_breakdowns": "action_type",
            "access_token": access_token,
        }

        logger.info(
            f"[TIMING] Fetching daily insights batch {batch_num}/{total_batches}: level={level}, time_range={time_range_str}, batch_size={len(batch_ids)}"
        )

        try:
            batch_start_time = time.time()
            response = requests.get(endpoint, params=params, timeout=60)
            response.raise_for_status()
            check_rate_limit_headers(response, "insights", account_id=account_id)
            data = response.json()
            batch_elapsed = time.time() - batch_start_time
            logger.info(f"[TIMING] Daily insights batch {batch_num}/{total_batches} completed in {batch_elapsed:.2f} seconds")

            if data.get("data"):
                for insight in data["data"]:
                    item_id = insight.get(level + "_id") or insight.get("id")
                    if not item_id:
                        continue

                    # Store daily insights as a list (one entry per day)
                    if item_id not in daily_insights_data:
                        daily_insights_data[item_id] = []
                    daily_insights_data[item_id].append(insight)

            # Rate limiting delay
            time.sleep(INSIGHTS_DELAY)

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching daily insights batch {batch_num}: {str(e)}")
            # Continue with other batches even if one fails
            continue

    logger.info(f"[TIMING] Fetched daily insights for {len(daily_insights_data)} items")
    return daily_insights_data


def fetch_ads_for_item(
    account_id: str,
    access_token: str,
    item_id: str,
    item_type: str,  # "campaign" or "adset"
) -> List[Dict]:
    """
    Fetch ads for a specific campaign or adset.

    Args:
        account_id: Meta Ad Account ID
        access_token: Meta Access Token
        item_id: Campaign ID or Adset ID
        item_type: "campaign" or "adset"

    Returns:
        List of ads with their status information
    """
    base_url = "https://graph.facebook.com/v21.0"

    # Ensure account_id has 'act_' prefix
    if not account_id.startswith("act_"):
        account_id = f"act_{account_id}"

    # Build endpoint based on item type
    if item_type == "campaign":
        endpoint = f"{base_url}/{item_id}/ads"
    elif item_type == "adset":
        endpoint = f"{base_url}/{item_id}/ads"
    else:
        logger.error(f"Invalid item_type for fetch_ads_for_item: {item_type}")
        return []

    fields = "id,name,status,effective_status"
    params = {
        "fields": fields,
        "access_token": access_token,
        "limit": 5000,  # High limit to get all ads
    }

    all_ads = []
    try:
        while True:
            response = requests.get(endpoint, params=params, timeout=60)
            response.raise_for_status()
            check_rate_limit_headers(response, "read", account_id=account_id)
            data = response.json()

            if data.get("data"):
                all_ads.extend(data["data"])

            # Check for pagination
            paging = data.get("paging")
            if paging and paging.get("next"):
                # Extract cursor from next URL
                next_url = paging.get("next")
                parsed = urlparse(next_url)
                query_params = parse_qs(parsed.query)
                if "after" in query_params:
                    params["after"] = query_params["after"][0]
                else:
                    break
            else:
                break

            time.sleep(READ_DELAY)

        logger.info(f"Fetched {len(all_ads)} ads for {item_type} {item_id}")
        return all_ads

    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching ads for {item_type} {item_id}: {e}")
        return []


def build_time_range_string(time_range: Dict[str, Any]) -> str:
    """Build Facebook API time_range parameter

    Note: Facebook API includes both start and end dates, so for N days we subtract (N-1) days
    to get exactly N days of data.
    """
    unit = time_range.get("unit", "days")
    amount = time_range.get("amount", 1)
    exclude_today = time_range.get("exclude_today", True)

    # Handle "today" unit - from 00:00 today to now
    if unit == "today":
        start_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        end_time = datetime.now()
        # Format as JSON string for Facebook API
        logger.debug(f"Time range (today only): {start_time.strftime('%Y-%m-%d')} to {end_time.strftime('%Y-%m-%d')}")
        return f"{{\"since\":\"{start_time.strftime('%Y-%m-%d')}\",\"until\":\"{end_time.strftime('%Y-%m-%d')}\"}}"

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

