"""Provenance publisher — public IPFS layer + commit-reveal CID anchoring.

Ties T0.3 (commit-reveal anchoring) to T1.4 (IPFS publishing):

  1. Build the PUBLIC provenance layer from a ReasoningTrace (papers cited,
     methodology, rigor / DSR / PBO scores, timestamp — NOT executable params;
     see ``build_public_provenance``).
  2. Pin it to IPFS via Pinata → CID.
  3. Anchor the CID on-chain as the commit-reveal ``storagePointer``.
  4. ``verify`` re-fetches the CID and checks it against the on-chain anchor.

PINATA_JWT gating (T0.5 no-silent-degradation): if unset, ``pin_public_provenance``
returns None with a loud structured WARN. The caller still reveals with an empty
storage pointer — the on-chain keccak256 hash remains the authoritative anchor — so
provenance is never silently dropped; it is loudly downgraded to "hash-only".
"""

from __future__ import annotations

import logging

from archimedes.chain.pinata_client import (
    PinataClient,
    build_public_provenance,
    canonical_bytes,
    pinata_client,
)
from archimedes.models.trace import ReasoningTrace

logger = logging.getLogger(__name__)


def public_provenance_for(trace: ReasoningTrace, rigor: dict | None = None) -> dict:
    """Project a ReasoningTrace onto its PUBLIC provenance layer (IPFS-safe).

    Pulls only publishable fields. ``rigor`` (optional) carries the strategy's
    DSR / PBO / rigor-gate scores when available — these are claims, safe to publish.
    The executable layer (weights, sizing params, code hashes) is excluded by
    ``build_public_provenance``.
    """
    return build_public_provenance(
        trace_id=trace.id,
        vault_address=trace.vault_address,
        decision_type=trace.decision_type.value,
        timestamp_iso=trace.timestamp.isoformat(),
        papers_cited=trace.strategies_referenced,
        methodology=trace.reasoning,
        rigor=rigor,
        reasoning=trace.reasoning,
        consulted_paper_hashes=trace.consulted_paper_hashes,
    )


async def pin_public_provenance(
    trace: ReasoningTrace,
    rigor: dict | None = None,
    client: PinataClient | None = None,
) -> tuple[str | None, dict]:
    """Pin the trace's public provenance layer to IPFS.

    Returns (cid, payload). ``cid`` is None (loud WARN, never raises) when
    PINATA_JWT is unset or Pinata errors — the caller falls back to a hash-only
    anchor. ``payload`` is always returned so it can be persisted off-chain and
    re-used by ``verify`` regardless of pin success.
    """
    client = client or pinata_client
    payload = public_provenance_for(trace, rigor)
    cid = await client.pin_json(payload, name=f"archimedes-provenance-{trace.id}")
    if cid is None:
        logger.warning(
            "Public provenance NOT pinned to IPFS — anchoring on-chain hash only "
            "(event=provenance_ipfs_skipped trace_id=%s)",
            trace.id,
        )
    return cid, payload


async def verify_provenance(
    cid: str,
    trace: ReasoningTrace,
    rigor: dict | None = None,
    client: PinataClient | None = None,
) -> bool:
    """Re-fetch ``cid`` from IPFS and check it equals the trace's public provenance.

    Proves the CID anchored on-chain still resolves to exactly the public layer the
    agent published — content hasn't drifted from the anchor. Returns False if the
    CID is empty, unfetchable, or its canonical bytes differ.
    """
    client = client or pinata_client
    expected = public_provenance_for(trace, rigor)
    return await client.verify(cid, expected)


__all__ = [
    "canonical_bytes",
    "pin_public_provenance",
    "public_provenance_for",
    "verify_provenance",
]
