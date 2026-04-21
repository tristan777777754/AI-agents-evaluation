import type {
  DatasetDetail,
  DatasetDiff,
  DatasetImportError,
  DatasetItemList,
  DatasetSnapshotList,
  DatasetSummary,
  DatasetUploadResult,
} from "../../shared/types";

const backendBaseUrl =
  process.env.NEXT_PUBLIC_BACKEND_BASE_URL ?? "http://localhost:8000";

export class BackendApiError extends Error {
  status: number;
  detail: unknown;

  constructor(message: string, status: number, detail: unknown) {
    super(message);
    this.name = "BackendApiError";
    this.status = status;
    this.detail = detail;
  }
}

export function getBackendBaseUrl(): string {
  return backendBaseUrl;
}

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

export async function listDatasets(): Promise<DatasetSummary[]> {
  const response = await fetch(`${backendBaseUrl}/api/v1/datasets`, {
    cache: "no-store",
  });
  return parseResponse<DatasetSummary[]>(response);
}

export async function getDatasetDetail(
  datasetId: string,
  snapshotId?: string,
): Promise<DatasetDetail> {
  const params = snapshotId ? `?snapshot_id=${encodeURIComponent(snapshotId)}` : "";
  const response = await fetch(`${backendBaseUrl}/api/v1/datasets/${datasetId}${params}`, {
    cache: "no-store",
  });
  return parseResponse<DatasetDetail>(response);
}

export async function getDatasetItems(
  datasetId: string,
  snapshotId?: string,
): Promise<DatasetItemList> {
  const params = snapshotId ? `?snapshot_id=${encodeURIComponent(snapshotId)}` : "";
  const response = await fetch(`${backendBaseUrl}/api/v1/datasets/${datasetId}/items${params}`, {
    cache: "no-store",
  });
  return parseResponse<DatasetItemList>(response);
}

export async function getDatasetSnapshots(datasetId: string): Promise<DatasetSnapshotList> {
  const response = await fetch(`${backendBaseUrl}/api/v1/datasets/${datasetId}/snapshots`, {
    cache: "no-store",
  });
  return parseResponse<DatasetSnapshotList>(response);
}

export async function getDatasetDiff(
  datasetId: string,
  fromSnapshotId: string,
  toSnapshotId: string,
): Promise<DatasetDiff> {
  const params = new URLSearchParams({
    from_snapshot: fromSnapshotId,
    to_snapshot: toSnapshotId,
  });
  const response = await fetch(`${backendBaseUrl}/api/v1/datasets/${datasetId}/diff?${params}`, {
    cache: "no-store",
  });
  return parseResponse<DatasetDiff>(response);
}

export function extractDatasetImportError(error: unknown): DatasetImportError | null {
  if (!(error instanceof BackendApiError)) {
    return null;
  }

  if (
    typeof error.detail === "object" &&
    error.detail !== null &&
    "message" in error.detail &&
    "errors" in error.detail
  ) {
    return error.detail as DatasetImportError;
  }

  if (
    typeof error.detail === "object" &&
    error.detail !== null &&
    "detail" in error.detail &&
    typeof error.detail.detail === "object" &&
    error.detail.detail !== null &&
    "message" in error.detail.detail &&
    "errors" in error.detail.detail
  ) {
    return error.detail.detail as DatasetImportError;
  }

  return null;
}

export function formatDatasetImportError(error: DatasetImportError): string[] {
  return error.errors.map((entry) => {
    const rowPrefix = entry.row_number ? `Row ${entry.row_number}` : "Upload";
    const fieldPrefix = entry.field ? `${entry.field}: ` : "";
    return `${rowPrefix} - ${fieldPrefix}${entry.message}`;
  });
}

export type {
  DatasetDetail,
  DatasetDiff,
  DatasetItemList,
  DatasetSnapshotList,
  DatasetSummary,
  DatasetUploadResult,
};
