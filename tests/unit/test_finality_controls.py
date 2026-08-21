"""Unit tests for protocol-aware settlement finality controls."""

from __future__ import annotations

import unittest

from ida_controls.domain.finality import FinalityEvidence
from ida_controls.domain.transfer import ObservedTransfer
from ida_controls.reconciliation.finality_controls import (
    evaluate_finality_control,
)
from ida_controls.reconciliation.result import (
    ControlStatus,
    ReasonCode,
)


class TestFinalityControls(unittest.TestCase):
    def test_finality_passes_when_transfer_block_is_canonical_and_finalized(
        self,
    ) -> None:
        transfer = ObservedTransfer(
            chain_id=8453,
            block_number=100,
            block_hash="0xaaa",
            transaction_hash="0xtx",
            log_index=1,
            token_contract="0xtoken",
            token_sender="0xsender",
            token_receiver="0xreceiver",
            amount_raw=5408,
            token_decimals=6,
            tx_submitter="0xsubmitter",
            receipt_status=1,
        )

        finality_evidence = FinalityEvidence(
            canonical_block_number=100,
            canonical_block_hash="0xaaa",
            safe_block_number=108,
            safe_block_hash="0xsafe",
            finalized_block_number=105,
            finalized_block_hash="0xfinal",
        )

        result = evaluate_finality_control(
            transfer,
            finality_evidence,
        )

        self.assertEqual(result.status, ControlStatus.PASS)
        self.assertEqual(
            result.reason,
            ReasonCode.FINALITY_REACHED,
        )


    def test_finality_fails_when_observed_block_is_not_canonical(
        self,
    ) -> None:
        transfer = ObservedTransfer(
            chain_id=8453,
            block_number=100,
            block_hash="0xaaa",
            transaction_hash="0xtx",
            log_index=1,
            token_contract="0xtoken",
            token_sender="0xsender",
            token_receiver="0xreceiver",
            amount_raw=5408,
            token_decimals=6,
            tx_submitter="0xsubmitter",
            receipt_status=1,
        )

        finality_evidence = FinalityEvidence(
            canonical_block_number=100,
            canonical_block_hash="0xbbb",
            safe_block_number=108,
            safe_block_hash="0xsafe",
            finalized_block_number=105,
            finalized_block_hash="0xfinal",
        )

        result = evaluate_finality_control(
            transfer,
            finality_evidence,
        )

        self.assertEqual(result.status, ControlStatus.FAIL)
        self.assertEqual(
            result.reason,
            ReasonCode.BLOCK_NOT_CANONICAL,
        )
        self.assertEqual(
            result.transaction_block_hash,
            "0xaaa",
        )
        self.assertEqual(
            result.canonical_block_hash,
            "0xbbb",
        )

    def test_finality_is_pending_when_canonical_block_is_not_yet_finalized(
        self,
    ) -> None:
        transfer = ObservedTransfer(
            chain_id=8453,
            block_number=110,
            block_hash="0xaaa",
            transaction_hash="0xtx",
            log_index=1,
            token_contract="0xtoken",
            token_sender="0xsender",
            token_receiver="0xreceiver",
            amount_raw=5408,
            token_decimals=6,
            tx_submitter="0xsubmitter",
            receipt_status=1,
        )

        finality_evidence = FinalityEvidence(
            canonical_block_number=110,
            canonical_block_hash="0xaaa",
            safe_block_number=112,
            safe_block_hash="0xsafe",
            finalized_block_number=105,
            finalized_block_hash="0xfinal",
        )

        result = evaluate_finality_control(
            transfer,
            finality_evidence,
        )

        self.assertEqual(result.status, ControlStatus.FAIL)
        self.assertEqual(
            result.reason,
            ReasonCode.FINALITY_NOT_REACHED,
        )
        self.assertEqual(
            result.transaction_block_number,
            110,
        )
        self.assertEqual(
            result.finalized_block_number,
            105,
        )


    def test_finality_is_unknown_when_finality_evidence_is_unavailable(
        self,
    ) -> None:
        transfer = ObservedTransfer(
            chain_id=8453,
            block_number=100,
            block_hash="0xaaa",
            transaction_hash="0xtx",
            log_index=1,
            token_contract="0xtoken",
            token_sender="0xsender",
            token_receiver="0xreceiver",
            amount_raw=5408,
            token_decimals=6,
            tx_submitter="0xsubmitter",
            receipt_status=1,
        )

        result = evaluate_finality_control(
            transfer,
            None,
        )

        self.assertEqual(
            result.status,
            ControlStatus.UNKNOWN,
        )
        self.assertEqual(
            result.reason,
            ReasonCode.INSUFFICIENT_EVIDENCE,
        )
        self.assertEqual(
            result.transaction_hash,
            transfer.transaction_hash,
        )
        self.assertEqual(
            result.transaction_block_number,
            100,
        )
        self.assertEqual(
            result.transaction_block_hash,
            "0xaaa",
        )
        self.assertIsNone(result.canonical_block_hash)
        self.assertIsNone(result.finalized_block_number)


if __name__ == "__main__":
    unittest.main()
