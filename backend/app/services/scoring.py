from __future__ import annotations

import math
import re
from typing import Any

from app.schemas.contracts import FailureReason


def significant_tokens(text: str) -> list[str]:
    return [
        token
        for token in re.findall(r"[a-z0-9]+", text.lower())
        if len(token) >= 3 or token.isdigit()
    ]


def keyword_overlap_score(expected_output: str | None, final_output: str | None) -> float:
    if not expected_output or not final_output:
        return 0.0

    expected_tokens = significant_tokens(expected_output)
    if not expected_tokens:
        return 0.0

    actual_text = final_output.lower()
    matched_tokens = sum(1 for token in expected_tokens if token in actual_text)
    return round(matched_tokens / len(expected_tokens), 2)


def score_for_failure(failure_reason: FailureReason | None) -> tuple[float, float, float, bool]:
    if failure_reason is None:
        return 1.0, 1.0, 1.0, True
    if failure_reason is FailureReason.answer_incorrect:
        return 0.0, 1.0, 1.0, False
    if failure_reason is FailureReason.tool_error:
        return 0.0, 0.0, 1.0, False
    if failure_reason is FailureReason.format_error:
        return 0.0, 1.0, 0.0, False
    return 0.0, 0.0, 0.0, False


def provider_from_model_name(model_name: str | None) -> str | None:
    if not model_name:
        return None

    lowered = model_name.lower()
    if lowered.startswith("gpt-") or lowered.startswith("o") or lowered.startswith("openai:"):
        return "openai"
    if lowered.startswith("anthropic:") or lowered.startswith("claude"):
        return "anthropic"
    return lowered.split(":", maxsplit=1)[0]


def validate_judge_compatibility(
    *,
    scorer_type: str,
    judge_provider: str | None,
    judge_model: str | None,
    agent_model: str | None,
    compatibility_policy: dict[str, object] | None = None,
) -> None:
    if scorer_type not in {"llm_judge", "rubric_based"}:
        return

    agent_provider = provider_from_model_name(agent_model)
    provider_separation_required = True
    same_model_disallowed = True
    blocked_same_provider_pairs: set[str] = set()
    if isinstance(compatibility_policy, dict):
        provider_separation_required = bool(
            compatibility_policy.get("provider_separation_required", True)
        )
        same_model_disallowed = bool(compatibility_policy.get("same_model_disallowed", True))
        blocked_pairs_raw = compatibility_policy.get("blocked_same_provider_pairs", [])
        if isinstance(blocked_pairs_raw, list):
            blocked_same_provider_pairs = {str(pair).lower() for pair in blocked_pairs_raw}

    pair_key = ""
    if judge_provider and agent_provider:
        ordered_pair = sorted([judge_provider.lower(), agent_provider.lower()])
        pair_key = f"{ordered_pair[0]}:{ordered_pair[1]}"

    if (
        provider_separation_required
        and judge_provider
        and agent_provider
        and judge_provider == agent_provider
    ):
        raise ValueError(
            "Judge-based scoring requires a judge provider different from the agent provider."
        )
    if pair_key and pair_key in blocked_same_provider_pairs:
        raise ValueError(
            "Judge compatibility policy blocked the requested agent/judge provider pairing."
        )
    if (
        same_model_disallowed
        and judge_model
        and agent_model
        and judge_model.lower() == agent_model.lower()
    ):
        raise ValueError(
            "Judge-based scoring requires a judge model different from the evaluated agent model."
        )


def llm_judge_score(
    *,
    expected_output: str | None,
    final_output: str | None,
    pass_threshold: float,
    judge_model: str | None,
    judge_provider: str | None,
) -> tuple[float, bool, dict[str, object]]:
    correctness = keyword_overlap_score(expected_output, final_output)
    pass_fail = correctness >= pass_threshold
    evidence: dict[str, object] = {
        "score_method": "llm_judge",
        "judge_model": judge_model,
        "judge_provider": judge_provider,
        "judge_verdict": "pass" if pass_fail else "fail",
        "matched_token_ratio": correctness,
        "reasoning_summary": (
            "Deterministic judge proxy accepted the answer because the expected "
            "evidence tokens were present."
            if pass_fail
            else "Deterministic judge proxy rejected the answer because required "
            "evidence tokens were missing."
        ),
    }
    return correctness, pass_fail, evidence


def rubric_based_score(
    *,
    rubric_json: dict[str, Any] | None,
    expected_output: str | None,
    final_output: str | None,
    trace_events: list[dict[str, object]],
    pass_threshold: float,
) -> tuple[float, bool, dict[str, object]]:
    rubric = rubric_json or {}
    actual_text = (final_output or "").lower()

    must_do = [str(item).strip() for item in rubric.get("must_do", []) if str(item).strip()]
    must_not_do = [
        str(item).strip() for item in rubric.get("must_not_do", []) if str(item).strip()
    ]
    max_steps_raw = rubric.get("max_steps")
    max_steps = int(max_steps_raw) if isinstance(max_steps_raw, int | float) else None

    checks_total = 0
    checks_passed = 0

    must_do_results = []
    for clause in must_do:
        checks_total += 1
        passed = clause.lower() in actual_text
        must_do_results.append({"clause": clause, "passed": passed})
        if passed:
            checks_passed += 1

    must_not_do_results = []
    for clause in must_not_do:
        checks_total += 1
        passed = clause.lower() not in actual_text
        must_not_do_results.append({"clause": clause, "passed": passed})
        if passed:
            checks_passed += 1

    step_check = None
    if max_steps is not None:
        checks_total += 1
        actual_steps = len(trace_events)
        passed = actual_steps <= max_steps
        step_check = {"max_steps": max_steps, "actual_steps": actual_steps, "passed": passed}
        if passed:
            checks_passed += 1

    if checks_total == 0:
        correctness = keyword_overlap_score(expected_output, final_output)
    else:
        correctness = round(checks_passed / checks_total, 2)

    pass_fail = correctness >= pass_threshold and all(
        result["passed"] for result in must_do_results + must_not_do_results
    )
    if step_check is not None:
        pass_fail = pass_fail and bool(step_check["passed"])

    evidence: dict[str, object] = {
        "score_method": "rubric_based",
        "rubric_applied": bool(rubric),
        "must_do": must_do_results,
        "must_not_do": must_not_do_results,
    }
    if step_check is not None:
        evidence["step_limit"] = step_check

    return correctness, pass_fail, evidence


def normal_cdf(value: float) -> float:
    return 0.5 * (1 + math.erf(value / math.sqrt(2)))


def build_judge_audit(
    *,
    scorer_type: str,
    agent_metadata: dict[str, object] | None,
    scorer_governance: dict[str, object] | None,
    evidence: dict[str, object] | None,
) -> dict[str, object] | None:
    if scorer_type not in {"llm_judge", "rubric_based"}:
        return None

    governance = scorer_governance or {}
    judge_raw = governance.get("judge")
    generator_raw = governance.get("generator")
    compatibility_raw = governance.get("compatibility")
    judge: dict[str, object] = judge_raw if isinstance(judge_raw, dict) else {}
    generator: dict[str, object] = generator_raw if isinstance(generator_raw, dict) else {}
    compatibility: dict[str, object] = (
        compatibility_raw if isinstance(compatibility_raw, dict) else {}
    )
    reasoning_summary = None
    if isinstance(evidence, dict) and isinstance(evidence.get("reasoning_summary"), str):
        reasoning_summary = evidence.get("reasoning_summary")
    reasoning_available = judge.get("reasoning_available")
    return {
        "audit_version": "phase16_v1",
        "generator": generator,
        "agent": agent_metadata or {},
        "judge": judge,
        "compatibility": compatibility,
        "reasoning_metadata": {
            "available": bool(reasoning_available),
            "summary": reasoning_summary,
            "placeholder": (
                None
                if reasoning_available
                else "Reasoning metadata unavailable for this scorer or provider."
            ),
        },
    }
