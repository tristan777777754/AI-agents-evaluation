import type { PhaseContractSnapshot } from "../../shared/types";

export const phase1ContractPreview: PhaseContractSnapshot = {
  phase: {
    current_phase: "Phase 1",
    scope: [
      "repo skeleton",
      "canonical backend schemas",
      "shared TypeScript contracts",
      "minimum frontend and backend health surfaces",
    ],
    non_goals: [
      "dataset upload workflow",
      "evaluation run engine",
      "trace viewer",
      "dashboard and compare features",
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
    eval_run: [
      "run_id",
      "agent_version_id",
      "dataset_id",
      "scorer_config_id",
      "status",
      "started_at",
      "completed_at",
    ],
  },
};
