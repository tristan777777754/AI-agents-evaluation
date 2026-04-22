import { describe, expect, it } from "vitest";

import type { TraceComparison } from "../../shared/types";

describe("phase 12 trace intelligence contracts", () => {
  it("supports additive side-by-side trace comparison payloads", () => {
    const comparison: TraceComparison = {
      baseline_run_id: "run_v1",
      candidate_run_id: "run_v2",
      dataset_item_id: "ds_item_006",
      category: "policy_lookup",
      input_text: "Where can enterprise users find the data retention policy?",
      expected_output: "Enterprise users can find it in the policy center knowledge base.",
      same_final_output: true,
      pass_fail_changed: false,
      overall_label: "regression",
      baseline: {
        run_id: "run_v1",
        task_run_id: "run_v1__task_006",
        dataset_item_id: "ds_item_006",
        category: "policy_lookup",
        status: "completed",
        pass_fail: true,
        failure_reason: null,
        input_text: "Where can enterprise users find the data retention policy?",
        expected_output: "Enterprise users can find it in the policy center knowledge base.",
        final_output: "Enterprise users can find it in the policy center knowledge base.",
        error_message: null,
        trace_id: "trace_run_v1__task_006",
        storage_path: "eval-traces/run_v1/run_v1__task_006.json",
        derived_metrics: {
          step_count: 2,
          tool_count: 0,
          tool_names: [],
          final_output_event_count: 1,
          error_event_count: 0,
          failure_step_index: null,
          max_steps: 2,
          excess_step_count: 0,
          efficiency_score: 1,
        },
        events: [
          {
            step_index: 0,
            event_type: "agent_start",
            message: null,
            tool_name: null,
            input: "Where can enterprise users find the data retention policy?",
            output: null,
            latency_ms: null,
            status: null,
            error: null,
          },
        ],
      },
      candidate: {
        run_id: "run_v2",
        task_run_id: "run_v2__task_006",
        dataset_item_id: "ds_item_006",
        category: "policy_lookup",
        status: "completed",
        pass_fail: true,
        failure_reason: null,
        input_text: "Where can enterprise users find the data retention policy?",
        expected_output: "Enterprise users can find it in the policy center knowledge base.",
        final_output: "Enterprise users can find it in the policy center knowledge base.",
        error_message: null,
        trace_id: "trace_run_v2__task_006",
        storage_path: "eval-traces/run_v2/run_v2__task_006.json",
        derived_metrics: {
          step_count: 4,
          tool_count: 2,
          tool_names: ["document_lookup"],
          final_output_event_count: 1,
          error_event_count: 0,
          failure_step_index: null,
          max_steps: 2,
          excess_step_count: 2,
          efficiency_score: 0.5,
        },
        events: [
          {
            step_index: 0,
            event_type: "agent_start",
            message: null,
            tool_name: null,
            input: "Where can enterprise users find the data retention policy?",
            output: null,
            latency_ms: null,
            status: null,
            error: null,
          },
        ],
      },
      regression_signals: [
        {
          signal_key: "more_steps",
          label: "More steps",
          direction: "regression",
          baseline_value: 2,
          candidate_value: 4,
          detail: "Candidate reached the same final answer with more steps.",
        },
      ],
      improvement_signals: [],
    };

    expect(comparison.baseline.derived_metrics.efficiency_score).toBe(1);
    expect(comparison.candidate.derived_metrics.excess_step_count).toBe(2);
    expect(comparison.regression_signals[0].signal_key).toBe("more_steps");
  });
});
