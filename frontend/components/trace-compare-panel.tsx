import Link from "next/link";

import type { TraceComparison } from "@/lib/runs";

type TraceComparePanelProps = {
  traceComparison: TraceComparison;
};

function renderJson(value: unknown): string {
  if (value == null) {
    return "null";
  }
  if (typeof value === "string") {
    return value;
  }
  return JSON.stringify(value, null, 2);
}

function metricLabel(value: number | null): string {
  if (value == null) {
    return "n/a";
  }
  return `${value}`;
}

export function TraceComparePanel({ traceComparison }: TraceComparePanelProps) {
  const signalCards = [
    ...traceComparison.regression_signals,
    ...traceComparison.improvement_signals,
  ];

  return (
    <section
      style={{
        display: "grid",
        gap: "1.5rem",
        padding: "1.5rem",
        borderRadius: "24px",
        border: "1px solid var(--border)",
        background: "var(--panel)",
        boxShadow: "var(--shadow)",
      }}
    >
      <div style={{ display: "grid", gap: "0.35rem" }}>
        <p style={{ margin: 0, color: "var(--muted)", letterSpacing: "0.08em", textTransform: "uppercase" }}>
          Trace Intelligence
        </p>
        <h3 style={{ margin: 0 }}>
          {traceComparison.dataset_item_id} · {traceComparison.overall_label}
        </h3>
        <p style={{ margin: 0, color: "var(--muted)" }}>
          Category {traceComparison.category} · same final output{" "}
          {traceComparison.same_final_output ? "yes" : "no"} · pass/fail changed{" "}
          {traceComparison.pass_fail_changed ? "yes" : "no"}
        </p>
      </div>

      <section
        style={{
          display: "grid",
          gap: "1rem",
          padding: "1rem",
          borderRadius: "18px",
          border: "1px solid var(--border)",
          background: "rgba(255,255,255,0.72)",
        }}
      >
        <div>
          <strong>Input</strong>
          <pre style={{ margin: "0.35rem 0 0", whiteSpace: "pre-wrap" }}>{traceComparison.input_text}</pre>
        </div>
        <div>
          <strong>Expected Output</strong>
          <pre style={{ margin: "0.35rem 0 0", whiteSpace: "pre-wrap" }}>
            {traceComparison.expected_output ?? "No expected output"}
          </pre>
        </div>
      </section>

      <section
        style={{
          display: "grid",
          gap: "1rem",
          gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
        }}
      >
        {signalCards.length === 0 ? (
          <div
            style={{
              padding: "1rem",
              borderRadius: "18px",
              border: "1px solid var(--border)",
              background: "rgba(255,255,255,0.72)",
              color: "var(--muted)",
            }}
          >
            No step-level deltas were detected for this item.
          </div>
        ) : (
          signalCards.map((signal) => (
            <article
              key={`${signal.direction}-${signal.signal_key}`}
              style={{
                display: "grid",
                gap: "0.35rem",
                padding: "1rem",
                borderRadius: "18px",
                border: "1px solid var(--border)",
                background: "rgba(255,255,255,0.72)",
              }}
            >
              <strong>{signal.label}</strong>
              <span style={{ color: "var(--muted)" }}>
                {signal.direction} · {String(signal.baseline_value ?? "n/a")} {"->"}{" "}
                {String(signal.candidate_value ?? "n/a")}
              </span>
              {signal.detail ? <span style={{ color: "var(--muted)" }}>{signal.detail}</span> : null}
            </article>
          ))
        )}
      </section>

      <section
        style={{
          display: "grid",
          gap: "1rem",
          gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
          alignItems: "start",
        }}
      >
        {[traceComparison.baseline, traceComparison.candidate].map((entry, index) => (
          <section
            key={entry.task_run_id}
            style={{
              display: "grid",
              gap: "1rem",
              padding: "1.25rem",
              borderRadius: "20px",
              border: "1px solid var(--border)",
              background: index === 0 ? "rgba(255,248,240,0.9)" : "rgba(241,248,246,0.92)",
            }}
          >
            <div style={{ display: "grid", gap: "0.25rem" }}>
              <strong>{index === 0 ? "Baseline" : "Candidate"}</strong>
              <span style={{ color: "var(--muted)" }}>
                Run {entry.run_id} · task {entry.task_run_id}
              </span>
              <div style={{ display: "flex", gap: "1rem", flexWrap: "wrap", color: "var(--muted)" }}>
                <span>status {entry.status}</span>
                <span>pass {entry.pass_fail == null ? "n/a" : entry.pass_fail ? "yes" : "no"}</span>
                <span>failure {entry.failure_reason ?? "none"}</span>
              </div>
              <Link href={`/runs/${entry.run_id}/tasks/${entry.task_run_id}`} style={{ color: "var(--accent)" }}>
                Open raw trace page
              </Link>
            </div>

            <div
              style={{
                display: "grid",
                gap: "0.75rem",
                gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))",
              }}
            >
              <article>
                <strong>Steps</strong>
                <div>{entry.derived_metrics.step_count}</div>
              </article>
              <article>
                <strong>Tool Calls</strong>
                <div>{entry.derived_metrics.tool_count}</div>
              </article>
              <article>
                <strong>Efficiency</strong>
                <div>{metricLabel(entry.derived_metrics.efficiency_score)}</div>
              </article>
              <article>
                <strong>Failure Step</strong>
                <div>{metricLabel(entry.derived_metrics.failure_step_index)}</div>
              </article>
            </div>

            <div style={{ display: "grid", gap: "0.75rem" }}>
              <div>
                <strong>Tool Path</strong>
                <div style={{ color: "var(--muted)" }}>
                  {entry.derived_metrics.tool_names.length > 0
                    ? entry.derived_metrics.tool_names.join(", ")
                    : "No tool usage"}
                </div>
              </div>
              <div>
                <strong>Final Output</strong>
                <pre style={{ margin: "0.35rem 0 0", whiteSpace: "pre-wrap" }}>
                  {entry.final_output ?? entry.error_message ?? "No output"}
                </pre>
              </div>
            </div>

            <div style={{ display: "grid", gap: "0.75rem" }}>
              {entry.events.map((event) => (
                <article
                  key={`${entry.task_run_id}-${event.step_index}-${event.event_type}`}
                  style={{
                    display: "grid",
                    gap: "0.5rem",
                    padding: "0.85rem",
                    borderRadius: "16px",
                    border: "1px solid var(--border)",
                    background: "rgba(255,255,255,0.72)",
                  }}
                >
                  <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap" }}>
                    <strong>#{event.step_index}</strong>
                    <span>{event.event_type}</span>
                    {event.tool_name ? <span>tool: {event.tool_name}</span> : null}
                    {event.status ? <span>status: {event.status}</span> : null}
                    {event.latency_ms != null ? <span>{event.latency_ms} ms</span> : null}
                  </div>
                  {event.message ? <div>{event.message}</div> : null}
                  {event.error ? <div style={{ color: "#9c2f17" }}>{event.error}</div> : null}
                  {event.input != null ? (
                    <pre style={{ margin: 0, whiteSpace: "pre-wrap" }}>{renderJson(event.input)}</pre>
                  ) : null}
                  {event.output != null ? (
                    <pre style={{ margin: 0, whiteSpace: "pre-wrap" }}>{renderJson(event.output)}</pre>
                  ) : null}
                </article>
              ))}
            </div>
          </section>
        ))}
      </section>
    </section>
  );
}
