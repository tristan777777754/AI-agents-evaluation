import { describe, expect, it } from "vitest";

import { phase1ContractPreview } from "./contracts";

describe("phase1ContractPreview", () => {
  it("keeps the canonical phase marker and run statuses", () => {
    expect(phase1ContractPreview.phase.current_phase).toBe("Phase 16");
    expect(phase1ContractPreview.run_statuses).toContain("partial_success");
    expect(phase1ContractPreview.entities.eval_run).toContain("status");
    expect(phase1ContractPreview.entities.eval_run).toContain("sampling");
    expect(phase1ContractPreview.entities.dataset_item).toContain("input_text");
    expect(phase1ContractPreview.entities.dataset_snapshot).toContain("checksum");
    expect(phase1ContractPreview.entities.score).toContain("evidence_json");
    expect(phase1ContractPreview.entities.score).toContain("judge_audit");
    expect(phase1ContractPreview.entities.agent_version).toContain("provider");
    expect(phase1ContractPreview.entities.scorer_config).toContain("governance");
    expect(phase1ContractPreview.entities.dataset).toContain("lifecycle_status");
  });
});
