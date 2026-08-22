"""Tests for canonical institutional asset validation."""

import unittest

from ida_controls.domain.asset_registry import (
    ApprovedAssetRecord,
    AssetRegistryEvidence,
)
from ida_controls.domain.instruction import ExpectedInstruction
from ida_controls.domain.transfer import ObservedTransfer
from ida_controls.reconciliation.canonical_asset_controls import (
    evaluate_canonical_asset_control,
)
from ida_controls.reconciliation.result import (
    ControlName,
    ControlStatus,
    ReasonCode,
)


BASE_USDC = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
OTHER_CONTRACT = "0x1111111111111111111111111111111111111111"


def expected_instruction(
    *,
    asset_id: str | None = "USDC",
    chain_id: int = 8453,
) -> ExpectedInstruction:
    return ExpectedInstruction(
        instruction_id="INST-CANONICAL-001",
        chain_id=chain_id,
        token_contract=BASE_USDC,
        token_sender="0x2222222222222222222222222222222222222222",
        token_receiver="0x3333333333333333333333333333333333333333",
        amount_raw=5408,
        asset_id=asset_id,
    )


def observed_transfer(
    *,
    chain_id: int = 8453,
    token_contract: str = BASE_USDC,
) -> ObservedTransfer:
    return ObservedTransfer(
        chain_id=chain_id,
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
        token_contract=token_contract,
        token_sender="0x2b4ee3387008e5ff1a9996fc8b48d2fd61389037",
        token_receiver="0xe9030014f5dae217d0a152f02a043567b16c1abf",
        amount_raw=5408,
        token_decimals=6,
        tx_submitter="0xa32ccda98ba7529705a059bd2d213da8de10d101",
        receipt_status=1,
    )


def base_usdc_record() -> ApprovedAssetRecord:
    return ApprovedAssetRecord(
        asset_id="USDC",
        chain_id=8453,
        token_contract=BASE_USDC,
        token_decimals=6,
        issuer="Circle",
        source="Circle official USDC contract-address documentation",
    )


class TestCanonicalAssetControls(unittest.TestCase):

    def test_canonical_base_usdc_passes(self) -> None:
        registry = AssetRegistryEvidence(
            records=(base_usdc_record(),),
            is_authoritative_complete=True,
        )

        result = evaluate_canonical_asset_control(
            expected_instruction(),
            observed_transfer(),
            registry,
        )

        self.assertEqual(result.control_name, ControlName.CANONICAL_ASSET)
        self.assertEqual(result.status, ControlStatus.PASS)
        self.assertEqual(result.reason, ReasonCode.CANONICAL_ASSET_MATCH)
        self.assertEqual(result.asset_id, "USDC")
        self.assertEqual(result.approved_token_contract, BASE_USDC)
        self.assertEqual(result.issuer, "Circle")
        self.assertIsNotNone(result.source)

    def test_noncanonical_contract_fails(self) -> None:
        registry = AssetRegistryEvidence(
            records=(base_usdc_record(),),
            is_authoritative_complete=True,
        )

        result = evaluate_canonical_asset_control(
            expected_instruction(),
            observed_transfer(token_contract=OTHER_CONTRACT),
            registry,
        )

        self.assertEqual(result.status, ControlStatus.FAIL)
        self.assertEqual(
            result.reason,
            ReasonCode.CANONICAL_ASSET_MISMATCH,
        )
        self.assertEqual(result.approved_token_contract, BASE_USDC)

    def test_unavailable_registry_is_unknown(self) -> None:
        result = evaluate_canonical_asset_control(
            expected_instruction(),
            observed_transfer(),
            None,
        )

        self.assertEqual(result.status, ControlStatus.UNKNOWN)
        self.assertEqual(
            result.reason,
            ReasonCode.INSUFFICIENT_EVIDENCE,
        )

    def test_missing_asset_id_is_unknown(self) -> None:
        registry = AssetRegistryEvidence(
            records=(base_usdc_record(),),
            is_authoritative_complete=True,
        )

        result = evaluate_canonical_asset_control(
            expected_instruction(asset_id=None),
            observed_transfer(),
            registry,
        )

        self.assertEqual(result.status, ControlStatus.UNKNOWN)
        self.assertEqual(
            result.reason,
            ReasonCode.INSUFFICIENT_EVIDENCE,
        )

    def test_missing_record_in_partial_registry_is_unknown(self) -> None:
        registry = AssetRegistryEvidence(
            records=(),
            is_authoritative_complete=False,
        )

        result = evaluate_canonical_asset_control(
            expected_instruction(),
            observed_transfer(),
            registry,
        )

        self.assertEqual(result.status, ControlStatus.UNKNOWN)
        self.assertEqual(
            result.reason,
            ReasonCode.INSUFFICIENT_EVIDENCE,
        )

    def test_missing_record_in_complete_registry_fails(self) -> None:
        registry = AssetRegistryEvidence(
            records=(),
            is_authoritative_complete=True,
        )

        result = evaluate_canonical_asset_control(
            expected_instruction(),
            observed_transfer(),
            registry,
        )

        self.assertEqual(result.status, ControlStatus.FAIL)
        self.assertEqual(
            result.reason,
            ReasonCode.ASSET_NOT_APPROVED,
        )

    def test_contract_comparison_is_case_insensitive(self) -> None:
        registry = AssetRegistryEvidence(
            records=(base_usdc_record(),),
            is_authoritative_complete=True,
        )

        result = evaluate_canonical_asset_control(
            expected_instruction(),
            observed_transfer(token_contract=BASE_USDC.upper()),
            registry,
        )

        self.assertEqual(result.status, ControlStatus.PASS)
        self.assertEqual(
            result.reason,
            ReasonCode.CANONICAL_ASSET_MATCH,
        )

    def test_matching_noncanonical_instruction_and_observation_still_fail(self) -> None:
        registry = AssetRegistryEvidence(
            records=(base_usdc_record(),),
            is_authoritative_complete=True,
        )

        expected = ExpectedInstruction(
            instruction_id="INST-CANONICAL-NONCANONICAL",
            chain_id=8453,
            token_contract=OTHER_CONTRACT,
            token_sender="0x2222222222222222222222222222222222222222",
            token_receiver="0x3333333333333333333333333333333333333333",
            amount_raw=5408,
            asset_id="USDC",
        )

        result = evaluate_canonical_asset_control(
            expected,
            observed_transfer(token_contract=OTHER_CONTRACT),
            registry,
        )

        self.assertEqual(result.status, ControlStatus.FAIL)
        self.assertEqual(
            result.reason,
            ReasonCode.CANONICAL_ASSET_MISMATCH,
        )

    def test_approved_different_asset_does_not_satisfy_usdc_instruction(self) -> None:
        weth_contract = "0x4200000000000000000000000000000000000006"

        weth = ApprovedAssetRecord(
            asset_id="WETH",
            chain_id=8453,
            token_contract=weth_contract,
            token_decimals=18,
            issuer="WETH protocol",
            source="Authoritative test registry record",
        )

        registry = AssetRegistryEvidence(
            records=(base_usdc_record(), weth),
            is_authoritative_complete=True,
        )

        expected = ExpectedInstruction(
            instruction_id="INST-USDC-BUT-WETH",
            chain_id=8453,
            token_contract=weth_contract,
            token_sender="0x2222222222222222222222222222222222222222",
            token_receiver="0x3333333333333333333333333333333333333333",
            amount_raw=5408,
            asset_id="USDC",
        )

        result = evaluate_canonical_asset_control(
            expected,
            observed_transfer(token_contract=weth_contract),
            registry,
        )

        self.assertEqual(result.status, ControlStatus.FAIL)
        self.assertEqual(
            result.reason,
            ReasonCode.CANONICAL_ASSET_MISMATCH,
        )
        self.assertEqual(result.approved_token_contract, BASE_USDC)


    def test_lookup_uses_observed_chain_identity(self) -> None:
        ethereum_usdc = ApprovedAssetRecord(
            asset_id="USDC",
            chain_id=1,
            token_contract=OTHER_CONTRACT,
            token_decimals=6,
            issuer="Circle",
            source="Authoritative test registry record",
        )

        registry = AssetRegistryEvidence(
            records=(base_usdc_record(), ethereum_usdc),
            is_authoritative_complete=True,
        )

        result = evaluate_canonical_asset_control(
            expected_instruction(chain_id=8453),
            observed_transfer(
                chain_id=1,
                token_contract=OTHER_CONTRACT,
            ),
            registry,
        )

        self.assertEqual(result.status, ControlStatus.PASS)
        self.assertEqual(
            result.reason,
            ReasonCode.CANONICAL_ASSET_MATCH,
        )
        self.assertEqual(result.observed_chain_id, 1)


class TestAssetRegistryEvidence(unittest.TestCase):

    def test_registry_lookup_normalizes_asset_id(self) -> None:
        registry = AssetRegistryEvidence(
            records=(base_usdc_record(),),
            is_authoritative_complete=True,
        )

        record = registry.find(" usdc ", 8453)

        self.assertEqual(record, base_usdc_record())

    def test_duplicate_asset_chain_records_are_rejected(self) -> None:
        duplicate = ApprovedAssetRecord(
            asset_id="usdc",
            chain_id=8453,
            token_contract=OTHER_CONTRACT,
            token_decimals=6,
            issuer="Circle",
            source="Duplicate test record",
        )

        with self.assertRaises(ValueError):
            AssetRegistryEvidence(
                records=(base_usdc_record(), duplicate),
                is_authoritative_complete=True,
            )


if __name__ == "__main__":
    unittest.main()
