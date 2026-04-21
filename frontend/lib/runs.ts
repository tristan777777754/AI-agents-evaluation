import type {
  RegistryList,
  ReviewDetail,
  ReviewQueue,
  ReviewUpsertRequest,
  RunComparison,
  RunDashboardSummary,
  RunCreateRequest,
  RunDetail,
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

export async function listRuns(): Promise<RunSummary[]> {
  const response = await fetch(`${getBackendBaseUrl()}/api/v1/runs`, {
    cache: "no-store",
  });
  return parseResponse<RunSummary[]>(response);
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

export async function getReviewQueue(): Promise<ReviewQueue> {
  const response = await fetch(`${getBackendBaseUrl()}/api/v1/reviews/queue`, {
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
  RegistryList,
  RunDashboardSummary,
  ReviewDetail,
  ReviewQueue,
  RunComparison,
  RunDetail,
  RunSummary,
  RunTaskList,
  TaskRunDetail,
  TraceDetail,
};
