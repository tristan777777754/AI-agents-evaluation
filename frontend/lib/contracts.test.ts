import { describe, expect, it } from "vitest";

import { phase1ContractPreview } from "./contracts";

describe("phase1ContractPreview", () => {
  it("keeps the canonical phase marker and run statuses", () => {
    expect(phase1ContractPreview.phase.current_phase).toBe("Phase 14");
    expect(phase1ContractPreview.run_statuses).toContain("partial_success");
    expect(phase1ContractPreview.entities.eval_run).toContain("status");
    expect(phase1ContractPreview.entities.dataset_item).toContain("input_text");
    expect(phase1ContractPreview.entities.dataset_snapshot).toContain("checksum");
    expect(phase1ContractPreview.entities.score).toContain("evidence_json");
    expect(phase1ContractPreview.entities.dataset).toContain("lifecycle_status");
  });
});
