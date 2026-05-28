from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class AppSettingRead(BaseModel):
    id: int
    title: str
    primary_color: str
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AppSettingUpdate(BaseModel):
    title: Optional[str] = None
    primary_color: Optional[str] = None
