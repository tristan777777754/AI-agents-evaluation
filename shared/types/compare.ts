import type { FailureReason, RunStatus } from "./contracts";

export type CompareMetricDelta = {
  baseline: number | null;
  candidate: number | null;
  delta: number | null;
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

export type RunComparison = {
  baseline_run_id: string;
  candidate_run_id: string;
  baseline_agent_version_id: string;
  candidate_agent_version_id: string;
  baseline_status: RunStatus;
  candidate_status: RunStatus;
  compared_task_count: number;
  improvement_count: number;
  regression_count: number;
  success_rate: CompareMetricDelta;
  average_latency_ms: CompareMetricDelta;
  total_cost: CompareMetricDelta;
  review_needed_count: CompareMetricDelta;
  category_deltas: CompareCategoryDelta[];
  improvements: CompareCase[];
  regressions: CompareCase[];
};
