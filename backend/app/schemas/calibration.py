from __future__ import annotations

from pydantic import BaseModel, Field


class CalibrationCategorySchema(BaseModel):
    category: str
    total_cases: int
    labelled_pass_cases: int
    predicted_pass_cases: int
    correct_cases: int
    accuracy: float


class CalibrationDisagreementSchema(BaseModel):
    dataset_item_id: str
    category: str
    expected_verdict: str
    predicted_verdict: str
    expected_failure_reason: str | None = None
    predicted_failure_reason: str | None = None
    correctness: float | None = None


class CalibrationReportSchema(BaseModel):
    fixture_id: str = Field(..., examples=["golden_set_support_faq_v1"])
    scorer_config_id: str = Field(..., examples=["sc_keyword_overlap_v1"])
    generated_at: str
    total_cases: int
    labelled_pass_cases: int
    labelled_fail_cases: int
    predicted_pass_cases: int
    predicted_fail_cases: int
    true_positive_count: int
    false_positive_count: int
    true_negative_count: int
    false_negative_count: int
    precision: float
    recall: float
    accuracy: float
    per_category: list[CalibrationCategorySchema]
    disagreements: list[CalibrationDisagreementSchema]


class JudgeConsistencyParticipantSchema(BaseModel):
    run_id: str
    scorer_config_id: str
    judge_model: str | None = None
    judge_provider: str | None = None


class JudgeConsistencyDisagreementSchema(BaseModel):
    dataset_item_id: str
    baseline_pass_fail: bool
    candidate_pass_fail: bool
    baseline_judge_summary: str | None = None
    candidate_judge_summary: str | None = None


class JudgeConsistencyReportSchema(BaseModel):
    report_id: str
    dataset_id: str
    dataset_snapshot_id: str | None = None
    compared_task_count: int
    agreement_count: int
    disagreement_count: int
    agreement_rate: float
    participants: list[JudgeConsistencyParticipantSchema]
    disagreements: list[JudgeConsistencyDisagreementSchema]
