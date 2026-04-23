import Link from "next/link";

import type { RunComparison, TraceComparison } from "@/lib/runs";
import { TraceComparePanel } from "@/components/trace-compare-panel";

type RunCompareViewProps = {
  comparison: RunComparison;
  selectedDatasetItemId?: string | null;
  traceComparison?: TraceComparison | null;
};

function metricLabel(value: number | null, suffix = ""): string {
  if (value == null) {
    return "N/A";
  }
  return `${value}${suffix}`;
}

function deltaLabel(value: number | null, invert = false): string {
  if (value == null) {
    return "N/A";
  }
  const adjusted = invert ? value * -1 : value;
  const sign = adjusted > 0 ? "+" : "";
  return `${sign}${adjusted}`;
}

function credibilityLabel(label: string): string {
  switch (label) {
    case "statistically_significant_improvement":
      return "Statistically significant improvement";
    case "statistically_significant_regression":
      return "Statistically significant regression";
    case "directional_improvement":
      return "Directional improvement";
    case "directional_regression":
      return "Directional regression";
    default:
      return "Inconclusive";
  }
}

export function RunCompareView({
  comparison,
  selectedDatasetItemId,
  traceComparison,
}: RunCompareViewProps) {
  const metrics = [
    {
      label: "Success rate delta",
      baseline: metricLabel(comparison.success_rate.baseline, "%"),
      candidate: metricLabel(comparison.success_rate.candidate, "%"),
      delta: deltaLabel(comparison.success_rate.delta),
    },
    {
      label: "Latency delta",
      baseline: metricLabel(comparison.average_latency_ms.baseline, " ms"),
      candidate: metricLabel(comparison.average_latency_ms.candidate, " ms"),
      delta: `${deltaLabel(comparison.average_latency_ms.delta, true)} ms`,
    },
    {
      label: "Cost delta",
      baseline: `$${(comparison.total_cost.baseline ?? 0).toFixed(4)}`,
      candidate: `$${(comparison.total_cost.candidate ?? 0).toFixed(4)}`,
      delta: `$${deltaLabel(comparison.total_cost.delta, true)}`,
    },
    {
      label: "Review-needed delta",
      baseline: metricLabel(comparison.review_needed_count.baseline),
      candidate: metricLabel(comparison.review_needed_count.candidate),
      delta: deltaLabel(comparison.review_needed_count.delta, true),
    },
  ];
  const traceCases = [...comparison.regressions, ...comparison.improvements];

  return (
    <section style={{ display: "grid", gap: "1.5rem" }}>
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
        <div style={{ display: "flex", justifyContent: "space-between", gap: "1rem", flexWrap: "wrap" }}>
          <div>
            <p style={{ margin: 0, color: "var(--muted)", letterSpacing: "0.08em", textTransform: "uppercase" }}>
              Run Comparison
            </p>
            <h2 style={{ margin: "0.35rem 0 0" }}>
              {comparison.baseline_run_id} vs {comparison.candidate_run_id}
            </h2>
          </div>
          <div style={{ display: "flex", gap: "1rem", flexWrap: "wrap" }}>
            <Link href={`/runs/${comparison.baseline_run_id}`} style={{ color: "var(--accent)" }}>
              Baseline run
            </Link>
            <Link href={`/runs/${comparison.candidate_run_id}`} style={{ color: "var(--accent)" }}>
              Candidate run
            </Link>
          </div>
        </div>

        <p style={{ margin: 0, color: "var(--muted)" }}>
          Compared {comparison.compared_task_count} shared tasks · {comparison.improvement_count} improvements ·{" "}
          {comparison.regression_count} regressions
        </p>

        <section
          style={{
            display: "grid",
            gap: "0.75rem",
            padding: "1rem",
            borderRadius: "18px",
            border: "1px solid var(--border)",
            background: "rgba(255,255,255,0.72)",
          }}
        >
          <strong>{credibilityLabel(comparison.credibility.label)}</strong>
          <span style={{ color: "var(--muted)" }}>
            Sample size {comparison.sample_size} · p-value{" "}
            {comparison.p_value == null ? "N/A" : comparison.p_value.toFixed(4)} · 95% CI{" "}
            {comparison.confidence_interval.lower == null || comparison.confidence_interval.upper == null
              ? "N/A"
              : `${comparison.confidence_interval.lower} to ${comparison.confidence_interval.upper} pp`}
          </span>
          <span style={{ color: "var(--muted)" }}>
            {comparison.is_significant
              ? "This pair clears the current significance threshold."
              : "Positive deltas without significance stay directional rather than confirmed."}
          </span>
        </section>

        {comparison.sampling ? (
          <section
            style={{
              display: "grid",
              gap: "0.75rem",
              padding: "1rem",
              borderRadius: "18px",
              border: "1px solid var(--border)",
              background: "rgba(255,255,255,0.72)",
            }}
          >
            <strong>Sampling interpretation: {comparison.sampling.interpretation.replaceAll("_", " ")}</strong>
            <span style={{ color: "var(--muted)" }}>{comparison.sampling.notes}</span>
            <div
              style={{
                display: "grid",
                gap: "1rem",
                gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
              }}
            >
              {[
                { label: "Baseline", value: comparison.sampling.baseline },
                { label: "Candidate", value: comparison.sampling.candidate },
              ].map((entry) => (
                <article
                  key={entry.label}
                  style={{
                    display: "grid",
                    gap: "0.35rem",
                    padding: "0.9rem 1rem",
                    borderRadius: "16px",
                    border: "1px solid var(--border)",
                    background: "rgba(250,248,245,0.88)",
                  }}
                >
                  <strong>{entry.label}</strong>
                  <span>
                    {entry.value.success_rate_mean == null ? "N/A" : `${entry.value.success_rate_mean}% mean`} ·{" "}
                    {entry.value.success_rate_stddev == null
                      ? "N/A"
                      : `${entry.value.success_rate_stddev} pp stddev`}
                  </span>
                  <span>
                    Consistency{" "}
                    {entry.value.consistency_rate == null ? "N/A" : `${entry.value.consistency_rate}%`}
                  </span>
                  <span style={{ color: "var(--muted)" }}>
                    {entry.value.completed_sample_count}/{entry.value.sample_count} samples ·{" "}
                    {entry.value.is_stable ? "stable" : "variable"}
                  </span>
                </article>
              ))}
            </div>
          </section>
        ) : null}

        <section
          style={{
            display: "grid",
            gap: "1rem",
            gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
          }}
        >
          {[
            { label: "Baseline lineage", value: comparison.lineage.baseline },
            { label: "Candidate lineage", value: comparison.lineage.candidate },
          ].map((entry) => (
            <article
              key={entry.label}
              style={{
                display: "grid",
                gap: "0.35rem",
                padding: "1rem",
                borderRadius: "18px",
                border: "1px solid var(--border)",
                background: "rgba(255,255,255,0.72)",
              }}
            >
              <strong>{entry.label}</strong>
              <span>Dataset snapshot {entry.value.dataset_snapshot_id ?? "n/a"}</span>
              <span>Agent snapshot {entry.value.agent_version_snapshot_hash}</span>
              <span>
                Scorer {entry.value.scorer_config_id} · {entry.value.scorer_snapshot_hash}
              </span>
              {entry.value.experiment_tag ? (
                <span style={{ color: "var(--muted)" }}>
                  Experiment {entry.value.experiment_tag}
                </span>
              ) : null}
            </article>
          ))}
        </section>

        <div
          style={{
            display: "grid",
            gap: "1rem",
            gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
          }}
        >
          {metrics.map((metric) => (
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
              <strong>{metric.delta}</strong>
              <span style={{ color: "var(--muted)" }}>
                {metric.baseline} {"->"} {metric.candidate}
              </span>
            </article>
          ))}
        </div>
      </section>

      <section
        style={{
          display: "grid",
          gap: "1rem",
          gridTemplateColumns: "minmax(0, 1.1fr) minmax(0, 1fr)",
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
              Category Deltas
            </p>
            <h3 style={{ margin: "0.35rem 0 0" }}>Success-rate shifts by category</h3>
          </div>

          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr>
                  <th style={{ textAlign: "left", padding: "0.75rem" }}>Category</th>
                  <th style={{ textAlign: "left", padding: "0.75rem" }}>Baseline</th>
                  <th style={{ textAlign: "left", padding: "0.75rem" }}>Candidate</th>
                  <th style={{ textAlign: "left", padding: "0.75rem" }}>Delta</th>
                </tr>
              </thead>
              <tbody>
                {comparison.category_deltas.map((entry) => (
                  <tr key={entry.category} style={{ borderTop: "1px solid var(--border)" }}>
                    <td style={{ padding: "0.75rem" }}>
                      <strong>{entry.category}</strong>
                    </td>
                    <td style={{ padding: "0.75rem" }}>{entry.baseline_success_rate}%</td>
                    <td style={{ padding: "0.75rem" }}>{entry.candidate_success_rate}%</td>
                    <td style={{ padding: "0.75rem" }}>{deltaLabel(entry.success_rate_delta)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <div style={{ display: "grid", gap: "1rem" }}>
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
            <div>
              <p style={{ margin: 0, color: "var(--muted)", letterSpacing: "0.08em", textTransform: "uppercase" }}>
                Improvements
              </p>
              <h3 style={{ margin: "0.35rem 0 0" }}>Recovered cases</h3>
            </div>
            {comparison.improvements.length === 0 ? (
              <p style={{ margin: 0, color: "var(--muted)" }}>No improvements in this pair.</p>
            ) : (
              comparison.improvements.map((item) => (
                <Link
                  key={`${item.dataset_item_id}-${item.candidate_task_run_id}`}
                  href={`/runs/${comparison.candidate_run_id}/tasks/${item.candidate_task_run_id}`}
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
                  <strong>{item.dataset_item_id}</strong>
                  <span>
                    {item.category} · {item.baseline_failure_reason ?? item.baseline_status} {"->"}{" "}
                    {item.candidate_status}
                  </span>
                </Link>
              ))
            )}
          </section>

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
            <div>
              <p style={{ margin: 0, color: "var(--muted)", letterSpacing: "0.08em", textTransform: "uppercase" }}>
                Regressions
              </p>
              <h3 style={{ margin: "0.35rem 0 0" }}>Cases that got worse</h3>
            </div>
            {comparison.regressions.length === 0 ? (
              <p style={{ margin: 0, color: "var(--muted)" }}>No regressions in this pair.</p>
            ) : (
              comparison.regressions.map((item) => (
                <Link
                  key={`${item.dataset_item_id}-${item.candidate_task_run_id}`}
                  href={`/runs/${comparison.candidate_run_id}/tasks/${item.candidate_task_run_id}`}
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
                  <strong>{item.dataset_item_id}</strong>
                  <span>
                    {item.category} · {item.baseline_status} {"->"}{" "}
                    {item.candidate_failure_reason ?? item.candidate_status}
                  </span>
                </Link>
              ))
            )}
          </section>
        </div>
      </section>

      <section
        style={{
          display: "grid",
          gap: "1rem",
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
          <div>
            <p style={{ margin: 0, color: "var(--muted)", letterSpacing: "0.08em", textTransform: "uppercase" }}>
              Trace Compare
            </p>
            <h3 style={{ margin: "0.35rem 0 0" }}>Side-by-side path evidence</h3>
          </div>
          {traceCases.length === 0 ? (
            <p style={{ margin: 0, color: "var(--muted)" }}>
              No improvement or regression cases are available for trace comparison.
            </p>
          ) : (
            <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap" }}>
              {traceCases.map((item) => (
                <Link
                  key={`trace-case-${item.dataset_item_id}`}
                  href={`/compare?baseline_run_id=${comparison.baseline_run_id}&candidate_run_id=${comparison.candidate_run_id}&dataset_item_id=${item.dataset_item_id}`}
                  style={{
                    padding: "0.7rem 0.9rem",
                    borderRadius: "999px",
                    border: "1px solid var(--border)",
                    background:
                      selectedDatasetItemId === item.dataset_item_id
                        ? "rgba(235, 122, 55, 0.16)"
                        : "rgba(255,255,255,0.72)",
                    color: "inherit",
                    textDecoration: "none",
                  }}
                >
                  {item.dataset_item_id}
                </Link>
              ))}
            </div>
          )}
        </section>

        {traceComparison ? (
          <TraceComparePanel traceComparison={traceComparison} />
        ) : traceCases.length > 0 ? (
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
            <strong>Trace comparison unavailable</strong>
            <p style={{ margin: 0, color: "var(--muted)" }}>
              Select a case chip above to inspect baseline and candidate trace paths side by side.
            </p>
          </section>
        ) : null}
      </section>
    </section>
  );
}
