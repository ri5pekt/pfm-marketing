from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any


class RuleBase(BaseModel):
    ad_account_id: int
    name: str
    description: Optional[str] = None
    enabled: bool = True
    schedule_cron: Optional[str] = None  # Cron expression for scheduling (nullable for manual-only rules)
    conditions: Dict[str, Any]  # Rule conditions (JSON)
    actions: Dict[str, Any]  # Actions to take when conditions met (JSON)
    meta_account_id: Optional[str] = None
    meta_access_token: Optional[str] = None


class RuleCreate(RuleBase):
    pass


class RuleUpdate(BaseModel):
    ad_account_id: Optional[int] = None
    name: Optional[str] = None
    description: Optional[str] = None
    enabled: Optional[bool] = None
    schedule_cron: Optional[str] = None
    conditions: Optional[Dict[str, Any]] = None
    actions: Optional[Dict[str, Any]] = None
    meta_account_id: Optional[str] = None
    meta_access_token: Optional[str] = None


class Rule(RuleBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    ad_account_id: int

    class Config:
        from_attributes = True


class RuleLog(BaseModel):
    id: int
    rule_id: int
    status: str  # success, error, skipped
    message: str
    details: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True

