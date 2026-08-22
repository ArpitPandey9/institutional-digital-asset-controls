"""Tests for the version-controlled Base USDC reference definition."""

import unittest

from ida_controls.domain.instruction import ExpectedInstruction
from ida_controls.domain.transfer import ObservedTransfer
from ida_controls.reconciliation.canonical_asset_controls import (
    evaluate_canonical_asset_control,
)
from ida_controls.reconciliation.result import (
    ControlStatus,
    ReasonCode,
)
from ida_controls.reference.base_usdc import (
    BASE_MAINNET_CHAIN_ID,
    BASE_USDC_CONTRACT,
    BASE_USDC_RECORD,
    BASE_USDC_REFERENCE_REGISTRY,
    CIRCLE_USDC_CONTRACTS_SOURCE,
)


class TestBaseUsdcReference(unittest.TestCase):

    def test_base_usdc_reference_preserves_authoritative_lineage(self) -> None:
        self.assertEqual(BASE_USDC_RECORD.asset_id, "USDC")
        self.assertEqual(BASE_USDC_RECORD.chain_id, 8453)
        self.assertEqual(
            BASE_USDC_RECORD.token_contract,
            BASE_USDC_CONTRACT,
        )
        self.assertEqual(BASE_USDC_RECORD.token_decimals, 6)
        self.assertEqual(BASE_USDC_RECORD.issuer, "Circle")
        self.assertEqual(
            BASE_USDC_RECORD.source,
            CIRCLE_USDC_CONTRACTS_SOURCE,
        )
        self.assertFalse(
            BASE_USDC_REFERENCE_REGISTRY.is_authoritative_complete
        )

    def test_real_base_usdc_observation_passes_reference_control(self) -> None:
        expected = ExpectedInstruction(
            instruction_id="INST-BASE-USDC-REFERENCE",
            chain_id=BASE_MAINNET_CHAIN_ID,
            token_contract=BASE_USDC_CONTRACT,
            token_sender="0x2b4ee3387008e5ff1a9996fc8b48d2fd61389037",
            token_receiver="0xe9030014f5dae217d0a152f02a043567b16c1abf",
            amount_raw=5408,
            asset_id="USDC",
        )

        observed = ObservedTransfer(
            chain_id=BASE_MAINNET_CHAIN_ID,
            block_number=50058636,
            block_hash=(
                "0x78a85bde41874f70bb5acbba6e6cd234d5f57282"
                "c25e1e9853939e9670da9b22"
            ),
            transaction_hash=(
                "0x942be0700ca598706f2d86770d6bafaec223ec3b"
                "42cc3a72b33f45e4d310f854"
            ),
            log_index=1,
            token_contract=BASE_USDC_CONTRACT,
            token_sender="0x2b4ee3387008e5ff1a9996fc8b48d2fd61389037",
            token_receiver="0xe9030014f5dae217d0a152f02a043567b16c1abf",
            amount_raw=5408,
            token_decimals=6,
            tx_submitter="0xa32ccda98ba7529705a059bd2d213da8de10d101",
            receipt_status=1,
        )

        result = evaluate_canonical_asset_control(
            expected,
            observed,
            BASE_USDC_REFERENCE_REGISTRY,
        )

        self.assertEqual(result.status, ControlStatus.PASS)
        self.assertEqual(
            result.reason,
            ReasonCode.CANONICAL_ASSET_MATCH,
        )
        self.assertEqual(result.issuer, "Circle")
        self.assertEqual(
            result.source,
            CIRCLE_USDC_CONTRACTS_SOURCE,
        )


if __name__ == "__main__":
    unittest.main()
