"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

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

export function CompareLauncherForm({ runs }: CompareLauncherFormProps) {
  const router = useRouter();
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const baselineRun = runs.find((run) => run.baseline) ?? runs[1] ?? runs[0];
  const baselineDefault = baselineRun?.run_id ?? "";
  const candidateDefault =
    runs.find((run) => run.run_id !== baselineDefault)?.run_id ?? runs[0]?.run_id ?? "";

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

    setErrorMessage(null);
    const params = new URLSearchParams({
      baseline_run_id: baselineRunId,
      candidate_run_id: candidateRunId,
    });
    router.push(`/compare?${params.toString()}`);
  }

  if (runs.length < 2) {
    return (
      <section style={panelStyle}>
        <div>
          <p style={{ margin: 0, color: "var(--muted)", letterSpacing: "0.08em", textTransform: "uppercase" }}>
            Compare Runs
          </p>
          <h2 style={{ margin: "0.35rem 0 0" }}>Need two persisted runs</h2>
        </div>
        <p style={{ margin: 0, color: "var(--muted)" }}>
          Launch at least two persisted runs before opening the compare view.
        </p>
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

      <label style={{ display: "grid", gap: "0.35rem" }}>
        <span>Baseline run</span>
        <select name="baseline_run_id" defaultValue={baselineDefault}>
          {runs.map((run) => (
            <option key={run.run_id} value={run.run_id}>
              {run.run_id} · {run.status}
              {run.baseline ? " · baseline" : ""}
            </option>
          ))}
        </select>
      </label>

      <label style={{ display: "grid", gap: "0.35rem" }}>
        <span>Candidate run</span>
        <select name="candidate_run_id" defaultValue={candidateDefault}>
          {runs.map((run) => (
            <option key={run.run_id} value={run.run_id}>
              {run.run_id} · {run.status}
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
