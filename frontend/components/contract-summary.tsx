import type { PhaseContractSnapshot } from "../../shared/types";

type ContractSummaryProps = {
  contract: PhaseContractSnapshot;
  backendBaseUrl: string;
};

export function ContractSummary({
  contract,
  backendBaseUrl,
}: ContractSummaryProps) {
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
      <div>
        <p style={{ margin: 0, color: "var(--muted)", letterSpacing: "0.08em", textTransform: "uppercase" }}>
          Phase Marker
        </p>
        <h2 style={{ margin: "0.35rem 0 0" }}>{contract.phase.current_phase}</h2>
      </div>

      <div>
        <p style={{ margin: 0, color: "var(--muted)" }}>Backend health surface</p>
        <code>{backendBaseUrl}/api/v1/meta/health</code>
      </div>

      <div>
        <p style={{ margin: "0 0 0.5rem", color: "var(--muted)" }}>Scope</p>
        <ul style={{ margin: 0, paddingLeft: "1.25rem" }}>
          {contract.phase.scope.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </div>

      <div>
        <p style={{ margin: "0 0 0.5rem", color: "var(--muted)" }}>Non-goals</p>
        <ul style={{ margin: 0, paddingLeft: "1.25rem" }}>
          {contract.phase.non_goals.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </div>

      <div>
        <p style={{ margin: "0 0 0.5rem", color: "var(--muted)" }}>Canonical run statuses</p>
        <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem" }}>
          {contract.run_statuses.map((status) => (
            <span
              key={status}
              style={{
                padding: "0.3rem 0.7rem",
                borderRadius: "999px",
                border: "1px solid var(--border)",
                background: "rgba(255,255,255,0.7)",
              }}
            >
              {status}
            </span>
          ))}
        </div>
      </div>
    </section>
  );
}
