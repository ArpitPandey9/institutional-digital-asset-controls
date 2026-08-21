"""Historical consumption identity for a processed settlement."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SettlementConsumptionRecord:
    """Previously consumed instruction-to-transfer association."""

    instruction_id: str
    chain_id: int
    transaction_hash: str
    log_index: int

    def __post_init__(self) -> None:
        """Validate settlement consumption identity."""
        if not self.instruction_id:
            raise ValueError("instruction_id cannot be empty")

        if self.chain_id <= 0:
            raise ValueError("chain_id must be positive")

        if not self.transaction_hash:
            raise ValueError("transaction_hash cannot be empty")

        if self.log_index < 0:
            raise ValueError("log_index cannot be negative")

    @property
    def transfer_identity(self) -> tuple[int, str, int]:
        """Return normalized exact transfer identity."""
        return (
            self.chain_id,
            self.transaction_hash.lower(),
            self.log_index,
        )
