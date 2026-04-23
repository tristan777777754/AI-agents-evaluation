import Link from "next/link";

import type { DatasetItemList } from "@/lib/datasets";

type DatasetItemsTableProps = {
  datasetItems: DatasetItemList;
  datasetId: string;
  filters: {
    tag?: string;
    category?: string;
  };
};

export function DatasetItemsTable({ datasetItems, datasetId, filters }: DatasetItemsTableProps) {
  const previousPage = datasetItems.page > 1 ? datasetItems.page - 1 : null;
  const nextPage = datasetItems.has_next_page ? datasetItems.page + 1 : null;

  function buildHref(page: number): string {
    const params = new URLSearchParams();
    params.set("page", String(page));
    if (filters.tag) {
      params.set("tag", filters.tag);
    }
    if (filters.category) {
      params.set("category", filters.category);
    }
    return `/datasets/${datasetId}?${params.toString()}`;
  }

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
          Preview
        </p>
        <h2 style={{ margin: "0.35rem 0 0" }}>{datasetItems.total_count} dataset items</h2>
      </div>

      <form
        method="get"
        style={{
          display: "grid",
          gap: "0.75rem",
          gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
        }}
      >
        <label style={{ display: "grid", gap: "0.35rem" }}>
          <span>Tag</span>
          <input name="tag" type="text" defaultValue={filters.tag ?? ""} placeholder="regression" />
        </label>
        <label style={{ display: "grid", gap: "0.35rem" }}>
          <span>Category</span>
          <input
            name="category"
            type="text"
            defaultValue={filters.category ?? ""}
            placeholder="refund_policy"
          />
        </label>
        <input type="hidden" name="page" value="1" />
        <button type="submit" style={{ width: "fit-content", alignSelf: "end" }}>
          Apply filters
        </button>
      </form>

      <div style={{ overflowX: "auto" }}>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr>
              <th style={{ textAlign: "left", padding: "0.75rem" }}>Item</th>
              <th style={{ textAlign: "left", padding: "0.75rem" }}>Category</th>
              <th style={{ textAlign: "left", padding: "0.75rem" }}>Source / Tags</th>
              <th style={{ textAlign: "left", padding: "0.75rem" }}>Input</th>
              <th style={{ textAlign: "left", padding: "0.75rem" }}>Expected Output</th>
            </tr>
          </thead>
          <tbody>
            {datasetItems.items.map((item) => (
              <tr key={item.dataset_item_id} style={{ borderTop: "1px solid var(--border)" }}>
                <td style={{ padding: "0.75rem", verticalAlign: "top" }}>{item.dataset_item_id}</td>
                <td style={{ padding: "0.75rem", verticalAlign: "top" }}>{item.category}</td>
                <td style={{ padding: "0.75rem", verticalAlign: "top" }}>
                  <div style={{ display: "grid", gap: "0.25rem" }}>
                    <span>{item.source_origin}</span>
                    <span style={{ color: "var(--muted)" }}>
                      {item.tags.length > 0 ? item.tags.join(", ") : "No tags"}
                    </span>
                  </div>
                </td>
                <td style={{ padding: "0.75rem", verticalAlign: "top" }}>{item.input_text}</td>
                <td style={{ padding: "0.75rem", verticalAlign: "top" }}>
                  {item.expected_output ?? <span style={{ color: "var(--muted)" }}>No expected output</span>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div style={{ display: "flex", gap: "0.75rem", alignItems: "center", flexWrap: "wrap" }}>
        <span style={{ color: "var(--muted)" }}>
          Page {datasetItems.page} · showing {datasetItems.items.length} of {datasetItems.total_count}
        </span>
        {previousPage ? (
          <Link href={buildHref(previousPage)} style={{ color: "var(--accent)" }}>
            Previous
          </Link>
        ) : null}
        {nextPage ? (
          <Link href={buildHref(nextPage)} style={{ color: "var(--accent)" }}>
            Next
          </Link>
        ) : null}
      </div>
    </section>
  );
}
