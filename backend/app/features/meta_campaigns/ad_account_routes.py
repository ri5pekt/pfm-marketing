from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.dependencies import get_current_active_user
from app.auth.models import User
from app.features.meta_campaigns import ad_account_schemas, ad_account_service
from app.features.meta_campaigns import campaign_service, campaign_schemas

router = APIRouter(prefix="/ad-accounts", tags=["ad-accounts"])


@router.get("", response_model=list[ad_account_schemas.AdAccount])
def get_ad_accounts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all ad accounts"""
    return ad_account_service.get_all_ad_accounts(db)


@router.get("/default", response_model=ad_account_schemas.AdAccount)
def get_default_ad_account(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get the default ad account"""
    account = ad_account_service.get_default_ad_account(db)
    if not account:
        raise HTTPException(status_code=404, detail="No default ad account found")
    return account


@router.post("", response_model=ad_account_schemas.AdAccount)
def create_ad_account(
    account_data: ad_account_schemas.AdAccountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new ad account"""
    return ad_account_service.create_ad_account(db, account_data)


@router.get("/{account_id}", response_model=ad_account_schemas.AdAccount)
def get_ad_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific ad account"""
    account = ad_account_service.get_ad_account(db, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Ad account not found")
    return account


@router.put("/{account_id}", response_model=ad_account_schemas.AdAccount)
def update_ad_account(
    account_id: int,
    account_data: ad_account_schemas.AdAccountUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update an ad account"""
    account = ad_account_service.update_ad_account(db, account_id, account_data)
    if not account:
        raise HTTPException(status_code=404, detail="Ad account not found")
    return account


@router.delete("/{account_id}")
def delete_ad_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete an ad account"""
    success = ad_account_service.delete_ad_account(db, account_id)
    if not success:
        raise HTTPException(status_code=404, detail="Ad account not found")
    return {"message": "Ad account deleted successfully"}


@router.get("/{account_id}/campaigns", response_model=campaign_schemas.CampaignsResponse)
def get_ad_account_campaigns(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get campaigns for an ad account from Meta API"""
    try:
        return campaign_service.get_campaigns_for_ad_account(db, account_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{account_id}/campaigns/{campaign_id}/adsets")
def get_campaign_ad_sets(
    account_id: int,
    campaign_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get ad sets for a campaign from Meta API"""
    try:
        account = ad_account_service.get_ad_account(db, account_id)
        if not account:
            raise HTTPException(status_code=404, detail="Ad account not found")
        if not account.meta_account_id or not account.meta_access_token:
            raise HTTPException(status_code=400, detail="Ad account credentials not configured")

        result = campaign_service.fetch_ad_sets_from_meta(
            ad_account_id=account.meta_account_id,
            access_token=account.meta_access_token,
            campaign_id=campaign_id
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{account_id}/adsets/{adset_id}/ads")
def get_ad_set_ads(
    account_id: int,
    adset_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get ads for an ad set from Meta API"""
    try:
        account = ad_account_service.get_ad_account(db, account_id)
        if not account:
            raise HTTPException(status_code=404, detail="Ad account not found")
        if not account.meta_account_id or not account.meta_access_token:
            raise HTTPException(status_code=400, detail="Ad account credentials not configured")

        result = campaign_service.fetch_ads_from_meta(
            ad_account_id=account.meta_account_id,
            access_token=account.meta_access_token,
            ad_set_id=adset_id
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{account_id}/test-connection")
def test_ad_account_connection(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Test the connection to Meta API for an ad account"""
    try:
        result = ad_account_service.test_ad_account_connection(db, account_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

