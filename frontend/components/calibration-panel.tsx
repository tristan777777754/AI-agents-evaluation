import type { CalibrationReport } from "@/lib/calibration";

type CalibrationPanelProps = {
  report: CalibrationReport | null;
  loadError?: string | null;
};

function formatPercent(value: number): string {
  return `${Math.round(value * 100)}%`;
}

export function CalibrationPanel({ report, loadError = null }: CalibrationPanelProps) {
  if (loadError) {
    return (
      <section
        style={{
          display: "grid",
          gap: "0.75rem",
          padding: "1.5rem",
          borderRadius: "24px",
          border: "1px solid rgba(174, 63, 19, 0.2)",
          background: "rgba(174, 63, 19, 0.08)",
        }}
      >
        <strong>Calibration unavailable</strong>
        <p style={{ margin: 0 }}>{loadError}</p>
      </section>
    );
  }

  if (!report) {
    return (
      <section
        style={{
          display: "grid",
          gap: "0.75rem",
          padding: "1.5rem",
          borderRadius: "24px",
          border: "1px solid var(--border)",
          background: "var(--panel)",
          boxShadow: "var(--shadow)",
        }}
      >
        <p style={{ margin: 0, color: "var(--muted)", letterSpacing: "0.08em", textTransform: "uppercase" }}>
          Calibration
        </p>
        <h2 style={{ margin: 0 }}>No calibration report yet</h2>
        <p style={{ margin: 0, color: "var(--muted)" }}>
          Phase 9 publishes a scorer calibration report from the human-labelled golden set.
        </p>
      </section>
    );
  }

  const kpis = [
    { label: "Precision", value: formatPercent(report.precision) },
    { label: "Recall", value: formatPercent(report.recall) },
    { label: "Accuracy", value: formatPercent(report.accuracy) },
    { label: "Disagreements", value: String(report.disagreements.length) },
  ];

  return (
    <section
      style={{
        display: "grid",
        gap: "1.25rem",
        padding: "1.5rem",
        borderRadius: "24px",
        border: "1px solid var(--border)",
        background: "var(--panel)",
        boxShadow: "var(--shadow)",
      }}
    >
      <div style={{ display: "grid", gap: "0.35rem" }}>
        <p style={{ margin: 0, color: "var(--muted)", letterSpacing: "0.08em", textTransform: "uppercase" }}>
          Calibration
        </p>
        <h2 style={{ margin: 0 }}>Golden set scorer quality</h2>
        <p style={{ margin: 0, color: "var(--muted)" }}>
          Fixture {report.fixture_id} · scorer {report.scorer_config_id} · {report.total_cases} labelled
          cases
        </p>
      </div>

      <div
        style={{
          display: "grid",
          gap: "1rem",
          gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
        }}
      >
        {kpis.map((metric) => (
          <article
            key={metric.label}
            style={{
              display: "grid",
              gap: "0.35rem",
              padding: "1rem",
              borderRadius: "18px",
              border: "1px solid var(--border)",
              background: "rgba(255,255,255,0.72)",
            }}
          >
            <span style={{ color: "var(--muted)" }}>{metric.label}</span>
            <strong style={{ fontSize: "1.5rem" }}>{metric.value}</strong>
          </article>
        ))}
      </div>

      <section
        style={{
          display: "grid",
          gap: "1rem",
          gridTemplateColumns: "minmax(0, 1.2fr) minmax(0, 1fr)",
        }}
      >
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr>
                <th style={{ textAlign: "left", padding: "0.75rem" }}>Category</th>
                <th style={{ textAlign: "left", padding: "0.75rem" }}>Accuracy</th>
                <th style={{ textAlign: "left", padding: "0.75rem" }}>Correct</th>
              </tr>
            </thead>
            <tbody>
              {report.per_category.map((row) => (
                <tr key={row.category} style={{ borderTop: "1px solid var(--border)" }}>
                  <td style={{ padding: "0.75rem" }}>{row.category}</td>
                  <td style={{ padding: "0.75rem" }}>{formatPercent(row.accuracy)}</td>
                  <td style={{ padding: "0.75rem" }}>
                    {row.correct_cases}/{row.total_cases}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <section
          style={{
            display: "grid",
            gap: "0.75rem",
            padding: "1rem",
            borderRadius: "18px",
            border: "1px solid var(--border)",
            background: "rgba(255,255,255,0.72)",
            alignContent: "start",
          }}
        >
          <strong>Confusion counts</strong>
          <span>TP {report.true_positive_count}</span>
          <span>FP {report.false_positive_count}</span>
          <span>TN {report.true_negative_count}</span>
          <span>FN {report.false_negative_count}</span>
          <span style={{ color: "var(--muted)", marginTop: "0.5rem" }}>
            {report.disagreements.length === 0
              ? "The scorer matches the golden labels on the current fixture."
              : "Inspect disagreement cases before trusting release decisions."}
          </span>
        </section>
      </section>
    </section>
  );
}
