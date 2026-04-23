from __future__ import annotations

from app.schemas.contracts import (
    DatasetItemSchema,
    DatasetSchema,
    DatasetSnapshotSchema,
    EvalRunSchema,
    PhaseContractSnapshot,
    RunStatus,
    SourceType,
)


def test_dataset_item_requires_input_text_and_category() -> None:
    item = DatasetItemSchema(
        dataset_item_id="ds_item_001",
        dataset_id="dataset_support_faq_v1",
        input_text="What is the refund policy?",
        category="refund_policy",
    )

    assert item.input_text == "What is the refund policy?"
    assert item.category == "refund_policy"


def test_phase_contract_snapshot_contains_core_entities() -> None:
    snapshot = PhaseContractSnapshot.build_default()

    assert snapshot.phase.current_phase == "Phase 15"
    assert "eval_run" in snapshot.entities
    assert "dataset_snapshot" in snapshot.entities
    assert RunStatus.partial_success in snapshot.run_statuses
    assert "evidence_json" in snapshot.entities["score"]
    assert "lifecycle_status" in snapshot.entities["dataset"]
    assert "sampling" in snapshot.entities["eval_run"]


def test_eval_run_schema_accepts_canonical_status_values() -> None:
    run = EvalRunSchema(
        run_id="run_20260420_001",
        agent_version_id="av_support_qa_v1",
        dataset_id="dataset_support_faq_v1",
        dataset_snapshot_id="dataset_support_faq_v1__snapshot_001",
        scorer_config_id="sc_rule_based_v1",
        status=RunStatus.pending,
        baseline=True,
        experiment_tag="phase10-check",
    )

    assert run.status is RunStatus.pending
    assert run.baseline is True


def test_dataset_schema_defaults_schema_version() -> None:
    dataset = DatasetSchema(
        dataset_id="dataset_support_faq_v1",
        name="Support FAQ Eval Set",
        source_type=SourceType.json,
    )

    assert dataset.schema_version == "1.0"
    assert dataset.lifecycle_status.value == "published"


def test_dataset_snapshot_schema_tracks_immutable_versions() -> None:
    snapshot = DatasetSnapshotSchema(
        dataset_snapshot_id="dataset_support_faq_v1__snapshot_001",
        dataset_id="dataset_support_faq_v1",
        version_number=1,
        checksum="abc123",
    )

    assert snapshot.version_number == 1
