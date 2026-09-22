"""Explicitly modeled demo scenarios for the control-plane dashboard.

These fixtures are synthetic demonstration inputs. They are not represented
as production, employer, client, custody, or private settlement data.
"""

from __future__ import annotations

from dataclasses import dataclass

from ida_controls.domain.consumption import SettlementConsumptionRecord
from ida_controls.domain.evidence import (
    ObservedSettlementEvidence,
    RpcChainEvidence,
)
from ida_controls.domain.finality import FinalityEvidence
from ida_controls.domain.instruction import ExpectedInstruction
from ida_controls.domain.transfer import ObservedTransfer
from ida_controls.domain.asset_registry import AssetRegistryEvidence
from ida_controls.reference.base_usdc import (
    BASE_MAINNET_CHAIN_ID,
    BASE_USDC_CONTRACT,
    BASE_USDC_REFERENCE_REGISTRY,
)


SENDER = "0x1111111111111111111111111111111111111111"
RECEIVER = "0x2222222222222222222222222222222222222222"
OTHER_RECEIVER = "0x3333333333333333333333333333333333333333"
TX_SUBMITTER = "0x4444444444444444444444444444444444444444"

NON_CANONICAL_USDC = "0x5555555555555555555555555555555555555555"

TX_HASH = "0x" + ("ab" * 32)
BLOCK_HASH = "0x" + ("cd" * 32)
BLOCK_NUMBER = 20_000_000
AMOUNT_RAW = 25_000_000


@dataclass(frozen=True, slots=True)
class DemoScenario:
    label: str
    description: str
    expected: ExpectedInstruction
    evidence: ObservedSettlementEvidence
    finality_evidence: FinalityEvidence | None
    history: tuple[SettlementConsumptionRecord, ...] | None
    asset_registry: AssetRegistryEvidence | None


def _expected(
    *,
    instruction_id: str = "INST-DEMO-001",
    token_contract: str = BASE_USDC_CONTRACT,
    receiver: str = RECEIVER,
) -> ExpectedInstruction:
    return ExpectedInstruction(
        instruction_id=instruction_id,
        chain_id=BASE_MAINNET_CHAIN_ID,
        token_contract=token_contract,
        token_sender=SENDER,
        token_receiver=receiver,
        amount_raw=AMOUNT_RAW,
        asset_id="USDC",
    )


def _transfer(
    *,
    token_contract: str = BASE_USDC_CONTRACT,
    receiver: str = RECEIVER,
) -> ObservedTransfer:
    return ObservedTransfer(
        chain_id=BASE_MAINNET_CHAIN_ID,
        block_number=BLOCK_NUMBER,
        block_hash=BLOCK_HASH,
        transaction_hash=TX_HASH,
        log_index=7,
        token_contract=token_contract,
        token_sender=SENDER,
        token_receiver=receiver,
        amount_raw=AMOUNT_RAW,
        token_decimals=6,
        tx_submitter=TX_SUBMITTER,
        receipt_status=1,
    )


def _evidence(
    transfer: ObservedTransfer,
) -> ObservedSettlementEvidence:
    return ObservedSettlementEvidence(
        transaction_hash=transfer.transaction_hash,
        receipt_status=transfer.receipt_status,
        transfer=transfer,
        chain_evidence=RpcChainEvidence(
            chain_id=BASE_MAINNET_CHAIN_ID,
        ),
    )


def _finality(
    transfer: ObservedTransfer,
    *,
    finalized_block_number: int,
) -> FinalityEvidence:
    return FinalityEvidence(
        canonical_block_number=transfer.block_number,
        canonical_block_hash=transfer.block_hash,
        safe_block_number=transfer.block_number + 2,
        safe_block_hash="0x" + ("ef" * 32),
        finalized_block_number=finalized_block_number,
        finalized_block_hash="0x" + ("12" * 32),
    )


def build_scenarios() -> dict[str, DemoScenario]:
    matching_transfer = _transfer()

    receiver_mismatch_transfer = _transfer(
        receiver=OTHER_RECEIVER,
    )

    noncanonical_transfer = _transfer(
        token_contract=NON_CANONICAL_USDC,
    )

    scenarios = [
        DemoScenario(
            label="Exact match — finalized",
            description=(
                "All modeled settlement terms match the observed transfer; "
                "the block is canonical and finalized; no prior consumption "
                "is present; the observed asset matches the trusted Base USDC "
                "reference."
            ),
            expected=_expected(),
            evidence=_evidence(matching_transfer),
            finality_evidence=_finality(
                matching_transfer,
                finalized_block_number=BLOCK_NUMBER + 1,
            ),
            history=(),
            asset_registry=BASE_USDC_REFERENCE_REGISTRY,
        ),
        DemoScenario(
            label="Receiver mismatch",
            description=(
                "Execution succeeds, but the ERC-20 Transfer recipient differs "
                "from the expected institutional settlement instruction."
            ),
            expected=_expected(),
            evidence=_evidence(receiver_mismatch_transfer),
            finality_evidence=_finality(
                receiver_mismatch_transfer,
                finalized_block_number=BLOCK_NUMBER + 1,
            ),
            history=(),
            asset_registry=BASE_USDC_REFERENCE_REGISTRY,
        ),
        DemoScenario(
            label="Pending finality",
            description=(
                "The transfer is canonical but its block has not yet entered "
                "the finalized range. The current FINALITY control therefore "
                "returns FAIL / FINALITY_NOT_REACHED; operationally this can "
                "represent a temporary pending state."
            ),
            expected=_expected(),
            evidence=_evidence(matching_transfer),
            finality_evidence=_finality(
                matching_transfer,
                finalized_block_number=BLOCK_NUMBER - 1,
            ),
            history=(),
            asset_registry=BASE_USDC_REFERENCE_REGISTRY,
        ),
        DemoScenario(
            label="Duplicate / replay",
            description=(
                "The same business instruction and exact blockchain transfer "
                "identity already appear in supplied processing history."
            ),
            expected=_expected(),
            evidence=_evidence(matching_transfer),
            finality_evidence=_finality(
                matching_transfer,
                finalized_block_number=BLOCK_NUMBER + 1,
            ),
            history=(
                SettlementConsumptionRecord(
                    instruction_id="INST-DEMO-001",
                    chain_id=matching_transfer.chain_id,
                    transaction_hash=matching_transfer.transaction_hash,
                    log_index=matching_transfer.log_index,
                ),
            ),
            asset_registry=BASE_USDC_REFERENCE_REGISTRY,
        ),
        DemoScenario(
            label="Partial evidence",
            description=(
                "Successful receipt and RPC chain identity are available, but "
                "no normalized Transfer evidence is available. Controls that "
                "depend on missing transfer evidence remain UNKNOWN rather than "
                "being guessed PASS or FAIL."
            ),
            expected=_expected(),
            evidence=ObservedSettlementEvidence(
                transaction_hash=TX_HASH,
                receipt_status=1,
                transfer=None,
                chain_evidence=RpcChainEvidence(
                    chain_id=BASE_MAINNET_CHAIN_ID,
                ),
            ),
            finality_evidence=None,
            history=(),
            asset_registry=BASE_USDC_REFERENCE_REGISTRY,
        ),
        DemoScenario(
            label="Expected = observed, but asset is non-canonical",
            description=(
                "The instruction and observed transfer both use the same "
                "non-canonical contract, so direct ASSET reconciliation can "
                "pass while independent CANONICAL_ASSET validation fails."
            ),
            expected=_expected(
                token_contract=NON_CANONICAL_USDC,
            ),
            evidence=_evidence(noncanonical_transfer),
            finality_evidence=_finality(
                noncanonical_transfer,
                finalized_block_number=BLOCK_NUMBER + 1,
            ),
            history=(),
            asset_registry=BASE_USDC_REFERENCE_REGISTRY,
        ),
    ]

    return {scenario.label: scenario for scenario in scenarios}
