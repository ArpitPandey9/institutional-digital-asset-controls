"""Build protocol-aware finality evidence from EVM JSON-RPC."""

from __future__ import annotations

from ida_controls.chains.evm import (
    get_block,
    get_block_by_tag,
    hex_to_int,
)
from ida_controls.domain.finality import FinalityEvidence


def build_finality_evidence(
    rpc_url: str,
    *,
    transaction_block_number: int,
) -> FinalityEvidence:
    """Build canonical, safe, and finalized block evidence for one TX block."""

    canonical_block = get_block(
        rpc_url,
        transaction_block_number,
        full_transactions=False,
    )

    safe_block = get_block_by_tag(
        rpc_url,
        "safe",
        full_transactions=False,
    )

    finalized_block = get_block_by_tag(
        rpc_url,
        "finalized",
        full_transactions=False,
    )

    return FinalityEvidence(
        canonical_block_number=hex_to_int(
            canonical_block["number"]
        ),
        canonical_block_hash=canonical_block["hash"],
        safe_block_number=hex_to_int(
            safe_block["number"]
        ),
        safe_block_hash=safe_block["hash"],
        finalized_block_number=hex_to_int(
            finalized_block["number"]
        ),
        finalized_block_hash=finalized_block["hash"],
    )
