"""Domain model for an expected digital-asset settlement instruction."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ExpectedInstruction:
    """What an institution expects to settle on-chain."""

    instruction_id: str

    chain_id: int
    token_contract: str

    token_sender: str
    token_receiver: str

    amount_raw: int

    asset_id: str | None = None

    def __post_init__(self) -> None:
        """Validate basic instruction invariants."""
        if not self.instruction_id:
            raise ValueError("instruction_id cannot be empty")

        if self.chain_id <= 0:
            raise ValueError("chain_id must be positive")

        if self.amount_raw < 0:
            raise ValueError("amount_raw cannot be negative")

        if self.asset_id is not None and not self.asset_id.strip():
            raise ValueError("asset_id cannot be empty when provided")
