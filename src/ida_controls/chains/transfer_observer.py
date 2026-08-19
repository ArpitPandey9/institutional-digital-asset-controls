"""Convert raw EVM evidence into normalized transfer evidence."""

from __future__ import annotations

from ida_controls.chains.erc20 import decode_transfer_log
from ida_controls.domain.transfer import ObservedTransfer


def build_observed_transfer(
    *,
    chain_id: int,
    transaction: dict,
    receipt: dict,
    transfer_log: dict,
    token_decimals: int,
) -> ObservedTransfer:
    """Build one ObservedTransfer from transaction, receipt, and Transfer log."""

    decoded = decode_transfer_log(transfer_log)

    tx_hash = transaction["hash"].lower()
    receipt_tx_hash = receipt["transactionHash"].lower()
    log_tx_hash = decoded["transaction_hash"].lower()

    if not (tx_hash == receipt_tx_hash == log_tx_hash):
        raise ValueError(
            "Transaction, receipt, and log do not belong to the same transaction"
        )

    tx_block = int(transaction["blockNumber"], 16)
    receipt_block = int(receipt["blockNumber"], 16)

    if not (
        tx_block
        == receipt_block
        == decoded["block_number"]
    ):
        raise ValueError(
            "Transaction, receipt, and log do not belong to the same block"
        )

    return ObservedTransfer(
        chain_id=chain_id,
        block_number=decoded["block_number"],
        block_hash=decoded["block_hash"],
        transaction_hash=decoded["transaction_hash"],
        log_index=decoded["log_index"],
        token_contract=decoded["contract_address"],
        token_sender=decoded["from_address"],
        token_receiver=decoded["to_address"],
        amount_raw=decoded["amount_raw"],
        token_decimals=token_decimals,
        tx_submitter=transaction["from"],
        receipt_status=int(receipt["status"], 16),
    )


def build_observed_transfers(
    *,
    chain_id: int,
    transaction: dict,
    receipt: dict,
    token_contract: str,
    token_decimals: int,
) -> list[ObservedTransfer]:
    """Build all matching token transfers from one transaction receipt."""

    from ida_controls.chains.erc20 import find_transfer_logs

    transfer_logs = find_transfer_logs(
        receipt["logs"],
        token_contract=token_contract,
    )

    return [
        build_observed_transfer(
            chain_id=chain_id,
            transaction=transaction,
            receipt=receipt,
            transfer_log=transfer_log,
            token_decimals=token_decimals,
        )
        for transfer_log in transfer_logs
    ]
