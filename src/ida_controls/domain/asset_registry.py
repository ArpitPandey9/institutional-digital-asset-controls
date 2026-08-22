"""Trusted asset-reference evidence for canonical asset validation."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ApprovedAssetRecord:
    """Institution-approved deployment of one digital asset on one chain."""

    asset_id: str
    chain_id: int
    token_contract: str
    token_decimals: int
    issuer: str
    source: str

    def __post_init__(self) -> None:
        if not self.asset_id.strip():
            raise ValueError("asset_id cannot be empty")

        if self.chain_id <= 0:
            raise ValueError("chain_id must be positive")

        if not self.token_contract.strip():
            raise ValueError("token_contract cannot be empty")

        if self.token_decimals < 0:
            raise ValueError("token_decimals cannot be negative")

        if not self.issuer.strip():
            raise ValueError("issuer cannot be empty")

        if not self.source.strip():
            raise ValueError("source cannot be empty")

    @property
    def registry_key(self) -> tuple[str, int]:
        """Return normalized business-asset and chain identity."""

        return (self.asset_id.strip().upper(), self.chain_id)


@dataclass(frozen=True, slots=True)
class AssetRegistryEvidence:
    """Available institution-approved asset-reference data."""

    records: tuple[ApprovedAssetRecord, ...]
    is_authoritative_complete: bool

    def __post_init__(self) -> None:
        keys = [record.registry_key for record in self.records]

        if len(keys) != len(set(keys)):
            raise ValueError(
                "Asset registry cannot contain duplicate asset_id/chain_id records"
            )

    def find(
        self,
        asset_id: str,
        chain_id: int,
    ) -> ApprovedAssetRecord | None:
        """Find the approved deployment for one business asset on one chain."""

        lookup_key = (asset_id.strip().upper(), chain_id)

        for record in self.records:
            if record.registry_key == lookup_key:
                return record

        return None
