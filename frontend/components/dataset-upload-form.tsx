"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import {
  BackendApiError,
  extractDatasetImportError,
  formatDatasetImportError,
  getBackendBaseUrl,
  type DatasetUploadResult,
} from "@/lib/datasets";

const panelStyle = {
  display: "grid",
  gap: "0.9rem",
  padding: "1.5rem",
  borderRadius: "24px",
  border: "1px solid var(--border)",
  background: "var(--panel)",
  boxShadow: "var(--shadow)",
} as const;

export function DatasetUploadForm() {
  const router = useRouter();
  const [submitting, setSubmitting] = useState(false);
  const [errorMessages, setErrorMessages] = useState<string[]>([]);

  async function handleSubmit(formData: FormData) {
    setSubmitting(true);
    setErrorMessages([]);

    try {
      const response = await fetch(`${getBackendBaseUrl()}/api/v1/datasets`, {
        method: "POST",
        body: formData,
      });
      const body = (await response.json()) as DatasetUploadResult | { detail?: unknown };

      if (!response.ok) {
        throw new BackendApiError(
          `Upload failed with status ${response.status}.`,
          response.status,
          body,
        );
      }

      const uploadResult = body as DatasetUploadResult;
      router.push(`/datasets/${uploadResult.dataset.dataset_id}`);
      router.refresh();
    } catch (error) {
      const importError = extractDatasetImportError(error);
      if (importError) {
        setErrorMessages(formatDatasetImportError(importError));
      } else if (error instanceof Error) {
        setErrorMessages([error.message]);
      } else {
        setErrorMessages(["Dataset upload failed for an unknown reason."]);
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form
      action={handleSubmit}
      style={panelStyle}
    >
      <div>
        <p style={{ margin: 0, color: "var(--muted)", letterSpacing: "0.08em", textTransform: "uppercase" }}>
          Upload Dataset
        </p>
        <h2 style={{ margin: "0.35rem 0 0" }}>JSON or CSV import</h2>
      </div>

      <label style={{ display: "grid", gap: "0.35rem" }}>
        <span>Name override</span>
        <input name="name" type="text" placeholder="Optional for JSON, helpful for CSV" />
      </label>

      <label style={{ display: "grid", gap: "0.35rem" }}>
        <span>Dataset ID override</span>
        <input name="dataset_id" type="text" placeholder="Optional stable id" />
      </label>

      <label style={{ display: "grid", gap: "0.35rem" }}>
        <span>Description override</span>
        <textarea name="description" rows={3} placeholder="Optional dataset description" />
      </label>

      <label style={{ display: "grid", gap: "0.35rem" }}>
        <span>Dataset file</span>
        <input name="file" type="file" accept=".json,.csv" required />
      </label>

      <button type="submit" disabled={submitting} style={{ width: "fit-content" }}>
        {submitting ? "Uploading..." : "Upload dataset"}
      </button>

      {errorMessages.length > 0 ? (
        <div
          style={{
            display: "grid",
            gap: "0.5rem",
            padding: "1rem",
            borderRadius: "16px",
            background: "rgba(174, 63, 19, 0.08)",
            border: "1px solid rgba(174, 63, 19, 0.2)",
          }}
        >
          <strong>Import failed</strong>
          <ul style={{ margin: 0, paddingLeft: "1.25rem" }}>
            {errorMessages.map((message) => (
              <li key={message}>{message}</li>
            ))}
          </ul>
        </div>
      ) : null}
    </form>
  );
}
