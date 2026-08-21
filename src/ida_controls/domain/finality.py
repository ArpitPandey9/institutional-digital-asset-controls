"""Protocol finality evidence for observed blockchain settlement."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FinalityEvidence:
    """Canonical, safe, and finalized block evidence from one RPC view."""

    canonical_block_number: int
    canonical_block_hash: str

    safe_block_number: int
    safe_block_hash: str

    finalized_block_number: int
    finalized_block_hash: str

    def __post_init__(self) -> None:
        block_numbers = (
            self.canonical_block_number,
            self.safe_block_number,
            self.finalized_block_number,
        )

        if any(block_number < 0 for block_number in block_numbers):
            raise ValueError("Finality block numbers cannot be negative")

        block_hashes = (
            self.canonical_block_hash,
            self.safe_block_hash,
            self.finalized_block_hash,
        )

        if any(not block_hash for block_hash in block_hashes):
            raise ValueError("Finality block hashes cannot be empty")
