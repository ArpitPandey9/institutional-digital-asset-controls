"""Streamlit demonstration interface for the settlement control engine."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict

import streamlit as st

from demo_data import build_scenarios
from ida_controls.reconciliation.orchestration import (
    evaluate_settlement_control_bundle,
)


def _compact_display(value: object) -> str:
    """Compact long hex identifiers for table readability."""
    if value is None:
        return "Unavailable"

    text = str(value)

    if text.startswith("0x") and len(text) > 20:
        return f"{text[:10]}…{text[-8:]}"

    return text


st.set_page_config(
    page_title="Institutional Digital Asset Control Plane",
    page_icon="◈",
    layout="wide",
)


scenarios = build_scenarios()

st.title("Institutional Digital Asset Control Plane")
st.caption(
    "Stablecoin settlement assurance, reconciliation and controls using "
    "explicit expected instructions and normalized blockchain evidence."
)

st.warning(
    "Engineering MVP / demonstration interface. Demo scenarios use explicitly "
    "modeled synthetic inputs and do not contain employer, client, custody, "
    "bank, or production settlement data."
)

with st.sidebar:
    st.header("Control Review")

    selected_label = st.selectbox(
        "Demonstration scenario",
        options=list(scenarios),
    )

    st.divider()

    st.markdown(
        """
**Control semantics**

- **PASS** — sufficient evidence supports the control condition.
- **FAIL** — sufficient evidence proves an adverse condition.
- **UNKNOWN** — required evidence is unavailable or insufficient.
"""
    )

    st.info(
        "The orchestrator intentionally does not create an overall business "
        "settlement status. Policy/disposition remains a separate layer."
    )


scenario = scenarios[selected_label]

bundle = evaluate_settlement_control_bundle(
    scenario.expected,
    scenario.evidence,
    finality_evidence=scenario.finality_evidence,
    history=scenario.history,
    asset_registry=scenario.asset_registry,
)

status_counts = Counter(
    finding.status.value
    for finding in bundle.findings
)

st.subheader(selected_label)
st.write(scenario.description)

metric_1, metric_2, metric_3, metric_4 = st.columns(4)

metric_1.metric(
    "Controls evaluated",
    len(bundle.findings),
)
metric_2.metric(
    "PASS",
    status_counts.get("PASS", 0),
)
metric_3.metric(
    "FAIL",
    status_counts.get("FAIL", 0),
)
metric_4.metric(
    "UNKNOWN",
    status_counts.get("UNKNOWN", 0),
)

st.caption(
    "Counts are independent control findings, not an aggregate settlement "
    "decision."
)

summary_tab, evidence_tab, detail_tab, boundary_tab = st.tabs(
    [
        "Control findings",
        "Evidence",
        "Detailed results",
        "Production boundary",
    ]
)


with summary_tab:
    st.subheader("Independent Control Findings")

    finding_rows = [
        {
            "Control": finding.control_name.value,
            "Status": finding.status.value,
            "Reason": finding.reason.value,
            "Transaction": _compact_display(finding.transaction_hash),
            "Log index": (
                finding.log_index
                if finding.log_index is not None
                else "Unavailable"
            ),
        }
        for finding in bundle.findings
    ]

    st.dataframe(
        finding_rows,
        width="stretch",
        hide_index=True,
    )

    failed_reasons = [
        finding.reason.value
        for finding in bundle.findings
        if finding.status.value == "FAIL"
    ]

    unknown_reasons = [
        finding.control_name.value
        for finding in bundle.findings
        if finding.status.value == "UNKNOWN"
    ]

    if failed_reasons:
        st.error(
            "Adverse control evidence: "
            + ", ".join(failed_reasons)
        )

    if unknown_reasons:
        st.warning(
            "Controls requiring unavailable evidence: "
            + ", ".join(unknown_reasons)
        )

    if not failed_reasons and not unknown_reasons:
        st.success(
            "All independently evaluated controls in this demonstration "
            "scenario returned PASS. This is not an institutional business "
            "disposition."
        )


with evidence_tab:
    st.subheader("Expected Settlement Instruction")

    expected = scenario.expected

    st.json(
        {
            "instruction_id": expected.instruction_id,
            "chain_id": expected.chain_id,
            "asset_id": expected.asset_id,
            "token_contract": expected.token_contract,
            "token_sender": expected.token_sender,
            "token_receiver": expected.token_receiver,
            "amount_raw": expected.amount_raw,
        }
    )

    st.subheader("Observed Blockchain Evidence")

    evidence = scenario.evidence

    evidence_summary = {
        "transaction_hash": (
            evidence.transaction_hash
            if evidence.transaction_hash is not None
            else "Unavailable"
        ),
        "receipt_status": evidence.receipt_status,
        "rpc_chain_id": (
            evidence.chain_evidence.chain_id
            if evidence.chain_evidence is not None
            else "Unavailable"
        ),
        "transfer_evidence_available": evidence.transfer is not None,
    }

    st.json(evidence_summary)

    if evidence.transfer is not None:
        transfer = evidence.transfer

        st.markdown("**Normalized ERC-20 Transfer Evidence**")

        st.json(
            {
                "chain_id": transfer.chain_id,
                "block_number": transfer.block_number,
                "block_hash": transfer.block_hash,
                "transaction_hash": transfer.transaction_hash,
                "log_index": transfer.log_index,
                "token_contract": transfer.token_contract,
                "token_sender": transfer.token_sender,
                "token_receiver": transfer.token_receiver,
                "amount_raw": transfer.amount_raw,
                "amount_token": str(transfer.amount_token),
                "token_decimals": transfer.token_decimals,
                "transaction_submitter": transfer.tx_submitter,
                "receipt_status": transfer.receipt_status,
            }
        )

        st.caption(
            "Transaction submitter and ERC-20 token sender are deliberately "
            "shown separately; they are not assumed to be the same actor."
        )

    else:
        st.info(
            "No normalized Transfer evidence is available in this scenario."
        )

    st.subheader("Supporting Evidence")

    if scenario.finality_evidence is not None:
        st.markdown("**Finality evidence**")
        st.json(asdict(scenario.finality_evidence))
    else:
        st.write("Finality evidence: **Unavailable**")

    if scenario.history is None:
        st.write("Processing history: **Unavailable**")
    else:
        st.write(
            f"Processing-history records supplied: **{len(scenario.history)}**"
        )

    if scenario.asset_registry is None:
        st.write("Trusted asset reference: **Unavailable**")
    else:
        st.write(
            "Trusted asset-reference records supplied: "
            f"**{len(scenario.asset_registry.records)}**"
        )


with detail_tab:
    st.subheader("Field-Level Reconciliation")

    field_rows = [
        {
            "Control": result.control_name.value,
            "Expected": _compact_display(result.expected_value),
            "Observed": _compact_display(result.observed_value),
            "Status": result.status.value,
            "Reason": result.reason.value,
            "Evidence source": (
                result.evidence_source.value
                if result.evidence_source is not None
                else "Unavailable"
            ),
        }
        for result in bundle.field_controls
    ]

    st.dataframe(
        field_rows,
        width="stretch",
        hide_index=True,
    )

    st.subheader("Finality")

    if bundle.finality_control is None:
        st.info(
            "Detailed finality result is unavailable because normalized "
            "transfer evidence is unavailable."
        )
    else:
        st.json(asdict(bundle.finality_control))

        if (
            bundle.finality_control.reason.value
            == "FINALITY_NOT_REACHED"
        ):
            st.info(
                "FINALITY_NOT_REACHED is a current control failure, but it may "
                "be operationally temporary/pending rather than a permanent "
                "settlement mismatch."
            )

    st.subheader("Duplicate / Replay Controls")

    duplicate_rows = [
        {
            "Control": result.control_name.value,
            "Status": result.status.value,
            "Reason": result.reason.value,
            "Prior matches": len(result.matched_records),
        }
        for result in bundle.duplicate_replay_controls
    ]

    st.dataframe(
        duplicate_rows,
        width="stretch",
        hide_index=True,
    )

    st.subheader("Canonical Asset")

    if bundle.canonical_asset_control is None:
        st.info(
            "Detailed canonical-asset result is unavailable because normalized "
            "transfer evidence is unavailable."
        )
    else:
        st.json(asdict(bundle.canonical_asset_control))


with boundary_tab:
    st.subheader("Current Engineering Boundary")

    st.markdown(
        """
This interface demonstrates the existing evidence and control engine. It is
**not represented as a production settlement platform**.

Current production gaps include:

- persistent and atomic duplicate/replay enforcement under concurrency;
- governed production asset-master / allowlist integration;
- institution-specific policy and overall business disposition;
- exception workflow and case management;
- persistent audit storage;
- sanctions / compliance screening;
- independent external evidence verification;
- production authentication, API and operations interface;
- production monitoring, deployment and service controls.

### Correct positioning

**Current:** working institutional-style engineering MVP / control-plane
prototype.

**Future production path:** connect governed expected-instruction sources,
production RPC infrastructure, durable processing history, approved reference
data, policy, persistence, operational workflow and monitoring.
"""
    )

    st.info(
        "Successful EVM execution is evidence of execution — not proof, by "
        "itself, of correct institutional settlement."
    )
