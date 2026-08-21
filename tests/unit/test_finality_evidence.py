"""Unit tests for protocol-aware finality evidence construction."""

from __future__ import annotations

import unittest
from unittest.mock import call, patch

from ida_controls.chains.finality import build_finality_evidence


class TestFinalityEvidence(unittest.TestCase):
    def test_build_finality_evidence_reads_canonical_safe_and_finalized_blocks(
        self,
    ) -> None:
        rpc_url = "https://example.invalid"

        canonical_block = {
            "number": "0x64",
            "hash": "0xaaa",
        }
        safe_block = {
            "number": "0x6c",
            "hash": "0xsafe",
        }
        finalized_block = {
            "number": "0x69",
            "hash": "0xfinal",
        }

        with (
            patch(
                "ida_controls.chains.finality.get_block",
                return_value=canonical_block,
            ) as get_block_mock,
            patch(
                "ida_controls.chains.finality.get_block_by_tag",
                side_effect=[safe_block, finalized_block],
            ) as get_block_by_tag_mock,
        ):
            evidence = build_finality_evidence(
                rpc_url,
                transaction_block_number=100,
            )

        self.assertEqual(evidence.canonical_block_number, 100)
        self.assertEqual(evidence.canonical_block_hash, "0xaaa")

        self.assertEqual(evidence.safe_block_number, 108)
        self.assertEqual(evidence.safe_block_hash, "0xsafe")

        self.assertEqual(evidence.finalized_block_number, 105)
        self.assertEqual(evidence.finalized_block_hash, "0xfinal")

        get_block_mock.assert_called_once_with(
            rpc_url,
            100,
            full_transactions=False,
        )

        self.assertEqual(
            get_block_by_tag_mock.call_args_list,
            [
                call(
                    rpc_url,
                    "safe",
                    full_transactions=False,
                ),
                call(
                    rpc_url,
                    "finalized",
                    full_transactions=False,
                ),
            ],
        )


if __name__ == "__main__":
    unittest.main()
