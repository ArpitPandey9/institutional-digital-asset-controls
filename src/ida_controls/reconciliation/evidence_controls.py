"""Evidence-aware settlement control evaluation."""

from __future__ import annotations

from ida_controls.domain.evidence import ObservedSettlementEvidence
from ida_controls.domain.instruction import ExpectedInstruction
from ida_controls.reconciliation.field_controls import (
    evaluate_direct_transfer_controls,
)
from ida_controls.reconciliation.result import (
    ControlName,
    ControlStatus,
    EvidenceSource,
    FieldControlResult,
    ReasonCode,
)


def evaluate_direct_transfer_evidence(
    expected: ExpectedInstruction,
    evidence: ObservedSettlementEvidence,
) -> tuple[FieldControlResult, ...]:
    """Evaluate settlement controls using the evidence currently available."""

    if evidence.transfer is not None:
        results = list(
            evaluate_direct_transfer_controls(
                expected,
                evidence.transfer,
            )
        )

        if evidence.chain_evidence is None:
            return tuple(results)

        chain_matches = (
            expected.chain_id
            == evidence.chain_evidence.chain_id
        )

        for index, result in enumerate(results):
            if result.control_name == ControlName.CHAIN:
                results[index] = FieldControlResult(
                    instruction_id=expected.instruction_id,
                    control_name=ControlName.CHAIN,
                    expected_value=expected.chain_id,
                    observed_value=evidence.chain_evidence.chain_id,
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
                    evidence_source=EvidenceSource.RPC_CHAIN_ID,
                    transaction_hash=evidence.transaction_hash,
                    log_index=evidence.transfer.log_index,
                )
                break

        return tuple(results)

    if evidence.receipt_status is None:
        execution_status = ControlStatus.UNKNOWN
        execution_reason = ReasonCode.INSUFFICIENT_EVIDENCE
        execution_source = None
    elif evidence.receipt_status == 1:
        execution_status = ControlStatus.PASS
        execution_reason = ReasonCode.EXECUTION_SUCCEEDED
        execution_source = EvidenceSource.TRANSACTION_RECEIPT_STATUS
    else:
        execution_status = ControlStatus.FAIL
        execution_reason = ReasonCode.EXECUTION_REVERTED
        execution_source = EvidenceSource.TRANSACTION_RECEIPT_STATUS

    results = [
        FieldControlResult(
            instruction_id=expected.instruction_id,
            control_name=ControlName.EXECUTION,
            expected_value=1,
            observed_value=evidence.receipt_status,
            status=execution_status,
            reason=execution_reason,
            evidence_source=execution_source,
            transaction_hash=evidence.transaction_hash,
            log_index=None,
        )
    ]

    if evidence.chain_evidence is None:
        results.append(
            FieldControlResult(
                instruction_id=expected.instruction_id,
                control_name=ControlName.CHAIN,
                expected_value=expected.chain_id,
                observed_value=None,
                status=ControlStatus.UNKNOWN,
                reason=ReasonCode.INSUFFICIENT_EVIDENCE,
                evidence_source=None,
                transaction_hash=evidence.transaction_hash,
                log_index=None,
            )
        )
    else:
        chain_matches = (
            expected.chain_id
            == evidence.chain_evidence.chain_id
        )

        results.append(
            FieldControlResult(
                instruction_id=expected.instruction_id,
                control_name=ControlName.CHAIN,
                expected_value=expected.chain_id,
                observed_value=evidence.chain_evidence.chain_id,
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
                evidence_source=EvidenceSource.RPC_CHAIN_ID,
                transaction_hash=evidence.transaction_hash,
                log_index=None,
            )
        )

    unavailable_controls = (
        (ControlName.ASSET, expected.token_contract),
        (ControlName.SENDER, expected.token_sender),
        (ControlName.RECEIVER, expected.token_receiver),
        (ControlName.AMOUNT, expected.amount_raw),
    )

    for control_name, expected_value in unavailable_controls:
        results.append(
            FieldControlResult(
                instruction_id=expected.instruction_id,
                control_name=control_name,
                expected_value=expected_value,
                observed_value=None,
                status=ControlStatus.UNKNOWN,
                reason=ReasonCode.INSUFFICIENT_EVIDENCE,
                evidence_source=None,
                transaction_hash=evidence.transaction_hash,
                log_index=None,
            )
        )

    return tuple(results)
