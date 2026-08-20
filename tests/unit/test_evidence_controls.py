"""Tests for evidence-aware settlement control evaluation."""

import unittest

from ida_controls.domain.evidence import (
    ObservedSettlementEvidence,
    RpcChainEvidence,
)
from ida_controls.domain.instruction import ExpectedInstruction
from ida_controls.domain.transfer import ObservedTransfer
from ida_controls.reconciliation.evidence_controls import (
    evaluate_direct_transfer_evidence,
)
from ida_controls.reconciliation.result import (
    ControlName,
    ControlStatus,
    EvidenceSource,
    ReasonCode,
)


class TestEvidenceAwareControls(unittest.TestCase):

    def test_missing_transfer_evidence_produces_unknown_field_controls(self) -> None:
        modeled_expected = ExpectedInstruction(
            instruction_id="modeled-instruction-004",
            chain_id=8453,
            token_contract="0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
            token_sender="0x2b4ee3387008e5ff1a9996fc8b48d2fd61389037",
            token_receiver="0xe9030014f5dae217d0a152f02a043567b16c1abf",
            amount_raw=5408,
        )

        evidence = ObservedSettlementEvidence(
            transaction_hash="0x942be0700ca598706f2d86770d6bafaec223ec3b42cc3a72b33f45e4d310f854",
            receipt_status=1,
            transfer=None,
        )

        results = evaluate_direct_transfer_evidence(
            modeled_expected,
            evidence,
        )

        by_control = {
            result.control_name: result
            for result in results
        }

        execution = by_control[ControlName.EXECUTION]

        self.assertEqual(execution.status, ControlStatus.PASS)
        self.assertEqual(
            execution.reason,
            ReasonCode.EXECUTION_SUCCEEDED,
        )
        self.assertEqual(execution.expected_value, 1)
        self.assertEqual(execution.observed_value, 1)
        self.assertEqual(
            execution.evidence_source,
            EvidenceSource.TRANSACTION_RECEIPT_STATUS,
        )

        unknown_controls = (
            ControlName.CHAIN,
            ControlName.ASSET,
            ControlName.SENDER,
            ControlName.RECEIVER,
            ControlName.AMOUNT,
        )

        for control_name in unknown_controls:
            result = by_control[control_name]

            self.assertEqual(result.status, ControlStatus.UNKNOWN)
            self.assertEqual(
                result.reason,
                ReasonCode.INSUFFICIENT_EVIDENCE,
            )
            self.assertIsNone(result.observed_value)
            self.assertIsNone(result.evidence_source)
            self.assertEqual(
                result.transaction_hash,
                evidence.transaction_hash,
            )
            self.assertIsNone(result.log_index)


    def test_reverted_receipt_fails_execution_and_leaves_transfer_controls_unknown(self) -> None:
        modeled_expected = ExpectedInstruction(
            instruction_id="modeled-instruction-005",
            chain_id=8453,
            token_contract="0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
            token_sender="0x2b4ee3387008e5ff1a9996fc8b48d2fd61389037",
            token_receiver="0xe9030014f5dae217d0a152f02a043567b16c1abf",
            amount_raw=5408,
        )

        evidence = ObservedSettlementEvidence(
            transaction_hash="0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            receipt_status=0,
            transfer=None,
        )

        results = evaluate_direct_transfer_evidence(
            modeled_expected,
            evidence,
        )

        by_control = {
            result.control_name: result
            for result in results
        }

        execution = by_control[ControlName.EXECUTION]

        self.assertEqual(execution.status, ControlStatus.FAIL)
        self.assertEqual(
            execution.reason,
            ReasonCode.EXECUTION_REVERTED,
        )
        self.assertEqual(execution.observed_value, 0)
        self.assertEqual(
            execution.evidence_source,
            EvidenceSource.TRANSACTION_RECEIPT_STATUS,
        )

        for control_name in (
            ControlName.CHAIN,
            ControlName.ASSET,
            ControlName.SENDER,
            ControlName.RECEIVER,
            ControlName.AMOUNT,
        ):
            result = by_control[control_name]

            self.assertEqual(result.status, ControlStatus.UNKNOWN)
            self.assertEqual(
                result.reason,
                ReasonCode.INSUFFICIENT_EVIDENCE,
            )
            self.assertIsNone(result.observed_value)
            self.assertIsNone(result.evidence_source)


    def test_missing_receipt_makes_all_controls_unknown(self) -> None:
        modeled_expected = ExpectedInstruction(
            instruction_id="modeled-instruction-006",
            chain_id=8453,
            token_contract="0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
            token_sender="0x2b4ee3387008e5ff1a9996fc8b48d2fd61389037",
            token_receiver="0xe9030014f5dae217d0a152f02a043567b16c1abf",
            amount_raw=5408,
        )

        evidence = ObservedSettlementEvidence(
            transaction_hash=None,
            receipt_status=None,
            transfer=None,
        )

        results = evaluate_direct_transfer_evidence(
            modeled_expected,
            evidence,
        )

        self.assertEqual(len(results), 6)

        for result in results:
            self.assertEqual(result.status, ControlStatus.UNKNOWN)
            self.assertEqual(
                result.reason,
                ReasonCode.INSUFFICIENT_EVIDENCE,
            )
            self.assertIsNone(result.observed_value)
            self.assertIsNone(result.evidence_source)
            self.assertIsNone(result.transaction_hash)
            self.assertIsNone(result.log_index)


    def test_complete_transfer_evidence_reuses_field_level_controls(self) -> None:
        modeled_expected = ExpectedInstruction(
            instruction_id="modeled-instruction-007",
            chain_id=8453,
            token_contract="0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
            token_sender="0x2b4ee3387008e5ff1a9996fc8b48d2fd61389037",
            token_receiver="0xe9030014f5dae217d0a152f02a043567b16c1abf",
            amount_raw=5408,
        )

        transfer = ObservedTransfer(
            chain_id=8453,
            block_number=50058636,
            block_hash="0x78a85bde41874f70bb5acbba6e6cd234d5f57282c25e1e9853939e9670da9b22",
            transaction_hash="0x942be0700ca598706f2d86770d6bafaec223ec3b42cc3a72b33f45e4d310f854",
            log_index=1,
            token_contract="0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
            token_sender="0x2b4ee3387008e5ff1a9996fc8b48d2fd61389037",
            token_receiver="0xe9030014f5dae217d0a152f02a043567b16c1abf",
            amount_raw=5408,
            token_decimals=6,
            tx_submitter="0xa32ccda98ba7529705a059bd2d213da8de10d101",
            receipt_status=1,
        )

        evidence = ObservedSettlementEvidence(
            transaction_hash=transfer.transaction_hash,
            receipt_status=transfer.receipt_status,
            transfer=transfer,
        )

        results = evaluate_direct_transfer_evidence(
            modeled_expected,
            evidence,
        )

        self.assertEqual(len(results), 6)

        for result in results:
            self.assertEqual(result.status, ControlStatus.PASS)
            self.assertEqual(
                result.transaction_hash,
                transfer.transaction_hash,
            )
            self.assertEqual(result.log_index, transfer.log_index)


    def test_rpc_chain_evidence_allows_chain_control_without_transfer(self) -> None:
        modeled_expected = ExpectedInstruction(
            instruction_id="modeled-instruction-008",
            chain_id=8453,
            token_contract="0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
            token_sender="0x2b4ee3387008e5ff1a9996fc8b48d2fd61389037",
            token_receiver="0xe9030014f5dae217d0a152f02a043567b16c1abf",
            amount_raw=5408,
        )

        evidence = ObservedSettlementEvidence(
            transaction_hash=(
                "0x942be0700ca598706f2d86770d6bafaec223ec3b42cc3a72b33f45e4d310f854"
            ),
            receipt_status=1,
            transfer=None,
            chain_evidence=RpcChainEvidence(
                chain_id=8453,
            ),
        )

        results = evaluate_direct_transfer_evidence(
            modeled_expected,
            evidence,
        )

        by_control = {
            result.control_name: result
            for result in results
        }

        execution = by_control[ControlName.EXECUTION]
        self.assertEqual(execution.status, ControlStatus.PASS)

        chain = by_control[ControlName.CHAIN]
        self.assertEqual(chain.status, ControlStatus.PASS)
        self.assertEqual(chain.reason, ReasonCode.MATCH)
        self.assertEqual(chain.expected_value, 8453)
        self.assertEqual(chain.observed_value, 8453)
        self.assertEqual(
            chain.evidence_source,
            EvidenceSource.RPC_CHAIN_ID,
        )

        receiver = by_control[ControlName.RECEIVER]
        self.assertEqual(receiver.status, ControlStatus.UNKNOWN)
        self.assertEqual(
            receiver.reason,
            ReasonCode.INSUFFICIENT_EVIDENCE,
        )
        self.assertIsNone(receiver.observed_value)
        self.assertIsNone(receiver.evidence_source)


    def test_rpc_chain_mismatch_fails_chain_without_transfer(self) -> None:
        modeled_expected = ExpectedInstruction(
            instruction_id="modeled-instruction-009",
            chain_id=8453,
            token_contract="0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
            token_sender="0x2b4ee3387008e5ff1a9996fc8b48d2fd61389037",
            token_receiver="0xe9030014f5dae217d0a152f02a043567b16c1abf",
            amount_raw=5408,
        )

        evidence = ObservedSettlementEvidence(
            transaction_hash=(
                "0x942be0700ca598706f2d86770d6bafaec223ec3b42cc3a72b33f45e4d310f854"
            ),
            receipt_status=1,
            transfer=None,
            chain_evidence=RpcChainEvidence(chain_id=1),
        )

        results = evaluate_direct_transfer_evidence(
            modeled_expected,
            evidence,
        )

        by_control = {
            result.control_name: result
            for result in results
        }

        chain = by_control[ControlName.CHAIN]
        self.assertEqual(chain.status, ControlStatus.FAIL)
        self.assertEqual(
            chain.reason,
            ReasonCode.CHAIN_ID_MISMATCH,
        )
        self.assertEqual(chain.expected_value, 8453)
        self.assertEqual(chain.observed_value, 1)
        self.assertEqual(
            chain.evidence_source,
            EvidenceSource.RPC_CHAIN_ID,
        )

        receiver = by_control[ControlName.RECEIVER]
        self.assertEqual(receiver.status, ControlStatus.UNKNOWN)
        self.assertEqual(
            receiver.reason,
            ReasonCode.INSUFFICIENT_EVIDENCE,
        )


if __name__ == "__main__":
    unittest.main()
