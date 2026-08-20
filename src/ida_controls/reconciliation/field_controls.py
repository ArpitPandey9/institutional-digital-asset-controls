"""Field-level controls for direct-transfer settlement reconciliation."""

from __future__ import annotations

from ida_controls.domain.instruction import ExpectedInstruction
from ida_controls.domain.transfer import ObservedTransfer
from ida_controls.reconciliation.result import (
    ControlName,
    ControlStatus,
    EvidenceSource,
    FieldControlResult,
    ReasonCode,
)


def evaluate_direct_transfer_controls(
    expected: ExpectedInstruction,
    observed: ObservedTransfer,
) -> tuple[FieldControlResult, ...]:
    """Evaluate each direct-transfer settlement control independently."""

    transaction_hash = observed.transaction_hash
    log_index = observed.log_index

    chain_matches = expected.chain_id == observed.chain_id
    asset_matches = (
        expected.token_contract.lower()
        == observed.token_contract.lower()
    )
    sender_matches = (
        expected.token_sender.lower()
        == observed.token_sender.lower()
    )
    receiver_matches = (
        expected.token_receiver.lower()
        == observed.token_receiver.lower()
    )
    amount_matches = expected.amount_raw == observed.amount_raw

    return (
        FieldControlResult(
            instruction_id=expected.instruction_id,
            control_name=ControlName.EXECUTION,
            expected_value=1,
            observed_value=observed.receipt_status,
            status=ControlStatus.PASS,
            reason=ReasonCode.EXECUTION_SUCCEEDED,
            evidence_source=EvidenceSource.TRANSACTION_RECEIPT_STATUS,
            transaction_hash=transaction_hash,
            log_index=log_index,
        ),
        FieldControlResult(
            instruction_id=expected.instruction_id,
            control_name=ControlName.CHAIN,
            expected_value=expected.chain_id,
            observed_value=observed.chain_id,
            status=(
                ControlStatus.PASS
                if chain_matches
                else ControlStatus.FAIL
            ),
            reason=(
                ReasonCode.MATCH
                if chain_matches
                else ReasonCode.CHAIN_ID_MISMATCH
            ),
            evidence_source=EvidenceSource.OBSERVED_TRANSFER_CHAIN_ID,
            transaction_hash=transaction_hash,
            log_index=log_index,
        ),
        FieldControlResult(
            instruction_id=expected.instruction_id,
            control_name=ControlName.ASSET,
            expected_value=expected.token_contract,
            observed_value=observed.token_contract,
            status=(
                ControlStatus.PASS
                if asset_matches
                else ControlStatus.FAIL
            ),
            reason=(
                ReasonCode.MATCH
                if asset_matches
                else ReasonCode.TOKEN_CONTRACT_MISMATCH
            ),
            evidence_source=EvidenceSource.ERC20_LOG_EMITTER,
            transaction_hash=transaction_hash,
            log_index=log_index,
        ),
        FieldControlResult(
            instruction_id=expected.instruction_id,
            control_name=ControlName.SENDER,
            expected_value=expected.token_sender,
            observed_value=observed.token_sender,
            status=(
                ControlStatus.PASS
                if sender_matches
                else ControlStatus.FAIL
            ),
            reason=(
                ReasonCode.MATCH
                if sender_matches
                else ReasonCode.SENDER_MISMATCH
            ),
            evidence_source=EvidenceSource.ERC20_TRANSFER_SENDER,
            transaction_hash=transaction_hash,
            log_index=log_index,
        ),
        FieldControlResult(
            instruction_id=expected.instruction_id,
            control_name=ControlName.RECEIVER,
            expected_value=expected.token_receiver,
            observed_value=observed.token_receiver,
            status=(
                ControlStatus.PASS
                if receiver_matches
                else ControlStatus.FAIL
            ),
            reason=(
                ReasonCode.MATCH
                if receiver_matches
                else ReasonCode.RECEIVER_MISMATCH
            ),
            evidence_source=EvidenceSource.ERC20_TRANSFER_RECEIVER,
            transaction_hash=transaction_hash,
            log_index=log_index,
        ),
        FieldControlResult(
            instruction_id=expected.instruction_id,
            control_name=ControlName.AMOUNT,
            expected_value=expected.amount_raw,
            observed_value=observed.amount_raw,
            status=(
                ControlStatus.PASS
                if amount_matches
                else ControlStatus.FAIL
            ),
            reason=(
                ReasonCode.MATCH
                if amount_matches
                else ReasonCode.AMOUNT_MISMATCH
            ),
            evidence_source=EvidenceSource.ERC20_TRANSFER_AMOUNT_RAW,
            transaction_hash=transaction_hash,
            log_index=log_index,
        ),
    )
