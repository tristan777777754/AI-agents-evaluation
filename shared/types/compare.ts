import type { FailureReason, RunStatus } from "./contracts";

export type CompareMetricDelta = {
  baseline: number | null;
  candidate: number | null;
  delta: number | null;
};

export type CompareConfidenceInterval = {
  lower: number | null;
  upper: number | null;
};

export type CompareCredibility = {
  label: string;
  sample_size: number;
  confidence_interval: CompareConfidenceInterval;
  p_value: number | null;
  is_significant: boolean;
};

export type CompareCategoryDelta = {
  category: string;
  baseline_total_tasks: number;
  candidate_total_tasks: number;
  baseline_success_rate: number;
  candidate_success_rate: number;
  success_rate_delta: number;
  baseline_failed_tasks: number;
  candidate_failed_tasks: number;
};

export type CompareCase = {
  dataset_item_id: string;
  category: string;
  baseline_task_run_id: string;
  candidate_task_run_id: string;
  baseline_status: RunStatus;
  candidate_status: RunStatus;
  baseline_failure_reason: FailureReason | null;
  candidate_failure_reason: FailureReason | null;
  baseline_final_output: string | null;
  candidate_final_output: string | null;
};

export type CompareRunLineage = {
  run_id: string;
  dataset_id: string;
  dataset_snapshot_id: string | null;
  agent_version_id: string;
  agent_version_snapshot_hash: string;
  scorer_config_id: string;
  scorer_snapshot_hash: string;
  baseline: boolean;
  experiment_tag: string | null;
};

export type CompareLineage = {
  baseline: CompareRunLineage;
  candidate: CompareRunLineage;
};

export type CompareSamplingEvidence = {
  group_id: string | null;
  representative_run_id: string;
  sample_count: number;
  completed_sample_count: number;
  sample_run_ids: string[];
  success_rate_mean: number | null;
  success_rate_stddev: number | null;
  success_rate_variance: number | null;
  consistency_rate: number | null;
  is_stable: boolean;
};

export type CompareSamplingAssessment = {
  interpretation: string;
  baseline: CompareSamplingEvidence;
  candidate: CompareSamplingEvidence;
  notes: string;
};

export type RunComparison = {
  baseline_run_id: string;
  candidate_run_id: string;
  baseline_agent_version_id: string;
  candidate_agent_version_id: string;
  baseline_status: RunStatus;
  candidate_status: RunStatus;
  compared_task_count: number;
  sample_size: number;
  improvement_count: number;
  regression_count: number;
  confidence_interval: CompareConfidenceInterval;
  p_value: number | null;
  is_significant: boolean;
  success_rate: CompareMetricDelta;
  average_latency_ms: CompareMetricDelta;
  total_cost: CompareMetricDelta;
  review_needed_count: CompareMetricDelta;
  credibility: CompareCredibility;
  lineage: CompareLineage;
  sampling: CompareSamplingAssessment | null;
  category_deltas: CompareCategoryDelta[];
  improvements: CompareCase[];
  regressions: CompareCase[];
};

export type TraceDerivedMetrics = {
  step_count: number;
  tool_count: number;
  tool_names: string[];
  final_output_event_count: number;
  error_event_count: number;
  failure_step_index: number | null;
  max_steps: number | null;
  excess_step_count: number | null;
  efficiency_score: number | null;
};

export type TraceComparisonEntry = {
  run_id: string;
  task_run_id: string;
  dataset_item_id: string;
  category: string;
  status: RunStatus;
  pass_fail: boolean | null;
  failure_reason: FailureReason | null;
  input_text: string;
  expected_output: string | null;
  final_output: string | null;
  error_message: string | null;
  trace_id: string;
  storage_path: string;
  derived_metrics: TraceDerivedMetrics;
  events: {
    step_index: number;
    event_type: string;
    message: string | null;
    tool_name: string | null;
    input: unknown | null;
    output: unknown | null;
    latency_ms: number | null;
    status: string | null;
    error: string | null;
  }[];
};

export type TraceComparisonSignal = {
  signal_key: string;
  label: string;
  direction: string;
  baseline_value: string | number | null;
  candidate_value: string | number | null;
  detail: string | null;
};

export type TraceComparison = {
  baseline_run_id: string;
  candidate_run_id: string;
  dataset_item_id: string;
  category: string;
  input_text: string;
  expected_output: string | null;
  same_final_output: boolean;
  pass_fail_changed: boolean;
  overall_label: string;
  baseline: TraceComparisonEntry;
  candidate: TraceComparisonEntry;
  regression_signals: TraceComparisonSignal[];
  improvement_signals: TraceComparisonSignal[];
};
