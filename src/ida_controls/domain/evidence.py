"""Observed evidence availability for settlement control evaluation."""

from __future__ import annotations

from dataclasses import dataclass

from ida_controls.domain.transfer import ObservedTransfer


@dataclass(frozen=True, slots=True)
class RpcChainEvidence:
    """Chain identity evidence obtained through Ethereum JSON-RPC."""

    chain_id: int

    def __post_init__(self) -> None:
        if self.chain_id <= 0:
            raise ValueError("RPC chain_id must be positive")


@dataclass(frozen=True, slots=True)
class ObservedSettlementEvidence:
    """Available blockchain evidence for one settlement evaluation."""

    transaction_hash: str | None
    receipt_status: int | None
    transfer: ObservedTransfer | None
    chain_evidence: RpcChainEvidence | None = None

    def __post_init__(self) -> None:
        if self.receipt_status not in (None, 0, 1):
            raise ValueError("receipt_status must be 0, 1, or None")

        if self.transfer is not None:
            if (
                self.transaction_hash is not None
                and self.transaction_hash.lower()
                != self.transfer.transaction_hash.lower()
            ):
                raise ValueError(
                    "Evidence transaction hash does not match observed transfer"
                )

            if (
                self.receipt_status is not None
                and self.receipt_status != self.transfer.receipt_status
            ):
                raise ValueError(
                    "Evidence receipt status does not match observed transfer"
                )

            if (
                self.chain_evidence is not None
                and self.chain_evidence.chain_id != self.transfer.chain_id
            ):
                raise ValueError(
                    "RPC chain evidence does not match observed transfer"
                )
