"""Tests for settlement-control orchestration."""

import unittest

from ida_controls.domain.consumption import SettlementConsumptionRecord
from ida_controls.domain.evidence import (
    ObservedSettlementEvidence,
    RpcChainEvidence,
)
from ida_controls.domain.finality import FinalityEvidence
from ida_controls.domain.instruction import ExpectedInstruction
from ida_controls.domain.transfer import ObservedTransfer
from ida_controls.reconciliation.orchestration import (
    evaluate_settlement_control_bundle,
)
from ida_controls.reconciliation.result import (
    ControlName,
    ControlStatus,
    ReasonCode,
)
from ida_controls.reference.base_usdc import (
    BASE_MAINNET_CHAIN_ID,
    BASE_USDC_CONTRACT,
    BASE_USDC_REFERENCE_REGISTRY,
)


OTHER_CONTRACT = "0x1111111111111111111111111111111111111111"
TX_HASH = (
    "0x942be0700ca598706f2d86770d6bafaec223ec3b"
    "42cc3a72b33f45e4d310f854"
)
BLOCK_HASH = (
    "0x78a85bde41874f70bb5acbba6e6cd234d5f57282"
    "c25e1e9853939e9670da9b22"
)


def expected_instruction(
    *,
    token_contract: str = BASE_USDC_CONTRACT,
) -> ExpectedInstruction:
    return ExpectedInstruction(
        instruction_id="INST-ORCH-001",
        chain_id=BASE_MAINNET_CHAIN_ID,
        token_contract=token_contract,
        token_sender="0x2b4ee3387008e5ff1a9996fc8b48d2fd61389037",
        token_receiver="0xe9030014f5dae217d0a152f02a043567b16c1abf",
        amount_raw=5408,
        asset_id="USDC",
    )


def observed_transfer(
    *,
    token_contract: str = BASE_USDC_CONTRACT,
) -> ObservedTransfer:
    return ObservedTransfer(
        chain_id=BASE_MAINNET_CHAIN_ID,
        block_number=50058636,
        block_hash=BLOCK_HASH,
        transaction_hash=TX_HASH,
        log_index=1,
        token_contract=token_contract,
        token_sender="0x2b4ee3387008e5ff1a9996fc8b48d2fd61389037",
        token_receiver="0xe9030014f5dae217d0a152f02a043567b16c1abf",
        amount_raw=5408,
        token_decimals=6,
        tx_submitter="0xa32ccda98ba7529705a059bd2d213da8de10d101",
        receipt_status=1,
    )


def complete_evidence(
    transfer: ObservedTransfer,
) -> ObservedSettlementEvidence:
    return ObservedSettlementEvidence(
        transaction_hash=transfer.transaction_hash,
        receipt_status=1,
        transfer=transfer,
        chain_evidence=RpcChainEvidence(
            chain_id=BASE_MAINNET_CHAIN_ID,
        ),
    )


def finalized_evidence(
    transfer: ObservedTransfer,
) -> FinalityEvidence:
    return FinalityEvidence(
        canonical_block_number=transfer.block_number,
        canonical_block_hash=transfer.block_hash,
        safe_block_number=transfer.block_number + 10,
        safe_block_hash="0xsafe",
        finalized_block_number=transfer.block_number + 5,
        finalized_block_hash="0xfinalized",
    )


class TestSettlementControlOrchestration(unittest.TestCase):

    def test_complete_evidence_preserves_ten_independent_findings(self) -> None:
        transfer = observed_transfer()

        bundle = evaluate_settlement_control_bundle(
            expected_instruction(),
            complete_evidence(transfer),
            finality_evidence=finalized_evidence(transfer),
            history=(),
            asset_registry=BASE_USDC_REFERENCE_REGISTRY,
        )

        self.assertEqual(
            [finding.control_name for finding in bundle.findings],
            [
                ControlName.EXECUTION,
                ControlName.CHAIN,
                ControlName.ASSET,
                ControlName.SENDER,
                ControlName.RECEIVER,
                ControlName.AMOUNT,
                ControlName.FINALITY,
                ControlName.INSTRUCTION_UNIQUENESS,
                ControlName.TRANSFER_UNIQUENESS,
                ControlName.CANONICAL_ASSET,
            ],
        )

        self.assertEqual(len(bundle.findings), 10)

        for finding in bundle.findings:
            self.assertEqual(finding.status, ControlStatus.PASS)

    def test_bundle_does_not_create_an_overall_settlement_status(self) -> None:
        transfer = observed_transfer()

        bundle = evaluate_settlement_control_bundle(
            expected_instruction(),
            complete_evidence(transfer),
            finality_evidence=finalized_evidence(transfer),
            history=(),
            asset_registry=BASE_USDC_REFERENCE_REGISTRY,
        )

        self.assertFalse(hasattr(bundle, "status"))
        self.assertFalse(hasattr(bundle, "overall_status"))

    def test_missing_transfer_preserves_transfer_dependent_unknowns(self) -> None:
        evidence = ObservedSettlementEvidence(
            transaction_hash=TX_HASH,
            receipt_status=1,
            transfer=None,
            chain_evidence=RpcChainEvidence(
                chain_id=BASE_MAINNET_CHAIN_ID,
            ),
        )

        bundle = evaluate_settlement_control_bundle(
            expected_instruction(),
            evidence,
            finality_evidence=None,
            history=(),
            asset_registry=BASE_USDC_REFERENCE_REGISTRY,
        )

        by_control = {
            finding.control_name: finding
            for finding in bundle.findings
        }

        self.assertEqual(
            by_control[ControlName.INSTRUCTION_UNIQUENESS].status,
            ControlStatus.PASS,
        )
        self.assertEqual(
            by_control[ControlName.INSTRUCTION_UNIQUENESS].reason,
            ReasonCode.NO_PRIOR_INSTRUCTION_CONSUMPTION,
        )

        for control_name in (
            ControlName.TRANSFER_UNIQUENESS,
            ControlName.FINALITY,
            ControlName.CANONICAL_ASSET,
        ):
            self.assertEqual(
                by_control[control_name].status,
                ControlStatus.UNKNOWN,
            )
            self.assertEqual(
                by_control[control_name].reason,
                ReasonCode.INSUFFICIENT_EVIDENCE,
            )

        self.assertIsNone(bundle.finality_control)
        self.assertEqual(
            len(bundle.duplicate_replay_controls),
            2,
        )
        self.assertIsNone(bundle.canonical_asset_control)

    def test_consumed_instruction_fails_even_when_transfer_is_missing(self) -> None:
        evidence = ObservedSettlementEvidence(
            transaction_hash=TX_HASH,
            receipt_status=1,
            transfer=None,
            chain_evidence=RpcChainEvidence(
                chain_id=BASE_MAINNET_CHAIN_ID,
            ),
        )

        history = (
            SettlementConsumptionRecord(
                instruction_id="INST-ORCH-001",
                chain_id=BASE_MAINNET_CHAIN_ID,
                transaction_hash="0xprior",
                log_index=0,
            ),
        )

        bundle = evaluate_settlement_control_bundle(
            expected_instruction(),
            evidence,
            finality_evidence=None,
            history=history,
            asset_registry=BASE_USDC_REFERENCE_REGISTRY,
        )

        by_control = {
            finding.control_name: finding
            for finding in bundle.findings
        }

        self.assertEqual(
            by_control[ControlName.INSTRUCTION_UNIQUENESS].status,
            ControlStatus.FAIL,
        )
        self.assertEqual(
            by_control[ControlName.INSTRUCTION_UNIQUENESS].reason,
            ReasonCode.INSTRUCTION_ALREADY_CONSUMED,
        )

        duplicate_by_control = {
            result.control_name: result
            for result in bundle.duplicate_replay_controls
        }

        self.assertEqual(
            duplicate_by_control[
                ControlName.INSTRUCTION_UNIQUENESS
            ].matched_records,
            history,
        )

        for control_name in (
            ControlName.TRANSFER_UNIQUENESS,
            ControlName.FINALITY,
            ControlName.CANONICAL_ASSET,
        ):
            self.assertEqual(
                by_control[control_name].status,
                ControlStatus.UNKNOWN,
            )

    def test_instruction_uniqueness_is_unknown_when_history_is_unavailable_and_transfer_is_missing(self) -> None:
        evidence = ObservedSettlementEvidence(
            transaction_hash=TX_HASH,
            receipt_status=1,
            transfer=None,
            chain_evidence=RpcChainEvidence(
                chain_id=BASE_MAINNET_CHAIN_ID,
            ),
        )

        bundle = evaluate_settlement_control_bundle(
            expected_instruction(),
            evidence,
            finality_evidence=None,
            history=None,
            asset_registry=BASE_USDC_REFERENCE_REGISTRY,
        )

        by_control = {
            finding.control_name: finding
            for finding in bundle.findings
        }

        self.assertEqual(
            by_control[ControlName.INSTRUCTION_UNIQUENESS].status,
            ControlStatus.UNKNOWN,
        )
        self.assertEqual(
            by_control[ControlName.INSTRUCTION_UNIQUENESS].reason,
            ReasonCode.INSUFFICIENT_EVIDENCE,
        )


    def test_missing_finality_evidence_is_preserved_without_aggregation(self) -> None:
        transfer = observed_transfer()

        bundle = evaluate_settlement_control_bundle(
            expected_instruction(),
            complete_evidence(transfer),
            finality_evidence=None,
            history=(),
            asset_registry=BASE_USDC_REFERENCE_REGISTRY,
        )

        by_control = {
            finding.control_name: finding
            for finding in bundle.findings
        }

        self.assertEqual(
            by_control[ControlName.FINALITY].status,
            ControlStatus.UNKNOWN,
        )
        self.assertEqual(
            by_control[ControlName.FINALITY].reason,
            ReasonCode.INSUFFICIENT_EVIDENCE,
        )

        self.assertEqual(
            by_control[ControlName.CANONICAL_ASSET].status,
            ControlStatus.PASS,
        )

    def test_duplicate_and_replay_failures_are_preserved_independently(self) -> None:
        transfer = observed_transfer()

        history = (
            SettlementConsumptionRecord(
                instruction_id="INST-ORCH-001",
                chain_id=transfer.chain_id,
                transaction_hash=transfer.transaction_hash,
                log_index=transfer.log_index,
            ),
        )

        bundle = evaluate_settlement_control_bundle(
            expected_instruction(),
            complete_evidence(transfer),
            finality_evidence=finalized_evidence(transfer),
            history=history,
            asset_registry=BASE_USDC_REFERENCE_REGISTRY,
        )

        by_control = {
            finding.control_name: finding
            for finding in bundle.findings
        }

        self.assertEqual(
            by_control[ControlName.INSTRUCTION_UNIQUENESS].status,
            ControlStatus.FAIL,
        )
        self.assertEqual(
            by_control[ControlName.TRANSFER_UNIQUENESS].status,
            ControlStatus.FAIL,
        )

        self.assertEqual(
            len(bundle.duplicate_replay_controls),
            2,
        )
        self.assertEqual(
            len(bundle.duplicate_replay_controls[0].matched_records),
            1,
        )
        self.assertEqual(
            len(bundle.duplicate_replay_controls[1].matched_records),
            1,
        )

    def test_matching_noncanonical_execution_preserves_both_asset_findings(self) -> None:
        transfer = observed_transfer(
            token_contract=OTHER_CONTRACT,
        )

        bundle = evaluate_settlement_control_bundle(
            expected_instruction(
                token_contract=OTHER_CONTRACT,
            ),
            complete_evidence(transfer),
            finality_evidence=finalized_evidence(transfer),
            history=(),
            asset_registry=BASE_USDC_REFERENCE_REGISTRY,
        )

        by_control = {
            finding.control_name: finding
            for finding in bundle.findings
        }

        self.assertEqual(
            by_control[ControlName.ASSET].status,
            ControlStatus.PASS,
        )
        self.assertEqual(
            by_control[ControlName.CANONICAL_ASSET].status,
            ControlStatus.FAIL,
        )
        self.assertEqual(
            by_control[ControlName.CANONICAL_ASSET].reason,
            ReasonCode.CANONICAL_ASSET_MISMATCH,
        )


if __name__ == "__main__":
    unittest.main()
