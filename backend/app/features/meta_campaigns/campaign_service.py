import requests
from typing import List
from app.features.meta_campaigns import campaign_schemas, models
from sqlalchemy.orm import Session
import logging
import time
import json

logger = logging.getLogger(__name__)

# API call delays to prevent rate limiting
READ_DELAY = 0.3  # Delay between read API calls (300ms)


def check_rate_limit_headers(response: requests.Response, api_type: str = "read"):
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
    """
    rate_limit_headers = {
        "X-App-Usage": response.headers.get("X-App-Usage"),
        "X-Ad-Account-Usage": response.headers.get("X-Ad-Account-Usage"),
        "X-Business-Use-Case-Usage": response.headers.get("X-Business-Use-Case-Usage")
    }

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
                    for account_id, usage_list in usage_data.items():
                        if isinstance(usage_list, list) and len(usage_list) > 0:
                            for usage_item in usage_list:
                                if isinstance(usage_item, dict):
                                    bc_call_count = usage_item.get("call_count", 0)
                                    bc_total_time = usage_item.get("total_time", 0)

                                    # Warn if usage is high
                                    if bc_call_count > 80 or bc_total_time > 80:
                                        warnings.append(f"{header_name} ({account_id}): call_count={bc_call_count}, total_time={bc_total_time}")

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


def test_meta_connection(ad_account_id: str, access_token: str) -> bool:
    """
    Test connection to Meta API by fetching a small chunk of campaigns (10).
    Only fetches the first page with no pagination to verify credentials work.

    Args:
        ad_account_id: Meta Ad Account ID (e.g., "act_123456789")
        access_token: Meta Access Token

    Returns:
        True if connection is successful, raises Exception otherwise
    """
    if not ad_account_id or not access_token:
        raise ValueError("Ad Account ID and Access Token are required")

    # Make a simple API call to test the connection
    # Fetch 10 campaigns from the first page only (no pagination)
    url = f"https://graph.facebook.com/v21.0/{ad_account_id}/campaigns"
    params = {
        "fields": "id,name,status,effective_status",
        "limit": 10,
        "access_token": access_token
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        check_rate_limit_headers(response, "read")
        data = response.json()
        campaigns = data.get("data", [])
        logger.info(f"Connection test successful: fetched {len(campaigns)} campaigns (first page only)")
        # If we get here, the connection works
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Connection test failed for ad account {ad_account_id}: {str(e)}")
        raise Exception(f"Failed to connect to Meta API: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error testing connection: {str(e)}")
        raise


def fetch_campaigns_from_meta(
    ad_account_id: str,
    access_token: str,
    limit: int = 2000
) -> campaign_schemas.CampaignsResponse:
    """
    Fetch all campaigns from Meta Graph API with pagination support.
    Loads all campaigns across multiple pages.

    Args:
        ad_account_id: Meta Ad Account ID (e.g., "act_123456789")
        access_token: Meta Access Token
        limit: Number of campaigns per page (default: 2000, max: 5000) - using 2000 to minimize API calls

    Returns:
        CampaignsResponse with list of all campaigns
    """
    if not ad_account_id or not access_token:
        raise ValueError("Ad Account ID and Access Token are required")

    all_campaigns = []
    url = f"https://graph.facebook.com/v21.0/{ad_account_id}/campaigns"
    params = {
        "fields": "id,name,status,effective_status",
        "limit": limit,
        "access_token": access_token
    }

    try:
        page_count = 0
        using_next_url = False
        while True:
            page_count += 1
            logger.info(f"Fetching campaigns page {page_count}...")

            if using_next_url:
                response = requests.get(url, timeout=30)
            else:
                response = requests.get(url, params=params, timeout=30)

            response.raise_for_status()
            check_rate_limit_headers(response, "read")
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
            logger.debug(f"Waiting {READ_DELAY}s before fetching next page to avoid rate limiting")

        logger.info(f"Fetched all campaigns: {len(all_campaigns)} total across {page_count} page(s)")
        return campaign_schemas.CampaignsResponse(data=all_campaigns, paging=None)
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching campaigns from Meta API: {str(e)}")
        raise Exception(f"Failed to fetch campaigns from Meta API: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error fetching campaigns: {str(e)}")
        raise


def get_campaigns_for_ad_account(
    db: Session,
    ad_account_id: int
) -> campaign_schemas.CampaignsResponse:
    """
    Get campaigns for an ad account using its Meta credentials

    Args:
        db: Database session
        ad_account_id: Ad Account ID

    Returns:
        CampaignsResponse with list of campaigns
    """
    account = db.query(models.AdAccount).filter(
        models.AdAccount.id == ad_account_id
    ).first()

    if not account:
        raise ValueError("Ad account not found")

    if not account.meta_account_id:
        raise ValueError("Ad account does not have a Meta Account ID configured")

    if not account.meta_access_token:
        raise ValueError("Ad account does not have a Meta Access Token configured")

    return fetch_campaigns_from_meta(
        ad_account_id=account.meta_account_id,
        access_token=account.meta_access_token
    )


def fetch_ad_sets_from_meta(
    ad_account_id: str,
    access_token: str,
    campaign_id: str,
    limit: int = 2000
) -> dict:
    """
    Fetch all ad sets for a campaign from Meta Graph API with pagination support.
    Loads all ad sets across multiple pages.

    Args:
        ad_account_id: Meta Ad Account ID (e.g., "act_123456789")
        access_token: Meta Access Token
        campaign_id: Campaign ID
        limit: Number of ad sets per page (default: 2000, max: 5000) - using 2000 to minimize API calls

    Returns:
        Dict with list of all ad sets
    """
    if not ad_account_id or not access_token or not campaign_id:
        raise ValueError("Ad Account ID, Access Token, and Campaign ID are required")

    all_ad_sets = []
    url = f"https://graph.facebook.com/v21.0/{campaign_id}/adsets"
    params = {
        "fields": "id,name,campaign_id,status,effective_status,daily_budget,lifetime_budget",
        "limit": limit,
        "access_token": access_token
    }

    try:
        page_count = 0
        using_next_url = False
        while True:
            page_count += 1
            logger.info(f"Fetching ad sets page {page_count} for campaign {campaign_id}...")

            if using_next_url:
                response = requests.get(url, timeout=30)
            else:
                response = requests.get(url, params=params, timeout=30)

            response.raise_for_status()
            check_rate_limit_headers(response, "read")
            data = response.json()
            page_ad_sets = data.get("data", [])
            all_ad_sets.extend(page_ad_sets)

            paging = data.get("paging", {})
            next_url = paging.get("next")

            if not next_url:
                break

            url = next_url
            using_next_url = True
            time.sleep(READ_DELAY)
            logger.debug(f"Waiting {READ_DELAY}s before fetching next page to avoid rate limiting")

        logger.info(f"Fetched all ad sets: {len(all_ad_sets)} total across {page_count} page(s)")
        return {"data": all_ad_sets, "paging": None}
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching ad sets from Meta API: {str(e)}")
        raise Exception(f"Failed to fetch ad sets from Meta API: {str(e)}")


def fetch_ads_from_meta(
    ad_account_id: str,
    access_token: str,
    ad_set_id: str,
    limit: int = 2000
) -> dict:
    """
    Fetch all ads for an ad set from Meta Graph API with pagination support.
    Loads all ads across multiple pages.

    Args:
        ad_account_id: Meta Ad Account ID (e.g., "act_123456789")
        access_token: Meta Access Token
        ad_set_id: Ad Set ID
        limit: Number of ads per page (default: 2000, max: 5000) - using 2000 to minimize API calls

    Returns:
        Dict with list of all ads
    """
    if not ad_account_id or not access_token or not ad_set_id:
        raise ValueError("Ad Account ID, Access Token, and Ad Set ID are required")

    all_ads = []
    url = f"https://graph.facebook.com/v21.0/{ad_set_id}/ads"
    params = {
        "fields": "id,name,adset_id,campaign_id,status,effective_status",
        "limit": limit,
        "access_token": access_token
    }

    try:
        page_count = 0
        using_next_url = False
        while True:
            page_count += 1
            logger.info(f"Fetching ads page {page_count} for ad set {ad_set_id}...")

            if using_next_url:
                response = requests.get(url, timeout=30)
            else:
                response = requests.get(url, params=params, timeout=30)

            response.raise_for_status()
            check_rate_limit_headers(response, "read")
            data = response.json()
            page_ads = data.get("data", [])
            all_ads.extend(page_ads)

            paging = data.get("paging", {})
            next_url = paging.get("next")

            if not next_url:
                break

            url = next_url
            using_next_url = True
            time.sleep(READ_DELAY)
            logger.debug(f"Waiting {READ_DELAY}s before fetching next page to avoid rate limiting")

        logger.info(f"Fetched all ads: {len(all_ads)} total across {page_count} page(s)")
        return {"data": all_ads, "paging": None}
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching ads from Meta API: {str(e)}")
        raise Exception(f"Failed to fetch ads from Meta API: {str(e)}")

