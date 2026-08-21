"""Generic read-only helpers for Ethereum-compatible chains."""

from __future__ import annotations

from ida_controls.chains.json_rpc import rpc_call


def hex_to_int(value: str) -> int:
    """Convert a hexadecimal JSON-RPC quantity to an integer."""
    return int(value, 16)


def get_latest_block_number(rpc_url: str) -> int:
    """Return the latest block number."""
    raw_block_number = rpc_call(rpc_url, "eth_blockNumber")
    return hex_to_int(raw_block_number)


def get_block(
    rpc_url: str,
    block_number: int,
    full_transactions: bool = True,
) -> dict:
    """Return a block by number."""
    block_hex = hex(block_number)

    block = rpc_call(
        rpc_url,
        "eth_getBlockByNumber",
        [block_hex, full_transactions],
    )

    if block is None:
        raise RuntimeError(f"Block not found: {block_number}")

    return block


def get_block_by_tag(
    rpc_url: str,
    tag: str,
    full_transactions: bool = True,
) -> dict:
    """Return a block by an Ethereum JSON-RPC block tag."""
    allowed_tags = {"latest", "safe", "finalized"}

    if tag not in allowed_tags:
        raise ValueError(
            f"Unsupported block tag: {tag}"
        )

    block = rpc_call(
        rpc_url,
        "eth_getBlockByNumber",
        [tag, full_transactions],
    )

    if block is None:
        raise RuntimeError(f"Block not found for tag: {tag}")

    return block


def get_transaction_receipt(rpc_url: str, tx_hash: str) -> dict | None:
    """Return the execution receipt for a transaction."""
    return rpc_call(
        rpc_url,
        "eth_getTransactionReceipt",
        [tx_hash],
    )


def get_transaction(rpc_url: str, tx_hash: str) -> dict | None:
    """Return a transaction by hash."""
    return rpc_call(
        rpc_url,
        "eth_getTransactionByHash",
        [tx_hash],
    )


def get_logs(
    rpc_url: str,
    *,
    from_block: int,
    to_block: int,
    address: str | None = None,
    topics: list | None = None,
) -> list[dict]:
    """Return logs matching an Ethereum JSON-RPC filter."""
    log_filter = {
        "fromBlock": hex(from_block),
        "toBlock": hex(to_block),
    }

    if address is not None:
        log_filter["address"] = address

    if topics is not None:
        log_filter["topics"] = topics

    return rpc_call(
        rpc_url,
        "eth_getLogs",
        [log_filter],
    )
