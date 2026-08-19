"""Tests for raw EVM evidence normalization."""

import unittest

from ida_controls.chains.transfer_observer import build_observed_transfer


TRANSFER_TOPIC = (
    "0xddf252ad1be2c89b69c2b068fc378daa"
    "952ba7f163c4a11628f55a4df523b3ef"
)


class TestTransferObserver(unittest.TestCase):

    def test_mismatched_transaction_hash_is_rejected(self) -> None:
        transaction = {
            "hash": "0xaaa",
            "from": "0xsubmitter",
            "blockNumber": "0x64",
        }

        receipt = {
            "transactionHash": "0xaaa",
            "blockNumber": "0x64",
            "status": "0x1",
        }

        transfer_log = {
            "address": "0xtoken",
            "topics": [
                TRANSFER_TOPIC,
                "0x" + ("0" * 24) + ("1" * 40),
                "0x" + ("0" * 24) + ("2" * 40),
            ],
            "data": "0x64",
            "transactionHash": "0xbbb",
            "blockNumber": "0x64",
            "blockHash": "0xblock",
            "logIndex": "0x0",
        }

        with self.assertRaises(ValueError):
            build_observed_transfer(
                chain_id=8453,
                transaction=transaction,
                receipt=receipt,
                transfer_log=transfer_log,
                token_decimals=6,
            )


if __name__ == "__main__":
    unittest.main()
