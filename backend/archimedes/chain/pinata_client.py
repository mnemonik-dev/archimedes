"""Pinata IPFS client — pins the PUBLIC provenance layer and verifies CIDs.

T1.4: the public provenance trace (papers cited, methodology, rigor / DSR / PBO
scores, timestamp) is pinned to IPFS via Pinata and the returned CID is anchored
on-chain (commit-reveal ``storagePointer``). The EXECUTABLE layer — strategy
weights, position-sizing params, code paths/hashes — is deliberately NOT pinned;
publishing it would leak the alpha. See ``build_public_provenance`` for the split.

Gating (coordinated with T0.5 no-silent-degradation):
  PINATA_JWT — Pinata JWT (scoped `pinJSONToIPFS` key). If unset, every pin/fetch
  degrades LOUDLY: a structured WARN is logged (event=pinata_degraded) and the call
  returns None rather than raising. Callers MUST treat None as "IPFS unavailable"
  and fall back to the on-chain hash anchor — never silently pretend it pinned.

Mock at the HTTP boundary (``aiohttp.ClientSession``) in tests — same convention as
``circle_service`` / ``circle_signer``. No network in unit tests.
"""

from __future__ import annotations

import json
import logging
import os

import aiohttp

logger = logging.getLogger(__name__)

# Pinata REST + public gateway. Pin via the API; fetch via the gateway.
PINATA_API_BASE = "https://api.pinata.cloud"
PINATA_GATEWAY = "https://gateway.pinata.cloud/ipfs"
_PIN_TIMEOUT_S = 30.0


class PinataClient:
    """Pins JSON to IPFS via Pinata and re-fetches it for verification.

    Stateless apart from the JWT; safe to use as a module singleton. All methods
    degrade to None (with a loud WARN) when ``PINATA_JWT`` is unset — they never
    raise on the missing-credential path, so the agent loop keeps running with the
    on-chain hash as the sole anchor.
    """

    def __init__(self, jwt: str | None = None) -> None:
        # Read once at construction so tests can inject; falls back to env.
        self._jwt: str = jwt if jwt is not None else os.getenv("PINATA_JWT", "")

    @property
    def is_configured(self) -> bool:
        return bool(self._jwt)

    def _warn_degraded(self, op: str) -> None:
        """Emit the structured no-silent-degradation WARN (T0.5)."""
        logger.warning(
            "Pinata IPFS unavailable — degrading to on-chain hash only "
            "(event=pinata_degraded op=%s reason=missing_PINATA_JWT)",
            op,
        )

    async def pin_json(self, payload: dict, *, name: str | None = None) -> str | None:
        """Pin a JSON object to IPFS; return its CID (IpfsHash) or None.

        Returns None — never raises — when PINATA_JWT is unset (loud WARN) or when
        the Pinata API errors / is unreachable (error logged). A None return is the
        signal to fall back to the on-chain hash anchor.
        """
        if not self.is_configured:
            self._warn_degraded("pin_json")
            return None

        body: dict = {"pinataContent": payload}
        if name:
            body["pinataMetadata"] = {"name": name}

        try:
            timeout = aiohttp.ClientTimeout(total=_PIN_TIMEOUT_S)
            async with (
                aiohttp.ClientSession(timeout=timeout) as session,
                session.post(
                    f"{PINATA_API_BASE}/pinning/pinJSONToIPFS",
                    json=body,
                    headers={
                        "Authorization": f"Bearer {self._jwt}",
                        "Content-Type": "application/json",
                    },
                ) as resp,
            ):
                data = await resp.json()
                if resp.status != 200:
                    # Don't leak the JWT or full body; log status + safe detail.
                    logger.error(
                        "Pinata pin failed (status=%s detail=%s)",
                        resp.status,
                        data.get("error") if isinstance(data, dict) else "unknown",
                    )
                    return None
                cid = data.get("IpfsHash")
                if not cid:
                    logger.error("Pinata pin returned no IpfsHash: %s", data)
                    return None
                logger.info("Pinned public provenance to IPFS: cid=%s", cid)
                return cid
        except Exception as e:  # network / timeout / JSON decode
            logger.error("Pinata pin error: %s", e)
            return None

    async def fetch_json(self, cid: str) -> dict | None:
        """Re-fetch the pinned JSON for a CID from the public gateway.

        Used by ``verify`` to round-trip the anchor. Returns None on any failure
        (missing CID, gateway error, non-JSON body) — never raises.
        """
        if not cid:
            return None
        try:
            timeout = aiohttp.ClientTimeout(total=_PIN_TIMEOUT_S)
            async with (
                aiohttp.ClientSession(timeout=timeout) as session,
                session.get(f"{PINATA_GATEWAY}/{cid}") as resp,
            ):
                if resp.status != 200:
                    logger.error("Pinata gateway fetch failed (status=%s cid=%s)", resp.status, cid)
                    return None
                return await resp.json()
        except Exception as e:
            logger.error("Pinata gateway fetch error (cid=%s): %s", cid, e)
            return None

    async def verify(self, cid: str, expected: dict) -> bool:
        """Re-fetch ``cid`` and check its canonical bytes equal ``expected``.

        This proves the CID anchored on-chain still resolves to exactly the public
        provenance payload the agent pinned — i.e. IPFS content has not drifted from
        the on-chain anchor. Canonicalizes both sides (sorted keys, no spaces) so
        key ordering never causes a false mismatch.
        """
        fetched = await self.fetch_json(cid)
        if fetched is None:
            return False
        return canonical_bytes(fetched) == canonical_bytes(expected)


def canonical_bytes(payload: dict) -> bytes:
    """Deterministic JSON encoding — sorted keys, no whitespace, UTF-8 bytes.

    Shared by the pin path and verify so the round-trip is byte-stable.
    """
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def build_public_provenance(
    *,
    trace_id: str,
    vault_address: str,
    decision_type: str,
    timestamp_iso: str,
    papers_cited: list[dict] | list[str],
    methodology: str,
    rigor: dict | None = None,
    reasoning: str = "",
    consulted_paper_hashes: list[str] | None = None,
) -> dict:
    """Assemble the PUBLIC provenance layer that is safe to pin to IPFS.

    INCLUDES (publishable, verifiable claims):
      - trace id, vault, decision type, timestamp
      - papers cited (titles / arxiv ids / dois) and consulted-paper content hashes
      - methodology summary (the *what*, not the executable *how*)
      - rigor scores: deflated Sharpe, DSR p-value, PBO, OOS Sharpe, rigor-gate pass
      - human-readable reasoning

    DELIBERATELY EXCLUDES (the executable / alpha layer — stays off IPFS):
      - target weights / allocations, position-sizing parameters
      - strategy code paths or code hashes
      - raw signal magnitudes per asset

    Keep this function the single source of truth for the split so nothing leaks
    the executable layer onto a public gateway.
    """
    return {
        "schema": "archimedes.public-provenance/v1",
        "trace_id": trace_id,
        "vault_address": vault_address,
        "decision_type": decision_type,
        "timestamp": timestamp_iso,
        "papers_cited": papers_cited,
        "consulted_paper_hashes": consulted_paper_hashes or [],
        "methodology": methodology,
        "rigor": rigor or {},
        "reasoning": reasoning,
    }


# Module singleton — reads PINATA_JWT from the environment at import time.
pinata_client = PinataClient()
