"""Orchestration of independent settlement controls into one audit bundle."""

from __future__ import annotations

from dataclasses import dataclass

from ida_controls.domain.asset_registry import AssetRegistryEvidence
from ida_controls.domain.consumption import SettlementConsumptionRecord
from ida_controls.domain.evidence import ObservedSettlementEvidence
from ida_controls.domain.finality import FinalityEvidence
from ida_controls.domain.instruction import ExpectedInstruction
from ida_controls.reconciliation.canonical_asset_controls import (
    CanonicalAssetControlResult,
    evaluate_canonical_asset_control,
)
from ida_controls.reconciliation.duplicate_replay_controls import (
    DuplicateReplayControlResult,
    evaluate_duplicate_replay_controls,
)
from ida_controls.reconciliation.evidence_controls import (
    evaluate_direct_transfer_evidence,
)
from ida_controls.reconciliation.finality_controls import (
    FinalityControlResult,
    evaluate_finality_control,
)
from ida_controls.reconciliation.result import (
    ControlName,
    ControlStatus,
    FieldControlResult,
    ReasonCode,
)


@dataclass(frozen=True, slots=True)
class ControlFinding:
    """Normalized index entry for one independent control outcome."""

    instruction_id: str
    control_name: ControlName
    status: ControlStatus
    reason: ReasonCode
    transaction_hash: str | None
    log_index: int | None


@dataclass(frozen=True, slots=True)
class SettlementControlBundle:
    """Auditable collection of control findings without business aggregation."""

    instruction_id: str
    transaction_hash: str | None

    findings: tuple[ControlFinding, ...]

    field_controls: tuple[FieldControlResult, ...]
    finality_control: FinalityControlResult | None
    duplicate_replay_controls: tuple[DuplicateReplayControlResult, ...]
    canonical_asset_control: CanonicalAssetControlResult | None


def evaluate_settlement_control_bundle(
    expected: ExpectedInstruction,
    evidence: ObservedSettlementEvidence,
    *,
    finality_evidence: FinalityEvidence | None,
    history: tuple[SettlementConsumptionRecord, ...] | None,
    asset_registry: AssetRegistryEvidence | None,
) -> SettlementControlBundle:
    """Run available independent controls and preserve their findings."""

    field_controls = evaluate_direct_transfer_evidence(
        expected,
        evidence,
    )

    findings = [
        ControlFinding(
            instruction_id=result.instruction_id,
            control_name=result.control_name,
            status=result.status,
            reason=result.reason,
            transaction_hash=result.transaction_hash,
            log_index=result.log_index,
        )
        for result in field_controls
    ]

    transfer = evidence.transfer

    duplicate_replay_controls = evaluate_duplicate_replay_controls(
        expected,
        transfer,
        history,
    )

    if transfer is None:
        findings.append(
            ControlFinding(
                instruction_id=expected.instruction_id,
                control_name=ControlName.FINALITY,
                status=ControlStatus.UNKNOWN,
                reason=ReasonCode.INSUFFICIENT_EVIDENCE,
                transaction_hash=evidence.transaction_hash,
                log_index=None,
            )
        )

        for result in duplicate_replay_controls:
            findings.append(
                ControlFinding(
                    instruction_id=result.instruction_id,
                    control_name=result.control_name,
                    status=result.status,
                    reason=result.reason,
                    transaction_hash=result.transaction_hash,
                    log_index=result.log_index,
                )
            )

        findings.append(
            ControlFinding(
                instruction_id=expected.instruction_id,
                control_name=ControlName.CANONICAL_ASSET,
                status=ControlStatus.UNKNOWN,
                reason=ReasonCode.INSUFFICIENT_EVIDENCE,
                transaction_hash=evidence.transaction_hash,
                log_index=None,
            )
        )

        return SettlementControlBundle(
            instruction_id=expected.instruction_id,
            transaction_hash=evidence.transaction_hash,
            findings=tuple(findings),
            field_controls=field_controls,
            finality_control=None,
            duplicate_replay_controls=duplicate_replay_controls,
            canonical_asset_control=None,
        )

    finality_control = evaluate_finality_control(
        transfer,
        finality_evidence,
    )

    findings.append(
        ControlFinding(
            instruction_id=expected.instruction_id,
            control_name=ControlName.FINALITY,
            status=finality_control.status,
            reason=finality_control.reason,
            transaction_hash=transfer.transaction_hash,
            log_index=transfer.log_index,
        )
    )

    for result in duplicate_replay_controls:
        findings.append(
            ControlFinding(
                instruction_id=result.instruction_id,
                control_name=result.control_name,
                status=result.status,
                reason=result.reason,
                transaction_hash=result.transaction_hash,
                log_index=result.log_index,
            )
        )

    canonical_asset_control = evaluate_canonical_asset_control(
        expected,
        transfer,
        asset_registry,
    )

    findings.append(
        ControlFinding(
            instruction_id=canonical_asset_control.instruction_id,
            control_name=canonical_asset_control.control_name,
            status=canonical_asset_control.status,
            reason=canonical_asset_control.reason,
            transaction_hash=canonical_asset_control.transaction_hash,
            log_index=canonical_asset_control.log_index,
        )
    )

    return SettlementControlBundle(
        instruction_id=expected.instruction_id,
        transaction_hash=transfer.transaction_hash,
        findings=tuple(findings),
        field_controls=field_controls,
        finality_control=finality_control,
        duplicate_replay_controls=duplicate_replay_controls,
        canonical_asset_control=canonical_asset_control,
    )
