from sqlalchemy.orm import Session
from app.features.meta_campaigns import models
from app.features.meta_campaigns import business_account_schemas
from app.features.meta_campaigns import campaign_service
from datetime import datetime, timedelta, timezone
import logging

logger = logging.getLogger(__name__)


def get_all_business_accounts(db: Session):
    return db.query(models.BusinessAccount).order_by(models.BusinessAccount.is_default.desc(), models.BusinessAccount.name).all()


def get_business_account(db: Session, account_id: int):
    return db.query(models.BusinessAccount).filter(models.BusinessAccount.id == account_id).first()


def get_default_business_account(db: Session):
    return db.query(models.BusinessAccount).filter(models.BusinessAccount.is_default == True).first()


def create_business_account(db: Session, account_data: business_account_schemas.BusinessAccountCreate):
    # If this is set as default, unset other defaults
    if account_data.is_default:
        db.query(models.BusinessAccount).filter(models.BusinessAccount.is_default == True).update({"is_default": False})

    account = models.BusinessAccount(**account_data.model_dump())
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


def update_business_account(db: Session, account_id: int, account_data: business_account_schemas.BusinessAccountUpdate):
    account = db.query(models.BusinessAccount).filter(models.BusinessAccount.id == account_id).first()
    if not account:
        return None

    update_data = account_data.model_dump(exclude_unset=True)

    # If setting as default, unset other defaults
    if update_data.get("is_default") is True:
        db.query(models.BusinessAccount).filter(
            models.BusinessAccount.is_default == True,
            models.BusinessAccount.id != account_id
        ).update({"is_default": False})

    for field, value in update_data.items():
        setattr(account, field, value)

    db.commit()
    db.refresh(account)
    return account


def delete_business_account(db: Session, account_id: int):
    account = db.query(models.BusinessAccount).filter(models.BusinessAccount.id == account_id).first()
    if not account:
        return False

    db.delete(account)
    db.commit()
    return True


def test_business_account_connection(db: Session, account_id: int, cooldown_seconds: int = 30) -> dict:
    """
    Test the connection to Meta API for a business account.
    Implements cooldown to prevent too frequent API calls.

    Args:
        db: Database session
        account_id: Business Account ID
        cooldown_seconds: Minimum seconds between connection tests (default: 30)

    Returns:
        dict with success status, message, and connection status
    """
    account = db.query(models.BusinessAccount).filter(models.BusinessAccount.id == account_id).first()
    if not account:
        raise ValueError("Business account not found")

    # Check cooldown
    now = datetime.now(timezone.utc)
    if account.connection_last_checked:
        # Ensure both datetimes are timezone-aware for comparison
        last_checked = account.connection_last_checked
        if last_checked.tzinfo is None:
            # If stored datetime is naive, assume UTC
            last_checked = last_checked.replace(tzinfo=timezone.utc)
        time_since_last_check = now - last_checked
        if time_since_last_check.total_seconds() < cooldown_seconds:
            remaining_seconds = int(cooldown_seconds - time_since_last_check.total_seconds())
            return {
                "success": False,
                "message": f"Please wait {remaining_seconds} seconds before testing again",
                "connection_status": account.connection_status,
                "connection_last_checked": account.connection_last_checked,
                "cooldown_active": True
            }

    # Validate credentials are present
    if not account.meta_account_id or not account.meta_access_token:
        account.connection_status = False
        account.connection_last_checked = now
        db.commit()
        return {
            "success": False,
            "message": "Meta Account ID or Access Token is missing",
            "connection_status": False,
            "connection_last_checked": account.connection_last_checked
        }

    # Test connection by making a simple API call (no pagination)
    try:
        # Use lightweight test function that only makes one API call
        campaign_service.test_meta_connection(
            ad_account_id=account.meta_account_id,
            access_token=account.meta_access_token
        )

        # Connection successful
        account.connection_status = True
        account.connection_last_checked = now
        db.commit()

        return {
            "success": True,
            "message": "Connection test successful",
            "connection_status": True,
            "connection_last_checked": account.connection_last_checked
        }

    except Exception as e:
        # Connection failed
        error_message = str(e)
        logger.error(f"Connection test failed for business account {account_id}: {error_message}")

        account.connection_status = False
        account.connection_last_checked = now
        db.commit()

        return {
            "success": False,
            "message": f"Connection test failed: {error_message}",
            "connection_status": False,
            "connection_last_checked": account.connection_last_checked
        }

