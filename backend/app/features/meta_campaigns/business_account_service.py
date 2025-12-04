from sqlalchemy.orm import Session
from app.features.meta_campaigns import models
from app.features.meta_campaigns import business_account_schemas


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

