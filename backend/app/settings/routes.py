from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.dependencies import get_current_active_user, get_current_admin_user
from app.auth.models import User
from app.settings import service
from app.settings.schemas import AppSettingRead, AppSettingUpdate

router = APIRouter()


@router.get("", response_model=AppSettingRead)
def read_settings(db: Session = Depends(get_db)):
    return service.get_settings(db)


@router.put("", response_model=AppSettingRead)
def write_settings(
    data: AppSettingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    return service.update_settings(db, data)
