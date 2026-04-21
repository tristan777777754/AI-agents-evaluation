import { describe, expect, it } from "vitest";

import type { DatasetDiff, RunCreateRequest } from "../../shared/types";

describe("phase 10 governance contracts", () => {
  it("supports dataset snapshot diff responses", () => {
    const diff: DatasetDiff = {
      dataset_id: "dataset_support_faq_v1",
      from_snapshot_id: "dataset_support_faq_v1__snapshot_001",
      to_snapshot_id: "dataset_support_faq_v1__snapshot_002",
      added_count: 1,
      removed_count: 1,
      changed_count: 1,
      added: [
        {
          dataset_item_id: "ds_item_021",
          dataset_id: "dataset_support_faq_v1",
          input_text: "Can enterprise admins enforce SSO for all members?",
          category: "security",
          difficulty: "medium",
          expected_output: "Yes.",
          rubric_json: null,
          reference_context: null,
          metadata_json: null,
        },
      ],
      removed: [],
      changed: [],
    };

    expect(diff.added_count).toBe(1);
    expect(diff.to_snapshot_id).toContain("snapshot_002");
  });

  it("supports experiment metadata on run creation", () => {
    const request: RunCreateRequest = {
      dataset_id: "dataset_support_faq_v1",
      agent_version_id: "av_support_qa_v1",
      scorer_config_id: "sc_rule_based_v1",
      adapter_type: "stub",
      adapter_config: {},
      experiment_tag: "phase10-governance",
      notes: "Baseline pin candidate.",
    };

    expect(request.experiment_tag).toBe("phase10-governance");
    expect(request.notes).toContain("Baseline");
  });
});
