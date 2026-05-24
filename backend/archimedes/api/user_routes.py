"""User profile API — optional profile keyed by wallet address.

Endpoints:
  GET  /api/user/profile/{wallet}   — retrieve profile (404 if not set)
  POST /api/user/profile             — create or update profile

Wallet IS the identity. No auth, no sessions, no tokens.
"""

from __future__ import annotations

import json
import logging

from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session

from archimedes.api.user_schemas import UserProfileCreate, UserProfileResponse
from archimedes.db import get_session
from archimedes.models.user_profile import UserProfile

logger = logging.getLogger(__name__)

user_router = APIRouter(prefix="/api/user", tags=["user"])


def _profile_to_response(p: UserProfile) -> UserProfileResponse:
    interests = json.loads(p.interests) if p.interests else None
    return UserProfileResponse(
        wallet_address=p.wallet_address,
        display_name=p.display_name,
        email=p.email,
        interests=interests,
        attribution=p.attribution,
        marketing_opt_in=p.marketing_opt_in,
    )


@user_router.get("/profile/{wallet}", response_model=UserProfileResponse)
async def get_profile(wallet: str):
    """Retrieve a wallet's profile. Returns 404 if not set."""
    session: Session = get_session()
    try:
        profile = session.query(UserProfile).filter(
            UserProfile.wallet_address == wallet.lower()
        ).first()
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        return _profile_to_response(profile)
    finally:
        session.close()


@user_router.post("/profile", response_model=UserProfileResponse)
async def upsert_profile(payload: UserProfileCreate):
    """Create or update a wallet's profile. All fields optional except wallet."""
    session: Session = get_session()
    try:
        wallet = payload.wallet_address.lower()
        profile = session.query(UserProfile).filter(
            UserProfile.wallet_address == wallet
        ).first()

        interests_json = json.dumps(payload.interests) if payload.interests else "[]"

        if profile:
            # Update existing
            if payload.display_name is not None:
                profile.display_name = payload.display_name
            if payload.email is not None:
                profile.email = payload.email
            profile.interests = interests_json
            if payload.attribution is not None:
                profile.attribution = payload.attribution
            profile.marketing_opt_in = payload.marketing_opt_in
        else:
            # Create new
            profile = UserProfile(
                wallet_address=wallet,
                display_name=payload.display_name,
                email=payload.email,
                interests=interests_json,
                attribution=payload.attribution,
                marketing_opt_in=payload.marketing_opt_in,
            )
            session.add(profile)

        session.commit()
        session.refresh(profile)
        return _profile_to_response(profile)
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        logger.error("upsert_profile failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()
