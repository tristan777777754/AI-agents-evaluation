import type { TaskRunDetail, TraceDetail } from "@/lib/runs";

type TaskTraceViewerProps = {
  task: TaskRunDetail;
  trace: TraceDetail;
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

export function TaskTraceViewer({ task, trace }: TaskTraceViewerProps) {
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
            Case Detail
          </p>
          <h2 style={{ margin: "0.35rem 0 0" }}>{task.dataset_item_id}</h2>
        </div>

        <div
          style={{
            display: "grid",
            gap: "0.85rem",
            gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
          }}
        >
          <div>
            <strong>Status</strong>
            <div>{task.status}</div>
          </div>
          <div>
            <strong>Failure Reason</strong>
            <div>{task.failure_reason ?? "none"}</div>
          </div>
          <div>
            <strong>Latency</strong>
            <div>{task.latency_ms ?? "N/A"} ms</div>
          </div>
          <div>
            <strong>Trace Steps</strong>
            <div>{trace.summary.step_count}</div>
          </div>
        </div>

        <div style={{ display: "grid", gap: "0.85rem" }}>
          <div>
            <strong>Input Text</strong>
            <pre style={{ whiteSpace: "pre-wrap", margin: "0.35rem 0 0" }}>{task.input_text}</pre>
          </div>
          <div>
            <strong>Expected Output</strong>
            <pre style={{ whiteSpace: "pre-wrap", margin: "0.35rem 0 0" }}>
              {task.expected_output ?? "No expected output"}
            </pre>
          </div>
          <div>
            <strong>Actual Output</strong>
            <pre style={{ whiteSpace: "pre-wrap", margin: "0.35rem 0 0" }}>
              {task.final_output ?? task.error_message ?? "No output"}
            </pre>
          </div>
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
            Trace Events
          </p>
          <h2 style={{ margin: "0.35rem 0 0" }}>{trace.events.length} ordered events</h2>
        </div>

        <div style={{ display: "grid", gap: "0.9rem" }}>
          {trace.events.map((event) => (
            <article
              key={`${event.step_index}-${event.event_type}`}
              style={{
                display: "grid",
                gap: "0.6rem",
                padding: "1rem",
                borderRadius: "18px",
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
    </section>
  );
}
