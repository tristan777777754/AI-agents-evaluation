import type {
  AgentVersion,
  EvalRun,
  FailureReason,
  RunStatus,
  ScorerConfig,
  TraceSummary,
} from "./contracts";

export type RunCreateRequest = {
  dataset_id: string;
  agent_version_id: string;
  scorer_config_id: string;
  adapter_type: string;
  adapter_config: Record<string, unknown>;
  experiment_tag: string | null;
  notes: string | null;
};

export type RunScore = {
  correctness: number | null;
  tool_use: number | null;
  formatting: number | null;
  pass_fail: boolean;
  review_needed: boolean;
  evidence_json: Record<string, unknown> | null;
};

export type RunTaskResult = {
  task_run_id: string;
  run_id: string;
  dataset_item_id: string;
  status: RunStatus;
  input_text: string;
  category: string;
  difficulty: string | null;
  expected_output: string | null;
  final_output: string | null;
  latency_ms: number | null;
  token_usage: Record<string, number> | null;
  cost: number | null;
  termination_reason: string | null;
  error_message: string | null;
  failure_reason: FailureReason | null;
  trace_summary: TraceSummary | null;
  score: RunScore | null;
  started_at: string | null;
  completed_at: string | null;
};

export type RunTaskList = {
  run_id: string;
  total_count: number;
  items: RunTaskResult[];
};

export type RunSummary = EvalRun & {
  adapter_type: string;
  total_tasks: number;
  completed_tasks: number;
  failed_tasks: number;
};

export type RunDetail = RunSummary & {
  agent_version: AgentVersion;
  scorer_config: ScorerConfig;
};

export type RegistryList = {
  agent_versions: AgentVersion[];
  scorer_configs: ScorerConfig[];
};
