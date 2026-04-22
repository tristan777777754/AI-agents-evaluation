import { describe, expect, it } from "vitest";

import type { RunComparison, TaskRunDetail } from "../../shared/types";

describe("phase 11 credibility contracts", () => {
  it("supports compare credibility metadata", () => {
    const comparison: RunComparison = {
      baseline_run_id: "run_v1",
      candidate_run_id: "run_v2",
      baseline_agent_version_id: "av_support_qa_v1",
      candidate_agent_version_id: "av_support_qa_v2",
      baseline_status: "partial_success",
      candidate_status: "completed",
      compared_task_count: 20,
      sample_size: 20,
      improvement_count: 1,
      regression_count: 0,
      confidence_interval: { lower: -4.8, upper: 14.8 },
      p_value: 0.3173,
      is_significant: false,
      success_rate: { baseline: 95, candidate: 100, delta: 5 },
      average_latency_ms: { baseline: 120, candidate: 120, delta: 0 },
      total_cost: { baseline: 0.019, candidate: 0.02, delta: 0.001 },
      review_needed_count: { baseline: 1, candidate: 0, delta: -1 },
      credibility: {
        label: "directional_improvement",
        sample_size: 20,
        confidence_interval: { lower: -4.8, upper: 14.8 },
        p_value: 0.3173,
        is_significant: false,
      },
      lineage: {
        baseline: {
          run_id: "run_v1",
          dataset_id: "dataset_support_faq_v1",
          dataset_snapshot_id: "dataset_support_faq_v1__snapshot_001",
          agent_version_id: "av_support_qa_v1",
          agent_version_snapshot_hash: "hash_v1",
          scorer_config_id: "sc_llm_judge_v1",
          scorer_snapshot_hash: "sc_hash_v1",
          baseline: true,
          experiment_tag: null,
        },
        candidate: {
          run_id: "run_v2",
          dataset_id: "dataset_support_faq_v1",
          dataset_snapshot_id: "dataset_support_faq_v1__snapshot_001",
          agent_version_id: "av_support_qa_v2",
          agent_version_snapshot_hash: "hash_v2",
          scorer_config_id: "sc_llm_judge_v1",
          scorer_snapshot_hash: "sc_hash_v1",
          baseline: false,
          experiment_tag: null,
        },
      },
      category_deltas: [],
      improvements: [],
      regressions: [],
    };

    expect(comparison.is_significant).toBe(false);
    expect(comparison.credibility.label).toBe("directional_improvement");
  });

  it("supports additive score evidence on task detail", () => {
    const task: TaskRunDetail = {
      task_run_id: "run_v2__task_001",
      run_id: "run_v2",
      dataset_item_id: "ds_item_001",
      status: "completed",
      input_text: "What is the refund policy?",
      category: "refund_policy",
      difficulty: "easy",
      expected_output: "Annual plans can be refunded within 30 days.",
      final_output: "Annual plans can be refunded within 30 days.",
      latency_ms: 100,
      token_usage: { prompt: 12, completion: 8 },
      cost: 0,
      termination_reason: "completed",
      error_message: null,
      failure_reason: null,
      trace_summary: {
        trace_id: "trace_001",
        task_run_id: "run_v2__task_001",
        step_count: 2,
        tool_count: 0,
        error_flag: false,
        storage_path: "eval-traces/run_v2/run_v2__task_001.json",
      },
      score: {
        correctness: 1,
        tool_use: 1,
        formatting: 1,
        pass_fail: true,
        review_needed: false,
        evidence_json: {
          score_method: "llm_judge",
          judge_provider: "anthropic",
          judge_verdict: "pass",
        },
      },
      started_at: null,
      completed_at: null,
      review: null,
    };

    expect(task.score?.evidence_json?.score_method).toBe("llm_judge");
  });
});
