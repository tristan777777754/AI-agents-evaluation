import type { AgentVersion } from "../../shared/types";

export type AdapterType = "stub" | "openai";

type AdapterConfigOptions = {
  adapterType: AdapterType;
  formData: FormData;
  agentVersion: AgentVersion | undefined;
};

function readString(formData: FormData, key: string): string {
  return String(formData.get(key) ?? "").trim();
}

function readNumber(
  formData: FormData,
  key: string,
  fallback: number,
  parser: (value: string) => number,
): number {
  const raw = readString(formData, key);
  if (!raw) {
    return fallback;
  }

  const parsed = parser(raw);
  return Number.isFinite(parsed) ? parsed : fallback;
}

export function buildAdapterConfig({
  adapterType,
  formData,
  agentVersion,
}: AdapterConfigOptions): Record<string, unknown> {
  if (adapterType === "stub") {
    return {
      failure_mode: readString(formData, "failure_mode") || "none",
    };
  }

  const config = agentVersion?.config_json ?? {};
  const defaultSystemPrompt =
    typeof config.system_prompt === "string" ? config.system_prompt : "";

  return {
    model: readString(formData, "model") || agentVersion?.model || "gpt-4.1-mini",
    system_prompt:
      readString(formData, "system_prompt") ||
      defaultSystemPrompt ||
      "You are a support QA assistant. Answer concisely and only from known policy facts.",
    temperature: readNumber(formData, "temperature", 0, Number.parseFloat),
    max_output_tokens: readNumber(formData, "max_output_tokens", 180, Number.parseInt),
  };
}
