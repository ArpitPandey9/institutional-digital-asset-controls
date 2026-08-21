"""Result types for settlement reconciliation."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ControlStatus(str, Enum):
    """High-level reconciliation outcome."""

    PASS = "PASS"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"


class ReasonCode(str, Enum):
    """Machine-readable reason for a reconciliation outcome."""

    MATCH = "MATCH"
    EXECUTION_SUCCEEDED = "EXECUTION_SUCCEEDED"
    EXACT_MATCH = "EXACT_MATCH"
    EXECUTION_REVERTED = "EXECUTION_REVERTED"
    CHAIN_ID_MISMATCH = "CHAIN_ID_MISMATCH"
    TOKEN_CONTRACT_MISMATCH = "TOKEN_CONTRACT_MISMATCH"
    SENDER_MISMATCH = "SENDER_MISMATCH"
    RECEIVER_MISMATCH = "RECEIVER_MISMATCH"
    AMOUNT_MISMATCH = "AMOUNT_MISMATCH"
    FINALITY_REACHED = "FINALITY_REACHED"
    FINALITY_NOT_REACHED = "FINALITY_NOT_REACHED"
    BLOCK_NOT_CANONICAL = "BLOCK_NOT_CANONICAL"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class ControlName(str, Enum):
    """Individual settlement control being evaluated."""

    EXECUTION = "EXECUTION"
    CHAIN = "CHAIN"
    ASSET = "ASSET"
    SENDER = "SENDER"
    RECEIVER = "RECEIVER"
    AMOUNT = "AMOUNT"
    FINALITY = "FINALITY"


class EvidenceSource(str, Enum):
    """Normalized source of observed evidence used by a control."""

    TRANSACTION_RECEIPT_STATUS = "transaction_receipt.status"
    RPC_CHAIN_ID = "rpc.eth_chainId"
    OBSERVED_TRANSFER_CHAIN_ID = "observed_transfer.chain_id"
    ERC20_LOG_EMITTER = "erc20_transfer_log.address"
    ERC20_TRANSFER_SENDER = "erc20_transfer_log.Transfer.from"
    ERC20_TRANSFER_RECEIVER = "erc20_transfer_log.Transfer.to"
    ERC20_TRANSFER_AMOUNT_RAW = "erc20_transfer_log.data_uint256"


ControlValue = str | int | bool | None


@dataclass(frozen=True, slots=True)
class FieldControlResult:
    """Auditable outcome for one settlement control."""

    instruction_id: str
    control_name: ControlName
    expected_value: ControlValue
    observed_value: ControlValue
    status: ControlStatus
    reason: ReasonCode
    evidence_source: EvidenceSource | None

    transaction_hash: str | None
    log_index: int | None


@dataclass(frozen=True, slots=True)
class ReconciliationResult:
    """Auditable result of comparing expected and observed settlement data."""

    instruction_id: str
    status: ControlStatus
    reason: ReasonCode

    transaction_hash: str | None
    log_index: int | None
