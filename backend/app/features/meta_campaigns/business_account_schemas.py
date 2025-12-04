from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class BusinessAccountBase(BaseModel):
    name: str
    description: Optional[str] = None
    meta_account_id: Optional[str] = None
    meta_access_token: Optional[str] = None
    is_default: bool = False


class BusinessAccountCreate(BusinessAccountBase):
    pass


class BusinessAccountUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    meta_account_id: Optional[str] = None
    meta_access_token: Optional[str] = None
    is_default: Optional[bool] = None


class BusinessAccount(BusinessAccountBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

