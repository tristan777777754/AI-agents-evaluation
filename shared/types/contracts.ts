export type RunStatus =
  | "pending"
  | "running"
  | "completed"
  | "failed"
  | "cancelled"
  | "partial_success";

export type FailureReason =
  | "answer_incorrect"
  | "tool_error"
  | "format_error"
  | "execution_failed";

export type SourceType = "json" | "csv" | "fixture" | "prompt" | "promotion";
export type DatasetSourceOrigin = "manual" | "generated" | "promoted_from_failure";
export type DatasetLifecycleStatus = "draft" | "published";
export type DatasetApprovalStatus = "pending_review" | "approved";

export type PhaseMarker = {
  current_phase: string;
  scope: string[];
  non_goals: string[];
};

export type Agent = {
  agent_id: string;
  name: string;
  description: string | null;
  owner_id: string | null;
  created_at: string | null;
};

export type AgentVersion = {
  agent_version_id: string;
  agent_id: string;
  version_name: string;
  model: string;
  prompt_hash: string;
  config_json: Record<string, unknown>;
  created_at: string | null;
};

export type Dataset = {
  dataset_id: string;
  name: string;
  description: string | null;
  schema_version: string;
  source_type: SourceType;
  source_origin: DatasetSourceOrigin;
  lifecycle_status: DatasetLifecycleStatus;
  approval_status: DatasetApprovalStatus;
  generated_prompt: string | null;
  approved_by: string | null;
  approved_at: string | null;
  latest_snapshot_id: string | null;
};

export type DatasetSnapshot = {
  dataset_snapshot_id: string;
  dataset_id: string;
  version_number: number;
  checksum: string;
  parent_snapshot_id: string | null;
  created_at: string | null;
};

export type DatasetItem = {
  dataset_item_id: string;
  dataset_id: string;
  input_text: string;
  category: string;
  difficulty: string | null;
  expected_output: string | null;
  rubric_json: Record<string, unknown> | null;
  reference_context: string | null;
  source_origin: DatasetSourceOrigin;
  source_task_run_id: string | null;
  tags: string[];
  metadata_json: Record<string, unknown> | null;
};

export type ScorerConfig = {
  scorer_config_id: string;
  name: string;
  type: string;
  weights_json: Record<string, number>;
  judge_model: string | null;
  judge_provider: string | null;
  thresholds_json: Record<string, number>;
};

export type EvalRun = {
  run_id: string;
  agent_version_id: string;
  dataset_id: string;
  dataset_snapshot_id: string | null;
  dataset_tag_filter: string[];
  scorer_config_id: string;
  status: RunStatus;
  baseline: boolean;
  experiment_tag: string | null;
  notes: string | null;
  started_at: string | null;
  completed_at: string | null;
};

export type EvalTaskRun = {
  task_run_id: string;
  run_id: string;
  dataset_item_id: string;
  dataset_item_tags: string[];
  status: RunStatus;
  final_output: string | null;
  latency_ms: number | null;
  token_usage: Record<string, number> | null;
  cost: number | null;
};

export type TraceSummary = {
  trace_id: string;
  task_run_id: string;
  step_count: number;
  tool_count: number;
  error_flag: boolean;
  storage_path: string;
};

export type Score = {
  score_id: string;
  task_run_id: string;
  correctness: number | null;
  tool_use: number | null;
  formatting: number | null;
  pass_fail: boolean;
  review_needed: boolean;
  evidence_json: Record<string, unknown> | null;
};

export type Review = {
  review_id: string;
  task_run_id: string;
  reviewer_id: string;
  verdict: string | null;
  failure_label: string | null;
  note: string | null;
};

export type PhaseContractSnapshot = {
  phase: PhaseMarker;
  run_statuses: RunStatus[];
  entities: Record<string, string[]>;
};
