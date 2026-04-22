"use client";

import Link from "next/link";
import { useState } from "react";

import type { ReviewDetail } from "@/lib/runs";
import { promoteTaskRunToDataset } from "@/lib/datasets";

type FailedCasePromoterProps = {
  taskRunId: string;
  datasetItemId: string;
  review: ReviewDetail | null;
};

const panelStyle = {
  display: "grid",
  gap: "0.9rem",
  padding: "1.5rem",
  borderRadius: "24px",
  border: "1px solid var(--border)",
  background: "var(--panel)",
  boxShadow: "var(--shadow)",
} as const;

export function FailedCasePromoter({ taskRunId, datasetItemId, review }: FailedCasePromoterProps) {
  const [submitting, setSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [promotedPath, setPromotedPath] = useState<{ datasetId: string; snapshotId: string } | null>(null);

  async function handleSubmit(formData: FormData) {
    setSubmitting(true);
    setErrorMessage(null);
    setPromotedPath(null);

    const targetDatasetId = String(formData.get("target_dataset_id") ?? "").trim();
    const targetDatasetName = String(formData.get("target_dataset_name") ?? "").trim();
    const tags = String(formData.get("tags") ?? "")
      .split(",")
      .map((tag) => tag.trim().toLowerCase())
      .filter(Boolean);

    try {
      const promoted = await promoteTaskRunToDataset(taskRunId, {
        target_dataset_id: targetDatasetId || null,
        target_dataset_name: targetDatasetName || null,
        tags,
      });
      setPromotedPath({
        datasetId: promoted.dataset.dataset_id,
        snapshotId: promoted.snapshot_id,
      });
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Promotion failed.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form action={handleSubmit} style={panelStyle}>
      <div>
        <p style={{ margin: 0, color: "var(--muted)", letterSpacing: "0.08em", textTransform: "uppercase" }}>
          Regression Promotion
        </p>
        <h2 style={{ margin: "0.35rem 0 0" }}>Promote failed case</h2>
      </div>

      <p style={{ margin: 0, color: "var(--muted)" }}>
        Dataset item {datasetItemId} can be promoted once it has a persisted reviewer verdict.
      </p>

      <label style={{ display: "grid", gap: "0.35rem" }}>
        <span>Target dataset id</span>
        <input
          name="target_dataset_id"
          type="text"
          defaultValue="dataset_regression_promoted"
          disabled={submitting || !review?.verdict}
        />
      </label>

      <label style={{ display: "grid", gap: "0.35rem" }}>
        <span>Target dataset name</span>
        <input
          name="target_dataset_name"
          type="text"
          defaultValue="Promoted Regression Dataset"
          disabled={submitting || !review?.verdict}
        />
      </label>

      <label style={{ display: "grid", gap: "0.35rem" }}>
        <span>Extra tags</span>
        <input name="tags" type="text" placeholder="refunds, escalation" disabled={submitting || !review?.verdict} />
      </label>

      <button type="submit" disabled={submitting || !review?.verdict}>
        {submitting ? "Promoting..." : "Promote to dataset"}
      </button>

      {!review?.verdict ? (
        <p style={{ margin: 0, color: "var(--muted)" }}>
          Add a reviewer verdict first. Promotion preserves lineage back to the reviewed task run.
        </p>
      ) : null}

      {promotedPath ? (
        <div
          style={{
            display: "grid",
            gap: "0.35rem",
            padding: "0.9rem 1rem",
            borderRadius: "16px",
            border: "1px solid rgba(34, 110, 82, 0.2)",
            background: "rgba(34, 110, 82, 0.08)",
          }}
        >
          <strong>Promotion completed</strong>
          <span>
            {promotedPath.datasetId} · snapshot {promotedPath.snapshotId}
          </span>
          <Link href={`/datasets/${promotedPath.datasetId}`} style={{ color: "var(--accent)" }}>
            Open promoted dataset
          </Link>
        </div>
      ) : null}

      {errorMessage ? (
        <div
          style={{
            padding: "0.9rem 1rem",
            borderRadius: "16px",
            border: "1px solid rgba(174, 63, 19, 0.2)",
            background: "rgba(174, 63, 19, 0.08)",
          }}
        >
          {errorMessage}
        </div>
      ) : null}
    </form>
  );
}
