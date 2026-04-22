from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.schemas.contracts import ScorerConfigSchema
from app.services.registry import _read_fixture

FIXTURE_DIR = Path(__file__).parent / "fixtures"


def _upload_dataset(client: TestClient) -> None:
    with (FIXTURE_DIR / "dataset_valid.json").open("rb") as handle:
        response = client.post(
            "/api/v1/datasets",
            files={"file": ("dataset_valid.json", handle, "application/json")},
        )
    assert response.status_code == 201, response.text


def test_llm_judge_persists_additive_score_evidence(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _upload_dataset(client)

    class JudgeFixtureAdapter:
        def run_task(self, input_text: str, config: dict[str, object]) -> dict[str, object]:
            output = str(config["expected_output"])
            return {
                "final_output": output,
                "latency_ms": 101,
                "token_usage": {"prompt": 18, "completion": 12},
                "cost": 0.0,
                "termination_reason": "completed",
                "error": None,
                "trace_events": [
                    {"step_index": 0, "event_type": "agent_start", "input": input_text},
                    {"step_index": 1, "event_type": "final_output", "output": output},
                ],
            }

    monkeypatch.setattr("app.services.runs._build_adapter", lambda _: JudgeFixtureAdapter())

    response = client.post(
        "/api/v1/runs",
        json={
            "dataset_id": "dataset_support_faq_v1",
            "agent_version_id": "av_support_qa_v1",
            "scorer_config_id": "sc_llm_judge_v1",
            "adapter_type": "stub",
            "adapter_config": {},
        },
    )

    assert response.status_code == 201, response.text
    run_id = response.json()["run_id"]

    tasks = client.get(f"/api/v1/runs/{run_id}/tasks")
    assert tasks.status_code == 200, tasks.text
    first_task = tasks.json()["items"][0]
    assert first_task["final_output"] == first_task["expected_output"]
    assert first_task["score"]["pass_fail"] is True
    assert first_task["score"]["evidence_json"]["score_method"] == "llm_judge"
    assert first_task["score"]["evidence_json"]["judge_provider"] == "anthropic"


def test_rubric_based_scorer_consumes_dataset_rubric_fields(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _upload_dataset(client)

    class RubricFixtureAdapter:
        def run_task(self, input_text: str, config: dict[str, object]) -> dict[str, object]:
            dataset_item_id = str(config["dataset_item_id"])
            if dataset_item_id == "ds_item_006":
                output = "Enterprise users can find it in the policy center knowledge base."
                trace_events = [
                    {"step_index": 0, "event_type": "agent_start", "input": input_text},
                    {"step_index": 1, "event_type": "tool_call", "tool_name": "document_lookup"},
                ]
            else:
                output = str(config["expected_output"])
                trace_events = [
                    {"step_index": 0, "event_type": "agent_start", "input": input_text},
                    {"step_index": 1, "event_type": "final_output", "output": output},
                ]
            return {
                "final_output": output,
                "latency_ms": 87,
                "token_usage": {"prompt": 15, "completion": 10},
                "cost": 0.0,
                "termination_reason": "completed",
                "error": None,
                "trace_events": trace_events,
            }

    monkeypatch.setattr("app.services.runs._build_adapter", lambda _: RubricFixtureAdapter())

    response = client.post(
        "/api/v1/runs",
        json={
            "dataset_id": "dataset_support_faq_v1",
            "agent_version_id": "av_support_qa_v1",
            "scorer_config_id": "sc_rubric_based_v1",
            "adapter_type": "stub",
            "adapter_config": {},
        },
    )

    assert response.status_code == 201, response.text
    run_id = response.json()["run_id"]

    tasks = client.get(f"/api/v1/runs/{run_id}/tasks")
    rubric_task = next(
        item for item in tasks.json()["items"] if item["dataset_item_id"] == "ds_item_006"
    )
    evidence = rubric_task["score"]["evidence_json"]

    assert evidence["score_method"] == "rubric_based"
    assert evidence["must_do"][0]["clause"] == "policy center"
    assert evidence["must_do"][0]["passed"] is True
    assert evidence["must_not_do"][0]["clause"] == "trust center"
    assert evidence["must_not_do"][0]["passed"] is True
    assert evidence["step_limit"]["max_steps"] == 2
    assert evidence["step_limit"]["actual_steps"] == 2


def test_compare_returns_recomputable_statistical_fields(client: TestClient) -> None:
    _upload_dataset(client)

    baseline = client.post(
        "/api/v1/runs",
        json={
            "dataset_id": "dataset_support_faq_v1",
            "agent_version_id": "av_support_qa_v1",
            "scorer_config_id": "sc_rule_based_v1",
            "adapter_type": "stub",
            "adapter_config": {"failure_map": {"ds_item_003": True}},
        },
    )
    assert baseline.status_code == 201, baseline.text

    candidate = client.post(
        "/api/v1/runs",
        json={
            "dataset_id": "dataset_support_faq_v1",
            "agent_version_id": "av_support_qa_v2",
            "scorer_config_id": "sc_rule_based_v1",
            "adapter_type": "stub",
            "adapter_config": {},
        },
    )
    assert candidate.status_code == 201, candidate.text

    comparison = client.get(
        "/api/v1/runs/compare",
        params={
            "baseline_run_id": baseline.json()["run_id"],
            "candidate_run_id": candidate.json()["run_id"],
        },
    )
    assert comparison.status_code == 200, comparison.text
    body = comparison.json()

    assert body["sample_size"] == 20
    assert body["confidence_interval"]["lower"] == -4.8
    assert body["confidence_interval"]["upper"] == 14.8
    assert body["p_value"] == 0.3173
    assert body["is_significant"] is False
    assert body["credibility"]["label"] == "directional_improvement"


def test_judge_compatibility_rejects_same_provider_by_default(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _upload_dataset(client)
    same_provider_config = ScorerConfigSchema.model_validate(
        _read_fixture("scorer_config_llm_judge.json")
    )
    same_provider_config.judge_provider = "openai"

    monkeypatch.setattr("app.services.runs.get_scorer_config", lambda _: same_provider_config)

    response = client.post(
        "/api/v1/runs",
        json={
            "dataset_id": "dataset_support_faq_v1",
            "agent_version_id": "av_support_qa_v1",
            "scorer_config_id": "sc_llm_judge_v1",
            "adapter_type": "stub",
            "adapter_config": {},
        },
    )

    assert response.status_code == 400
    assert "judge provider different" in response.json()["detail"].lower()
