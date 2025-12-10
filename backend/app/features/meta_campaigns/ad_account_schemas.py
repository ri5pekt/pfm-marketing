from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class AdAccountBase(BaseModel):
    name: str
    description: Optional[str] = None
    meta_account_id: Optional[str] = None
    meta_access_token: Optional[str] = None
    slack_webhook_url: Optional[str] = None
    is_default: bool = False


class AdAccountCreate(AdAccountBase):
    pass


class AdAccountUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    meta_account_id: Optional[str] = None
    meta_access_token: Optional[str] = None
    slack_webhook_url: Optional[str] = None
    is_default: Optional[bool] = None


class AdAccount(AdAccountBase):
    id: int
    connection_status: Optional[bool] = None
    connection_last_checked: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

