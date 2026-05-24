"""UserProfile — optional wallet-linked profile for personalized UX.

Wallet address is the primary key. All fields are optional.
Created on first POST from the WelcomeProfileModal.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, Boolean, DateTime
from sqlalchemy.orm import Session

from archimedes.models.chat import Base


class UserProfile(Base):
    """Optional profile keyed by wallet address."""

    __tablename__ = "user_profiles"

    wallet_address = Column(String(42), primary_key=True)  # 0x-prefixed EVM address
    display_name = Column(String(128), nullable=True)
    email = Column(String(256), nullable=True)
    interests = Column(Text, nullable=True, default="[]")  # JSON list of strings
    attribution = Column(String(256), nullable=True)
    marketing_opt_in = Column(Boolean, nullable=False, default=False)
    created_at = Column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at = Column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
