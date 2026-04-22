import Link from "next/link";

import { RunCompareView } from "@/components/run-compare-view";
import { BackendApiError } from "@/lib/datasets";
import { getRunComparison, getTraceComparison } from "@/lib/runs";

type ComparePageProps = {
  searchParams: Promise<{
    baseline_run_id?: string;
    candidate_run_id?: string;
    dataset_item_id?: string;
  }>;
};

export default async function ComparePage({ searchParams }: ComparePageProps) {
  const {
    baseline_run_id: baselineRunId,
    candidate_run_id: candidateRunId,
    dataset_item_id: requestedDatasetItemId,
  } = await searchParams;

  if (!baselineRunId || !candidateRunId) {
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
            border: "1px solid var(--border)",
            background: "var(--panel)",
            boxShadow: "var(--shadow)",
          }}
        >
          <h1 style={{ margin: 0 }}>Select two runs to compare</h1>
          <p style={{ margin: 0, color: "var(--muted)" }}>
            Open this page from the homepage compare launcher with a baseline and candidate run.
          </p>
        </section>
      </main>
    );
  }

  try {
    const comparison = await getRunComparison(baselineRunId, candidateRunId);
    const selectedDatasetItemId =
      requestedDatasetItemId ??
      comparison.regressions[0]?.dataset_item_id ??
      comparison.improvements[0]?.dataset_item_id ??
      null;
    const traceComparison = selectedDatasetItemId
      ? await getTraceComparison(baselineRunId, candidateRunId, selectedDatasetItemId)
      : null;

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
        <RunCompareView
          comparison={comparison}
          selectedDatasetItemId={selectedDatasetItemId}
          traceComparison={traceComparison}
        />
      </main>
    );
  } catch (error) {
    const message =
      error instanceof BackendApiError || error instanceof Error
        ? error.message
        : "Comparison could not be loaded.";

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
            border: "1px solid rgba(174, 63, 19, 0.2)",
            background: "rgba(174, 63, 19, 0.08)",
          }}
        >
          <h1 style={{ margin: 0 }}>Comparison unavailable</h1>
          <p style={{ margin: 0 }}>{message}</p>
        </section>
      </main>
    );
  }
}
