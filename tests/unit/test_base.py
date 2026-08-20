"""Unit tests for Base chain identity and RPC evidence construction."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from ida_controls.chains.base import (
    build_rpc_chain_evidence,
    get_chain_id,
)


class TestBaseChainEvidence(unittest.TestCase):
    def test_get_chain_id_calls_eth_chain_id_and_parses_hex(self) -> None:
        rpc_url = "https://example.invalid"

        with patch(
            "ida_controls.chains.base.rpc_call",
            return_value="0x2105",
        ) as rpc_call_mock:
            chain_id = get_chain_id(rpc_url)

        self.assertEqual(chain_id, 8453)
        rpc_call_mock.assert_called_once_with(
            rpc_url,
            "eth_chainId",
        )


    def test_build_rpc_chain_evidence_uses_rpc_chain_id(self) -> None:
        rpc_url = "https://example.invalid"

        with patch(
            "ida_controls.chains.base.get_chain_id",
            return_value=8453,
        ) as get_chain_id_mock:
            evidence = build_rpc_chain_evidence(rpc_url)

        self.assertEqual(evidence.chain_id, 8453)
        get_chain_id_mock.assert_called_once_with(rpc_url)


if __name__ == "__main__":
    unittest.main()
