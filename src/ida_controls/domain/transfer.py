"""Domain model for an observed on-chain token transfer."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class ObservedTransfer:
    """Normalized evidence for one observed token Transfer event."""

    chain_id: int

    block_number: int
    block_hash: str
    transaction_hash: str
    log_index: int

    token_contract: str
    token_sender: str
    token_receiver: str

    amount_raw: int
    token_decimals: int

    tx_submitter: str
    receipt_status: int

    def __post_init__(self) -> None:
        """Validate basic structural invariants."""
        if self.chain_id <= 0:
            raise ValueError("chain_id must be positive")

        if self.block_number < 0:
            raise ValueError("block_number cannot be negative")

        if self.log_index < 0:
            raise ValueError("log_index cannot be negative")

        if self.amount_raw < 0:
            raise ValueError("amount_raw cannot be negative")

        if self.token_decimals < 0:
            raise ValueError("token_decimals cannot be negative")

        if self.receipt_status not in (0, 1):
            raise ValueError("receipt_status must be 0 or 1")

    @property
    def amount_token(self) -> Decimal:
        """Return the human-readable token amount without using float."""
        scale = Decimal(10) ** self.token_decimals
        return Decimal(self.amount_raw) / scale

    @property
    def execution_succeeded(self) -> bool:
        """Return whether EVM execution completed successfully."""
        return self.receipt_status == 1
