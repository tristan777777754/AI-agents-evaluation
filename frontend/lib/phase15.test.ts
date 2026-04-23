import { describe, expect, it } from "vitest";

import type {
  RunComparison,
  RunDashboardSummary,
  RunDetail,
  SampledRunCreateResponse,
} from "../../shared/types";

describe("phase 15 reliability sampling contracts", () => {
  it("supports sampled run launch responses and additive run metadata", () => {
    const response: SampledRunCreateResponse = {
      group_id: "sample_group_demo",
      sample_count: 3,
      runs: [
        {
          run_id: "run_sample_1",
          agent_version_id: "av_support_qa_v2",
          dataset_id: "dataset_support_faq_v1",
          dataset_snapshot_id: "dataset_support_faq_v1__snapshot_001",
          dataset_tag_filter: [],
          scorer_config_id: "sc_rule_based_v1",
          status: "completed",
          baseline: false,
          experiment_tag: "phase15-sampling",
          notes: null,
          sampling: {
            group_id: "sample_group_demo",
            sample_index: 1,
            sample_count: 3,
          },
          started_at: null,
          completed_at: null,
          adapter_type: "stub",
          total_tasks: 20,
          completed_tasks: 20,
          failed_tasks: 0,
          agent_version: {
            agent_version_id: "av_support_qa_v2",
            agent_id: "agent_support_qa",
            version_name: "v2",
            model: "gpt-4.1-mini",
            provider: "openai",
            prompt_hash: "sha256:v2",
            config_json: {},
            created_at: null,
            governance: null,
          },
          scorer_config: {
            scorer_config_id: "sc_rule_based_v1",
            name: "Rule based",
            type: "rule_based",
            weights_json: {},
            judge_model: null,
            judge_provider: null,
            thresholds_json: {},
            governance: null,
          },
        } satisfies RunDetail,
      ],
    };

    expect(response.runs[0]?.sampling?.sample_index).toBe(1);
    expect(response.runs[0]?.sampling?.group_id).toBe("sample_group_demo");
  });

  it("supports summary variability metrics sourced from persisted samples", () => {
    const summary: RunDashboardSummary = {
      run_id: "run_sample_1",
      agent_version_id: "av_support_qa_v2",
      dataset_id: "dataset_support_faq_v1",
      scorer_config_id: "sc_rule_based_v1",
      status: "completed",
      total_tasks: 20,
      successful_tasks: 20,
      failed_tasks: 0,
      review_needed_count: 0,
      success_rate: 100,
      average_latency_ms: 120,
      total_cost: 0.02,
      sampling: {
        group_id: "sample_group_demo",
        sample_index: 1,
        sample_count: 3,
        completed_sample_count: 3,
        sample_run_ids: ["run_sample_1", "run_sample_2", "run_sample_3"],
        consistency_rate: 80,
        success_rate: { mean: 91.67, stddev: 8.5, variance: 72.22, min: 80, max: 100 },
        average_latency_ms: { mean: 120, stddev: 0, variance: 0, min: 120, max: 120 },
        total_cost: { mean: 0.02, stddev: 0, variance: 0, min: 0.02, max: 0.02 },
      },
      category_breakdown: [],
      failure_breakdown: [],
      failed_cases: [],
    };

    expect(summary.sampling?.success_rate.mean).toBe(91.67);
    expect(summary.sampling?.consistency_rate).toBe(80);
  });

  it("supports compare interpretations for unstable regressions", () => {
    const comparison: RunComparison = {
      baseline_run_id: "run_stable_1",
      candidate_run_id: "run_unstable_1",
      baseline_agent_version_id: "av_support_qa_v1",
      candidate_agent_version_id: "av_support_qa_v2",
      baseline_status: "completed",
      candidate_status: "completed",
      compared_task_count: 20,
      sample_size: 20,
      improvement_count: 0,
      regression_count: 0,
      confidence_interval: { lower: null, upper: null },
      p_value: null,
      is_significant: false,
      success_rate: { baseline: 100, candidate: 100, delta: 0 },
      average_latency_ms: { baseline: 120, candidate: 120, delta: 0 },
      total_cost: { baseline: 0.02, candidate: 0.02, delta: 0 },
      review_needed_count: { baseline: 0, candidate: 0, delta: 0 },
      credibility: {
        label: "inconclusive",
        sample_size: 20,
        confidence_interval: { lower: null, upper: null },
        p_value: null,
        is_significant: false,
      },
      lineage: {
        baseline: {
          run_id: "run_stable_1",
          dataset_id: "dataset_support_faq_v1",
          dataset_snapshot_id: "dataset_support_faq_v1__snapshot_001",
          agent_version_id: "av_support_qa_v1",
          agent_version_snapshot_hash: "hash_v1",
          scorer_config_id: "sc_rule_based_v1",
          scorer_snapshot_hash: "sc_hash",
          baseline: true,
          experiment_tag: null,
        },
        candidate: {
          run_id: "run_unstable_1",
          dataset_id: "dataset_support_faq_v1",
          dataset_snapshot_id: "dataset_support_faq_v1__snapshot_001",
          agent_version_id: "av_support_qa_v2",
          agent_version_snapshot_hash: "hash_v2",
          scorer_config_id: "sc_rule_based_v1",
          scorer_snapshot_hash: "sc_hash",
          baseline: false,
          experiment_tag: "phase15-sampling",
        },
      },
      sampling: {
        interpretation: "unstable_regression",
        baseline: {
          group_id: "sample_group_stable",
          representative_run_id: "run_stable_1",
          sample_count: 3,
          completed_sample_count: 3,
          sample_run_ids: ["run_stable_1", "run_stable_2", "run_stable_3"],
          success_rate_mean: 100,
          success_rate_stddev: 0,
          success_rate_variance: 0,
          consistency_rate: 100,
          is_stable: true,
        },
        candidate: {
          group_id: "sample_group_unstable",
          representative_run_id: "run_unstable_1",
          sample_count: 3,
          completed_sample_count: 3,
          sample_run_ids: ["run_unstable_1", "run_unstable_2", "run_unstable_3"],
          success_rate_mean: 91.67,
          success_rate_stddev: 8.5,
          success_rate_variance: 72.22,
          consistency_rate: 80,
          is_stable: false,
        },
        notes: "Baseline stddev 0.0 pp with consistency 100.0%. Candidate stddev 8.5 pp with consistency 80.0%.",
      },
      category_deltas: [],
      improvements: [],
      regressions: [],
    };

    expect(comparison.sampling?.interpretation).toBe("unstable_regression");
    expect(comparison.sampling?.candidate.is_stable).toBe(false);
  });
});
