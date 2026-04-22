"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { generateDatasetDraft, type DatasetDetail } from "@/lib/datasets";

const panelStyle = {
  display: "grid",
  gap: "0.9rem",
  padding: "1.5rem",
  borderRadius: "24px",
  border: "1px solid var(--border)",
  background: "var(--panel)",
  boxShadow: "var(--shadow)",
} as const;

export function DatasetDraftGenerator() {
  const router = useRouter();
  const [submitting, setSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [createdDraft, setCreatedDraft] = useState<DatasetDetail | null>(null);

  async function handleSubmit(formData: FormData) {
    setSubmitting(true);
    setErrorMessage(null);
    setCreatedDraft(null);

    const name = String(formData.get("name") ?? "").trim();
    const prompt = String(formData.get("prompt") ?? "").trim();
    const description = String(formData.get("description") ?? "").trim();
    const itemCount = Number(formData.get("item_count") ?? 3);
    const tags = String(formData.get("tags") ?? "")
      .split(",")
      .map((tag) => tag.trim().toLowerCase())
      .filter(Boolean);

    try {
      const draft = await generateDatasetDraft({
        name,
        prompt,
        description: description || null,
        item_count: itemCount,
        tags,
      });
      setCreatedDraft(draft);
      router.refresh();
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Draft generation failed.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form action={handleSubmit} style={panelStyle}>
      <div>
        <p style={{ margin: 0, color: "var(--muted)", letterSpacing: "0.08em", textTransform: "uppercase" }}>
          Dataset Flywheel
        </p>
        <h2 style={{ margin: "0.35rem 0 0" }}>Generate prompt-derived draft</h2>
      </div>

      <label style={{ display: "grid", gap: "0.35rem" }}>
        <span>Draft name</span>
        <input name="name" type="text" placeholder="Refund edge cases" disabled={submitting} required />
      </label>

      <label style={{ display: "grid", gap: "0.35rem" }}>
        <span>Generation prompt</span>
        <textarea
          name="prompt"
          rows={4}
          placeholder="Create support policy edge cases about refunds and billing disputes."
          disabled={submitting}
          required
        />
      </label>

      <label style={{ display: "grid", gap: "0.35rem" }}>
        <span>Description</span>
        <input
          name="description"
          type="text"
          placeholder="Draft dataset for reviewer approval before benchmark use."
          disabled={submitting}
        />
      </label>

      <div style={{ display: "grid", gap: "0.9rem", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))" }}>
        <label style={{ display: "grid", gap: "0.35rem" }}>
          <span>Item count</span>
          <input name="item_count" type="number" min={1} max={10} defaultValue={3} disabled={submitting} />
        </label>

        <label style={{ display: "grid", gap: "0.35rem" }}>
          <span>Seed tags</span>
          <input name="tags" type="text" placeholder="refunds, billing" disabled={submitting} />
        </label>
      </div>

      <button type="submit" disabled={submitting}>
        {submitting ? "Generating..." : "Create draft"}
      </button>

      {createdDraft ? (
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
          <strong>Draft created</strong>
          <span>
            {createdDraft.dataset_id} · snapshot {createdDraft.snapshot_id}
          </span>
          <Link href={`/datasets/${createdDraft.dataset_id}`} style={{ color: "var(--accent)" }}>
            Open dataset draft
          </Link>
        </div>
      ) : null}

      {errorMessage ? (
        <div
          style={{
            display: "grid",
            gap: "0.35rem",
            padding: "0.9rem 1rem",
            borderRadius: "16px",
            border: "1px solid rgba(174, 63, 19, 0.2)",
            background: "rgba(174, 63, 19, 0.08)",
          }}
        >
          <strong>Draft generation failed</strong>
          <span>{errorMessage}</span>
        </div>
      ) : null}
    </form>
  );
}
