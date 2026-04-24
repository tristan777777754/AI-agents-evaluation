import { describe, expect, it } from "vitest";

import type { AgentVersion } from "../../shared/types";
import { buildAdapterConfig } from "./run-launcher";

const agentVersion: AgentVersion = {
  agent_version_id: "av_support_v2",
  agent_id: "agent_support",
  version_name: "v2",
  model: "gpt-4.1",
  provider: "openai",
  prompt_hash: "hash_v2",
  config_json: {
    system_prompt: "Answer with exact policy details.",
  },
  created_at: null,
  governance: null,
};

describe("buildAdapterConfig", () => {
  it("builds stub config from failure mode", () => {
    const formData = new FormData();
    formData.set("failure_mode", "all");

    expect(
      buildAdapterConfig({
        adapterType: "stub",
        formData,
        agentVersion,
      }),
    ).toEqual({
      failure_mode: "all",
    });
  });

  it("builds openai config from explicit form values", () => {
    const formData = new FormData();
    formData.set("model", "gpt-4.1-mini");
    formData.set("system_prompt", "Be precise.");
    formData.set("temperature", "0.2");
    formData.set("max_output_tokens", "256");

    expect(
      buildAdapterConfig({
        adapterType: "openai",
        formData,
        agentVersion,
      }),
    ).toEqual({
      model: "gpt-4.1-mini",
      system_prompt: "Be precise.",
      temperature: 0.2,
      max_output_tokens: 256,
    });
  });

  it("falls back to agent version defaults for openai config", () => {
    const formData = new FormData();

    expect(
      buildAdapterConfig({
        adapterType: "openai",
        formData,
        agentVersion,
      }),
    ).toEqual({
      model: "gpt-4.1",
      system_prompt: "Answer with exact policy details.",
      temperature: 0,
      max_output_tokens: 180,
    });
  });
});
