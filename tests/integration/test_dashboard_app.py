"""Headless integration tests for the Streamlit control-plane dashboard."""

from __future__ import annotations

import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest


REPO_ROOT = Path(__file__).resolve().parents[2]
APP_PATH = REPO_ROOT / "dashboard" / "app.py"
APP_TIMEOUT_SECONDS = 30


class DashboardAppTest(unittest.TestCase):
    def run_app(self) -> AppTest:
        return AppTest.from_file(
            APP_PATH,
            default_timeout=APP_TIMEOUT_SECONDS,
        ).run()

    @staticmethod
    def metric_values(app: AppTest) -> dict[str, str]:
        return {metric.label: metric.value for metric in app.metric}

    @staticmethod
    def select_scenario(app: AppTest, label: str) -> None:
        app.selectbox[0].select(label).run(
            timeout=APP_TIMEOUT_SECONDS,
        )

    def assert_metrics(
        self,
        app: AppTest,
        *,
        passed: str,
        failed: str,
        unknown: str,
    ) -> None:
        metrics = self.metric_values(app)

        self.assertEqual(metrics["Controls evaluated"], "10")
        self.assertEqual(metrics["PASS"], passed)
        self.assertEqual(metrics["FAIL"], failed)
        self.assertEqual(metrics["UNKNOWN"], unknown)

    def test_exact_match_finalized_smoke(self) -> None:
        app = self.run_app()

        self.assertEqual(len(app.exception), 0)
        self.assertEqual(
            [title.value for title in app.title],
            ["Institutional Digital Asset Control Plane"],
        )

        self.assertEqual(len(app.selectbox), 1)
        self.assertEqual(
            app.selectbox[0].label,
            "Demonstration scenario",
        )
        self.assertEqual(
            app.selectbox[0].value,
            "Exact match — finalized",
        )

        self.assert_metrics(
            app,
            passed="10",
            failed="0",
            unknown="0",
        )

    def test_receiver_mismatch_produces_receiver_fail(self) -> None:
        app = self.run_app()
        self.select_scenario(app, "Receiver mismatch")

        self.assertEqual(len(app.exception), 0)
        self.assert_metrics(
            app,
            passed="9",
            failed="1",
            unknown="0",
        )

        error_messages = [item.value for item in app.error]

        self.assertTrue(
            any(
                "RECEIVER_MISMATCH" in message
                for message in error_messages
            ),
            error_messages,
        )

    def test_pending_finality_produces_finality_fail(self) -> None:
        app = self.run_app()
        self.select_scenario(app, "Pending finality")

        self.assertEqual(len(app.exception), 0)
        self.assert_metrics(
            app,
            passed="9",
            failed="1",
            unknown="0",
        )

        error_messages = [item.value for item in app.error]

        self.assertTrue(
            any(
                "FINALITY_NOT_REACHED" in message
                for message in error_messages
            ),
            error_messages,
        )

    def test_duplicate_replay_produces_two_failures(self) -> None:
        app = self.run_app()
        self.select_scenario(app, "Duplicate / replay")

        self.assertEqual(len(app.exception), 0)
        self.assert_metrics(
            app,
            passed="8",
            failed="2",
            unknown="0",
        )

        error_text = " ".join(
            item.value for item in app.error
        )

        self.assertIn(
            "INSTRUCTION_ALREADY_CONSUMED",
            error_text,
        )
        self.assertIn(
            "TRANSFER_ALREADY_CONSUMED",
            error_text,
        )

    def test_partial_evidence_produces_seven_unknown_findings(self) -> None:
        app = self.run_app()
        self.select_scenario(app, "Partial evidence")

        self.assertEqual(len(app.exception), 0)
        self.assert_metrics(
            app,
            passed="3",
            failed="0",
            unknown="7",
        )

        warning_messages = [item.value for item in app.warning]

        self.assertTrue(
            any(
                "Controls requiring unavailable evidence" in message
                for message in warning_messages
            ),
            warning_messages,
        )

    def test_noncanonical_asset_fails_canonical_asset_only(self) -> None:
        app = self.run_app()
        self.select_scenario(
            app,
            "Expected = observed, but asset is non-canonical",
        )

        self.assertEqual(len(app.exception), 0)
        self.assert_metrics(
            app,
            passed="9",
            failed="1",
            unknown="0",
        )

        error_messages = [item.value for item in app.error]

        self.assertTrue(
            any(
                "CANONICAL_ASSET_MISMATCH" in message
                for message in error_messages
            ),
            error_messages,
        )


if __name__ == "__main__":
    unittest.main()
