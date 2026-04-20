import { describe, expect, it } from "vitest";

import { phase1ContractPreview } from "./contracts";

describe("phase1ContractPreview", () => {
  it("keeps the canonical phase marker and run statuses", () => {
    expect(phase1ContractPreview.phase.current_phase).toBe("Phase 1");
    expect(phase1ContractPreview.run_statuses).toContain("partial_success");
    expect(phase1ContractPreview.entities.eval_run).toContain("status");
  });
});
