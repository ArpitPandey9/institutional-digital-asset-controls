# Institutional Digital Asset Control Plane

## Stablecoin Settlement Assurance, Reconciliation & Controls

This repository implements an evidence-based control workflow for reconciling a modeled digital-asset settlement instruction against observed on-chain execution.

The current MVP focuses on Base Mainnet and canonical USDC. It is designed to demonstrate how blockchain evidence can be normalized, validated, reconciled, and translated into auditable control outcomes while maintaining a clear distinction between transaction execution and settlement correctness.

**Verification status:** 64 unit tests passing.

## Current Capabilities

- Read-only JSON-RPC connectivity for EVM-compatible chains
- Base Mainnet chain verification
- RPC-derived chain identity evidence using `eth_chainId`
- Independent chain-control evaluation from RPC chain evidence, including when transfer evidence is unavailable
- Transaction, receipt, block, and log retrieval
- Protocol-aware `safe` and `finalized` block retrieval through JSON-RPC
- Canonical block-hash verification for observed settlement evidence
- Finality controls with explicit `PASS`, `FAIL`, and `UNKNOWN` outcomes
- Duplicate and replay controls using independent instruction-uniqueness and transfer-uniqueness evaluation
- Historical settlement-consumption matching using exact transfer identity: chain ID, transaction hash, and log index
- Auditable preservation of all matched prior consumption records
- Evidence-aware `UNKNOWN` uniqueness outcomes when processing history is unavailable
- ERC-20 `Transfer` event identification and decoding
- Canonical asset validation against independent trusted reference data
- Business-level asset identity separated from token-contract identity
- Version-controlled Base Mainnet USDC reference sourced from Circle's official contract documentation
- Chain-scoped canonical asset evaluation with explicit `PASS`, `FAIL`, and `UNKNOWN` outcomes
- Partial-registry semantics that avoid treating missing reference coverage as evidence of non-approval
- Transaction, receipt, and event lineage validation
- Immutable normalization of observed token-transfer evidence
- Exact raw-unit token accounting without floating-point source-of-truth calculations
- Modeled expected settlement instructions
- Direct expected-versus-observed reconciliation
- `PASS`, `FAIL`, and `UNKNOWN` control outcome types
- Structured field-level audit result types and independent field-level control evaluation
- Evidence-aware `UNKNOWN` outcomes when receipt or transfer evidence is unavailable
- Explicit evidence-availability modeling without weakening complete transfer observations
- Evidence-lineage consistency checks across transaction hash, receipt status, and RPC-derived chain identity
- Settlement-control orchestration across field reconciliation, finality, duplicate/replay, and canonical asset controls
- One auditable settlement-control bundle containing normalized control findings alongside detailed underlying control results
- Evidence-dependent orchestration that preserves independently evaluable findings when other evidence is unavailable
- No orchestrator-level aggregate settlement status; business disposition is intentionally kept separate from control findings
- Python `src/` package layout with deterministic unit-test discovery

## Evidence and Control Model

The observed side is derived from blockchain evidence. The expected side is currently modeled locally for reconciliation and control testing and does not represent private client, bank, custody, employer, or production settlement data.

The implementation preserves explicit distinctions between:

- **RPC chain evidence** - connected network identity obtained through `eth_chainId`
- **Finality evidence** - canonical block identity plus protocol `safe` and `finalized` heads
- **Transaction evidence** - what was submitted to the network
- **Receipt evidence** - execution status and emitted logs
- **ERC-20 event evidence** - token-level sender, receiver, and raw transferred amount
- **Expected instruction** - the modeled settlement terms against which observed evidence is evaluated
- **Processing-history evidence** - prior instruction-to-transfer consumption records used to evaluate settlement uniqueness
- **Trusted asset-reference evidence** - independently maintained asset identity, chain deployment, contract address, decimals, issuer, and source provenance used for canonical asset validation

The transaction submitter (`tx.from`) is not assumed to be the ERC-20 token sender. Sender and receiver controls use evidence derived from the decoded `Transfer` event.

## Core Control Principle

Successful EVM execution does not, by itself, establish successful institutional settlement.

A transaction may execute successfully while still failing a settlement control when the observed chain, asset, sender, receiver, or amount does not match the expected instruction.

The control model therefore separates:

1. **Observation** - what occurred on-chain
2. **Reconciliation** - how observed evidence compares with the expected instruction
3. **Control decision** - whether available evidence supports `PASS`, `FAIL`, or `UNKNOWN`

Unavailable evidence is not treated as evidence of either a match or a mismatch.

Duplicate and replay evaluation applies two independent controls. Instruction uniqueness checks whether the modeled instruction has already been consumed, while transfer uniqueness checks whether the exact on-chain transfer identity `(chain_id, transaction_hash, log_index)` has already been consumed. A previously unseen instruction and transfer pass their respective uniqueness controls. Reuse produces a failed uniqueness control, while unavailable processing history produces `UNKNOWN`. All matching historical records are retained in the control result for auditability.

Finality evaluation separately verifies that the originally observed block remains canonical and that the transaction block has entered the RPC-reported `finalized` range. A canonical transaction that has not yet reached that range fails the current finality condition with `FINALITY_NOT_REACHED`; operationally, this represents pending finality rather than a permanent settlement mismatch.

Canonical asset validation is intentionally independent from expected-versus-observed contract reconciliation. The expected instruction carries a business-level `asset_id`; the control then evaluates the token contract actually observed on the executed chain against trusted reference data for that requested asset. This allows the engine to distinguish an instruction that was faithfully executed from an execution that used the correct approved asset.

A matching expected and observed contract therefore does not, by itself, establish canonical asset validity. Missing reference evidence produces `UNKNOWN`. A missing asset record produces `FAIL` only when the supplied registry is explicitly modeled as an authoritative complete allowlist.

Settlement-control orchestration composes the independent control outcomes into a single auditable bundle without replacing their underlying evidence or result types. The bundle preserves normalized findings for review while retaining detailed field, finality, duplicate/replay, and canonical-asset results where those controls can be evaluated.

Evidence dependencies remain control-specific. For example, when transfer evidence is unavailable but processing history is available, instruction uniqueness can still be evaluated independently, while transfer uniqueness, finality, and canonical-asset validation remain `UNKNOWN` where their required observed evidence is absent.

The orchestrator does not calculate an overall settlement `PASS`, `FAIL`, or `UNKNOWN` disposition. Aggregate business disposition is intentionally reserved for a separate policy layer so that control findings remain distinct from institution-specific decision rules.

## Canonical Asset Reference

The repository currently includes a deliberately narrow reference definition for Circle-issued USDC on Base Mainnet:

- Asset: `USDC`
- Chain ID: `8453`
- Contract: `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`
- Decimals: `6`
- Issuer: Circle
- Authoritative source: https://developers.circle.com/stablecoins/usdc-contract-addresses

This version-controlled reference preserves provenance for the current MVP. It is not represented as a complete institutional asset allowlist. A production implementation would normally consume a governed, reviewed, versioned institutional asset master maintained from authoritative issuer, protocol, or chain sources.

## Current Limitations

This repository is an engineering MVP and should not be interpreted as a production settlement platform.

The following capabilities are not yet fully implemented:

- Persistent and atomic duplicate/replay enforcement across concurrent processing
- Governed production asset-master integration and complete institutional allowlist management
- Policy-driven overall settlement disposition
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

The current foundation establishes package configuration, deterministic test discovery, normalized on-chain transfer evidence, modeled settlement instructions, direct reconciliation, independent field-level controls, evidence-aware `UNKNOWN` outcomes, RPC-derived chain identity evidence, protocol-aware finality evidence, canonical block verification, finality control outcomes, duplicate/replay detection through independent instruction- and transfer-uniqueness controls, independent canonical asset validation against trusted reference data, and settlement-control orchestration into one auditable bundle of independent findings and detailed results.

Duplicate/replay evaluation currently operates against supplied processing-history records. Instruction uniqueness remains independently evaluable when transfer evidence is unavailable, while transfer uniqueness remains `UNKNOWN` without an exact observed transfer identity. Production-grade prevention would additionally require persistent, atomic storage and concurrency-safe uniqueness enforcement.

The current orchestrator intentionally does not assign an aggregate business disposition. Subsequent development will focus on exception handling, explicit policy and disposition rules, production-grade reference-data governance, and broader audit capabilities before additional control-plane functionality is introduced.
