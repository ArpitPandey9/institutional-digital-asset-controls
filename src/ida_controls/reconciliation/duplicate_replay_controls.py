"""Duplicate and replay controls for previously consumed settlements."""

from __future__ import annotations

from dataclasses import dataclass

from ida_controls.domain.consumption import SettlementConsumptionRecord
from ida_controls.domain.instruction import ExpectedInstruction
from ida_controls.domain.transfer import ObservedTransfer
from ida_controls.reconciliation.result import (
    ControlName,
    ControlStatus,
    ReasonCode,
)


@dataclass(frozen=True, slots=True)
class DuplicateReplayControlResult:
    """Auditable outcome for one settlement uniqueness control."""

    instruction_id: str
    control_name: ControlName
    status: ControlStatus
    reason: ReasonCode

    chain_id: int | None
    transaction_hash: str | None
    log_index: int | None

    matched_records: tuple[SettlementConsumptionRecord, ...]


def evaluate_duplicate_replay_controls(
    expected: ExpectedInstruction,
    observed: ObservedTransfer | None,
    history: tuple[SettlementConsumptionRecord, ...] | None,
) -> tuple[DuplicateReplayControlResult, ...]:
    """Evaluate instruction and transfer uniqueness against processing history."""

    chain_id = observed.chain_id if observed is not None else None
    transaction_hash = (
        observed.transaction_hash
        if observed is not None
        else None
    )
    log_index = observed.log_index if observed is not None else None

    if history is None:
        return (
            DuplicateReplayControlResult(
                instruction_id=expected.instruction_id,
                control_name=ControlName.INSTRUCTION_UNIQUENESS,
                status=ControlStatus.UNKNOWN,
                reason=ReasonCode.INSUFFICIENT_EVIDENCE,
                chain_id=chain_id,
                transaction_hash=transaction_hash,
                log_index=log_index,
                matched_records=(),
            ),
            DuplicateReplayControlResult(
                instruction_id=expected.instruction_id,
                control_name=ControlName.TRANSFER_UNIQUENESS,
                status=ControlStatus.UNKNOWN,
                reason=ReasonCode.INSUFFICIENT_EVIDENCE,
                chain_id=chain_id,
                transaction_hash=transaction_hash,
                log_index=log_index,
                matched_records=(),
            ),
        )

    instruction_matches = tuple(
        record
        for record in history
        if record.instruction_id == expected.instruction_id
    )

    instruction_result = DuplicateReplayControlResult(
        instruction_id=expected.instruction_id,
        control_name=ControlName.INSTRUCTION_UNIQUENESS,
        status=(
            ControlStatus.FAIL
            if instruction_matches
            else ControlStatus.PASS
        ),
        reason=(
            ReasonCode.INSTRUCTION_ALREADY_CONSUMED
            if instruction_matches
            else ReasonCode.NO_PRIOR_INSTRUCTION_CONSUMPTION
        ),
        chain_id=chain_id,
        transaction_hash=transaction_hash,
        log_index=log_index,
        matched_records=instruction_matches,
    )

    if observed is None:
        transfer_result = DuplicateReplayControlResult(
            instruction_id=expected.instruction_id,
            control_name=ControlName.TRANSFER_UNIQUENESS,
            status=ControlStatus.UNKNOWN,
            reason=ReasonCode.INSUFFICIENT_EVIDENCE,
            chain_id=None,
            transaction_hash=None,
            log_index=None,
            matched_records=(),
        )
        return (
            instruction_result,
            transfer_result,
        )

    observed_transfer_identity = (
        observed.chain_id,
        observed.transaction_hash.lower(),
        observed.log_index,
    )

    transfer_matches = tuple(
        record
        for record in history
        if record.transfer_identity == observed_transfer_identity
    )

    transfer_result = DuplicateReplayControlResult(
        instruction_id=expected.instruction_id,
        control_name=ControlName.TRANSFER_UNIQUENESS,
        status=(
            ControlStatus.FAIL
            if transfer_matches
            else ControlStatus.PASS
        ),
        reason=(
            ReasonCode.TRANSFER_ALREADY_CONSUMED
            if transfer_matches
            else ReasonCode.NO_PRIOR_TRANSFER_CONSUMPTION
        ),
        chain_id=observed.chain_id,
        transaction_hash=observed.transaction_hash,
        log_index=observed.log_index,
        matched_records=transfer_matches,
    )

    return (
        instruction_result,
        transfer_result,
    )
