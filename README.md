# Institutional Digital Asset Control Plane

## Stablecoin Settlement Assurance, Reconciliation & Controls

This repository implements an evidence-based control workflow for reconciling a modeled digital-asset settlement instruction against observed on-chain execution.

The current MVP focuses on Base Mainnet and canonical USDC. It is designed to demonstrate how blockchain evidence can be normalized, validated, reconciled, and translated into auditable control outcomes while maintaining a clear distinction between transaction execution and settlement correctness.

## Current Capabilities

- Read-only JSON-RPC connectivity for EVM-compatible chains
- Base Mainnet chain verification
- Transaction, receipt, block, and log retrieval
- ERC-20 `Transfer` event identification and decoding
- Transaction, receipt, and event lineage validation
- Immutable normalization of observed token-transfer evidence
- Exact raw-unit token accounting without floating-point source-of-truth calculations
- Modeled expected settlement instructions
- Direct expected-versus-observed reconciliation
- `PASS`, `FAIL`, and `UNKNOWN` control outcome types
- Structured field-level audit result types and independent field-level control evaluation
- Python `src/` package layout with deterministic unit-test discovery

## Evidence and Control Model

The observed side is derived from blockchain evidence. The expected side is currently modeled locally for reconciliation and control testing and does not represent private client, bank, custody, employer, or production settlement data.

The implementation preserves explicit distinctions between:

- **Transaction evidence** - what was submitted to the network
- **Receipt evidence** - execution status and emitted logs
- **ERC-20 event evidence** - token-level sender, receiver, and raw transferred amount
- **Expected instruction** - the modeled settlement terms against which observed evidence is evaluated

The transaction submitter (`tx.from`) is not assumed to be the ERC-20 token sender. Sender and receiver controls use evidence derived from the decoded `Transfer` event.

## Core Control Principle

Successful EVM execution does not, by itself, establish successful institutional settlement.

A transaction may execute successfully while still failing a settlement control when the observed chain, asset, sender, receiver, or amount does not match the expected instruction.

The control model therefore separates:

1. **Observation** - what occurred on-chain
2. **Reconciliation** - how observed evidence compares with the expected instruction
3. **Control decision** - whether available evidence supports `PASS`, `FAIL`, or `UNKNOWN`

Unavailable evidence is not treated as evidence of either a match or a mismatch.

## Current Limitations

This repository is an engineering MVP and should not be interpreted as a production settlement platform.

The following capabilities are not yet fully implemented:

- Automatic derivation of `UNKNOWN` from unavailable or insufficient evidence
- Finality controls
- Duplicate and replay controls
- Canonical asset registry controls
- Exception workflow and case management
- Persistent audit storage
- Sanctions screening
- Independent external verification
- Production API and operations interface

The current direct-transfer reconciliation path also does not treat routed or multi-hop token movement as equivalent to a direct expected transfer.

## Development

Install the package in editable mode:

```bash
python -m pip install -e .
```

Run the current test suite:

```bash
python -m unittest discover -s tests -p 'test_*.py' -v
```

## Project Status

The current foundation establishes package configuration, deterministic test discovery, normalized on-chain transfer evidence, modeled settlement instructions, direct reconciliation, auditable result types, and independent field-level evaluation across execution, chain, asset, sender, receiver, and amount controls.

Subsequent development will focus on evidence-aware `UNKNOWN` handling and stronger upstream evidence provenance before broader control-plane capabilities are introduced.
