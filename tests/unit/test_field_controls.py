"""Tests for field-level direct-transfer settlement controls."""

import unittest

from ida_controls.domain.instruction import ExpectedInstruction
from ida_controls.domain.transfer import ObservedTransfer
from ida_controls.reconciliation.field_controls import (
    evaluate_direct_transfer_controls,
)
from ida_controls.reconciliation.result import (
    ControlName,
    ControlStatus,
    EvidenceSource,
    ReasonCode,
)


class TestDirectTransferFieldControls(unittest.TestCase):

    def test_records_all_controls_when_sender_and_receiver_mismatch(self) -> None:
        modeled_expected = ExpectedInstruction(
            instruction_id="modeled-instruction-001",
            chain_id=8453,
            token_contract="0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
            token_sender="0x1111111111111111111111111111111111111111",
            token_receiver="0x2222222222222222222222222222222222222222",
            amount_raw=5408,
        )

        observed = ObservedTransfer(
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

        results = evaluate_direct_transfer_controls(
            modeled_expected,
            observed,
        )

        self.assertEqual(
            [result.control_name for result in results],
            [
                ControlName.EXECUTION,
                ControlName.CHAIN,
                ControlName.ASSET,
                ControlName.SENDER,
                ControlName.RECEIVER,
                ControlName.AMOUNT,
            ],
        )

        by_control = {
            result.control_name: result
            for result in results
        }

        self.assertEqual(
            by_control[ControlName.EXECUTION].status,
            ControlStatus.PASS,
        )
        self.assertEqual(
            by_control[ControlName.EXECUTION].reason,
            ReasonCode.EXECUTION_SUCCEEDED,
        )
        self.assertEqual(
            by_control[ControlName.EXECUTION].evidence_source,
            EvidenceSource.TRANSACTION_RECEIPT_STATUS,
        )

        self.assertEqual(
            by_control[ControlName.CHAIN].status,
            ControlStatus.PASS,
        )
        self.assertEqual(
            by_control[ControlName.CHAIN].reason,
            ReasonCode.MATCH,
        )
        self.assertEqual(
            by_control[ControlName.CHAIN].evidence_source,
            EvidenceSource.OBSERVED_TRANSFER_CHAIN_ID,
        )

        self.assertEqual(
            by_control[ControlName.ASSET].status,
            ControlStatus.PASS,
        )
        self.assertEqual(
            by_control[ControlName.ASSET].reason,
            ReasonCode.MATCH,
        )

        self.assertEqual(
            by_control[ControlName.SENDER].status,
            ControlStatus.FAIL,
        )
        self.assertEqual(
            by_control[ControlName.SENDER].reason,
            ReasonCode.SENDER_MISMATCH,
        )

        self.assertEqual(
            by_control[ControlName.RECEIVER].status,
            ControlStatus.FAIL,
        )
        self.assertEqual(
            by_control[ControlName.RECEIVER].reason,
            ReasonCode.RECEIVER_MISMATCH,
        )

        self.assertEqual(
            by_control[ControlName.AMOUNT].status,
            ControlStatus.PASS,
        )
        self.assertEqual(
            by_control[ControlName.AMOUNT].reason,
            ReasonCode.MATCH,
        )

        for result in results:
            self.assertEqual(
                result.transaction_hash,
                observed.transaction_hash,
            )
            self.assertEqual(
                result.log_index,
                observed.log_index,
            )


    def test_all_matching_controls_preserve_audit_lineage(self) -> None:
        modeled_expected = ExpectedInstruction(
            instruction_id="modeled-instruction-002",
            chain_id=8453,
            token_contract="0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
            token_sender="0x2b4ee3387008e5ff1a9996fc8b48d2fd61389037",
            token_receiver="0xe9030014f5dae217d0a152f02a043567b16c1abf",
            amount_raw=5408,
        )

        observed = ObservedTransfer(
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

        results = evaluate_direct_transfer_controls(
            modeled_expected,
            observed,
        )

        by_control = {
            result.control_name: result
            for result in results
        }

        expected_audit = {
            ControlName.EXECUTION: (
                1,
                1,
                ReasonCode.EXECUTION_SUCCEEDED,
                EvidenceSource.TRANSACTION_RECEIPT_STATUS,
            ),
            ControlName.CHAIN: (
                modeled_expected.chain_id,
                observed.chain_id,
                ReasonCode.MATCH,
                EvidenceSource.OBSERVED_TRANSFER_CHAIN_ID,
            ),
            ControlName.ASSET: (
                modeled_expected.token_contract,
                observed.token_contract,
                ReasonCode.MATCH,
                EvidenceSource.ERC20_LOG_EMITTER,
            ),
            ControlName.SENDER: (
                modeled_expected.token_sender,
                observed.token_sender,
                ReasonCode.MATCH,
                EvidenceSource.ERC20_TRANSFER_SENDER,
            ),
            ControlName.RECEIVER: (
                modeled_expected.token_receiver,
                observed.token_receiver,
                ReasonCode.MATCH,
                EvidenceSource.ERC20_TRANSFER_RECEIVER,
            ),
            ControlName.AMOUNT: (
                modeled_expected.amount_raw,
                observed.amount_raw,
                ReasonCode.MATCH,
                EvidenceSource.ERC20_TRANSFER_AMOUNT_RAW,
            ),
        }

        self.assertEqual(len(results), 6)

        for control_name, (
            expected_value,
            observed_value,
            reason,
            evidence_source,
        ) in expected_audit.items():
            result = by_control[control_name]

            self.assertEqual(result.status, ControlStatus.PASS)
            self.assertEqual(result.reason, reason)
            self.assertEqual(result.expected_value, expected_value)
            self.assertEqual(result.observed_value, observed_value)
            self.assertEqual(result.evidence_source, evidence_source)



    def test_records_chain_asset_and_amount_mismatches_independently(self) -> None:
        modeled_expected = ExpectedInstruction(
            instruction_id="modeled-instruction-003",
            chain_id=1,
            token_contract="0x1111111111111111111111111111111111111111",
            token_sender="0x2b4ee3387008e5ff1a9996fc8b48d2fd61389037",
            token_receiver="0xe9030014f5dae217d0a152f02a043567b16c1abf",
            amount_raw=6000,
        )

        observed = ObservedTransfer(
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

        results = evaluate_direct_transfer_controls(
            modeled_expected,
            observed,
        )

        by_control = {
            result.control_name: result
            for result in results
        }

        self.assertEqual(
            by_control[ControlName.EXECUTION].status,
            ControlStatus.PASS,
        )

        self.assertEqual(
            by_control[ControlName.CHAIN].status,
            ControlStatus.FAIL,
        )
        self.assertEqual(
            by_control[ControlName.CHAIN].reason,
            ReasonCode.CHAIN_ID_MISMATCH,
        )

        self.assertEqual(
            by_control[ControlName.ASSET].status,
            ControlStatus.FAIL,
        )
        self.assertEqual(
            by_control[ControlName.ASSET].reason,
            ReasonCode.TOKEN_CONTRACT_MISMATCH,
        )

        self.assertEqual(
            by_control[ControlName.SENDER].status,
            ControlStatus.PASS,
        )

        self.assertEqual(
            by_control[ControlName.RECEIVER].status,
            ControlStatus.PASS,
        )

        self.assertEqual(
            by_control[ControlName.AMOUNT].status,
            ControlStatus.FAIL,
        )
        self.assertEqual(
            by_control[ControlName.AMOUNT].reason,
            ReasonCode.AMOUNT_MISMATCH,
        )


if __name__ == "__main__":
    unittest.main()
