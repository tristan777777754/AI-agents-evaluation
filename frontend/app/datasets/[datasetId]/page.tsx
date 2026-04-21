import Link from "next/link";
import { notFound } from "next/navigation";

import { DatasetItemsTable } from "@/components/dataset-items-table";
import { BackendApiError, getDatasetDetail, getDatasetItems } from "@/lib/datasets";

type DatasetDetailPageProps = {
  params: Promise<{ datasetId: string }>;
};

export default async function DatasetDetailPage({ params }: DatasetDetailPageProps) {
  const { datasetId } = await params;

  try {
    const [dataset, datasetItems] = await Promise.all([
      getDatasetDetail(datasetId),
      getDatasetItems(datasetId),
    ]);

    return (
      <main
        style={{
          padding: "3rem 1.5rem 4rem",
          display: "grid",
          gap: "1.5rem",
          maxWidth: "1120px",
          margin: "0 auto",
        }}
      >
        <Link href="/" style={{ color: "var(--accent)" }}>
          Back to datasets
        </Link>

        <section
          style={{
            display: "grid",
            gap: "0.75rem",
            padding: "2rem",
            borderRadius: "28px",
            background:
              "linear-gradient(135deg, rgba(255,250,245,0.94), rgba(255,239,222,0.9))",
            border: "1px solid var(--border)",
            boxShadow: "var(--shadow)",
          }}
        >
          <p style={{ margin: 0, color: "var(--muted)" }}>{dataset.dataset_id}</p>
          <h1 style={{ margin: 0 }}>{dataset.name}</h1>
          <p style={{ margin: 0, maxWidth: "48rem" }}>
            {dataset.description ?? "No dataset description provided."}
          </p>
          <p style={{ margin: 0 }}>
            {dataset.item_count} items · categories: {dataset.categories.join(", ") || "none"}
          </p>
          <p style={{ margin: 0, color: "var(--muted)" }}>
            Snapshot {dataset.snapshot_id} · version {dataset.snapshot_version} of {dataset.snapshot_count}
            {dataset.latest_snapshot_id ? ` · latest ${dataset.latest_snapshot_id}` : ""}
          </p>
        </section>

        <DatasetItemsTable datasetItems={datasetItems} />
      </main>
    );
  } catch (error) {
    if (error instanceof BackendApiError && error.status === 404) {
      notFound();
    }
    throw error;
  }
}
