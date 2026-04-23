"use client";

import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";

import type { RunSummary } from "@/lib/runs";

type CompareLauncherFormProps = {
  runs: RunSummary[];
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

const comparableStatuses = new Set(["completed", "partial_success"]);

export function CompareLauncherForm({ runs }: CompareLauncherFormProps) {
  const router = useRouter();
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const comparableRuns = runs.filter((run) => comparableStatuses.has(run.status));
  const datasetCounts = comparableRuns.reduce<Record<string, number>>((counts, run) => {
    counts[run.dataset_id] = (counts[run.dataset_id] ?? 0) + 1;
    return counts;
  }, {});
  const firstComparableDatasetId = Object.entries(datasetCounts).find(([, count]) => count >= 2)?.[0];
  const preferredRuns = firstComparableDatasetId
    ? comparableRuns.filter((run) => run.dataset_id === firstComparableDatasetId)
    : comparableRuns;
  const baselineRun = preferredRuns.find((run) => run.baseline) ?? preferredRuns[1] ?? preferredRuns[0];
  const baselineDefault = baselineRun?.run_id ?? "";
  const [selectedBaselineRunId, setSelectedBaselineRunId] = useState(baselineDefault);
  const selectedBaselineRun =
    comparableRuns.find((run) => run.run_id === selectedBaselineRunId) ?? baselineRun;
  const candidateOptions = useMemo(
    () =>
      selectedBaselineRun
        ? comparableRuns.filter(
            (run) =>
              run.run_id !== selectedBaselineRun.run_id &&
              run.dataset_id === selectedBaselineRun.dataset_id,
          )
        : [],
    [comparableRuns, selectedBaselineRun],
  );
  const candidateDefault = candidateOptions[0]?.run_id ?? "";

  function handleSubmit(formData: FormData) {
    const baselineRunId = String(formData.get("baseline_run_id") ?? "");
    const candidateRunId = String(formData.get("candidate_run_id") ?? "");

    if (!baselineRunId || !candidateRunId) {
      setErrorMessage("Select both a baseline run and a candidate run.");
      return;
    }
    if (baselineRunId === candidateRunId) {
      setErrorMessage("Pick two different runs for comparison.");
      return;
    }
    const baseline = comparableRuns.find((run) => run.run_id === baselineRunId);
    const candidate = comparableRuns.find((run) => run.run_id === candidateRunId);
    if (!baseline || !candidate) {
      setErrorMessage("Only completed or partial-success runs can be compared.");
      return;
    }
    if (baseline.dataset_id !== candidate.dataset_id) {
      setErrorMessage("Pick two runs from the same dataset.");
      return;
    }

    setErrorMessage(null);
    const params = new URLSearchParams({
      baseline_run_id: baselineRunId,
      candidate_run_id: candidateRunId,
    });
    router.push(`/compare?${params.toString()}`);
  }

  if (comparableRuns.length < 2 || !firstComparableDatasetId) {
    return (
      <section style={panelStyle}>
        <div>
          <p style={{ margin: 0, color: "var(--muted)", letterSpacing: "0.08em", textTransform: "uppercase" }}>
            Compare Runs
          </p>
          <h2 style={{ margin: "0.35rem 0 0" }}>Need two persisted runs</h2>
        </div>
        <p style={{ margin: 0, color: "var(--muted)" }}>
          Compare needs two completed or partially completed runs. Start one baseline run, then
          start another candidate run against the same dataset.
        </p>
        <ol style={{ margin: 0, paddingLeft: "1.25rem", color: "var(--muted)", lineHeight: 1.55 }}>
          <li>Go to Step 2, Run evaluation.</li>
          <li>Start a run for the current agent version.</li>
          <li>Change the agent version or settings, then start a second run.</li>
          <li>Come back here and select baseline vs candidate.</li>
        </ol>
      </section>
    );
  }

  return (
    <form action={handleSubmit} style={panelStyle}>
      <div>
        <p style={{ margin: 0, color: "var(--muted)", letterSpacing: "0.08em", textTransform: "uppercase" }}>
          Compare Runs
        </p>
        <h2 style={{ margin: "0.35rem 0 0" }}>Baseline vs candidate</h2>
      </div>

      <p style={{ margin: 0, color: "var(--muted)", lineHeight: 1.5 }}>
        Pick the older or approved run as the baseline, then pick the newer run as the candidate.
        The compare page will show metric deltas, regressions, improvements, and trace differences.
      </p>

      <label style={{ display: "grid", gap: "0.35rem" }}>
        <span>Baseline run</span>
        <select
          name="baseline_run_id"
          value={selectedBaselineRunId}
          onChange={(event) => {
            setSelectedBaselineRunId(event.target.value);
            setErrorMessage(null);
          }}
        >
          {comparableRuns.map((run) => (
            <option key={run.run_id} value={run.run_id}>
              {run.run_id} · {run.dataset_id}
              {run.baseline ? " · baseline" : ""}
            </option>
          ))}
        </select>
      </label>

      <label style={{ display: "grid", gap: "0.35rem" }}>
        <span>Candidate run</span>
        <select name="candidate_run_id" defaultValue={candidateDefault}>
          {candidateOptions.map((run) => (
            <option key={run.run_id} value={run.run_id}>
              {run.run_id} · {run.dataset_id}
              {run.baseline ? " · baseline" : ""}
            </option>
          ))}
        </select>
      </label>

      <button type="submit" style={{ width: "fit-content" }}>
        Open compare view
      </button>

      {errorMessage ? (
        <p style={{ margin: 0, color: "rgb(174, 63, 19)" }}>{errorMessage}</p>
      ) : null}
    </form>
  );
}
