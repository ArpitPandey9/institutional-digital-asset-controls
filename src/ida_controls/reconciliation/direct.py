"""Strict direct-transfer settlement reconciliation."""

from __future__ import annotations

from ida_controls.domain.instruction import ExpectedInstruction
from ida_controls.domain.transfer import ObservedTransfer
from ida_controls.reconciliation.result import (
    ControlStatus,
    ReasonCode,
    ReconciliationResult,
)


def reconcile_direct_transfer(
    expected: ExpectedInstruction,
    observed: ObservedTransfer,
) -> ReconciliationResult:
    """Compare one expected instruction with one observed direct transfer."""

    def result(
        status: ControlStatus,
        reason: ReasonCode,
    ) -> ReconciliationResult:
        return ReconciliationResult(
            instruction_id=expected.instruction_id,
            status=status,
            reason=reason,
            transaction_hash=observed.transaction_hash,
            log_index=observed.log_index,
        )

    if expected.chain_id != observed.chain_id:
        return result(
            ControlStatus.FAIL,
            ReasonCode.CHAIN_ID_MISMATCH,
        )

    if expected.token_contract.lower() != observed.token_contract.lower():
        return result(
            ControlStatus.FAIL,
            ReasonCode.TOKEN_CONTRACT_MISMATCH,
        )

    if expected.token_sender.lower() != observed.token_sender.lower():
        return result(
            ControlStatus.FAIL,
            ReasonCode.SENDER_MISMATCH,
        )

    if expected.token_receiver.lower() != observed.token_receiver.lower():
        return result(
            ControlStatus.FAIL,
            ReasonCode.RECEIVER_MISMATCH,
        )

    if expected.amount_raw != observed.amount_raw:
        return result(
            ControlStatus.FAIL,
            ReasonCode.AMOUNT_MISMATCH,
        )

    return result(
        ControlStatus.PASS,
        ReasonCode.EXACT_MATCH,
    )
