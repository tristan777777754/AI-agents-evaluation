"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import type { DatasetSummary } from "@/lib/datasets";
import { createRun, type RegistryList } from "@/lib/runs";

type RunLauncherFormProps = {
  datasets: DatasetSummary[];
  registry: RegistryList;
};

const panelStyle = {
  display: "grid",
  gap: "0.9rem",
  padding: "1.5rem",
  borderRadius: "24px",
  border: "1px solid var(--border)",
  background: "var(--panel)",
  boxShadow: "var(--shadow)",
} as const;

export function RunLauncherForm({ datasets, registry }: RunLauncherFormProps) {
  const router = useRouter();
  const [submitting, setSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const defaultAgentVersion = registry.agent_versions[0]?.agent_version_id ?? "";
  const defaultScorerConfig = registry.scorer_configs[0]?.scorer_config_id ?? "";
  const defaultDataset = datasets[0]?.dataset_id ?? "";

  async function handleSubmit(formData: FormData) {
    setSubmitting(true);
    setErrorMessage(null);

    const failureMode = String(formData.get("failure_mode") ?? "none");
    const datasetId = String(formData.get("dataset_id") ?? "");
    const agentVersionId = String(formData.get("agent_version_id") ?? "");
    const scorerConfigId = String(formData.get("scorer_config_id") ?? "");
    const experimentTag = String(formData.get("experiment_tag") ?? "").trim();
    const notes = String(formData.get("notes") ?? "").trim();

    try {
      const run = await createRun({
        dataset_id: datasetId,
        agent_version_id: agentVersionId,
        scorer_config_id: scorerConfigId,
        adapter_type: "stub",
        adapter_config: {
          failure_mode: failureMode,
        },
        experiment_tag: experimentTag || null,
        notes: notes || null,
      });
      router.push(`/runs/${run.run_id}`);
      router.refresh();
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Run creation failed.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form action={handleSubmit} style={panelStyle}>
      <div>
        <p style={{ margin: 0, color: "var(--muted)", letterSpacing: "0.08em", textTransform: "uppercase" }}>
          Evaluation Run
        </p>
        <h2 style={{ margin: "0.35rem 0 0" }}>Launch deterministic stub run</h2>
      </div>

      <label style={{ display: "grid", gap: "0.35rem" }}>
        <span>Dataset</span>
        <select name="dataset_id" defaultValue={defaultDataset} disabled={submitting || datasets.length === 0}>
          {datasets.map((dataset) => (
            <option key={dataset.dataset_id} value={dataset.dataset_id}>
              {dataset.name} ({dataset.item_count} items)
            </option>
          ))}
        </select>
      </label>

      <label style={{ display: "grid", gap: "0.35rem" }}>
        <span>Agent version</span>
        <select
          name="agent_version_id"
          defaultValue={defaultAgentVersion}
          disabled={submitting || registry.agent_versions.length === 0}
        >
          {registry.agent_versions.map((agentVersion) => (
            <option key={agentVersion.agent_version_id} value={agentVersion.agent_version_id}>
              {agentVersion.version_name} · {agentVersion.model}
            </option>
          ))}
        </select>
      </label>

      <label style={{ display: "grid", gap: "0.35rem" }}>
        <span>Scorer config</span>
        <select
          name="scorer_config_id"
          defaultValue={defaultScorerConfig}
          disabled={submitting || registry.scorer_configs.length === 0}
        >
          {registry.scorer_configs.map((scorerConfig) => (
            <option key={scorerConfig.scorer_config_id} value={scorerConfig.scorer_config_id}>
              {scorerConfig.name}
            </option>
          ))}
        </select>
      </label>

      <label style={{ display: "grid", gap: "0.35rem" }}>
        <span>Failure mode</span>
        <select name="failure_mode" defaultValue="none" disabled={submitting}>
          <option value="none">Completed</option>
          <option value="all">Force full failure</option>
        </select>
      </label>

      <label style={{ display: "grid", gap: "0.35rem" }}>
        <span>Experiment tag</span>
        <input
          name="experiment_tag"
          type="text"
          placeholder="phase10-governance"
          disabled={submitting}
        />
      </label>

      <label style={{ display: "grid", gap: "0.35rem" }}>
        <span>Notes</span>
        <textarea
          name="notes"
          placeholder="Optional run context for compare lineage."
          rows={3}
          disabled={submitting}
        />
      </label>

      <button
        type="submit"
        disabled={
          submitting ||
          datasets.length === 0 ||
          registry.agent_versions.length === 0 ||
          registry.scorer_configs.length === 0
        }
        style={{ width: "fit-content" }}
      >
        {submitting ? "Starting..." : "Start run"}
      </button>

      {errorMessage ? (
        <div
          style={{
            display: "grid",
            gap: "0.5rem",
            padding: "1rem",
            borderRadius: "16px",
            background: "rgba(174, 63, 19, 0.08)",
            border: "1px solid rgba(174, 63, 19, 0.2)",
          }}
        >
          <strong>Run creation failed</strong>
          <p style={{ margin: 0 }}>{errorMessage}</p>
        </div>
      ) : null}
    </form>
  );
}
