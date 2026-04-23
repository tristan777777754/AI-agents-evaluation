import type {
  AgentCreateRequest,
  AgentVersionCreateRequest,
  AutoCompare,
  RegistryList,
  RegistryDefaults,
  RegistryDefaultsUpdateRequest,
  ReviewDetail,
  ReviewQueue,
  ReviewUpsertRequest,
  QuickRunRequest,
  QuickRunResponse,
  RunComparison,
  TraceComparison,
  RunDashboardSummary,
  RunCreateRequest,
  RunDetail,
  RunListPage,
  SampledRunCreateRequest,
  SampledRunCreateResponse,
  RunSummary,
  RunTaskList,
  TaskRunDetail,
  TraceDetail,
} from "../../shared/types";
import { BackendApiError, getBackendBaseUrl } from "./datasets";

async function parseResponse<T>(response: Response): Promise<T> {
  if (response.ok) {
    return (await response.json()) as T;
  }

  let detail: unknown = null;
  try {
    detail = await response.json();
  } catch {
    detail = await response.text();
  }

  throw new BackendApiError(
    `Backend request failed with status ${response.status}.`,
    response.status,
    detail,
  );
}

export async function getRegistry(): Promise<RegistryList> {
  const response = await fetch(`${getBackendBaseUrl()}/api/v1/registry`, {
    cache: "no-store",
  });
  return parseResponse<RegistryList>(response);
}

function parseRunListHeaders(response: Response, items: RunSummary[]): RunListPage {
  return {
    items,
    total_count: Number(response.headers.get("X-Total-Count") ?? items.length),
    page: Number(response.headers.get("X-Page") ?? 1),
    per_page: Number(response.headers.get("X-Per-Page") ?? (items.length || 1)),
    has_next_page: response.headers.get("X-Has-Next-Page") === "true",
  };
}

export async function createAgent(payload: AgentCreateRequest): Promise<void> {
  const response = await fetch(`${getBackendBaseUrl()}/api/v1/registry/agents`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
  await parseResponse(response);
}

export async function createAgentVersion(payload: AgentVersionCreateRequest): Promise<void> {
  const response = await fetch(`${getBackendBaseUrl()}/api/v1/registry/agent-versions`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
  await parseResponse(response);
}

export async function updateRegistryDefaults(
  payload: RegistryDefaultsUpdateRequest,
): Promise<RegistryDefaults> {
  const response = await fetch(`${getBackendBaseUrl()}/api/v1/registry/defaults`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
  return parseResponse<RegistryDefaults>(response);
}

export async function listRuns(options?: {
  page?: number;
  per_page?: number;
  status?: string;
  dataset_id?: string;
  agent_version_id?: string;
}): Promise<RunListPage> {
  const params = new URLSearchParams();
  if (options?.page) {
    params.set("page", String(options.page));
  }
  if (options?.per_page) {
    params.set("per_page", String(options.per_page));
  }
  if (options?.status) {
    params.set("status", options.status);
  }
  if (options?.dataset_id) {
    params.set("dataset_id", options.dataset_id);
  }
  if (options?.agent_version_id) {
    params.set("agent_version_id", options.agent_version_id);
  }
  const query = params.size > 0 ? `?${params.toString()}` : "";
  const response = await fetch(`${getBackendBaseUrl()}/api/v1/runs${query}`, {
    cache: "no-store",
  });
  const items = await parseResponse<RunSummary[]>(response);
  return parseRunListHeaders(response, items);
}

export async function getRunDetail(runId: string): Promise<RunDetail> {
  const response = await fetch(`${getBackendBaseUrl()}/api/v1/runs/${runId}`, {
    cache: "no-store",
  });
  return parseResponse<RunDetail>(response);
}

export async function getRunTasks(runId: string): Promise<RunTaskList> {
  const response = await fetch(`${getBackendBaseUrl()}/api/v1/runs/${runId}/tasks`, {
    cache: "no-store",
  });
  return parseResponse<RunTaskList>(response);
}

export async function createRun(payload: RunCreateRequest): Promise<RunDetail> {
  const response = await fetch(`${getBackendBaseUrl()}/api/v1/runs`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
  return parseResponse<RunDetail>(response);
}

export async function createSampledRuns(
  payload: SampledRunCreateRequest,
): Promise<SampledRunCreateResponse> {
  const response = await fetch(`${getBackendBaseUrl()}/api/v1/runs/sampling`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
  return parseResponse<SampledRunCreateResponse>(response);
}

export async function createQuickRun(payload: QuickRunRequest): Promise<QuickRunResponse> {
  const response = await fetch(`${getBackendBaseUrl()}/api/v1/runs/quick`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
  return parseResponse<QuickRunResponse>(response);
}

export async function pinRunBaseline(runId: string, baseline: boolean): Promise<RunDetail> {
  const response = await fetch(`${getBackendBaseUrl()}/api/v1/runs/${runId}/baseline`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ baseline }),
  });
  return parseResponse<RunDetail>(response);
}

export async function getTaskRunDetail(taskRunId: string): Promise<TaskRunDetail> {
  const response = await fetch(`${getBackendBaseUrl()}/api/v1/task-runs/${taskRunId}`, {
    cache: "no-store",
  });
  return parseResponse<TaskRunDetail>(response);
}

export async function getTaskTrace(taskRunId: string): Promise<TraceDetail> {
  const response = await fetch(`${getBackendBaseUrl()}/api/v1/task-runs/${taskRunId}/trace`, {
    cache: "no-store",
  });
  return parseResponse<TraceDetail>(response);
}

export async function getRunDashboardSummary(runId: string): Promise<RunDashboardSummary> {
  const response = await fetch(`${getBackendBaseUrl()}/api/v1/runs/${runId}/summary`, {
    cache: "no-store",
  });
  return parseResponse<RunDashboardSummary>(response);
}

export async function getRunComparison(
  baselineRunId: string,
  candidateRunId: string,
): Promise<RunComparison> {
  const params = new URLSearchParams({
    baseline_run_id: baselineRunId,
    candidate_run_id: candidateRunId,
  });
  const response = await fetch(`${getBackendBaseUrl()}/api/v1/runs/compare?${params.toString()}`, {
    cache: "no-store",
  });
  return parseResponse<RunComparison>(response);
}

export async function getAutoCompare(runId: string): Promise<AutoCompare> {
  const response = await fetch(`${getBackendBaseUrl()}/api/v1/runs/${runId}/auto-compare`, {
    cache: "no-store",
  });
  return parseResponse<AutoCompare>(response);
}

export async function getTraceComparison(
  baselineRunId: string,
  candidateRunId: string,
  datasetItemId: string,
): Promise<TraceComparison> {
  const params = new URLSearchParams({
    baseline: baselineRunId,
    candidate: candidateRunId,
    dataset_item_id: datasetItemId,
  });
  const response = await fetch(`${getBackendBaseUrl()}/api/v1/compare/traces?${params.toString()}`, {
    cache: "no-store",
  });
  return parseResponse<TraceComparison>(response);
}

export async function getReviewQueue(options?: {
  page?: number;
  per_page?: number;
  review_status?: string;
  failure_reason?: string;
}): Promise<ReviewQueue> {
  const params = new URLSearchParams();
  if (options?.page) {
    params.set("page", String(options.page));
  }
  if (options?.per_page) {
    params.set("per_page", String(options.per_page));
  }
  if (options?.review_status) {
    params.set("review_status", options.review_status);
  }
  if (options?.failure_reason) {
    params.set("failure_reason", options.failure_reason);
  }
  const query = params.size > 0 ? `?${params.toString()}` : "";
  const response = await fetch(`${getBackendBaseUrl()}/api/v1/reviews/queue${query}`, {
    cache: "no-store",
  });
  return parseResponse<ReviewQueue>(response);
}

export async function upsertTaskReview(
  taskRunId: string,
  payload: ReviewUpsertRequest,
): Promise<ReviewDetail> {
  const response = await fetch(`${getBackendBaseUrl()}/api/v1/task-runs/${taskRunId}/review`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
  return parseResponse<ReviewDetail>(response);
}

export type {
  AutoCompare,
  RegistryList,
  RunDashboardSummary,
  QuickRunResponse,
  ReviewDetail,
  ReviewQueue,
  RunComparison,
  TraceComparison,
  RunDetail,
  RunListPage,
  SampledRunCreateResponse,
  RunSummary,
  RunTaskList,
  TaskRunDetail,
  TraceDetail,
};
