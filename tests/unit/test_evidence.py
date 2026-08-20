"""Tests for settlement evidence consistency rules."""

import unittest

from ida_controls.domain.evidence import (
    ObservedSettlementEvidence,
    RpcChainEvidence,
)
from ida_controls.domain.transfer import ObservedTransfer


class TestObservedSettlementEvidence(unittest.TestCase):

    def make_transfer(self) -> ObservedTransfer:
        return ObservedTransfer(
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

    def test_rejects_mismatched_transaction_hash(self) -> None:
        transfer = self.make_transfer()

        with self.assertRaisesRegex(
            ValueError,
            "Evidence transaction hash does not match observed transfer",
        ):
            ObservedSettlementEvidence(
                transaction_hash=(
                    "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
                    "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
                ),
                receipt_status=1,
                transfer=transfer,
            )

    def test_rejects_mismatched_receipt_status(self) -> None:
        transfer = self.make_transfer()

        with self.assertRaisesRegex(
            ValueError,
            "Evidence receipt status does not match observed transfer",
        ):
            ObservedSettlementEvidence(
                transaction_hash=transfer.transaction_hash,
                receipt_status=0,
                transfer=transfer,
            )

    def test_rejects_invalid_receipt_status(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "receipt_status must be 0, 1, or None",
        ):
            ObservedSettlementEvidence(
                transaction_hash=None,
                receipt_status=2,
                transfer=None,
            )


    def test_rejects_rpc_chain_evidence_that_conflicts_with_transfer(self) -> None:
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

        with self.assertRaisesRegex(
            ValueError,
            "RPC chain evidence does not match observed transfer",
        ):
            ObservedSettlementEvidence(
                transaction_hash=transfer.transaction_hash,
                receipt_status=1,
                transfer=transfer,
                chain_evidence=RpcChainEvidence(chain_id=1),
            )


if __name__ == "__main__":
    unittest.main()
