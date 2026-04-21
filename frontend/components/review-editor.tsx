"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import type { ReviewDetail, TaskRunDetail } from "@/lib/runs";
import { upsertTaskReview } from "@/lib/runs";

type ReviewEditorProps = {
  task: TaskRunDetail;
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

function initialReviewerId(review: ReviewDetail | null): string {
  return review?.reviewer_id ?? "reviewer_demo";
}

export function ReviewEditor({ task }: ReviewEditorProps) {
  const router = useRouter();
  const [submitting, setSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [savedMessage, setSavedMessage] = useState<string | null>(null);

  async function handleSubmit(formData: FormData) {
    setSubmitting(true);
    setErrorMessage(null);
    setSavedMessage(null);

    try {
      await upsertTaskReview(task.task_run_id, {
        reviewer_id: String(formData.get("reviewer_id") ?? ""),
        verdict: String(formData.get("verdict") ?? "") || null,
        failure_label: String(formData.get("failure_label") ?? "") || null,
        note: String(formData.get("note") ?? "") || null,
      });
      setSavedMessage("Review saved.");
      router.refresh();
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Review could not be saved.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form action={handleSubmit} style={panelStyle}>
      <div>
        <p style={{ margin: 0, color: "var(--muted)", letterSpacing: "0.08em", textTransform: "uppercase" }}>
          Review Verdict
        </p>
        <h2 style={{ margin: "0.35rem 0 0" }}>
          {task.review ? "Update persisted review" : "Record reviewer decision"}
        </h2>
      </div>

      <label style={{ display: "grid", gap: "0.35rem" }}>
        <span>Reviewer ID</span>
        <input
          name="reviewer_id"
          type="text"
          required
          defaultValue={initialReviewerId(task.review)}
        />
      </label>

      <label style={{ display: "grid", gap: "0.35rem" }}>
        <span>Verdict</span>
        <select name="verdict" defaultValue={task.review?.verdict ?? ""}>
          <option value="">No verdict yet</option>
          <option value="confirmed_issue">Confirmed issue</option>
          <option value="acceptable_risk">Acceptable risk</option>
          <option value="needs_follow_up">Needs follow-up</option>
        </select>
      </label>

      <label style={{ display: "grid", gap: "0.35rem" }}>
        <span>Failure label</span>
        <input
          name="failure_label"
          type="text"
          defaultValue={task.review?.failure_label ?? task.failure_reason ?? ""}
          placeholder="Optional override or normalized label"
        />
      </label>

      <label style={{ display: "grid", gap: "0.35rem" }}>
        <span>Reviewer note</span>
        <textarea
          name="note"
          rows={5}
          defaultValue={task.review?.note ?? ""}
          placeholder="Add a concise reviewer decision or follow-up note."
        />
      </label>

      <button type="submit" disabled={submitting} style={{ width: "fit-content" }}>
        {submitting ? "Saving..." : "Save review"}
      </button>

      {savedMessage ? <p style={{ margin: 0, color: "rgb(34, 113, 74)" }}>{savedMessage}</p> : null}
      {errorMessage ? <p style={{ margin: 0, color: "rgb(174, 63, 19)" }}>{errorMessage}</p> : null}
    </form>
  );
}
