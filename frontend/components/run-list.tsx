import Link from "next/link";

import type { RunSummary } from "@/lib/runs";

type RunListProps = {
  runs: RunSummary[];
};

export function RunList({ runs }: RunListProps) {
  return (
    <section
      style={{
        display: "grid",
        gap: "1rem",
        padding: "1.5rem",
        borderRadius: "24px",
        border: "1px solid var(--border)",
        background: "var(--panel)",
        boxShadow: "var(--shadow)",
      }}
    >
      <div>
        <p style={{ margin: 0, color: "var(--muted)", letterSpacing: "0.08em", textTransform: "uppercase" }}>
          Recent Runs
        </p>
        <h2 style={{ margin: "0.35rem 0 0" }}>Persisted execution history</h2>
      </div>

      {runs.length === 0 ? (
        <p style={{ margin: 0, color: "var(--muted)" }}>
          No runs created yet. Start a run to unlock real summary metrics and trace-backed review.
        </p>
      ) : (
        <div style={{ display: "grid", gap: "0.9rem" }}>
          {runs.map((run) => (
            <Link
              key={run.run_id}
              href={`/runs/${run.run_id}`}
              style={{
                display: "grid",
                gap: "0.35rem",
                padding: "1rem 1.1rem",
                borderRadius: "18px",
                border: "1px solid var(--border)",
                color: "inherit",
                textDecoration: "none",
                background: "rgba(255,255,255,0.74)",
              }}
            >
              <strong>{run.run_id}</strong>
              <span>
                {run.status} · {run.completed_tasks}/{run.total_tasks} completed · {run.failed_tasks} failed
              </span>
              <span style={{ color: "var(--muted)" }}>
                Dataset {run.dataset_id} · Agent {run.agent_version_id}
              </span>
            </Link>
          ))}
        </div>
      )}
    </section>
  );
}
