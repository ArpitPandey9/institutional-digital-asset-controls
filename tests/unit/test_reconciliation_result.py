"""Tests for auditable reconciliation result types."""

from dataclasses import FrozenInstanceError
import unittest

from ida_controls.reconciliation.result import (
    ControlName,
    ControlStatus,
    EvidenceSource,
    FieldControlResult,
    ReasonCode,
)


class TestFieldControlResult(unittest.TestCase):

    def make_receiver_mismatch_result(self) -> FieldControlResult:
        return FieldControlResult(
            instruction_id="instruction-001",
            control_name=ControlName.RECEIVER,
            expected_value="0x1111111111111111111111111111111111111111",
            observed_value="0x2222222222222222222222222222222222222222",
            status=ControlStatus.FAIL,
            reason=ReasonCode.RECEIVER_MISMATCH,
            evidence_source=EvidenceSource.ERC20_TRANSFER_RECEIVER,
            transaction_hash="0xabc",
            log_index=1,
        )

    def test_receiver_mismatch_preserves_audit_evidence(self) -> None:
        result = self.make_receiver_mismatch_result()

        self.assertEqual(result.control_name, ControlName.RECEIVER)
        self.assertEqual(
            result.expected_value,
            "0x1111111111111111111111111111111111111111",
        )
        self.assertEqual(
            result.observed_value,
            "0x2222222222222222222222222222222222222222",
        )
        self.assertEqual(result.status, ControlStatus.FAIL)
        self.assertEqual(result.reason, ReasonCode.RECEIVER_MISMATCH)
        self.assertEqual(
            result.evidence_source,
            EvidenceSource.ERC20_TRANSFER_RECEIVER,
        )
        self.assertEqual(result.transaction_hash, "0xabc")
        self.assertEqual(result.log_index, 1)

    def test_unknown_can_represent_unavailable_observed_evidence(self) -> None:
        result = FieldControlResult(
            instruction_id="instruction-002",
            control_name=ControlName.RECEIVER,
            expected_value="0x1111111111111111111111111111111111111111",
            observed_value=None,
            status=ControlStatus.UNKNOWN,
            reason=ReasonCode.INSUFFICIENT_EVIDENCE,
            evidence_source=EvidenceSource.ERC20_TRANSFER_RECEIVER,
            transaction_hash=None,
            log_index=None,
        )

        self.assertIsNone(result.observed_value)
        self.assertEqual(result.status, ControlStatus.UNKNOWN)
        self.assertEqual(result.reason, ReasonCode.INSUFFICIENT_EVIDENCE)

    def test_field_control_result_is_immutable(self) -> None:
        result = self.make_receiver_mismatch_result()

        with self.assertRaises(FrozenInstanceError):
            result.status = ControlStatus.PASS


if __name__ == "__main__":
    unittest.main()
