import type { FailureReason } from "./contracts";

export type ReviewDetail = {
  review_id: string;
  task_run_id: string;
  run_id: string;
  dataset_item_id: string;
  reviewer_id: string;
  verdict: string | null;
  failure_label: string | null;
  note: string | null;
  created_at: string | null;
  updated_at: string | null;
};

export type ReviewUpsertRequest = {
  reviewer_id: string;
  verdict: string | null;
  failure_label: string | null;
  note: string | null;
};

export type ReviewQueueItem = {
  task_run_id: string;
  run_id: string;
  dataset_item_id: string;
  category: string;
  input_text: string;
  status: string;
  review_needed: boolean;
  failure_reason: FailureReason | null;
  error_message: string | null;
  final_output: string | null;
  review_status: string;
  review: ReviewDetail | null;
};

export type ReviewQueue = {
  total_count: number;
  pending_count: number;
  reviewed_count: number;
  page: number;
  per_page: number;
  has_next_page: boolean;
  items: ReviewQueueItem[];
};
