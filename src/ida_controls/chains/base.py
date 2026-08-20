"""Base Mainnet chain verification."""

from ida_controls.chains.json_rpc import rpc_call
from ida_controls.domain.evidence import RpcChainEvidence


BASE_MAINNET_CHAIN_ID = 8453


def get_chain_id(rpc_url: str) -> int:
    """Return the connected chain ID as an integer."""
    raw_chain_id = rpc_call(rpc_url, "eth_chainId")
    return int(raw_chain_id, 16)


def build_rpc_chain_evidence(rpc_url: str) -> RpcChainEvidence:
    """Build chain identity evidence from the connected RPC endpoint."""
    return RpcChainEvidence(
        chain_id=get_chain_id(rpc_url),
    )


def verify_base_mainnet(rpc_url: str) -> bool:
    """Verify that the RPC endpoint is connected to Base Mainnet."""
    return get_chain_id(rpc_url) == BASE_MAINNET_CHAIN_ID
