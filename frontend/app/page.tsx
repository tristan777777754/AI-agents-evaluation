import { ContractSummary } from "@/components/contract-summary";
import { phase1ContractPreview } from "@/lib/contracts";

const backendBaseUrl =
  process.env.NEXT_PUBLIC_BACKEND_BASE_URL ?? "http://localhost:8000";

export default function HomePage() {
  return (
    <main
      style={{
        padding: "3rem 1.5rem 4rem",
        display: "grid",
        gap: "2rem",
        maxWidth: "1120px",
        margin: "0 auto",
      }}
    >
      <section
        style={{
          display: "grid",
          gap: "1rem",
          padding: "2rem",
          borderRadius: "28px",
          background:
            "linear-gradient(135deg, rgba(255,250,245,0.94), rgba(255,239,222,0.9))",
          border: "1px solid var(--border)",
          boxShadow: "var(--shadow)",
        }}
      >
        <p
          style={{
            margin: 0,
            color: "var(--accent)",
            letterSpacing: "0.12em",
            textTransform: "uppercase",
          }}
        >
          Agent Quality Engineering
        </p>
        <h1 style={{ margin: 0, fontSize: "clamp(2.4rem, 6vw, 5rem)", lineHeight: 0.95 }}>
          Agent Evaluation Workbench
        </h1>
        <p style={{ margin: 0, maxWidth: "48rem", fontSize: "1.1rem", lineHeight: 1.6 }}>
          Phase 1 only establishes the foundation: repo skeleton, canonical contracts,
          environment scaffolding, and minimum startup surfaces for the Next.js frontend
          and FastAPI backend.
        </p>
      </section>

      <ContractSummary contract={phase1ContractPreview} backendBaseUrl={backendBaseUrl} />
    </main>
  );
}
