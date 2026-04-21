import type { PhaseContractSnapshot } from "../../shared/types";

const backendBaseUrl = process.env.NEXT_PUBLIC_BACKEND_BASE_URL ?? "http://localhost:8000";

export const phase1ContractPreview: PhaseContractSnapshot = {
  phase: {
    current_phase: "Phase 9",
    scope: [
      "human-labelled golden set for scorer verification",
      "read-only calibration reporting for precision, recall, and accuracy",
      "per-category scorer quality metrics derived from fixture-backed comparisons",
      "homepage calibration visibility without mutating canonical run scores",
    ],
    non_goals: [
      "LLM-as-judge calibration",
      "multi-scorer benchmark orchestration",
      "rewriting historical run score records",
      "changing canonical score schema for completed runs",
    ],
  },
  run_statuses: [
    "pending",
    "running",
    "completed",
    "failed",
    "cancelled",
    "partial_success",
  ],
  entities: {
    agent: ["agent_id", "name", "description", "owner_id", "created_at"],
    agent_version: [
      "agent_version_id",
      "agent_id",
      "version_name",
      "model",
      "prompt_hash",
      "config_json",
      "created_at",
    ],
    dataset: ["dataset_id", "name", "description", "schema_version", "source_type"],
    dataset_item: [
      "dataset_item_id",
      "dataset_id",
      "input_text",
      "category",
      "difficulty",
      "expected_output",
      "rubric_json",
      "reference_context",
      "metadata_json",
    ],
    scorer_config: [
      "scorer_config_id",
      "name",
      "type",
      "weights_json",
      "judge_model",
      "thresholds_json",
    ],
    eval_run: [
      "run_id",
      "agent_version_id",
      "dataset_id",
      "scorer_config_id",
      "status",
      "started_at",
      "completed_at",
    ],
    eval_task_run: [
      "task_run_id",
      "run_id",
      "dataset_item_id",
      "status",
      "final_output",
      "latency_ms",
      "token_usage",
      "cost",
    ],
    trace: ["trace_id", "task_run_id", "step_count", "tool_count", "error_flag", "storage_path"],
    score: [
      "score_id",
      "task_run_id",
      "correctness",
      "tool_use",
      "formatting",
      "pass_fail",
      "review_needed",
    ],
    review: ["review_id", "task_run_id", "reviewer_id", "verdict", "failure_label", "note"],
  },
};

export async function getContractSnapshot(): Promise<PhaseContractSnapshot> {
  const response = await fetch(`${backendBaseUrl}/api/v1/meta/contracts`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Contracts request failed with ${response.status}.`);
  }

  return (await response.json()) as PhaseContractSnapshot;
}
