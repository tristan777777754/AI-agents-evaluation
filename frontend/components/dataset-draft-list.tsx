"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { approveDatasetDraft, type DatasetDraftList } from "@/lib/datasets";

type DatasetDraftListProps = {
  drafts: DatasetDraftList | null;
  loadError?: string | null;
};

const panelStyle = {
  display: "grid",
  gap: "1rem",
  padding: "1.5rem",
  borderRadius: "24px",
  border: "1px solid var(--border)",
  background: "var(--panel)",
  boxShadow: "var(--shadow)",
} as const;

export function DatasetDraftList({ drafts, loadError = null }: DatasetDraftListProps) {
  const router = useRouter();
  const [reviewerId, setReviewerId] = useState("reviewer_demo");
  const [busyId, setBusyId] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  async function handleApprove(datasetId: string) {
    setBusyId(datasetId);
    setErrorMessage(null);
    try {
      await approveDatasetDraft(datasetId, {
        reviewer_id: reviewerId,
        note: "Phase 13 draft approved for runnable snapshot use.",
      });
      router.refresh();
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Approval failed.");
    } finally {
      setBusyId(null);
    }
  }

  if (loadError) {
    return (
      <section style={panelStyle}>
        <strong>Dataset drafts unavailable</strong>
        <p style={{ margin: 0 }}>{loadError}</p>
      </section>
    );
  }

  return (
    <section style={panelStyle}>
      <div>
        <p style={{ margin: 0, color: "var(--muted)", letterSpacing: "0.08em", textTransform: "uppercase" }}>
          Draft Review
        </p>
        <h2 style={{ margin: "0.35rem 0 0" }}>
          {drafts?.total_count ?? 0} dataset drafts awaiting approval
        </h2>
      </div>

      <label style={{ display: "grid", gap: "0.35rem", maxWidth: "18rem" }}>
        <span>Reviewer id</span>
        <input value={reviewerId} onChange={(event) => setReviewerId(event.target.value)} />
      </label>

      {!drafts || drafts.items.length === 0 ? (
        <p style={{ margin: 0, color: "var(--muted)" }}>
          Generated drafts stay out of runnable selectors until approved.
        </p>
      ) : (
        <div style={{ display: "grid", gap: "0.75rem" }}>
          {drafts.items.map((draft) => (
            <div
              key={draft.dataset_id}
              style={{
                display: "grid",
                gap: "0.35rem",
                padding: "0.9rem 1rem",
                borderRadius: "16px",
                border: "1px solid var(--border)",
                background: "rgba(255,255,255,0.72)",
              }}
            >
              <strong>{draft.name}</strong>
              <span>
                {draft.dataset_id} · {draft.item_count} items · {draft.source_origin}
              </span>
              <span style={{ color: "var(--muted)" }}>
                {draft.generated_prompt ?? draft.description ?? "No draft prompt recorded."}
              </span>
              <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap" }}>
                <button
                  type="button"
                  onClick={() => handleApprove(draft.dataset_id)}
                  disabled={busyId === draft.dataset_id || !reviewerId.trim()}
                >
                  {busyId === draft.dataset_id ? "Approving..." : "Approve draft"}
                </button>
                <Link href={`/datasets/${draft.dataset_id}`} style={{ color: "var(--accent)" }}>
                  Inspect draft
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}

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
    </section>
  );
}
