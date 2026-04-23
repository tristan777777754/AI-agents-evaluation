import type { PhaseContractSnapshot } from "../../shared/types";

const backendBaseUrl = process.env.NEXT_PUBLIC_BACKEND_BASE_URL ?? "http://localhost:8000";

export const phase1ContractPreview: PhaseContractSnapshot = {
  phase: {
    current_phase: "Phase 16",
    scope: [
      "generator, agent, and judge metadata stored as explicit governed roles",
      "compatibility rules that reject risky self-judge or same-model evaluation setups",
      "judge audit-trail persistence for model, prompt, and reasoning metadata",
      "cross-judge consistency reporting derived from persisted evaluation artifacts",
    ],
    non_goals: [
      "bring-your-own-key or tenant-scoped credential flows",
      "replacing the existing scorer abstraction with a new platform",
      "changing canonical run statuses, compare semantics, or baseline meaning",
      "turning the workbench into a provider marketplace or multi-tenant SaaS",
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
      "provider",
      "prompt_hash",
      "config_json",
      "governance",
      "created_at",
    ],
    dataset: [
      "dataset_id",
      "name",
      "description",
      "schema_version",
      "source_type",
      "source_origin",
      "lifecycle_status",
      "approval_status",
      "generated_prompt",
      "approved_by",
      "approved_at",
      "latest_snapshot_id",
    ],
    dataset_snapshot: [
      "dataset_snapshot_id",
      "dataset_id",
      "version_number",
      "checksum",
      "parent_snapshot_id",
      "created_at",
    ],
    dataset_item: [
      "dataset_item_id",
      "dataset_id",
      "input_text",
      "category",
      "difficulty",
      "expected_output",
      "rubric_json",
      "reference_context",
      "source_origin",
      "source_task_run_id",
      "tags",
      "metadata_json",
    ],
    scorer_config: [
      "scorer_config_id",
      "name",
      "type",
      "weights_json",
      "judge_model",
      "judge_provider",
      "thresholds_json",
      "governance",
    ],
    eval_run: [
      "run_id",
      "agent_version_id",
      "dataset_id",
      "dataset_snapshot_id",
      "dataset_tag_filter",
      "scorer_config_id",
      "status",
      "baseline",
      "experiment_tag",
      "notes",
      "sampling",
      "started_at",
      "completed_at",
    ],
    eval_task_run: [
      "task_run_id",
      "run_id",
      "dataset_item_id",
      "dataset_item_tags",
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
      "evidence_json",
      "judge_audit",
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
