import Link from "next/link";
import { notFound } from "next/navigation";

import { RunTaskTable } from "@/components/run-task-table";
import { BackendApiError } from "@/lib/datasets";
import { getRunDetail, getRunTasks } from "@/lib/runs";

type RunDetailPageProps = {
  params: Promise<{ runId: string }>;
};

export default async function RunDetailPage({ params }: RunDetailPageProps) {
  const { runId } = await params;

  try {
    const [run, runTasks] = await Promise.all([getRunDetail(runId), getRunTasks(runId)]);

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
        <Link href="/" style={{ color: "var(--accent)" }}>
          Back to workbench
        </Link>

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
          <p style={{ margin: 0, color: "var(--muted)" }}>{run.run_id}</p>
          <h1 style={{ margin: 0 }}>Run status: {run.status}</h1>
          <p style={{ margin: 0 }}>
            Dataset {run.dataset_id} · Agent {run.agent_version.version_name} · Scorer{" "}
            {run.scorer_config.name}
          </p>
          <p style={{ margin: 0 }}>
            {run.completed_tasks}/{run.total_tasks} completed · {run.failed_tasks} failed · adapter{" "}
            {run.adapter_type}
          </p>
          <p style={{ margin: 0, color: "var(--muted)" }}>
            Snapshot {run.dataset_snapshot_id ?? "n/a"} · {run.baseline ? "Baseline run" : "Candidate run"}
            {run.experiment_tag ? ` · Experiment ${run.experiment_tag}` : ""}
          </p>
          {run.notes ? <p style={{ margin: 0, color: "var(--muted)" }}>{run.notes}</p> : null}
        </section>

        <RunTaskTable runTasks={runTasks} />
      </main>
    );
  } catch (error) {
    if (error instanceof BackendApiError && error.status === 404) {
      notFound();
    }
    throw error;
  }
}
