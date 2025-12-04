from pydantic import BaseModel
from typing import Optional, List


class Campaign(BaseModel):
    id: str
    name: str
    status: str
    effective_status: str

    class Config:
        from_attributes = True


class CampaignsResponse(BaseModel):
    data: List[Campaign]
    paging: Optional[dict] = None

