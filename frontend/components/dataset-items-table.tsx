import type { DatasetItemList } from "@/lib/datasets";

type DatasetItemsTableProps = {
  datasetItems: DatasetItemList;
};

export function DatasetItemsTable({ datasetItems }: DatasetItemsTableProps) {
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
    </section>
  );
}
