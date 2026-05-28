from sqlalchemy.orm import Session
from app.settings.models import AppSetting
from app.settings.schemas import AppSettingUpdate


DEFAULT_TITLE = "PFM Marketing"
DEFAULT_PRIMARY_COLOR = "#0099ff"


def get_settings(db: Session) -> AppSetting:
    setting = db.query(AppSetting).first()
    if not setting:
        setting = AppSetting(title=DEFAULT_TITLE, primary_color=DEFAULT_PRIMARY_COLOR)
        db.add(setting)
        db.commit()
        db.refresh(setting)
    return setting


def update_settings(db: Session, data: AppSettingUpdate) -> AppSetting:
    setting = get_settings(db)
    if data.title is not None:
        setting.title = data.title
    if data.primary_color is not None:
        setting.primary_color = data.primary_color
    db.commit()
    db.refresh(setting)
    return setting


def seed_default_settings(db: Session) -> None:
    """Create default settings row if none exists."""
    existing = db.query(AppSetting).first()
    if not existing:
        setting = AppSetting(title=DEFAULT_TITLE, primary_color=DEFAULT_PRIMARY_COLOR)
        db.add(setting)
        db.commit()
