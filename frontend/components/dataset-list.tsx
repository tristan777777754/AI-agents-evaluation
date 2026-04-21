import Link from "next/link";

import type { DatasetSummary } from "@/lib/datasets";

type DatasetListProps = {
  datasets: DatasetSummary[];
};

export function DatasetList({ datasets }: DatasetListProps) {
  return (
    <section
      style={{
        display: "grid",
        gap: "1rem",
        padding: "1.5rem",
        borderRadius: "24px",
        border: "1px solid var(--border)",
        background: "var(--panel)",
        boxShadow: "var(--shadow)",
      }}
    >
      <div>
        <p style={{ margin: 0, color: "var(--muted)", letterSpacing: "0.08em", textTransform: "uppercase" }}>
          Datasets
        </p>
        <h2 style={{ margin: "0.35rem 0 0" }}>Persisted imports</h2>
      </div>

      {datasets.length === 0 ? (
        <p style={{ margin: 0, color: "var(--muted)" }}>
          No datasets uploaded yet. Import a JSON or CSV file to create the Phase 2 baseline.
        </p>
      ) : (
        <div style={{ display: "grid", gap: "0.9rem" }}>
          {datasets.map((dataset) => (
            <Link
              key={dataset.dataset_id}
              href={`/datasets/${dataset.dataset_id}`}
              style={{
                display: "grid",
                gap: "0.35rem",
                padding: "1rem 1.1rem",
                borderRadius: "18px",
                border: "1px solid var(--border)",
                color: "inherit",
                textDecoration: "none",
                background: "rgba(255,255,255,0.74)",
              }}
            >
              <strong>{dataset.name}</strong>
              <span style={{ color: "var(--muted)" }}>{dataset.dataset_id}</span>
              <span>
                {dataset.item_count} items · {dataset.source_type.toUpperCase()} · schema{" "}
                {dataset.schema_version}
              </span>
            </Link>
          ))}
        </div>
      )}
    </section>
  );
}
