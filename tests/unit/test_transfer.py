"""Tests for the ObservedTransfer domain model."""

from decimal import Decimal
import unittest

from ida_controls.domain.transfer import ObservedTransfer


class TestObservedTransfer(unittest.TestCase):

    def make_transfer(self) -> ObservedTransfer:
        return ObservedTransfer(
            chain_id=8453,
            block_number=50058636,
            block_hash="unknown-for-now",
            transaction_hash=(
                "0x942be0700ca598706f2d86770d6bafaec223ec3b42cc3a72b33f45e4d310f854"
            ),
            log_index=1,
            token_contract="0x833589fcd6edb6e08f4c7c32d4f71b54bda02913",
            token_sender="0x2b4ee3387008e5ff1a9996fc8b48d2fd61389037",
            token_receiver="0xe9030014f5dae217d0a152f02a043567b16c1abf",
            amount_raw=5408,
            token_decimals=6,
            tx_submitter="0xa32ccda98ba7529705a059bd2d213da8de10d101",
            receipt_status=1,
        )

    def test_amount_is_exact_decimal(self) -> None:
        transfer = self.make_transfer()

        self.assertEqual(
            transfer.amount_token,
            Decimal("0.005408"),
        )

    def test_execution_succeeded(self) -> None:
        transfer = self.make_transfer()

        self.assertTrue(transfer.execution_succeeded)

    def test_transaction_submitter_and_token_sender_are_distinct(self) -> None:
        transfer = self.make_transfer()

        self.assertNotEqual(
            transfer.tx_submitter,
            transfer.token_sender,
        )

    def test_negative_amount_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            ObservedTransfer(
                chain_id=8453,
                block_number=1,
                block_hash="example",
                transaction_hash="example",
                log_index=0,
                token_contract="example",
                token_sender="example",
                token_receiver="example",
                amount_raw=-1,
                token_decimals=6,
                tx_submitter="example",
                receipt_status=1,
            )


if __name__ == "__main__":
    unittest.main()
