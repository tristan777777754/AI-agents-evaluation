import { CompareLauncherForm } from "@/components/compare-launcher-form";
import { ContractSummary } from "@/components/contract-summary";
import { DatasetList } from "@/components/dataset-list";
import { DatasetUploadForm } from "@/components/dataset-upload-form";
import { ReviewQueuePanel } from "@/components/review-queue-panel";
import { RunDashboard } from "@/components/run-dashboard";
import { RunLauncherForm } from "@/components/run-launcher-form";
import { RunList } from "@/components/run-list";
import { phase1ContractPreview } from "@/lib/contracts";
import { listDatasets, type DatasetSummary } from "@/lib/datasets";
import {
  getRegistry,
  getReviewQueue,
  getRunDashboardSummary,
  listRuns,
  type RegistryList,
  type ReviewQueue,
  type RunDashboardSummary,
  type RunSummary,
} from "@/lib/runs";

const backendBaseUrl = process.env.NEXT_PUBLIC_BACKEND_BASE_URL ?? "http://localhost:8000";

export default async function HomePage() {
  let datasets: DatasetSummary[] = [];
  let runs: RunSummary[] = [];
  let registry: RegistryList = { agent_versions: [], scorer_configs: [] };
  let datasetLoadError: string | null = null;
  let dashboardSummary: RunDashboardSummary | null = null;
  let dashboardLoadError: string | null = null;
  let reviewQueue: ReviewQueue | null = null;
  let reviewQueueLoadError: string | null = null;

  try {
    [datasets, runs, registry] = await Promise.all([listDatasets(), listRuns(), getRegistry()]);
  } catch (error) {
    datasetLoadError =
      error instanceof Error ? error.message : "Workbench data could not be loaded.";
  }

  try {
    reviewQueue = await getReviewQueue();
  } catch (error) {
    reviewQueueLoadError =
      error instanceof Error ? error.message : "Review queue could not be loaded.";
  }

  if (!datasetLoadError && runs.length > 0) {
    try {
      dashboardSummary = await getRunDashboardSummary(runs[0].run_id);
    } catch (error) {
      dashboardLoadError =
        error instanceof Error ? error.message : "Dashboard metrics could not be loaded.";
    }
  }

  return (
    <main
      style={{
        padding: "3rem 1.5rem 4rem",
        display: "grid",
        gap: "2rem",
        maxWidth: "1120px",
        margin: "0 auto",
      }}
    >
      <section
        style={{
          display: "grid",
          gap: "1rem",
          padding: "2rem",
          borderRadius: "28px",
          background:
            "linear-gradient(135deg, rgba(255,250,245,0.94), rgba(255,239,222,0.9))",
          border: "1px solid var(--border)",
          boxShadow: "var(--shadow)",
        }}
      >
        <p
          style={{
            margin: 0,
            color: "var(--accent)",
            letterSpacing: "0.12em",
            textTransform: "uppercase",
          }}
        >
          Agent Quality Engineering
        </p>
        <h1 style={{ margin: 0, fontSize: "clamp(2.4rem, 6vw, 5rem)", lineHeight: 0.95 }}>
          Agent Evaluation Workbench
        </h1>
        <p style={{ margin: 0, maxWidth: "48rem", fontSize: "1.1rem", lineHeight: 1.6 }}>
          Phase 6 adds run comparison and persisted reviewer verdicts on top of the existing
          dashboard: compare two real runs, inspect regressions, and route flagged cases into a
          review queue without fake data.
        </p>
      </section>

      <ContractSummary contract={phase1ContractPreview} backendBaseUrl={backendBaseUrl} />

      <RunDashboard summary={dashboardSummary} loadError={dashboardLoadError} />

      <section
        style={{
          display: "grid",
          gap: "1.5rem",
          gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
          alignItems: "start",
        }}
      >
        <CompareLauncherForm runs={runs} />
        <ReviewQueuePanel queue={reviewQueue} loadError={reviewQueueLoadError} />
      </section>

      <section
        style={{
          display: "grid",
          gap: "1.5rem",
          gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
          alignItems: "start",
        }}
      >
        <DatasetUploadForm />
        {datasetLoadError ? (
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
            <strong>Dataset list unavailable</strong>
            <p style={{ margin: 0 }}>{datasetLoadError}</p>
          </section>
        ) : (
          <>
            <DatasetList datasets={datasets} />
            <RunLauncherForm datasets={datasets} registry={registry} />
          </>
        )}
      </section>

      {!datasetLoadError ? <RunList runs={runs} /> : null}
    </main>
  );
}
