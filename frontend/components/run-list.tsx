import Link from "next/link";

import type { RegistryList, RunListPage } from "@/lib/runs";

type RunListProps = {
  runPage: RunListPage;
  registry: RegistryList;
  filters: {
    status?: string;
    agent_version_id?: string;
  };
};

export function RunList({ runPage, registry, filters }: RunListProps) {
  const previousPage = runPage.page > 1 ? runPage.page - 1 : null;
  const nextPage = runPage.has_next_page ? runPage.page + 1 : null;

  function buildHref(page: number): string {
    const params = new URLSearchParams();
    params.set("runs_page", String(page));
    if (filters.status) {
      params.set("runs_status", filters.status);
    }
    if (filters.agent_version_id) {
      params.set("runs_agent_version_id", filters.agent_version_id);
    }
    return `/?${params.toString()}`;
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
          Recent Runs
        </p>
        <h2 style={{ margin: "0.35rem 0 0" }}>Persisted execution history</h2>
      </div>

      <form method="get" style={{ display: "grid", gap: "0.75rem", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))" }}>
        <label style={{ display: "grid", gap: "0.35rem" }}>
          <span>Status</span>
          <select name="runs_status" defaultValue={filters.status ?? ""}>
            <option value="">All statuses</option>
            <option value="pending">pending</option>
            <option value="running">running</option>
            <option value="completed">completed</option>
            <option value="failed">failed</option>
            <option value="partial_success">partial_success</option>
            <option value="cancelled">cancelled</option>
          </select>
        </label>
        <label style={{ display: "grid", gap: "0.35rem" }}>
          <span>Agent version</span>
          <select
            name="runs_agent_version_id"
            defaultValue={filters.agent_version_id ?? ""}
          >
            <option value="">All versions</option>
            {registry.agent_versions.map((agentVersion) => (
              <option key={agentVersion.agent_version_id} value={agentVersion.agent_version_id}>
                {agentVersion.version_name} · {agentVersion.model}
              </option>
            ))}
          </select>
        </label>
        <input type="hidden" name="runs_page" value="1" />
        <button type="submit" style={{ width: "fit-content", alignSelf: "end" }}>
          Apply filters
        </button>
      </form>

      {runPage.items.length === 0 ? (
        <p style={{ margin: 0, color: "var(--muted)" }}>
          No runs created yet. Start a run to unlock real summary metrics and trace-backed review.
        </p>
      ) : (
        <div style={{ display: "grid", gap: "0.9rem" }}>
          {runPage.items.map((run) => (
            <Link
              key={run.run_id}
              href={`/runs/${run.run_id}`}
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
              <div style={{ display: "flex", gap: "0.5rem", alignItems: "center", flexWrap: "wrap" }}>
                <strong>{run.run_id}</strong>
                {run.baseline ? (
                  <span
                    style={{
                      padding: "0.2rem 0.5rem",
                      borderRadius: "999px",
                      background: "rgba(28, 121, 78, 0.12)",
                      color: "rgb(28, 121, 78)",
                      fontSize: "0.8rem",
                    }}
                  >
                    Baseline
                  </span>
                ) : null}
                {run.experiment_tag ? (
                  <span style={{ color: "var(--muted)", fontSize: "0.85rem" }}>
                    {run.experiment_tag}
                  </span>
                ) : null}
              </div>
              <span>
                {run.status} · {run.completed_tasks}/{run.total_tasks} completed · {run.failed_tasks} failed
              </span>
              <span style={{ color: "var(--muted)" }}>
                Dataset {run.dataset_id} · snapshot {run.dataset_snapshot_id ?? "n/a"} · Agent{" "}
                {run.agent_version_id}
              </span>
              {run.sampling ? (
                <span style={{ color: "var(--muted)" }}>
                  Sampling group {run.sampling.group_id} · sample {run.sampling.sample_index}/
                  {run.sampling.sample_count}
                </span>
              ) : null}
              {run.notes ? <span style={{ color: "var(--muted)" }}>{run.notes}</span> : null}
            </Link>
          ))}
        </div>
      )}

      <div style={{ display: "flex", gap: "0.75rem", alignItems: "center", flexWrap: "wrap" }}>
        <span style={{ color: "var(--muted)" }}>
          Page {runPage.page} · showing {runPage.items.length} of {runPage.total_count}
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
