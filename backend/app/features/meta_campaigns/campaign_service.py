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


def get_campaigns_for_business_account(
    db: Session,
    business_account_id: int
) -> campaign_schemas.CampaignsResponse:
    """
    Get campaigns for a business account using its Meta credentials

    Args:
        db: Database session
        business_account_id: Business Account ID

    Returns:
        CampaignsResponse with list of campaigns
    """
    account = db.query(models.BusinessAccount).filter(
        models.BusinessAccount.id == business_account_id
    ).first()

    if not account:
        raise ValueError("Business account not found")

    if not account.meta_account_id:
        raise ValueError("Business account does not have a Meta Account ID configured")

    if not account.meta_access_token:
        raise ValueError("Business account does not have a Meta Access Token configured")

    return fetch_campaigns_from_meta(
        ad_account_id=account.meta_account_id,
        access_token=account.meta_access_token
    )

