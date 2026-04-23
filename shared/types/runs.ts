import type {
  Agent,
  AgentVersion,
  EvalRun,
  FailureReason,
  RunStatus,
  ScorerConfig,
  TraceSummary,
} from "./contracts";
import type { RunComparison } from "./compare";

export type RunCreateRequest = {
  dataset_id: string;
  agent_version_id: string;
  scorer_config_id: string;
  dataset_tag_filter?: string[];
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
  dataset_item_tags: string[];
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

export type RunListPage = {
  items: RunSummary[];
  total_count: number;
  page: number;
  per_page: number;
  has_next_page: boolean;
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

export type RegistryDefaults = {
  default_dataset_id: string | null;
  default_scorer_config_id: string | null;
};

export type RegistryList = {
  agents: Agent[];
  agent_versions: AgentVersion[];
  scorer_configs: ScorerConfig[];
  defaults: RegistryDefaults;
};

export type AgentCreateRequest = {
  agent_id: string;
  name: string;
  description?: string | null;
  owner_id?: string | null;
};

export type AgentVersionCreateRequest = {
  agent_version_id: string;
  agent_id: string;
  version_name: string;
  model: string;
  prompt_hash: string;
  config_json: Record<string, unknown>;
};

export type RegistryDefaultsUpdateRequest = RegistryDefaults;

export type QuickRunRequest = {
  agent_version_id: string;
  adapter_type: string;
  adapter_config: Record<string, unknown>;
  experiment_tag: string | null;
  notes: string | null;
};

export type AutoCompare = {
  baseline_run_id: string | null;
  candidate_run_id: string;
  selection_reason: string | null;
  comparison: RunComparison | null;
};

export type QuickRunResponse = {
  run: RunDetail;
  auto_compare: AutoCompare;
};
