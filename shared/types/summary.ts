import type { FailureReason, RunStatus } from "./contracts";

export type SamplingAggregateMetric = {
  mean: number | null;
  stddev: number | null;
  variance: number | null;
  min: number | null;
  max: number | null;
};

export type RunSamplingSummary = {
  group_id: string;
  sample_index: number;
  sample_count: number;
  completed_sample_count: number;
  sample_run_ids: string[];
  consistency_rate: number | null;
  success_rate: SamplingAggregateMetric;
  average_latency_ms: SamplingAggregateMetric;
  total_cost: SamplingAggregateMetric;
};

export type DashboardCategorySummary = {
  category: string;
  total_tasks: number;
  successful_tasks: number;
  failed_tasks: number;
  success_rate: number;
  average_latency_ms: number | null;
  total_cost: number;
};

export type DashboardFailureSummary = {
  failure_reason: FailureReason;
  count: number;
};

export type DashboardFailedCase = {
  task_run_id: string;
  run_id: string;
  dataset_item_id: string;
  category: string;
  failure_reason: FailureReason;
  error_message: string | null;
  final_output: string | null;
};

export type RunDashboardSummary = {
  run_id: string;
  agent_version_id: string;
  dataset_id: string;
  scorer_config_id: string;
  status: RunStatus;
  total_tasks: number;
  successful_tasks: number;
  failed_tasks: number;
  review_needed_count: number;
  success_rate: number;
  average_latency_ms: number | null;
  total_cost: number;
  sampling: RunSamplingSummary | null;
  category_breakdown: DashboardCategorySummary[];
  failure_breakdown: DashboardFailureSummary[];
  failed_cases: DashboardFailedCase[];
};
