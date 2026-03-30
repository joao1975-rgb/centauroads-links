"""
Schemas Pydantic — validación de datos de entrada/salida
"""

from pydantic import BaseModel, HttpUrl
from typing import Optional
from datetime import datetime


# ---------------------------------------------------------------------------
# Links
# ---------------------------------------------------------------------------

class LinkCreate(BaseModel):
    slug: str
    target_url: HttpUrl
    name: str
    description: Optional[str] = ""
    category: Optional[str] = "general"


class LinkUpdate(BaseModel):
    target_url: Optional[HttpUrl] = None
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    is_active: Optional[bool] = None


class LinkOut(BaseModel):
    id: int
    slug: str
    target_url: str
    name: str
    description: str
    category: str
    is_active: bool
    click_count: int
    created_at: datetime
    last_clicked_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Clicks / Stats
# ---------------------------------------------------------------------------

class ClickOut(BaseModel):
    id: int
    ip: str
    user_agent: str
    referer: str
    clicked_at: datetime

    class Config:
        from_attributes = True


class LinkStats(BaseModel):
    link: LinkOut
    total_clicks: int
    recent_clicks: list[ClickOut]
