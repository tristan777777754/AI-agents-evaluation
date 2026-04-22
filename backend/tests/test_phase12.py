from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

FIXTURE_DIR = Path(__file__).parent / "fixtures"


def _upload_dataset(client: TestClient) -> None:
    with (FIXTURE_DIR / "dataset_valid.json").open("rb") as handle:
        response = client.post(
            "/api/v1/datasets",
            files={"file": ("dataset_valid.json", handle, "application/json")},
        )
    assert response.status_code == 201, response.text


def _trace_fixture() -> dict[str, object]:
    return json.loads((FIXTURE_DIR / "trace_compare_phase12.json").read_text(encoding="utf-8"))


def _create_trace_run(
    client: TestClient,
    *,
    agent_version_id: str,
    trace_profile: str,
) -> str:
    response = client.post(
        "/api/v1/runs",
        json={
            "dataset_id": "dataset_support_faq_v1",
            "agent_version_id": agent_version_id,
            "scorer_config_id": "sc_rubric_based_v1",
            "adapter_type": "stub",
            "adapter_config": {"trace_profile": trace_profile},
        },
    )
    assert response.status_code == 201, response.text
    return str(response.json()["run_id"])


def test_trace_compare_api_surfaces_regression_and_improvement_signals(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _upload_dataset(client)
    trace_fixture = _trace_fixture()

    class TraceFixtureAdapter:
        def run_task(self, input_text: str, config: dict[str, object]) -> dict[str, object]:
            profile = str(config.get("trace_profile", "baseline"))
            dataset_item_id = str(config["dataset_item_id"])
            expected_output = str(config["expected_output"])
            events = [
                {"step_index": 0, "event_type": "agent_start", "input": input_text},
                {"step_index": 1, "event_type": "final_output", "output": expected_output},
            ]

            if dataset_item_id == trace_fixture["regression_case"]["dataset_item_id"]:
                selected = trace_fixture["regression_case"][f"{profile}_steps"]
                events = [dict(event) for event in selected]
            elif dataset_item_id == trace_fixture["improvement_case"]["dataset_item_id"]:
                selected = trace_fixture["improvement_case"][f"{profile}_steps"]
                events = [dict(event) for event in selected]

            final_output = None
            for event in reversed(events):
                output = event.get("output")
                if isinstance(output, str):
                    final_output = output
                    break

            return {
                "final_output": final_output or expected_output,
                "latency_ms": 90,
                "token_usage": {"prompt": 9, "completion": 7},
                "cost": 0.0,
                "termination_reason": "completed",
                "error": None,
                "trace_events": events,
            }

    monkeypatch.setattr("app.services.runs._build_adapter", lambda _: TraceFixtureAdapter())

    baseline_run_id = _create_trace_run(
        client,
        agent_version_id="av_support_qa_v1",
        trace_profile="baseline",
    )
    candidate_run_id = _create_trace_run(
        client,
        agent_version_id="av_support_qa_v2",
        trace_profile="candidate",
    )

    regression = client.get(
        "/api/v1/compare/traces",
        params={
            "baseline": baseline_run_id,
            "candidate": candidate_run_id,
            "dataset_item_id": "ds_item_006",
        },
    )
    assert regression.status_code == 200, regression.text
    regression_body = regression.json()
    assert regression_body["baseline"]["derived_metrics"]["efficiency_score"] == 1.0
    assert regression_body["candidate"]["derived_metrics"]["efficiency_score"] == 0.5
    assert regression_body["same_final_output"] is True
    assert regression_body["overall_label"] == "regression"
    assert {signal["signal_key"] for signal in regression_body["regression_signals"]} >= {
        "more_steps",
        "more_tool_calls",
        "efficiency_score",
    }

    improvement = client.get(
        "/api/v1/compare/traces",
        params={
            "baseline": baseline_run_id,
            "candidate": candidate_run_id,
            "dataset_item_id": "ds_item_007",
        },
    )
    assert improvement.status_code == 200, improvement.text
    improvement_body = improvement.json()
    assert improvement_body["overall_label"] == "improvement"
    assert {signal["signal_key"] for signal in improvement_body["improvement_signals"]} >= {
        "fewer_steps",
        "fewer_tool_calls",
    }
    assert improvement_body["baseline"]["events"][1]["event_type"] == "tool_call"
    assert improvement_body["candidate"]["events"][1]["event_type"] == "final_output"


def test_trace_compare_requires_real_persisted_traces(client: TestClient) -> None:
    _upload_dataset(client)

    baseline_run = client.post(
        "/api/v1/runs",
        json={
            "dataset_id": "dataset_support_faq_v1",
            "agent_version_id": "av_support_qa_v1",
            "scorer_config_id": "sc_rule_based_v1",
            "adapter_type": "stub",
            "adapter_config": {},
        },
    )
    candidate_run = client.post(
        "/api/v1/runs",
        json={
            "dataset_id": "dataset_support_faq_v1",
            "agent_version_id": "av_support_qa_v2",
            "scorer_config_id": "sc_rule_based_v1",
            "adapter_type": "stub",
            "adapter_config": {},
        },
    )

    assert baseline_run.status_code == 201, baseline_run.text
    assert candidate_run.status_code == 201, candidate_run.text

    missing_case = client.get(
        "/api/v1/compare/traces",
        params={
            "baseline": baseline_run.json()["run_id"],
            "candidate": candidate_run.json()["run_id"],
            "dataset_item_id": "ds_item_missing",
        },
    )
    assert missing_case.status_code == 404
