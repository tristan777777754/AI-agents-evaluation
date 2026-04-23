"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import type { DatasetSummary } from "@/lib/datasets";
import {
  createAgent,
  createAgentVersion,
  updateRegistryDefaults,
  type RegistryList,
} from "@/lib/runs";

type RegistryManagerProps = {
  datasets: DatasetSummary[];
  registry: RegistryList;
};

const panelStyle = {
  display: "grid",
  gap: "1rem",
  padding: "1.5rem",
  borderRadius: "24px",
  border: "1px solid var(--border)",
  background: "var(--panel)",
  boxShadow: "var(--shadow)",
} as const;

export function RegistryManager({ datasets, registry }: RegistryManagerProps) {
  const router = useRouter();
  const [defaultsError, setDefaultsError] = useState<string | null>(null);
  const [agentError, setAgentError] = useState<string | null>(null);
  const [versionError, setVersionError] = useState<string | null>(null);
  const [savingDefaults, setSavingDefaults] = useState(false);
  const [savingAgent, setSavingAgent] = useState(false);
  const [savingVersion, setSavingVersion] = useState(false);

  async function handleDefaultsSubmit(formData: FormData) {
    setSavingDefaults(true);
    setDefaultsError(null);
    try {
      await updateRegistryDefaults({
        default_dataset_id: String(formData.get("default_dataset_id") ?? "") || null,
        default_scorer_config_id:
          String(formData.get("default_scorer_config_id") ?? "") || null,
      });
      router.refresh();
    } catch (error) {
      setDefaultsError(error instanceof Error ? error.message : "Defaults update failed.");
    } finally {
      setSavingDefaults(false);
    }
  }

  async function handleAgentSubmit(formData: FormData) {
    setSavingAgent(true);
    setAgentError(null);
    try {
      await createAgent({
        agent_id: String(formData.get("agent_id") ?? "").trim(),
        name: String(formData.get("name") ?? "").trim(),
        description: String(formData.get("description") ?? "").trim() || null,
        owner_id: String(formData.get("owner_id") ?? "").trim() || null,
      });
      router.refresh();
    } catch (error) {
      setAgentError(error instanceof Error ? error.message : "Agent creation failed.");
    } finally {
      setSavingAgent(false);
    }
  }

  async function handleVersionSubmit(formData: FormData) {
    setSavingVersion(true);
    setVersionError(null);
    try {
      await createAgentVersion({
        agent_version_id: String(formData.get("agent_version_id") ?? "").trim(),
        agent_id: String(formData.get("agent_id") ?? "").trim(),
        version_name: String(formData.get("version_name") ?? "").trim(),
        model: String(formData.get("model") ?? "").trim(),
        prompt_hash: String(formData.get("prompt_hash") ?? "").trim(),
        config_json: {
          system_prompt: String(formData.get("system_prompt") ?? "").trim(),
          adapter_type: "stub",
        },
      });
      router.refresh();
    } catch (error) {
      setVersionError(
        error instanceof Error ? error.message : "Agent version creation failed.",
      );
    } finally {
      setSavingVersion(false);
    }
  }

  return (
    <section style={panelStyle}>
      <div>
        <p
          style={{
            margin: 0,
            color: "var(--muted)",
            letterSpacing: "0.08em",
            textTransform: "uppercase",
          }}
        >
          Registry
        </p>
        <h2 style={{ margin: "0.35rem 0 0" }}>Runtime agents, versions, and defaults</h2>
      </div>

      <form action={handleDefaultsSubmit} style={{ display: "grid", gap: "0.75rem" }}>
        <strong>Quick-run defaults</strong>
        <label style={{ display: "grid", gap: "0.35rem" }}>
          <span>Default dataset</span>
          <select
            name="default_dataset_id"
            defaultValue={registry.defaults.default_dataset_id ?? ""}
            disabled={savingDefaults}
          >
            <option value="">Select dataset</option>
            {datasets.map((dataset) => (
              <option key={dataset.dataset_id} value={dataset.dataset_id}>
                {dataset.name}
              </option>
            ))}
          </select>
        </label>
        <label style={{ display: "grid", gap: "0.35rem" }}>
          <span>Default scorer</span>
          <select
            name="default_scorer_config_id"
            defaultValue={registry.defaults.default_scorer_config_id ?? ""}
            disabled={savingDefaults}
          >
            <option value="">Select scorer</option>
            {registry.scorer_configs.map((scorer) => (
              <option key={scorer.scorer_config_id} value={scorer.scorer_config_id}>
                {scorer.name}
              </option>
            ))}
          </select>
        </label>
        <button type="submit" style={{ width: "fit-content" }} disabled={savingDefaults}>
          {savingDefaults ? "Saving..." : "Save defaults"}
        </button>
        {defaultsError ? <p style={{ margin: 0, color: "rgb(174, 63, 19)" }}>{defaultsError}</p> : null}
      </form>

      <form action={handleAgentSubmit} style={{ display: "grid", gap: "0.75rem" }}>
        <strong>Create agent</strong>
        <label style={{ display: "grid", gap: "0.35rem" }}>
          <span>Agent ID</span>
          <input name="agent_id" type="text" placeholder="agent_support_qa" disabled={savingAgent} />
        </label>
        <label style={{ display: "grid", gap: "0.35rem" }}>
          <span>Name</span>
          <input name="name" type="text" placeholder="Support QA" disabled={savingAgent} />
        </label>
        <label style={{ display: "grid", gap: "0.35rem" }}>
          <span>Description</span>
          <input name="description" type="text" placeholder="Short description" disabled={savingAgent} />
        </label>
        <label style={{ display: "grid", gap: "0.35rem" }}>
          <span>Owner ID</span>
          <input name="owner_id" type="text" placeholder="ai-eng" disabled={savingAgent} />
        </label>
        <button type="submit" style={{ width: "fit-content" }} disabled={savingAgent}>
          {savingAgent ? "Creating..." : "Create agent"}
        </button>
        {agentError ? <p style={{ margin: 0, color: "rgb(174, 63, 19)" }}>{agentError}</p> : null}
      </form>

      <form action={handleVersionSubmit} style={{ display: "grid", gap: "0.75rem" }}>
        <strong>Create immutable version</strong>
        <label style={{ display: "grid", gap: "0.35rem" }}>
          <span>Agent</span>
          <select name="agent_id" defaultValue={registry.agents[0]?.agent_id ?? ""} disabled={savingVersion}>
            {registry.agents.map((agent) => (
              <option key={agent.agent_id} value={agent.agent_id}>
                {agent.name}
              </option>
            ))}
          </select>
        </label>
        <label style={{ display: "grid", gap: "0.35rem" }}>
          <span>Version ID</span>
          <input
            name="agent_version_id"
            type="text"
            placeholder="av_support_qa_v3"
            disabled={savingVersion}
          />
        </label>
        <label style={{ display: "grid", gap: "0.35rem" }}>
          <span>Version name</span>
          <input name="version_name" type="text" placeholder="v3" disabled={savingVersion} />
        </label>
        <label style={{ display: "grid", gap: "0.35rem" }}>
          <span>Model</span>
          <input name="model" type="text" placeholder="gpt-4.1-mini" disabled={savingVersion} />
        </label>
        <label style={{ display: "grid", gap: "0.35rem" }}>
          <span>Prompt hash</span>
          <input
            name="prompt_hash"
            type="text"
            placeholder="sha256:v3-demo-hash"
            disabled={savingVersion}
          />
        </label>
        <label style={{ display: "grid", gap: "0.35rem" }}>
          <span>System prompt</span>
          <textarea
            name="system_prompt"
            rows={3}
            placeholder="Runtime-created immutable prompt snapshot."
            disabled={savingVersion}
          />
        </label>
        <button type="submit" style={{ width: "fit-content" }} disabled={savingVersion}>
          {savingVersion ? "Creating..." : "Create version"}
        </button>
        {versionError ? <p style={{ margin: 0, color: "rgb(174, 63, 19)" }}>{versionError}</p> : null}
      </form>
    </section>
  );
}
