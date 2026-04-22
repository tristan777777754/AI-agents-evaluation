from __future__ import annotations

import json
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

from app.schemas.calibration import (
    CalibrationCategorySchema,
    CalibrationDisagreementSchema,
    CalibrationReportSchema,
)
from app.schemas.contracts import DatasetItemSchema, DatasetSchema, FailureReason
from app.services.registry import get_scorer_config
from app.services.runs import _score_task

FIXTURE_DIR = Path(__file__).resolve().parents[2] / "tests" / "fixtures"
GOLDEN_SET_FIXTURE = FIXTURE_DIR / "golden_set.json"


def _read_fixture() -> dict[str, object]:
    return json.loads(GOLDEN_SET_FIXTURE.read_text(encoding="utf-8"))


def _iso_now() -> str:
    return datetime.now(UTC).isoformat()


def _as_failure_reason(value: object) -> FailureReason | None:
    if not isinstance(value, str) or value == "":
        return None
    return FailureReason(value)


def get_latest_calibration_report() -> CalibrationReportSchema:
    fixture = _read_fixture()
    dataset = DatasetSchema.model_validate(fixture)
    scorer_config_id = str(fixture.get("scorer_config_id", "sc_keyword_overlap_v1"))
    scorer_config = get_scorer_config(scorer_config_id)
    thresholds = scorer_config.thresholds_json
    pass_threshold = (
        float(thresholds.get("pass_fail", 0.8))
        if isinstance(thresholds.get("pass_fail", 0.8), int | float)
        else 0.8
    )
    items_raw = fixture.get("items", [])
    if not isinstance(items_raw, list):
        raise ValueError("Golden set items must be a list.")

    true_positive_count = 0
    false_positive_count = 0
    true_negative_count = 0
    false_negative_count = 0
    disagreements: list[CalibrationDisagreementSchema] = []
    category_totals: dict[str, dict[str, int]] = defaultdict(
        lambda: {
            "total_cases": 0,
            "labelled_pass_cases": 0,
            "predicted_pass_cases": 0,
            "correct_cases": 0,
        }
    )

    for raw_item in items_raw:
        item = DatasetItemSchema.model_validate(raw_item)
        metadata = item.metadata_json or {}
        expected_verdict = str(metadata.get("expected_verdict", "fail"))
        expected_failure_reason = _as_failure_reason(metadata.get("expected_failure_reason"))
        actual_failure_reason = _as_failure_reason(metadata.get("actual_failure_reason"))
        candidate_output_raw = metadata.get("candidate_output")
        candidate_output = candidate_output_raw if isinstance(candidate_output_raw, str) else None

        correctness, _, _, pass_fail, _ = _score_task(
            scorer_type=scorer_config.type,
            failure_reason=actual_failure_reason,
            expected_output=item.expected_output,
            final_output=candidate_output,
            rubric_json=item.rubric_json,
            trace_events=[],
            pass_threshold=pass_threshold,
            judge_model=scorer_config.judge_model,
            judge_provider=scorer_config.judge_provider,
        )
        predicted_failure_reason = actual_failure_reason
        if predicted_failure_reason is None and not pass_fail:
            predicted_failure_reason = FailureReason.answer_incorrect
        predicted_verdict = "pass" if pass_fail else "fail"

        category_stats = category_totals[item.category]
        category_stats["total_cases"] += 1
        if expected_verdict == "pass":
            category_stats["labelled_pass_cases"] += 1
        if predicted_verdict == "pass":
            category_stats["predicted_pass_cases"] += 1

        is_correct = predicted_verdict == expected_verdict
        if is_correct:
            category_stats["correct_cases"] += 1

        if expected_verdict == "pass" and predicted_verdict == "pass":
            true_positive_count += 1
        elif expected_verdict == "fail" and predicted_verdict == "pass":
            false_positive_count += 1
        elif expected_verdict == "fail" and predicted_verdict == "fail":
            true_negative_count += 1
        else:
            false_negative_count += 1

        if not is_correct or predicted_failure_reason != expected_failure_reason:
            expected_failure_reason_value = (
                expected_failure_reason.value if expected_failure_reason is not None else None
            )
            predicted_failure_reason_value = (
                predicted_failure_reason.value if predicted_failure_reason is not None else None
            )
            disagreements.append(
                CalibrationDisagreementSchema(
                    dataset_item_id=item.dataset_item_id,
                    category=item.category,
                    expected_verdict=expected_verdict,
                    predicted_verdict=predicted_verdict,
                    expected_failure_reason=expected_failure_reason_value,
                    predicted_failure_reason=predicted_failure_reason_value,
                    correctness=correctness,
                )
            )

    total_cases = (
        true_positive_count
        + false_positive_count
        + true_negative_count
        + false_negative_count
    )
    labelled_pass_cases = true_positive_count + false_negative_count
    labelled_fail_cases = true_negative_count + false_positive_count
    predicted_pass_cases = true_positive_count + false_positive_count
    predicted_fail_cases = true_negative_count + false_negative_count
    precision = round(
        true_positive_count / predicted_pass_cases if predicted_pass_cases else 0.0,
        2,
    )
    recall = round(true_positive_count / labelled_pass_cases if labelled_pass_cases else 0.0, 2)
    accuracy = round(
        (true_positive_count + true_negative_count) / total_cases if total_cases else 0.0,
        2,
    )

    per_category = [
        CalibrationCategorySchema(
            category=category,
            total_cases=stats["total_cases"],
            labelled_pass_cases=stats["labelled_pass_cases"],
            predicted_pass_cases=stats["predicted_pass_cases"],
            correct_cases=stats["correct_cases"],
            accuracy=round(
                stats["correct_cases"] / stats["total_cases"] if stats["total_cases"] else 0.0,
                2,
            ),
        )
        for category, stats in sorted(category_totals.items())
    ]

    return CalibrationReportSchema(
        fixture_id=dataset.dataset_id,
        scorer_config_id=scorer_config.scorer_config_id,
        generated_at=_iso_now(),
        total_cases=total_cases,
        labelled_pass_cases=labelled_pass_cases,
        labelled_fail_cases=labelled_fail_cases,
        predicted_pass_cases=predicted_pass_cases,
        predicted_fail_cases=predicted_fail_cases,
        true_positive_count=true_positive_count,
        false_positive_count=false_positive_count,
        true_negative_count=true_negative_count,
        false_negative_count=false_negative_count,
        precision=precision,
        recall=recall,
        accuracy=accuracy,
        per_category=per_category,
        disagreements=disagreements,
    )
