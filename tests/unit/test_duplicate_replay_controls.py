"""Unit tests for duplicate and replay settlement controls."""

from __future__ import annotations

import unittest

from ida_controls.domain.consumption import SettlementConsumptionRecord
from ida_controls.domain.instruction import ExpectedInstruction
from ida_controls.domain.transfer import ObservedTransfer
from ida_controls.reconciliation.duplicate_replay_controls import (
    evaluate_duplicate_replay_controls,
)
from ida_controls.reconciliation.result import (
    ControlName,
    ControlStatus,
    ReasonCode,
)


class TestDuplicateReplayControls(unittest.TestCase):
    def make_instruction(self, instruction_id: str) -> ExpectedInstruction:
        return ExpectedInstruction(
            instruction_id=instruction_id,
            chain_id=8453,
            token_contract="0xtoken",
            token_sender="0xsender",
            token_receiver="0xreceiver",
            amount_raw=5408,
        )

    def make_transfer(
        self,
        transaction_hash: str,
        log_index: int,
        chain_id: int = 8453,
    ) -> ObservedTransfer:
        return ObservedTransfer(
            chain_id=chain_id,
            block_number=100,
            block_hash="0xblock",
            transaction_hash=transaction_hash,
            log_index=log_index,
            token_contract="0xtoken",
            token_sender="0xsender",
            token_receiver="0xreceiver",
            amount_raw=5408,
            token_decimals=6,
            tx_submitter="0xsubmitter",
            receipt_status=1,
        )

    def record(
        self,
        instruction_id: str,
        transaction_hash: str,
        log_index: int,
        chain_id: int = 8453,
    ) -> SettlementConsumptionRecord:
        return SettlementConsumptionRecord(
            instruction_id=instruction_id,
            chain_id=chain_id,
            transaction_hash=transaction_hash,
            log_index=log_index,
        )

    @staticmethod
    def by_control(results):
        return {
            result.control_name: result
            for result in results
        }

    def test_new_instruction_and_new_transfer_pass_both_controls(self) -> None:
        results = evaluate_duplicate_replay_controls(
            self.make_instruction("INST-1401"),
            self.make_transfer("0xbbb", 2),
            history=(),
        )

        by_control = self.by_control(results)

        instruction = by_control[ControlName.INSTRUCTION_UNIQUENESS]
        transfer = by_control[ControlName.TRANSFER_UNIQUENESS]

        self.assertEqual(instruction.status, ControlStatus.PASS)
        self.assertEqual(
            instruction.reason,
            ReasonCode.NO_PRIOR_INSTRUCTION_CONSUMPTION,
        )
        self.assertEqual(instruction.matched_records, ())

        self.assertEqual(transfer.status, ControlStatus.PASS)
        self.assertEqual(
            transfer.reason,
            ReasonCode.NO_PRIOR_TRANSFER_CONSUMPTION,
        )
        self.assertEqual(transfer.matched_records, ())

    def test_reused_instruction_fails_instruction_control_only(self) -> None:
        prior = self.record("INST-1500", "0xaaa", 1)

        results = evaluate_duplicate_replay_controls(
            self.make_instruction("INST-1500"),
            self.make_transfer("0xbbb", 2),
            history=(prior,),
        )

        by_control = self.by_control(results)

        instruction = by_control[ControlName.INSTRUCTION_UNIQUENESS]
        transfer = by_control[ControlName.TRANSFER_UNIQUENESS]

        self.assertEqual(instruction.status, ControlStatus.FAIL)
        self.assertEqual(
            instruction.reason,
            ReasonCode.INSTRUCTION_ALREADY_CONSUMED,
        )
        self.assertEqual(instruction.matched_records, (prior,))

        self.assertEqual(transfer.status, ControlStatus.PASS)

    def test_reused_transfer_fails_transfer_control_only(self) -> None:
        prior = self.record("INST-1600", "0xaaa", 1)

        results = evaluate_duplicate_replay_controls(
            self.make_instruction("INST-1601"),
            self.make_transfer("0xaaa", 1),
            history=(prior,),
        )

        by_control = self.by_control(results)

        instruction = by_control[ControlName.INSTRUCTION_UNIQUENESS]
        transfer = by_control[ControlName.TRANSFER_UNIQUENESS]

        self.assertEqual(instruction.status, ControlStatus.PASS)

        self.assertEqual(transfer.status, ControlStatus.FAIL)
        self.assertEqual(
            transfer.reason,
            ReasonCode.TRANSFER_ALREADY_CONSUMED,
        )
        self.assertEqual(transfer.matched_records, (prior,))

    def test_exact_duplicate_fails_and_preserves_both_findings(self) -> None:
        prior = self.record("INST-1700", "0xaaa", 1)

        results = evaluate_duplicate_replay_controls(
            self.make_instruction("INST-1700"),
            self.make_transfer("0xaaa", 1),
            history=(prior,),
        )

        by_control = self.by_control(results)

        instruction = by_control[ControlName.INSTRUCTION_UNIQUENESS]
        transfer = by_control[ControlName.TRANSFER_UNIQUENESS]

        self.assertEqual(instruction.status, ControlStatus.FAIL)
        self.assertEqual(
            instruction.reason,
            ReasonCode.INSTRUCTION_ALREADY_CONSUMED,
        )
        self.assertEqual(instruction.matched_records, (prior,))

        self.assertEqual(transfer.status, ControlStatus.FAIL)
        self.assertEqual(
            transfer.reason,
            ReasonCode.TRANSFER_ALREADY_CONSUMED,
        )
        self.assertEqual(transfer.matched_records, (prior,))

    def test_independent_collisions_preserve_both_historical_matches(self) -> None:
        instruction_prior = self.record("INST-1800", "0xaaa", 1)
        transfer_prior = self.record("INST-1801", "0xbbb", 2)

        results = evaluate_duplicate_replay_controls(
            self.make_instruction("INST-1800"),
            self.make_transfer("0xbbb", 2),
            history=(instruction_prior, transfer_prior),
        )

        by_control = self.by_control(results)

        instruction = by_control[ControlName.INSTRUCTION_UNIQUENESS]
        transfer = by_control[ControlName.TRANSFER_UNIQUENESS]

        self.assertEqual(instruction.status, ControlStatus.FAIL)
        self.assertEqual(
            instruction.matched_records,
            (instruction_prior,),
        )

        self.assertEqual(transfer.status, ControlStatus.FAIL)
        self.assertEqual(
            transfer.matched_records,
            (transfer_prior,),
        )

    def test_unavailable_history_makes_both_controls_unknown(self) -> None:
        results = evaluate_duplicate_replay_controls(
            self.make_instruction("INST-1900"),
            self.make_transfer("0xccc", 3),
            history=None,
        )

        for result in results:
            self.assertEqual(result.status, ControlStatus.UNKNOWN)
            self.assertEqual(
                result.reason,
                ReasonCode.INSUFFICIENT_EVIDENCE,
            )
            self.assertEqual(result.matched_records, ())

    def test_same_transaction_hash_with_different_log_index_is_not_same_transfer(
        self,
    ) -> None:
        prior = self.record("INST-2000", "0xaaa", 1)

        results = evaluate_duplicate_replay_controls(
            self.make_instruction("INST-2001"),
            self.make_transfer("0xaaa", 2),
            history=(prior,),
        )

        by_control = self.by_control(results)

        self.assertEqual(
            by_control[ControlName.INSTRUCTION_UNIQUENESS].status,
            ControlStatus.PASS,
        )
        self.assertEqual(
            by_control[ControlName.TRANSFER_UNIQUENESS].status,
            ControlStatus.PASS,
        )

    def test_transaction_hash_comparison_is_case_insensitive(self) -> None:
        prior = self.record("INST-2100", "0xAbC", 4)

        results = evaluate_duplicate_replay_controls(
            self.make_instruction("INST-2101"),
            self.make_transfer("0xabc", 4),
            history=(prior,),
        )

        by_control = self.by_control(results)

        self.assertEqual(
            by_control[ControlName.TRANSFER_UNIQUENESS].status,
            ControlStatus.FAIL,
        )


    def test_transfer_identity_is_scoped_by_chain_id(self) -> None:
        prior = self.record(
            "INST-2200",
            "0xaaa",
            1,
            chain_id=1,
        )

        results = evaluate_duplicate_replay_controls(
            self.make_instruction("INST-2201"),
            self.make_transfer(
                "0xaaa",
                1,
                chain_id=8453,
            ),
            history=(prior,),
        )

        by_control = self.by_control(results)
        transfer = by_control[ControlName.TRANSFER_UNIQUENESS]

        self.assertEqual(transfer.status, ControlStatus.PASS)
        self.assertEqual(transfer.chain_id, 8453)

    def test_preserves_all_matching_historical_records(self) -> None:
        instruction_prior_1 = self.record(
            "INST-2300",
            "0xaaa",
            1,
        )
        instruction_prior_2 = self.record(
            "INST-2300",
            "0xbbb",
            2,
        )
        transfer_prior_1 = self.record(
            "INST-2301",
            "0xccc",
            3,
        )
        transfer_prior_2 = self.record(
            "INST-2302",
            "0xccc",
            3,
        )

        results = evaluate_duplicate_replay_controls(
            self.make_instruction("INST-2300"),
            self.make_transfer("0xccc", 3),
            history=(
                instruction_prior_1,
                instruction_prior_2,
                transfer_prior_1,
                transfer_prior_2,
            ),
        )

        by_control = self.by_control(results)

        self.assertEqual(
            by_control[
                ControlName.INSTRUCTION_UNIQUENESS
            ].matched_records,
            (
                instruction_prior_1,
                instruction_prior_2,
            ),
        )
        self.assertEqual(
            by_control[
                ControlName.TRANSFER_UNIQUENESS
            ].matched_records,
            (
                transfer_prior_1,
                transfer_prior_2,
            ),
        )


if __name__ == "__main__":
    unittest.main()
