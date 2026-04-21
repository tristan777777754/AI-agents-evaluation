import { BackendApiError, getBackendBaseUrl } from "./datasets";

export type CalibrationCategory = {
  category: string;
  total_cases: number;
  labelled_pass_cases: number;
  predicted_pass_cases: number;
  correct_cases: number;
  accuracy: number;
};

export type CalibrationDisagreement = {
  dataset_item_id: string;
  category: string;
  expected_verdict: string;
  predicted_verdict: string;
  expected_failure_reason: string | null;
  predicted_failure_reason: string | null;
  correctness: number | null;
};

export type CalibrationReport = {
  fixture_id: string;
  scorer_config_id: string;
  generated_at: string;
  total_cases: number;
  labelled_pass_cases: number;
  labelled_fail_cases: number;
  predicted_pass_cases: number;
  predicted_fail_cases: number;
  true_positive_count: number;
  false_positive_count: number;
  true_negative_count: number;
  false_negative_count: number;
  precision: number;
  recall: number;
  accuracy: number;
  per_category: CalibrationCategory[];
  disagreements: CalibrationDisagreement[];
};

export async function getLatestCalibrationReport(): Promise<CalibrationReport> {
  const response = await fetch(`${getBackendBaseUrl()}/api/v1/calibration/latest`, {
    cache: "no-store",
  });

  if (response.ok) {
    return (await response.json()) as CalibrationReport;
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
