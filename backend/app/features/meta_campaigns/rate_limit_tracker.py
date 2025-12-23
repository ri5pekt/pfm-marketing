import logging
import time
import json
import requests
from typing import Dict, Optional

logger = logging.getLogger(__name__)

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


def check_rate_limit_headers(response: requests.Response, api_type: str = "read", account_id: Optional[str] = None):
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

