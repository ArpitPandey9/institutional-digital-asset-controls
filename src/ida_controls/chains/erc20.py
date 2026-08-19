"""Minimal ERC-20 event decoding helpers."""

from __future__ import annotations


TRANSFER_TOPIC0 = (
    "0xddf252ad1be2c89b69c2b068fc378daa"
    "952ba7f163c4a11628f55a4df523b3ef"
)


def topic_to_address(topic: str) -> str:
    """Decode an indexed Ethereum address from a 32-byte log topic."""
    return "0x" + topic[-40:]


def decode_uint256(data: str) -> int:
    """Decode a uint256 value from ABI-encoded hexadecimal data."""
    return int(data, 16)


def decode_transfer_log(log: dict) -> dict:
    """Decode a standard ERC-20 Transfer event log."""
    topics = log["topics"]

    if len(topics) < 3:
        raise ValueError("Transfer log must contain at least 3 topics")

    if topics[0].lower() != TRANSFER_TOPIC0:
        raise ValueError("Log is not an ERC-20 Transfer event")

    return {
        "contract_address": log["address"],
        "from_address": topic_to_address(topics[1]),
        "to_address": topic_to_address(topics[2]),
        "amount_raw": decode_uint256(log["data"]),
        "transaction_hash": log["transactionHash"],
        "block_number": int(log["blockNumber"], 16),
        "block_hash": log["blockHash"],
        "log_index": int(log["logIndex"], 16),
    }


def is_transfer_log(
    log: dict,
    *,
    token_contract: str | None = None,
) -> bool:
    """Return whether a log is an ERC-20 Transfer event."""

    topics = log.get("topics", [])

    if not topics:
        return False

    if topics[0].lower() != TRANSFER_TOPIC0:
        return False

    if token_contract is not None:
        emitter = log.get("address")

        if emitter is None:
            return False

        if emitter.lower() != token_contract.lower():
            return False

    return True


def find_transfer_logs(
    logs: list[dict],
    *,
    token_contract: str | None = None,
) -> list[dict]:
    """Return all matching ERC-20 Transfer logs."""

    return [
        log
        for log in logs
        if is_transfer_log(
            log,
            token_contract=token_contract,
        )
    ]
