import { describe, expect, it } from "vitest";

import type { RunSummary } from "../../shared/types";

describe("run summary contract", () => {
  it("supports completed and partial_success counts", () => {
    const run: RunSummary = {
      run_id: "run_demo",
      agent_version_id: "av_support_qa_v1",
      dataset_id: "dataset_support_faq_v1",
      dataset_snapshot_id: "dataset_support_faq_v1__snapshot_001",
      dataset_tag_filter: [],
      scorer_config_id: "sc_rule_based_v1",
      status: "partial_success",
      baseline: true,
      experiment_tag: "phase10-governance",
      notes: "Pinned baseline run.",
      sampling: null,
      started_at: null,
      completed_at: null,
      adapter_type: "stub",
      total_tasks: 12,
      completed_tasks: 10,
      failed_tasks: 2,
    };

    expect(run.status).toBe("partial_success");
    expect(run.failed_tasks).toBe(2);
    expect(run.baseline).toBe(true);
  });
});
