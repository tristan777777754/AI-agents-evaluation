import { describe, expect, it } from "vitest";

import type { RunDashboardSummary } from "../../shared/types";

describe("run dashboard summary contract", () => {
  it("supports KPI, category, and failed case data", () => {
    const summary: RunDashboardSummary = {
      run_id: "run_demo",
      agent_version_id: "av_support_qa_v1",
      dataset_id: "dataset_support_faq_v1",
      scorer_config_id: "sc_rule_based_v1",
      status: "partial_success",
      total_tasks: 12,
      successful_tasks: 8,
      failed_tasks: 4,
      review_needed_count: 4,
      success_rate: 66.67,
      average_latency_ms: 120,
      total_cost: 0.0111,
      sampling: null,
      category_breakdown: [
        {
          category: "security",
          total_tasks: 3,
          successful_tasks: 1,
          failed_tasks: 2,
          success_rate: 33.33,
          average_latency_ms: 120,
          total_cost: 0.0021,
        },
      ],
      failure_breakdown: [{ failure_reason: "tool_error", count: 1 }],
      failed_cases: [
        {
          task_run_id: "run_demo__task_010",
          run_id: "run_demo",
          dataset_item_id: "ds_item_010",
          category: "security",
          failure_reason: "tool_error",
          error_message: "tool failed",
          final_output: null,
        },
      ],
    };

    expect(summary.success_rate).toBe(66.67);
    expect(summary.category_breakdown[0]?.failed_tasks).toBe(2);
    expect(summary.failed_cases[0]?.failure_reason).toBe("tool_error");
  });
});
