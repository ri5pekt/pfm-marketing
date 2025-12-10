import requests
from typing import List
from app.features.meta_campaigns import campaign_schemas, models
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)


def fetch_campaigns_from_meta(
    ad_account_id: str,
    access_token: str,
    limit: int = 100
) -> campaign_schemas.CampaignsResponse:
    """
    Fetch campaigns from Meta Graph API

    Args:
        ad_account_id: Meta Ad Account ID (e.g., "act_123456789")
        access_token: Meta Access Token
        limit: Maximum number of campaigns to fetch (default: 100)

    Returns:
        CampaignsResponse with list of campaigns
    """
    if not ad_account_id or not access_token:
        raise ValueError("Ad Account ID and Access Token are required")

    url = f"https://graph.facebook.com/v21.0/{ad_account_id}/campaigns"
    params = {
        "fields": "id,name,status,effective_status",
        "limit": limit,
        "access_token": access_token
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()

        data = response.json()
        return campaign_schemas.CampaignsResponse(**data)
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
    limit: int = 100
) -> dict:
    """
    Fetch ad sets for a campaign from Meta Graph API

    Args:
        ad_account_id: Meta Ad Account ID (e.g., "act_123456789")
        access_token: Meta Access Token
        campaign_id: Campaign ID
        limit: Maximum number of ad sets to fetch (default: 100)

    Returns:
        Dict with list of ad sets
    """
    if not ad_account_id or not access_token or not campaign_id:
        raise ValueError("Ad Account ID, Access Token, and Campaign ID are required")

    url = f"https://graph.facebook.com/v21.0/{campaign_id}/adsets"
    params = {
        "fields": "id,name,campaign_id,status,effective_status,daily_budget,lifetime_budget",
        "limit": limit,
        "access_token": access_token
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching ad sets from Meta API: {str(e)}")
        raise Exception(f"Failed to fetch ad sets from Meta API: {str(e)}")


def fetch_ads_from_meta(
    ad_account_id: str,
    access_token: str,
    ad_set_id: str,
    limit: int = 100
) -> dict:
    """
    Fetch ads for an ad set from Meta Graph API

    Args:
        ad_account_id: Meta Ad Account ID (e.g., "act_123456789")
        access_token: Meta Access Token
        ad_set_id: Ad Set ID
        limit: Maximum number of ads to fetch (default: 100)

    Returns:
        Dict with list of ads
    """
    if not ad_account_id or not access_token or not ad_set_id:
        raise ValueError("Ad Account ID, Access Token, and Ad Set ID are required")

    url = f"https://graph.facebook.com/v21.0/{ad_set_id}/ads"
    params = {
        "fields": "id,name,adset_id,campaign_id,status,effective_status",
        "limit": limit,
        "access_token": access_token
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching ads from Meta API: {str(e)}")
        raise Exception(f"Failed to fetch ads from Meta API: {str(e)}")

