from __future__ import annotations

from fastapi.testclient import TestClient


def _upload_dataset(client: TestClient) -> None:
    with open("backend/tests/fixtures/dataset_valid.json", "rb") as handle:
        response = client.post(
            "/api/v1/datasets",
            files={"file": ("dataset_valid.json", handle, "application/json")},
        )
    assert response.status_code == 201, response.text


def test_registry_and_run_detail_expose_governed_role_metadata(client: TestClient) -> None:
    _upload_dataset(client)

    registry = client.get("/api/v1/registry")
    assert registry.status_code == 200, registry.text
    scorer = next(
        item
        for item in registry.json()["scorer_configs"]
        if item["scorer_config_id"] == "sc_llm_judge_v1"
    )
    assert scorer["governance"]["generator"]["role"] == "generator"
    assert scorer["governance"]["judge"]["prompt_version"] == "phase16_v1"
    assert scorer["governance"]["compatibility"]["provider_separation_required"] is True

    run = client.post(
        "/api/v1/runs",
        json={
            "dataset_id": "dataset_support_faq_v1",
            "agent_version_id": "av_support_qa_v1",
            "scorer_config_id": "sc_llm_judge_v1",
            "adapter_type": "stub",
            "adapter_config": {},
        },
    )
    assert run.status_code == 201, run.text

    detail = client.get(f"/api/v1/runs/{run.json()['run_id']}")
    assert detail.status_code == 200, detail.text
    body = detail.json()
    assert body["agent_version"]["provider"] == "openai"
    assert body["agent_version"]["governance"]["role"] == "agent"
    assert body["scorer_config"]["governance"]["judge"]["provider"] == "anthropic"


def test_phase16_compatibility_rejects_same_model_judge(
    client: TestClient,
    monkeypatch,
) -> None:
    from app.schemas.contracts import ScorerConfigSchema
    from app.services.registry import _read_fixture

    _upload_dataset(client)
    config = ScorerConfigSchema.model_validate(_read_fixture("scorer_config_llm_judge.json"))
    config.judge_model = "gpt-4.1-mini"

    monkeypatch.setattr("app.services.runs.get_scorer_config", lambda _: config)

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
    assert "judge model different" in response.json()["detail"].lower()


def test_judge_audit_persists_prompt_and_reasoning_metadata(client: TestClient) -> None:
    _upload_dataset(client)

    run = client.post(
        "/api/v1/runs",
        json={
            "dataset_id": "dataset_support_faq_v1",
            "agent_version_id": "av_support_qa_v1",
            "scorer_config_id": "sc_llm_judge_v1",
            "adapter_type": "stub",
            "adapter_config": {},
        },
    )
    assert run.status_code == 201, run.text

    tasks = client.get(f"/api/v1/runs/{run.json()['run_id']}/tasks")
    assert tasks.status_code == 200, tasks.text
    first_task = tasks.json()["items"][0]
    judge_audit = first_task["score"]["judge_audit"]

    assert judge_audit["judge"]["provider"] == "anthropic"
    assert judge_audit["judge"]["model"] == "claude-3-5-sonnet"
    assert judge_audit["judge"]["prompt_version"] == "phase16_v1"
    assert judge_audit["agent"]["provider"] == "openai"
    assert judge_audit["reasoning_metadata"]["available"] is True
    assert "expected evidence tokens" in judge_audit["reasoning_metadata"]["summary"]


def test_judge_consistency_report_uses_persisted_runs(
    client: TestClient,
    monkeypatch,
) -> None:
    _upload_dataset(client)

    class ConsistencyAdapter:
        def run_task(self, input_text: str, config: dict[str, object]) -> dict[str, object]:
            expected_output = str(config["expected_output"])
            dataset_item_id = str(config["dataset_item_id"])
            output = expected_output
            if dataset_item_id == "ds_item_006":
                output = (
                    "Enterprise users can find it in the policy center knowledge base, "
                    "not the trust center."
                )
            return {
                "final_output": output,
                "latency_ms": 40,
                "token_usage": {"prompt": 10, "completion": 8},
                "cost": 0.0,
                "termination_reason": "completed",
                "error": None,
                "trace_events": [
                    {"step_index": 0, "event_type": "agent_start", "input": input_text},
                    {"step_index": 1, "event_type": "final_output", "output": output},
                ],
            }

    monkeypatch.setattr("app.services.runs._build_adapter", lambda _: ConsistencyAdapter())

    llm_run = client.post(
        "/api/v1/runs",
        json={
            "dataset_id": "dataset_support_faq_v1",
            "agent_version_id": "av_support_qa_v1",
            "scorer_config_id": "sc_llm_judge_v1",
            "adapter_type": "stub",
            "adapter_config": {},
        },
    )
    rubric_run = client.post(
        "/api/v1/runs",
        json={
            "dataset_id": "dataset_support_faq_v1",
            "agent_version_id": "av_support_qa_v1",
            "scorer_config_id": "sc_rubric_based_v1",
            "adapter_type": "stub",
            "adapter_config": {},
        },
    )
    assert llm_run.status_code == 201, llm_run.text
    assert rubric_run.status_code == 201, rubric_run.text

    response = client.get(
        "/api/v1/calibration/judge-consistency",
        params={
            "baseline_run_id": llm_run.json()["run_id"],
            "candidate_run_id": rubric_run.json()["run_id"],
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()

    assert body["compared_task_count"] == 20
    assert body["agreement_rate"] < 1.0
    assert body["participants"][0]["scorer_config_id"] == "sc_llm_judge_v1"
    assert body["participants"][1]["scorer_config_id"] == "sc_rubric_based_v1"
    assert any(item["dataset_item_id"] == "ds_item_006" for item in body["disagreements"])
