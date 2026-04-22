import Link from "next/link";
import { notFound } from "next/navigation";

import { FailedCasePromoter } from "@/components/failed-case-promoter";
import { ReviewEditor } from "@/components/review-editor";
import { TaskTraceViewer } from "@/components/task-trace-viewer";
import { BackendApiError } from "@/lib/datasets";
import { getTaskRunDetail, getTaskTrace } from "@/lib/runs";

type TaskDetailPageProps = {
  params: Promise<{ runId: string; taskRunId: string }>;
};

export default async function TaskDetailPage({ params }: TaskDetailPageProps) {
  const { runId, taskRunId } = await params;

  try {
    const [task, trace] = await Promise.all([getTaskRunDetail(taskRunId), getTaskTrace(taskRunId)]);

    return (
      <main
        style={{
          padding: "3rem 1.5rem 4rem",
          display: "grid",
          gap: "1.5rem",
          maxWidth: "1120px",
          margin: "0 auto",
        }}
      >
        <div style={{ display: "flex", gap: "1rem", flexWrap: "wrap" }}>
          <Link href={`/runs/${runId}`} style={{ color: "var(--accent)" }}>
            Back to run
          </Link>
          <Link href="/reviews" style={{ color: "var(--accent)" }}>
            Open review queue
          </Link>
          <Link href="/" style={{ color: "var(--accent)" }}>
            Back to workbench
          </Link>
        </div>

        <section
          style={{
            display: "grid",
            gap: "0.75rem",
            padding: "2rem",
            borderRadius: "28px",
            background:
              "linear-gradient(135deg, rgba(255,250,245,0.94), rgba(255,239,222,0.9))",
            border: "1px solid var(--border)",
            boxShadow: "var(--shadow)",
          }}
        >
          <p style={{ margin: 0, color: "var(--muted)" }}>{task.task_run_id}</p>
          <h1 style={{ margin: 0 }}>Trace Viewer</h1>
          <p style={{ margin: 0 }}>
            Run {task.run_id} · dataset item {task.dataset_item_id} · classification{" "}
            {task.failure_reason ?? "success"}
          </p>
        </section>

        <TaskTraceViewer task={task} trace={trace} />
        <ReviewEditor task={task} />
        <FailedCasePromoter
          taskRunId={task.task_run_id}
          datasetItemId={task.dataset_item_id}
          review={task.review}
        />
      </main>
    );
  } catch (error) {
    if (error instanceof BackendApiError && error.status === 404) {
      notFound();
    }
    throw error;
  }
}
