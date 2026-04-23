import Link from "next/link";
import { notFound } from "next/navigation";

import { RunDetailLive } from "@/components/run-detail-live";
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

        <RunDetailLive initialRun={run} initialTasks={runTasks} />
      </main>
    );
  } catch (error) {
    if (error instanceof BackendApiError && error.status === 404) {
      notFound();
    }
    throw error;
  }
}
