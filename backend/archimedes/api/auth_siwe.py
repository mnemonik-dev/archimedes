"""SIWE (Sign-In with Ethereum) session authentication — EIP-4361.

Implements wallet-signature-based auth so the X-Wallet-Address header
is no longer trusted. Users prove wallet ownership by signing a nonce;
the backend verifies the signature and issues a session cookie.

Endpoints:
  GET  /api/auth/nonce          — request a challenge nonce
  POST /api/auth/verify         — submit signed message → session cookie
  POST /api/auth/logout         — clear session cookie

Session middleware:
  get_verified_wallet(request)  — extract wallet from session cookie
                                  Returns None if not authenticated.

References:
  - EIP-4361: https://eips.ethereum.org/EIPS/eip-4361
  - eth_account: https://eth-account.readthedocs.io/
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import secrets
import time

from fastapi import APIRouter, HTTPException, Request, Response

logger = logging.getLogger(__name__)

auth_router = APIRouter(prefix="/api/auth", tags=["auth"])

# Session signing key — derived from EMAIL_ENCRYPTION_KEY or a random per-boot key.
# In production, EMAIL_ENCRYPTION_KEY is required (fail-closed in main.py), so
# sessions persist across restarts. In dev, a random key means sessions reset on restart.
_SESSION_SECRET = os.getenv("EMAIL_ENCRYPTION_KEY", secrets.token_hex(32))
_SESSION_TTL_SECONDS = 24 * 60 * 60  # 24 hours
_NONCE_TTL_SECONDS = 300  # 5 minutes

# In-memory nonce store. Production would use Redis, but for the hackathon
# this is sufficient — nonces are short-lived (5 min TTL) and single-use.
_pending_nonces: dict[str, float] = {}  # nonce → expiry timestamp

_COOKIE_NAME = "archimedes_session"


def _sign_session(wallet: str, issued_at: float) -> str:
    """Create an HMAC-signed session token."""
    payload = json.dumps({"wallet": wallet.lower(), "iat": issued_at})
    sig = hmac.new(_SESSION_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
    # Base64 would be cleaner but hex+json is simpler to debug
    return f"{payload}|{sig}"


def _verify_session(token: str) -> str | None:
    """Verify session token and return wallet address, or None if invalid."""
    try:
        payload_str, sig = token.rsplit("|", 1)
        expected = hmac.new(_SESSION_SECRET.encode(), payload_str.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected):
            return None
        payload = json.loads(payload_str)
        if time.time() - payload["iat"] > _SESSION_TTL_SECONDS:
            return None  # expired
        return payload["wallet"]
    except Exception:
        return None


def get_verified_wallet(request: Request) -> str | None:
    """Extract the authenticated wallet address from the session cookie.

    Returns the lowercase wallet address if the session is valid, None otherwise.
    This replaces the old X-Wallet-Address header trust model.
    """
    token = request.cookies.get(_COOKIE_NAME)
    if not token:
        return None
    return _verify_session(token)


def require_verified_wallet(request: Request) -> str:
    """FastAPI dependency: require a valid SIWE session. Raises 401 if not authenticated."""
    wallet = get_verified_wallet(request)
    if not wallet:
        raise HTTPException(status_code=401, detail="Authentication required. Connect your wallet and sign in.")
    return wallet


# ── Endpoints ─────────────────────────────────────────────────


@auth_router.get("/nonce")
async def get_nonce():
    """Issue a challenge nonce for SIWE signing."""
    # Clean expired nonces
    now = time.time()
    expired = [n for n, exp in _pending_nonces.items() if exp < now]
    for n in expired:
        del _pending_nonces[n]

    nonce = secrets.token_hex(16)
    _pending_nonces[nonce] = now + _NONCE_TTL_SECONDS

    return {
        "nonce": nonce,
        "domain": os.getenv("PUBLIC_DOMAIN", "https://archimedes-arc.app")
        .replace("https://", "")
        .replace("http://", ""),
        "issued_at": int(now),
        "expiry_seconds": _NONCE_TTL_SECONDS,
    }


@auth_router.post("/verify")
async def verify_signature(request: Request, response: Response):
    """Verify a signed SIWE message and issue a session cookie.

    Body: { "message": "<SIWE message text>", "signature": "0x..." }
    """
    from eth_account import Account
    from eth_account.messages import encode_defunct

    body = await request.json()
    message = body.get("message", "")
    signature = body.get("signature", "")

    if not message or not signature:
        raise HTTPException(status_code=400, detail="message and signature are required")

    # Extract nonce from the message (SIWE format: "Nonce: <value>")
    nonce = None
    wallet_from_message = None
    for line in message.split("\n"):
        line = line.strip()
        if line.startswith("Nonce: "):
            nonce = line[7:].strip()
        if line.startswith("0x") and len(line) == 42:
            wallet_from_message = line.lower()

    if not nonce:
        raise HTTPException(status_code=400, detail="Nonce not found in message")

    # Verify nonce is pending and not expired
    expiry = _pending_nonces.pop(nonce, None)
    if expiry is None:
        raise HTTPException(status_code=401, detail="Nonce not found or already used")
    if time.time() > expiry:
        raise HTTPException(status_code=401, detail="Nonce expired")

    # Recover the signer address from the signature
    try:
        signable = encode_defunct(text=message)
        recovered = Account.recover_message(signable, signature=signature)
        recovered_lower = recovered.lower()
    except Exception as exc:
        logger.warning("SIWE signature recovery failed: %s", exc)
        raise HTTPException(status_code=401, detail="Invalid signature") from exc

    # Verify the recovered address matches the claimed wallet
    if wallet_from_message and recovered_lower != wallet_from_message:
        raise HTTPException(
            status_code=401,
            detail=f"Signature address {recovered_lower} does not match claimed wallet {wallet_from_message}",
        )

    # Issue session cookie
    now = time.time()
    token = _sign_session(recovered_lower, now)

    response.set_cookie(
        key=_COOKIE_NAME,
        value=token,
        httponly=True,  # Not accessible via JavaScript (XSS-safe)
        secure=True,  # HTTPS only
        samesite="strict",  # CSRF protection
        max_age=_SESSION_TTL_SECONDS,
        path="/",
    )

    logger.info("SIWE session issued for wallet %s", recovered_lower[:10])

    return {
        "status": "authenticated",
        "wallet": recovered_lower,
        "expires_in": _SESSION_TTL_SECONDS,
    }


@auth_router.post("/logout")
async def logout(response: Response):
    """Clear the session cookie."""
    response.delete_cookie(key=_COOKIE_NAME, path="/")
    return {"status": "logged_out"}


@auth_router.get("/session")
async def get_session(request: Request):
    """Check current session status."""
    wallet = get_verified_wallet(request)
    if wallet:
        return {"authenticated": True, "wallet": wallet}
    return {"authenticated": False, "wallet": None}
