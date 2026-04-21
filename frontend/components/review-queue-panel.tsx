import Link from "next/link";

import type { ReviewQueue } from "@/lib/runs";

type ReviewQueuePanelProps = {
  queue: ReviewQueue | null;
  loadError?: string | null;
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

export function ReviewQueuePanel({ queue, loadError = null }: ReviewQueuePanelProps) {
  if (loadError) {
    return (
      <section style={panelStyle}>
        <strong>Review queue unavailable</strong>
        <p style={{ margin: 0 }}>{loadError}</p>
      </section>
    );
  }

  if (!queue) {
    return (
      <section style={panelStyle}>
        <div>
          <p style={{ margin: 0, color: "var(--muted)", letterSpacing: "0.08em", textTransform: "uppercase" }}>
            Review Queue
          </p>
          <h2 style={{ margin: "0.35rem 0 0" }}>No review-needed tasks yet</h2>
        </div>
        <p style={{ margin: 0, color: "var(--muted)" }}>
          Review queue cards appear after persisted task results flag cases for manual follow-up.
        </p>
      </section>
    );
  }

  return (
    <section style={panelStyle}>
      <div style={{ display: "flex", justifyContent: "space-between", gap: "1rem", flexWrap: "wrap" }}>
        <div>
          <p style={{ margin: 0, color: "var(--muted)", letterSpacing: "0.08em", textTransform: "uppercase" }}>
            Review Queue
          </p>
          <h2 style={{ margin: "0.35rem 0 0" }}>
            {queue.pending_count} pending · {queue.reviewed_count} reviewed
          </h2>
        </div>
        <Link href="/reviews" style={{ color: "var(--accent)" }}>
          Open review queue
        </Link>
      </div>

      {queue.items.length === 0 ? (
        <p style={{ margin: 0, color: "var(--muted)" }}>No tasks currently require manual review.</p>
      ) : (
        <div style={{ display: "grid", gap: "0.75rem" }}>
          {queue.items.slice(0, 4).map((item) => (
            <Link
              key={item.task_run_id}
              href={`/runs/${item.run_id}/tasks/${item.task_run_id}`}
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
                {item.category} · {item.failure_reason ?? item.status} · {item.review_status}
              </span>
              <span style={{ color: "var(--muted)" }}>
                {item.review?.note ?? item.error_message ?? item.final_output ?? item.input_text}
              </span>
            </Link>
          ))}
        </div>
      )}
    </section>
  );
}
