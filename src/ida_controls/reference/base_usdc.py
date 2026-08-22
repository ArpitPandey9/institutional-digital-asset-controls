"""Reference definition for Circle-issued USDC on Base Mainnet."""

from __future__ import annotations

from ida_controls.domain.asset_registry import (
    ApprovedAssetRecord,
    AssetRegistryEvidence,
)

BASE_MAINNET_CHAIN_ID = 8453

BASE_USDC_CONTRACT = (
    "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
)

CIRCLE_USDC_CONTRACTS_SOURCE = (
    "https://developers.circle.com/stablecoins/usdc-contract-addresses"
)

BASE_USDC_RECORD = ApprovedAssetRecord(
    asset_id="USDC",
    chain_id=BASE_MAINNET_CHAIN_ID,
    token_contract=BASE_USDC_CONTRACT,
    token_decimals=6,
    issuer="Circle",
    source=CIRCLE_USDC_CONTRACTS_SOURCE,
)

# This repository currently carries a deliberately narrow reference dataset.
# It must not be interpreted as a complete institutional asset allowlist.
BASE_USDC_REFERENCE_REGISTRY = AssetRegistryEvidence(
    records=(BASE_USDC_RECORD,),
    is_authoritative_complete=False,
)
