import type { FailureReason, TraceSummary } from "./contracts";
import type { ReviewDetail } from "./reviews";
import type { RunTaskResult } from "./runs";

export type TraceEvent = {
  step_index: number;
  event_type: string;
  message: string | null;
  tool_name: string | null;
  input: unknown | null;
  output: unknown | null;
  latency_ms: number | null;
  status: string | null;
  error: string | null;
};

export type TaskRunDetail = RunTaskResult & {
  failure_reason: FailureReason | null;
  trace_summary: TraceSummary | null;
  review: ReviewDetail | null;
};

export type TraceDetail = {
  trace_id: string;
  task_run_id: string;
  run_id: string;
  failure_reason: FailureReason | null;
  input_text: string;
  expected_output: string | null;
  final_output: string | null;
  error_message: string | null;
  summary: TraceSummary;
  events: TraceEvent[];
};
