"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import type { DatasetSummary } from "@/lib/datasets";
import { buildAdapterConfig, type AdapterType } from "@/lib/run-launcher";
import { createQuickRun, createRun, createSampledRuns, type RegistryList } from "@/lib/runs";

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
  const [quickSubmitting, setQuickSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [quickErrorMessage, setQuickErrorMessage] = useState<string | null>(null);
  const [quickAdapterType, setQuickAdapterType] = useState<AdapterType>("openai");
  const [runAdapterType, setRunAdapterType] = useState<AdapterType>("openai");

  const defaultAgentVersion = registry.agent_versions[0]?.agent_version_id ?? "";
  const defaultScorerConfig = registry.scorer_configs[0]?.scorer_config_id ?? "";
  const defaultDataset = datasets[0]?.dataset_id ?? "";
  const quickDataset = registry.defaults.default_dataset_id;
  const quickScorer = registry.defaults.default_scorer_config_id;

  async function handleQuickRun(formData: FormData) {
    setQuickSubmitting(true);
    setQuickErrorMessage(null);

    try {
      const adapterType = String(formData.get("adapter_type") ?? "openai") as AdapterType;
      const agentVersionId = String(formData.get("agent_version_id") ?? "");
      const agentVersion = registry.agent_versions.find(
        (candidate) => candidate.agent_version_id === agentVersionId,
      );
      const experimentTag = String(formData.get("experiment_tag") ?? "").trim();
      const notes = String(formData.get("notes") ?? "").trim();
      const response = await createQuickRun({
        agent_version_id: agentVersionId,
        adapter_type: adapterType,
        adapter_config: buildAdapterConfig({
          adapterType,
          formData,
          agentVersion,
        }),
        experiment_tag: experimentTag || null,
        notes: notes || null,
      });
      if (response.auto_compare.comparison && response.auto_compare.baseline_run_id) {
        const params = new URLSearchParams({
          baseline_run_id: response.auto_compare.baseline_run_id,
          candidate_run_id: response.auto_compare.candidate_run_id,
        });
        router.push(`/compare?${params.toString()}`);
      } else {
        router.push(`/runs/${response.run.run_id}`);
      }
      router.refresh();
    } catch (error) {
      setQuickErrorMessage(error instanceof Error ? error.message : "Quick run failed.");
    } finally {
      setQuickSubmitting(false);
    }
  }

  async function handleSubmit(formData: FormData) {
    setSubmitting(true);
    setErrorMessage(null);

    const datasetId = String(formData.get("dataset_id") ?? "");
    const agentVersionId = String(formData.get("agent_version_id") ?? "");
    const agentVersion = registry.agent_versions.find(
      (candidate) => candidate.agent_version_id === agentVersionId,
    );
    const scorerConfigId = String(formData.get("scorer_config_id") ?? "");
    const adapterType = String(formData.get("adapter_type") ?? "openai") as AdapterType;
    const experimentTag = String(formData.get("experiment_tag") ?? "").trim();
    const notes = String(formData.get("notes") ?? "").trim();
    const datasetTagFilter = String(formData.get("dataset_tag_filter") ?? "")
      .split(",")
      .map((tag) => tag.trim().toLowerCase())
      .filter(Boolean);
    const sampleCount = Number(formData.get("sample_count") ?? "1") || 1;

    try {
      if (sampleCount > 1) {
        const response = await createSampledRuns({
          dataset_id: datasetId,
          agent_version_id: agentVersionId,
          scorer_config_id: scorerConfigId,
          dataset_tag_filter: datasetTagFilter,
          adapter_type: adapterType,
          adapter_config: buildAdapterConfig({
            adapterType,
            formData,
            agentVersion,
          }),
          experiment_tag: experimentTag || null,
          notes: notes || null,
          sampling: {
            sample_count: sampleCount,
            sample_overrides: [],
          },
        });
        router.push(`/runs/${response.runs[0]?.run_id ?? ""}`);
      } else {
        const run = await createRun({
          dataset_id: datasetId,
          agent_version_id: agentVersionId,
          scorer_config_id: scorerConfigId,
          dataset_tag_filter: datasetTagFilter,
          adapter_type: adapterType,
          adapter_config: buildAdapterConfig({
            adapterType,
            formData,
            agentVersion,
          }),
          experiment_tag: experimentTag || null,
          notes: notes || null,
        });
        router.push(`/runs/${run.run_id}`);
      }
      router.refresh();
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Run creation failed.");
    } finally {
      setSubmitting(false);
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
          Evaluation Run
        </p>
        <h2 style={{ margin: "0.35rem 0 0" }}>Quick run or full launch</h2>
      </div>

      <form action={handleQuickRun} style={{ display: "grid", gap: "0.75rem" }}>
        <strong>Quick run from defaults</strong>
        <p style={{ margin: 0, color: "var(--muted)" }}>
          Uses dataset <code>{quickDataset ?? "not configured"}</code> and scorer{" "}
          <code>{quickScorer ?? "not configured"}</code>.
        </p>

        <label style={{ display: "grid", gap: "0.35rem" }}>
          <span>Agent version</span>
          <select
            name="agent_version_id"
            defaultValue={defaultAgentVersion}
            disabled={quickSubmitting || registry.agent_versions.length === 0}
          >
            {registry.agent_versions.map((agentVersion) => (
              <option key={agentVersion.agent_version_id} value={agentVersion.agent_version_id}>
                {agentVersion.version_name} · {agentVersion.model}
              </option>
            ))}
          </select>
        </label>

        <label style={{ display: "grid", gap: "0.35rem" }}>
          <span>Adapter</span>
          <select
            name="adapter_type"
            value={quickAdapterType}
            onChange={(event) => setQuickAdapterType(event.target.value as AdapterType)}
            disabled={quickSubmitting}
          >
            <option value="openai">OpenAI</option>
            <option value="stub">Stub</option>
          </select>
        </label>

        {quickAdapterType === "openai" ? (
          <>
            <label style={{ display: "grid", gap: "0.35rem" }}>
              <span>Model</span>
              <input
                name="model"
                type="text"
                placeholder="gpt-4.1-mini"
                defaultValue={registry.agent_versions[0]?.model ?? "gpt-4.1-mini"}
                disabled={quickSubmitting}
              />
            </label>

            <label style={{ display: "grid", gap: "0.35rem" }}>
              <span>System prompt</span>
              <textarea
                name="system_prompt"
                rows={4}
                placeholder="Use the selected agent version prompt or override it here."
                disabled={quickSubmitting}
              />
            </label>

            <label style={{ display: "grid", gap: "0.35rem" }}>
              <span>Temperature</span>
              <input
                name="temperature"
                type="number"
                min={0}
                max={2}
                step="0.1"
                defaultValue={0}
                disabled={quickSubmitting}
              />
            </label>

            <label style={{ display: "grid", gap: "0.35rem" }}>
              <span>Max output tokens</span>
              <input
                name="max_output_tokens"
                type="number"
                min={1}
                max={4096}
                defaultValue={180}
                disabled={quickSubmitting}
              />
            </label>
          </>
        ) : (
          <label style={{ display: "grid", gap: "0.35rem" }}>
            <span>Failure mode</span>
            <select name="failure_mode" defaultValue="none" disabled={quickSubmitting}>
              <option value="none">Completed</option>
              <option value="all">Force full failure</option>
            </select>
          </label>
        )}

        <label style={{ display: "grid", gap: "0.35rem" }}>
          <span>Experiment tag</span>
          <input name="experiment_tag" type="text" placeholder="phase14-quick-run" disabled={quickSubmitting} />
        </label>

        <label style={{ display: "grid", gap: "0.35rem" }}>
          <span>Notes</span>
          <textarea
            name="notes"
            rows={2}
            placeholder="Quick run context"
            disabled={quickSubmitting}
          />
        </label>

        <button
          type="submit"
          style={{ width: "fit-content" }}
          disabled={
            quickSubmitting ||
            registry.agent_versions.length === 0 ||
            !quickDataset ||
            !quickScorer
          }
        >
          {quickSubmitting ? "Launching..." : "Start quick run"}
        </button>
        {quickErrorMessage ? (
          <p style={{ margin: 0, color: "rgb(174, 63, 19)" }}>{quickErrorMessage}</p>
        ) : null}
      </form>

      <form action={handleSubmit} style={{ display: "grid", gap: "0.75rem" }}>
        <strong>Full run launch</strong>

        <label style={{ display: "grid", gap: "0.35rem" }}>
          <span>Dataset</span>
          <select
            name="dataset_id"
            defaultValue={defaultDataset}
            disabled={submitting || datasets.length === 0}
          >
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
          <span>Adapter</span>
          <select
            name="adapter_type"
            value={runAdapterType}
            onChange={(event) => setRunAdapterType(event.target.value as AdapterType)}
            disabled={submitting}
          >
            <option value="openai">OpenAI</option>
            <option value="stub">Stub</option>
          </select>
        </label>

        {runAdapterType === "openai" ? (
          <>
            <label style={{ display: "grid", gap: "0.35rem" }}>
              <span>Model</span>
              <input
                name="model"
                type="text"
                placeholder="gpt-4.1-mini"
                defaultValue={registry.agent_versions[0]?.model ?? "gpt-4.1-mini"}
                disabled={submitting}
              />
            </label>

            <label style={{ display: "grid", gap: "0.35rem" }}>
              <span>System prompt</span>
              <textarea
                name="system_prompt"
                rows={4}
                placeholder="Leave blank to use the selected agent version prompt."
                disabled={submitting}
              />
            </label>

            <label style={{ display: "grid", gap: "0.35rem" }}>
              <span>Temperature</span>
              <input
                name="temperature"
                type="number"
                min={0}
                max={2}
                step="0.1"
                defaultValue={0}
                disabled={submitting}
              />
            </label>

            <label style={{ display: "grid", gap: "0.35rem" }}>
              <span>Max output tokens</span>
              <input
                name="max_output_tokens"
                type="number"
                min={1}
                max={4096}
                defaultValue={180}
                disabled={submitting}
              />
            </label>
          </>
        ) : (
          <label style={{ display: "grid", gap: "0.35rem" }}>
            <span>Failure mode</span>
            <select name="failure_mode" defaultValue="none" disabled={submitting}>
              <option value="none">Completed</option>
              <option value="all">Force full failure</option>
            </select>
          </label>
        )}

        <label style={{ display: "grid", gap: "0.35rem" }}>
          <span>Sample count</span>
          <input
            name="sample_count"
            type="number"
            min={1}
            max={10}
            defaultValue={1}
            disabled={submitting}
          />
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
          <span>Dataset tag filter</span>
          <input
            name="dataset_tag_filter"
            type="text"
            placeholder="refunds, regression"
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
        <p style={{ margin: 0, color: "var(--muted)" }}>
          Use sample count greater than 1 to launch a repeated-run group with persisted sampling
          metadata. OpenAI runs require a valid backend <code>OPENAI_API_KEY</code>.
        </p>
      </form>
    </section>
  );
}
