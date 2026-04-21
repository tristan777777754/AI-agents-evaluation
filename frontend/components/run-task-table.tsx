import Link from "next/link";

import type { RunTaskList } from "@/lib/runs";

type RunTaskTableProps = {
  runTasks: RunTaskList;
};

export function RunTaskTable({ runTasks }: RunTaskTableProps) {
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
          Task Results
        </p>
        <h2 style={{ margin: "0.35rem 0 0" }}>{runTasks.total_count} persisted task runs</h2>
      </div>

      <div style={{ overflowX: "auto" }}>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr>
              <th style={{ textAlign: "left", padding: "0.75rem" }}>Task</th>
              <th style={{ textAlign: "left", padding: "0.75rem" }}>Status</th>
              <th style={{ textAlign: "left", padding: "0.75rem" }}>Category</th>
              <th style={{ textAlign: "left", padding: "0.75rem" }}>Output</th>
              <th style={{ textAlign: "left", padding: "0.75rem" }}>Score</th>
            </tr>
          </thead>
          <tbody>
            {runTasks.items.map((task) => (
              <tr key={task.task_run_id} style={{ borderTop: "1px solid var(--border)" }}>
                <td style={{ padding: "0.75rem", verticalAlign: "top" }}>
                  <Link
                    href={`/runs/${task.run_id}/tasks/${task.task_run_id}`}
                    style={{ color: "var(--accent)", fontWeight: 700, textDecoration: "none" }}
                  >
                    {task.dataset_item_id}
                  </Link>
                  <div style={{ color: "var(--muted)", marginTop: "0.35rem" }}>{task.input_text}</div>
                </td>
                <td style={{ padding: "0.75rem", verticalAlign: "top" }}>{task.status}</td>
                <td style={{ padding: "0.75rem", verticalAlign: "top" }}>{task.category}</td>
                <td style={{ padding: "0.75rem", verticalAlign: "top" }}>
                  {task.final_output ?? task.error_message ?? "No output"}
                </td>
                <td style={{ padding: "0.75rem", verticalAlign: "top" }}>
                  {task.score ? `${task.score.correctness ?? 0} / ${task.score.pass_fail ? "pass" : "fail"}` : "N/A"}
                  {task.failure_reason ? (
                    <div style={{ color: "var(--muted)", marginTop: "0.35rem" }}>{task.failure_reason}</div>
                  ) : null}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
