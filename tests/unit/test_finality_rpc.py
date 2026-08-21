"""Unit tests for protocol finality block retrieval."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from ida_controls.chains.evm import get_block_by_tag


class TestFinalityRpc(unittest.TestCase):
    def test_get_finalized_block_uses_finalized_rpc_tag(self) -> None:
        rpc_url = "https://example.invalid"
        finalized_block = {
            "number": "0x69",
            "hash": "0xabc",
        }

        with patch(
            "ida_controls.chains.evm.rpc_call",
            return_value=finalized_block,
        ) as rpc_call_mock:
            block = get_block_by_tag(
                rpc_url,
                "finalized",
                full_transactions=False,
            )

        self.assertEqual(block, finalized_block)
        rpc_call_mock.assert_called_once_with(
            rpc_url,
            "eth_getBlockByNumber",
            ["finalized", False],
        )


if __name__ == "__main__":
    unittest.main()
