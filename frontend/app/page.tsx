import { CalibrationPanel } from "@/components/calibration-panel";
import { CompareLauncherForm } from "@/components/compare-launcher-form";
import { ContractSummary } from "@/components/contract-summary";
import { DatasetDraftGenerator } from "@/components/dataset-draft-generator";
import { DatasetDraftList } from "@/components/dataset-draft-list";
import { DatasetList } from "@/components/dataset-list";
import { DatasetUploadForm } from "@/components/dataset-upload-form";
import { RegistryManager } from "@/components/registry-manager";
import { ReviewQueuePanel } from "@/components/review-queue-panel";
import { RunDashboard } from "@/components/run-dashboard";
import { RunLauncherForm } from "@/components/run-launcher-form";
import { RunList } from "@/components/run-list";
import { getLatestCalibrationReport, type CalibrationReport } from "@/lib/calibration";
import { getContractSnapshot, phase1ContractPreview } from "@/lib/contracts";
import {
  listDatasetDrafts,
  listDatasets,
  type DatasetDraftList as DatasetDraftListType,
  type DatasetSummary,
} from "@/lib/datasets";
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

type HomePageProps = {
  searchParams: Promise<{
    runs_page?: string;
    runs_status?: string;
    runs_agent_version_id?: string;
  }>;
};

export default async function HomePage({ searchParams }: HomePageProps) {
  const resolvedSearchParams = await searchParams;
  const runsPageNumber = Number(resolvedSearchParams.runs_page ?? "1") || 1;
  const runsStatus = resolvedSearchParams.runs_status?.trim() || undefined;
  const runsAgentVersionId =
    resolvedSearchParams.runs_agent_version_id?.trim() || undefined;
  let datasets: DatasetSummary[] = [];
  let runPage = {
    items: [] as RunSummary[],
    total_count: 0,
    page: runsPageNumber,
    per_page: 10,
    has_next_page: false,
  };
  let registry: RegistryList = {
    agents: [],
    agent_versions: [],
    scorer_configs: [],
    defaults: {
      default_dataset_id: null,
      default_scorer_config_id: null,
    },
  };
  let datasetLoadError: string | null = null;
  let dashboardSummary: RunDashboardSummary | null = null;
  let dashboardLoadError: string | null = null;
  let reviewQueue: ReviewQueue | null = null;
  let reviewQueueLoadError: string | null = null;
  let datasetDrafts: DatasetDraftListType | null = null;
  let datasetDraftLoadError: string | null = null;
  let calibrationReport: CalibrationReport | null = null;
  let calibrationLoadError: string | null = null;
  let contractSnapshot = phase1ContractPreview;

  try {
    [datasets, runPage, registry] = await Promise.all([
      listDatasets(),
      listRuns({
        page: runsPageNumber,
        per_page: 10,
        status: runsStatus,
        agent_version_id: runsAgentVersionId,
      }),
      getRegistry(),
    ]);
  } catch (error) {
    datasetLoadError =
      error instanceof Error ? error.message : "Workbench data could not be loaded.";
  }

  try {
    reviewQueue = await getReviewQueue({ page: 1, per_page: 4 });
  } catch (error) {
    reviewQueueLoadError =
      error instanceof Error ? error.message : "Review queue could not be loaded.";
  }

  try {
    datasetDrafts = await listDatasetDrafts();
  } catch (error) {
    datasetDraftLoadError =
      error instanceof Error ? error.message : "Dataset drafts could not be loaded.";
  }

  try {
    calibrationReport = await getLatestCalibrationReport();
  } catch (error) {
    calibrationLoadError =
      error instanceof Error ? error.message : "Calibration metrics could not be loaded.";
  }

  try {
    contractSnapshot = await getContractSnapshot();
  } catch {
    contractSnapshot = phase1ContractPreview;
  }

  if (!datasetLoadError && runPage.items.length > 0) {
    try {
      dashboardSummary = await getRunDashboardSummary(runPage.items[0].run_id);
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
          Phase 16 formalizes generator, agent, and judge governance so teams can audit who scored
          what, reject risky self-judge setups, and inspect cross-judge consistency without
          changing the existing compare path.
        </p>
      </section>

      <ContractSummary contract={contractSnapshot} backendBaseUrl={backendBaseUrl} />

      <CalibrationPanel report={calibrationReport} loadError={calibrationLoadError} />

      <RunDashboard summary={dashboardSummary} loadError={dashboardLoadError} />

      <section
        style={{
          display: "grid",
          gap: "1.5rem",
          gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
          alignItems: "start",
        }}
      >
        <CompareLauncherForm runs={runPage.items} />
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

      {!datasetLoadError ? <RegistryManager datasets={datasets} registry={registry} /> : null}

      <section
        style={{
          display: "grid",
          gap: "1.5rem",
          gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
          alignItems: "start",
        }}
      >
        <DatasetDraftGenerator />
        <DatasetDraftList drafts={datasetDrafts} loadError={datasetDraftLoadError} />
      </section>

      {!datasetLoadError ? (
        <RunList
          runPage={runPage}
          registry={registry}
          filters={{ status: runsStatus, agent_version_id: runsAgentVersionId }}
        />
      ) : null}
    </main>
  );
}
