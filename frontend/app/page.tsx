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
import { WorkbenchTabs } from "@/components/workbench-tabs";
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

function StatusBadge({
  label,
  value,
  tone = "neutral",
}: {
  label: string;
  value: string | number;
  tone?: "neutral" | "ready" | "attention";
}) {
  return (
    <article className={`status-card status-card--${tone}`}>
      <span>{label}</span>
      <strong>{value}</strong>
    </article>
  );
}

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
    <main className="home-shell">
      <section className="hero-panel">
        <div className="hero-copy">
          <p className="eyebrow">Agent Quality Engineering</p>
          <h1>Evaluate an agent version against real datasets</h1>
          <p>
            Import a dataset, run a persisted evaluation, inspect traces, compare versions, and
            send uncertain cases to review.
          </p>
        </div>

        <div className="hero-actions" aria-label="Primary workbench actions">
          <span>Start by defining an agent version, then run it against a dataset.</span>
        </div>
      </section>

      <section className="workflow-panel" aria-labelledby="workflow-heading">
        <div className="section-heading">
          <p className="eyebrow">Start Here</p>
          <h2 id="workflow-heading">The evaluation path</h2>
        </div>
        <div className="workflow-steps">
          <a href="#datasets" className="workflow-step">
            <span>1</span>
            <strong>Import dataset</strong>
            <small>Validated JSON or CSV items become persisted dataset records.</small>
          </a>
          <a href="#launch-run" className="workflow-step">
            <span>2</span>
            <strong>Launch run</strong>
            <small>Select an agent version, scorer, adapter mode, and optional sampling.</small>
          </a>
          <a href="#results" className="workflow-step">
            <span>3</span>
            <strong>Inspect outcome</strong>
            <small>Open task results, traces, dashboard metrics, compare, and review queue.</small>
          </a>
        </div>
      </section>

      <section className="status-grid" aria-label="Current workspace status">
        <StatusBadge label="Datasets" value={datasetLoadError ? "Unavailable" : datasets.length} />
        <StatusBadge label="Runs" value={datasetLoadError ? "Unavailable" : runPage.total_count} />
        <StatusBadge
          label="Agent versions"
          value={datasetLoadError ? "Unavailable" : registry.agent_versions.length}
        />
        <StatusBadge
          label="Review pending"
          value={reviewQueueLoadError ? "Unavailable" : reviewQueue?.pending_count ?? 0}
          tone={(reviewQueue?.pending_count ?? 0) > 0 ? "attention" : "ready"}
        />
      </section>

      <WorkbenchTabs
        registryPanel={
          !datasetLoadError ? <RegistryManager datasets={datasets} registry={registry} /> : null
        }
        datasetsPanel={
          <div className="two-column">
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
              <DatasetList datasets={datasets} />
            )}
          </div>
        }
        launchPanel={
          !datasetLoadError ? <RunLauncherForm datasets={datasets} registry={registry} /> : null
        }
        resultsPanel={
          <div className="section-stack">
            <RunDashboard summary={dashboardSummary} loadError={dashboardLoadError} />
            {!datasetLoadError ? (
              <RunList
                runPage={runPage}
                registry={registry}
                filters={{ status: runsStatus, agent_version_id: runsAgentVersionId }}
              />
            ) : null}
          </div>
        }
        comparePanel={
          <div className="two-column">
            <CompareLauncherForm runs={runPage.items} />
            <ReviewQueuePanel queue={reviewQueue} loadError={reviewQueueLoadError} />
          </div>
        }
        draftsPanel={
          <div className="two-column">
            <DatasetDraftGenerator />
            <DatasetDraftList drafts={datasetDrafts} loadError={datasetDraftLoadError} />
          </div>
        }
        governancePanel={
          <div className="two-column">
            <CalibrationPanel report={calibrationReport} loadError={calibrationLoadError} />
            <ContractSummary contract={contractSnapshot} backendBaseUrl={backendBaseUrl} />
          </div>
        }
      />
    </main>
  );
}
