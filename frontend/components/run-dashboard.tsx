import Link from "next/link";

import type { RunDashboardSummary } from "@/lib/runs";

type RunDashboardProps = {
  summary: RunDashboardSummary | null;
  loadError?: string | null;
};

function metricValue(value: number | null, suffix = ""): string {
  if (value == null) {
    return "N/A";
  }
  return `${value}${suffix}`;
}

export function RunDashboard({ summary, loadError = null }: RunDashboardProps) {
  if (loadError) {
    return (
      <section
        style={{
          display: "grid",
          gap: "0.75rem",
          padding: "1.5rem",
          borderRadius: "24px",
          border: "1px solid rgba(174, 63, 19, 0.2)",
          background: "rgba(174, 63, 19, 0.08)",
        }}
      >
        <strong>Dashboard unavailable</strong>
        <p style={{ margin: 0 }}>{loadError}</p>
      </section>
    );
  }

  if (!summary) {
    return (
      <section
        style={{
          display: "grid",
          gap: "0.75rem",
          padding: "1.5rem",
          borderRadius: "24px",
          border: "1px solid var(--border)",
          background: "var(--panel)",
          boxShadow: "var(--shadow)",
        }}
      >
        <p style={{ margin: 0, color: "var(--muted)", letterSpacing: "0.08em", textTransform: "uppercase" }}>
          Summary Dashboard
        </p>
        <h2 style={{ margin: 0 }}>No real run data yet</h2>
        <p style={{ margin: 0, color: "var(--muted)" }}>
          Launch a run first. Phase 5 metrics only appear after real task results have been
          persisted.
        </p>
      </section>
    );
  }

  const kpis = [
    { label: "Success rate", value: metricValue(summary.success_rate, "%") },
    { label: "Average latency", value: metricValue(summary.average_latency_ms, " ms") },
    { label: "Total cost", value: `$${summary.total_cost.toFixed(4)}` },
    { label: "Review needed", value: String(summary.review_needed_count) },
  ];

  return (
    <section
      style={{
        display: "grid",
        gap: "1.5rem",
      }}
    >
      <section
        style={{
          display: "grid",
          gap: "0.75rem",
          padding: "1.5rem",
          borderRadius: "24px",
          border: "1px solid var(--border)",
          background: "var(--panel)",
          boxShadow: "var(--shadow)",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", gap: "1rem", flexWrap: "wrap" }}>
          <div>
            <p style={{ margin: 0, color: "var(--muted)", letterSpacing: "0.08em", textTransform: "uppercase" }}>
              Summary Dashboard
            </p>
            <h2 style={{ margin: "0.35rem 0 0" }}>Latest run: {summary.run_id}</h2>
          </div>
          <Link href={`/runs/${summary.run_id}`} style={{ color: "var(--accent)", alignSelf: "start" }}>
            Open run detail
          </Link>
        </div>

        <p style={{ margin: 0, color: "var(--muted)" }}>
          Status {summary.status} · {summary.successful_tasks}/{summary.total_tasks} succeeded ·{" "}
          {summary.failed_tasks} failed
        </p>

        <div
          style={{
            display: "grid",
            gap: "1rem",
            gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
          }}
        >
          {kpis.map((metric) => (
            <article
              key={metric.label}
              style={{
                display: "grid",
                gap: "0.35rem",
                padding: "1rem",
                borderRadius: "18px",
                border: "1px solid var(--border)",
                background: "rgba(255,255,255,0.72)",
              }}
            >
              <span style={{ color: "var(--muted)" }}>{metric.label}</span>
              <strong style={{ fontSize: "1.5rem" }}>{metric.value}</strong>
            </article>
          ))}
        </div>
      </section>

      <section
        style={{
          display: "grid",
          gap: "1rem",
          gridTemplateColumns: "minmax(0, 1.4fr) minmax(0, 1fr)",
        }}
      >
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
              Category Breakdown
            </p>
            <h3 style={{ margin: "0.35rem 0 0" }}>Real aggregated run metrics</h3>
          </div>

          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr>
                  <th style={{ textAlign: "left", padding: "0.75rem" }}>Category</th>
                  <th style={{ textAlign: "left", padding: "0.75rem" }}>Success</th>
                  <th style={{ textAlign: "left", padding: "0.75rem" }}>Latency</th>
                  <th style={{ textAlign: "left", padding: "0.75rem" }}>Cost</th>
                </tr>
              </thead>
              <tbody>
                {summary.category_breakdown.map((row) => (
                  <tr key={row.category} style={{ borderTop: "1px solid var(--border)" }}>
                    <td style={{ padding: "0.75rem" }}>
                      <strong>{row.category}</strong>
                      <div style={{ color: "var(--muted)", marginTop: "0.25rem" }}>
                        {row.total_tasks} tasks
                      </div>
                    </td>
                    <td style={{ padding: "0.75rem" }}>
                      {row.success_rate}% ({row.successful_tasks}/{row.total_tasks})
                    </td>
                    <td style={{ padding: "0.75rem" }}>{metricValue(row.average_latency_ms, " ms")}</td>
                    <td style={{ padding: "0.75rem" }}>${row.total_cost.toFixed(4)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

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
              Failure Signals
            </p>
            <h3 style={{ margin: "0.35rem 0 0" }}>Breakdown and case navigation</h3>
          </div>

          <div style={{ display: "grid", gap: "0.75rem" }}>
            {summary.failure_breakdown.length === 0 ? (
              <p style={{ margin: 0, color: "var(--muted)" }}>No failed tasks in this run.</p>
            ) : (
              summary.failure_breakdown.map((entry) => (
                <div
                  key={entry.failure_reason}
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    gap: "1rem",
                    padding: "0.85rem 1rem",
                    borderRadius: "16px",
                    border: "1px solid var(--border)",
                    background: "rgba(255,255,255,0.72)",
                  }}
                >
                  <span>{entry.failure_reason}</span>
                  <strong>{entry.count}</strong>
                </div>
              ))
            )}
          </div>

          <div style={{ display: "grid", gap: "0.75rem" }}>
            <strong>Failed cases</strong>
            {summary.failed_cases.length === 0 ? (
              <p style={{ margin: 0, color: "var(--muted)" }}>No failed cases to review.</p>
            ) : (
              summary.failed_cases.slice(0, 6).map((task) => (
                <Link
                  key={task.task_run_id}
                  href={`/runs/${task.run_id}/tasks/${task.task_run_id}`}
                  style={{
                    display: "grid",
                    gap: "0.25rem",
                    padding: "0.9rem 1rem",
                    borderRadius: "16px",
                    border: "1px solid var(--border)",
                    background: "rgba(255,255,255,0.72)",
                    color: "inherit",
                    textDecoration: "none",
                  }}
                >
                  <strong>{task.dataset_item_id}</strong>
                  <span>
                    {task.category} · {task.failure_reason}
                  </span>
                  <span style={{ color: "var(--muted)" }}>
                    {task.error_message ?? task.final_output ?? "Inspect trace for details"}
                  </span>
                </Link>
              ))
            )}
          </div>
        </section>
      </section>
    </section>
  );
}
