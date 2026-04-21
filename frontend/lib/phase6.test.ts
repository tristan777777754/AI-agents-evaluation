import { describe, expect, it } from "vitest";

import type { ReviewQueue, RunComparison } from "../../shared/types";

describe("phase 6 compare and review contracts", () => {
  it("supports pairwise run comparison deltas", () => {
    const comparison: RunComparison = {
      baseline_run_id: "run_v1",
      candidate_run_id: "run_v2",
      baseline_agent_version_id: "av_support_qa_v1",
      candidate_agent_version_id: "av_support_qa_v2",
      baseline_status: "partial_success",
      candidate_status: "completed",
      compared_task_count: 12,
      improvement_count: 2,
      regression_count: 1,
      success_rate: { baseline: 83.33, candidate: 91.67, delta: 8.34 },
      average_latency_ms: { baseline: 120, candidate: 118, delta: -2 },
      total_cost: { baseline: 0.011, candidate: 0.0105, delta: -0.0005 },
      review_needed_count: { baseline: 2, candidate: 1, delta: -1 },
      category_deltas: [
        {
          category: "refund_policy",
          baseline_total_tasks: 3,
          candidate_total_tasks: 3,
          baseline_success_rate: 66.67,
          candidate_success_rate: 100,
          success_rate_delta: 33.33,
          baseline_failed_tasks: 1,
          candidate_failed_tasks: 0,
        },
      ],
      improvements: [
        {
          dataset_item_id: "ds_item_003",
          category: "refund_policy",
          baseline_task_run_id: "run_v1__task_003",
          candidate_task_run_id: "run_v2__task_003",
          baseline_status: "failed",
          candidate_status: "completed",
          baseline_failure_reason: "execution_failed",
          candidate_failure_reason: null,
          baseline_final_output: null,
          candidate_final_output: "resolved answer",
        },
      ],
      regressions: [],
    };

    expect(comparison.improvement_count).toBe(2);
    expect(comparison.category_deltas[0]?.success_rate_delta).toBe(33.33);
  });

  it("supports review queue items with persisted verdicts", () => {
    const queue: ReviewQueue = {
      total_count: 2,
      pending_count: 1,
      reviewed_count: 1,
      items: [
        {
          task_run_id: "run_v2__task_003",
          run_id: "run_v2",
          dataset_item_id: "ds_item_003",
          category: "refund_policy",
          input_text: "What is the refund policy?",
          status: "failed",
          review_needed: true,
          failure_reason: "execution_failed",
          error_message: "Deterministic stub failure.",
          final_output: null,
          review_status: "reviewed",
          review: {
            review_id: "review_001",
            task_run_id: "run_v2__task_003",
            run_id: "run_v2",
            dataset_item_id: "ds_item_003",
            reviewer_id: "reviewer_demo",
            verdict: "confirmed_issue",
            failure_label: "execution_failed",
            note: "Confirmed via trace.",
            created_at: null,
            updated_at: null,
          },
        },
      ],
    };

    expect(queue.reviewed_count).toBe(1);
    expect(queue.items[0]?.review?.verdict).toBe("confirmed_issue");
  });
});
