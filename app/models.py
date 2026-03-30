"""
Modelos de base de datos
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from .database import Base


class Link(Base):
    __tablename__ = "links"

    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String(100), unique=True, index=True, nullable=False)
    target_url = Column(Text, nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, default="")
    category = Column(String(100), default="general")
    is_active = Column(Boolean, default=True)
    click_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_clicked_at = Column(DateTime, nullable=True)

    clicks = relationship("Click", back_populates="link", cascade="all, delete-orphan")


class Click(Base):
    __tablename__ = "clicks"

    id = Column(Integer, primary_key=True, index=True)
    link_id = Column(Integer, ForeignKey("links.id"), nullable=False)
    ip = Column(String(50), default="")
    user_agent = Column(Text, default="")
    referer = Column(Text, default="")
    clicked_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    link = relationship("Link", back_populates="clicks")
