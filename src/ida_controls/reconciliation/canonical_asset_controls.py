"""Canonical asset validation against trusted institutional reference data."""

from __future__ import annotations

from dataclasses import dataclass

from ida_controls.domain.asset_registry import AssetRegistryEvidence
from ida_controls.domain.instruction import ExpectedInstruction
from ida_controls.domain.transfer import ObservedTransfer
from ida_controls.reconciliation.result import (
    ControlName,
    ControlStatus,
    ReasonCode,
)


@dataclass(frozen=True, slots=True)
class CanonicalAssetControlResult:
    """Auditable outcome of canonical asset validation."""

    instruction_id: str
    control_name: ControlName
    asset_id: str | None

    observed_chain_id: int
    observed_token_contract: str

    approved_token_contract: str | None
    approved_token_decimals: int | None
    issuer: str | None
    source: str | None

    status: ControlStatus
    reason: ReasonCode

    transaction_hash: str
    log_index: int


def evaluate_canonical_asset_control(
    expected: ExpectedInstruction,
    observed: ObservedTransfer,
    registry: AssetRegistryEvidence | None,
) -> CanonicalAssetControlResult:
    """Validate the observed token against approved asset reference data."""

    def result(
        *,
        status: ControlStatus,
        reason: ReasonCode,
        approved_token_contract: str | None = None,
        approved_token_decimals: int | None = None,
        issuer: str | None = None,
        source: str | None = None,
    ) -> CanonicalAssetControlResult:
        return CanonicalAssetControlResult(
            instruction_id=expected.instruction_id,
            control_name=ControlName.CANONICAL_ASSET,
            asset_id=expected.asset_id,
            observed_chain_id=observed.chain_id,
            observed_token_contract=observed.token_contract,
            approved_token_contract=approved_token_contract,
            approved_token_decimals=approved_token_decimals,
            issuer=issuer,
            source=source,
            status=status,
            reason=reason,
            transaction_hash=observed.transaction_hash,
            log_index=observed.log_index,
        )

    if expected.asset_id is None:
        return result(
            status=ControlStatus.UNKNOWN,
            reason=ReasonCode.INSUFFICIENT_EVIDENCE,
        )

    if registry is None:
        return result(
            status=ControlStatus.UNKNOWN,
            reason=ReasonCode.INSUFFICIENT_EVIDENCE,
        )

    approved = registry.find(
        asset_id=expected.asset_id,
        chain_id=observed.chain_id,
    )

    if approved is None:
        if registry.is_authoritative_complete:
            return result(
                status=ControlStatus.FAIL,
                reason=ReasonCode.ASSET_NOT_APPROVED,
            )

        return result(
            status=ControlStatus.UNKNOWN,
            reason=ReasonCode.INSUFFICIENT_EVIDENCE,
        )

    canonical_matches = (
        observed.token_contract.lower()
        == approved.token_contract.lower()
    )

    return result(
        status=(
            ControlStatus.PASS
            if canonical_matches
            else ControlStatus.FAIL
        ),
        reason=(
            ReasonCode.CANONICAL_ASSET_MATCH
            if canonical_matches
            else ReasonCode.CANONICAL_ASSET_MISMATCH
        ),
        approved_token_contract=approved.token_contract,
        approved_token_decimals=approved.token_decimals,
        issuer=approved.issuer,
        source=approved.source,
    )
