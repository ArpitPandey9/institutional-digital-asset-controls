"""Protocol-aware settlement finality controls."""

from __future__ import annotations

from dataclasses import dataclass

from ida_controls.domain.finality import FinalityEvidence
from ida_controls.domain.transfer import ObservedTransfer
from ida_controls.reconciliation.result import (
    ControlStatus,
    ReasonCode,
)


@dataclass(frozen=True, slots=True)
class FinalityControlResult:
    """Auditable outcome of evaluating settlement finality."""

    status: ControlStatus
    reason: ReasonCode

    transaction_hash: str
    transaction_block_number: int
    transaction_block_hash: str

    canonical_block_hash: str | None
    finalized_block_number: int | None


def evaluate_finality_control(
    transfer: ObservedTransfer,
    evidence: FinalityEvidence | None,
) -> FinalityControlResult:
    """Evaluate whether observed transfer evidence is canonical and finalized."""

    if evidence is None:
        return FinalityControlResult(
            status=ControlStatus.UNKNOWN,
            reason=ReasonCode.INSUFFICIENT_EVIDENCE,
            transaction_hash=transfer.transaction_hash,
            transaction_block_number=transfer.block_number,
            transaction_block_hash=transfer.block_hash,
            canonical_block_hash=None,
            finalized_block_number=None,
        )

    canonical_matches = (
        evidence.canonical_block_number
        == transfer.block_number
        and evidence.canonical_block_hash.lower()
        == transfer.block_hash.lower()
    )

    if not canonical_matches:
        return FinalityControlResult(
            status=ControlStatus.FAIL,
            reason=ReasonCode.BLOCK_NOT_CANONICAL,
            transaction_hash=transfer.transaction_hash,
            transaction_block_number=transfer.block_number,
            transaction_block_hash=transfer.block_hash,
            canonical_block_hash=evidence.canonical_block_hash,
            finalized_block_number=evidence.finalized_block_number,
        )

    if transfer.block_number <= evidence.finalized_block_number:
        return FinalityControlResult(
            status=ControlStatus.PASS,
            reason=ReasonCode.FINALITY_REACHED,
            transaction_hash=transfer.transaction_hash,
            transaction_block_number=transfer.block_number,
            transaction_block_hash=transfer.block_hash,
            canonical_block_hash=evidence.canonical_block_hash,
            finalized_block_number=evidence.finalized_block_number,
        )

    return FinalityControlResult(
        status=ControlStatus.FAIL,
        reason=ReasonCode.FINALITY_NOT_REACHED,
        transaction_hash=transfer.transaction_hash,
        transaction_block_number=transfer.block_number,
        transaction_block_hash=transfer.block_hash,
        canonical_block_hash=evidence.canonical_block_hash,
        finalized_block_number=evidence.finalized_block_number,
    )
