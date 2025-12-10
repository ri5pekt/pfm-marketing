from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.dependencies import get_current_active_user
from app.auth.models import User
from app.features.meta_campaigns import business_account_schemas, business_account_service
from app.features.meta_campaigns import campaign_service, campaign_schemas

router = APIRouter(prefix="/business-accounts", tags=["business-accounts"])


@router.get("", response_model=list[business_account_schemas.BusinessAccount])
def get_business_accounts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all business accounts"""
    return business_account_service.get_all_business_accounts(db)


@router.get("/default", response_model=business_account_schemas.BusinessAccount)
def get_default_business_account(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get the default business account"""
    account = business_account_service.get_default_business_account(db)
    if not account:
        raise HTTPException(status_code=404, detail="No default business account found")
    return account


@router.post("", response_model=business_account_schemas.BusinessAccount)
def create_business_account(
    account_data: business_account_schemas.BusinessAccountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new business account"""
    return business_account_service.create_business_account(db, account_data)


@router.get("/{account_id}", response_model=business_account_schemas.BusinessAccount)
def get_business_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific business account"""
    account = business_account_service.get_business_account(db, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Business account not found")
    return account


@router.put("/{account_id}", response_model=business_account_schemas.BusinessAccount)
def update_business_account(
    account_id: int,
    account_data: business_account_schemas.BusinessAccountUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update a business account"""
    account = business_account_service.update_business_account(db, account_id, account_data)
    if not account:
        raise HTTPException(status_code=404, detail="Business account not found")
    return account


@router.delete("/{account_id}")
def delete_business_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a business account"""
    success = business_account_service.delete_business_account(db, account_id)
    if not success:
        raise HTTPException(status_code=404, detail="Business account not found")
    return {"message": "Business account deleted successfully"}


@router.get("/{account_id}/campaigns", response_model=campaign_schemas.CampaignsResponse)
def get_business_account_campaigns(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get campaigns for a business account from Meta API"""
    try:
        return campaign_service.get_campaigns_for_business_account(db, account_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{account_id}/test-connection")
def test_business_account_connection(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Test the connection to Meta API for a business account"""
    try:
        result = business_account_service.test_business_account_connection(db, account_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

