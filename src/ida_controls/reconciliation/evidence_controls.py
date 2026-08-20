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
        return evaluate_direct_transfer_controls(
            expected,
            evidence.transfer,
        )

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

    unavailable_controls = (
        (ControlName.CHAIN, expected.chain_id),
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
