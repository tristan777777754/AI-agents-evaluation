"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { RunTaskTable } from "@/components/run-task-table";
import {
  getAutoCompare,
  getRunDetail,
  getRunTasks,
  type AutoCompare,
  type RunDetail,
  type RunTaskList,
} from "@/lib/runs";

type RunDetailLiveProps = {
  initialRun: RunDetail;
  initialTasks: RunTaskList;
};

const heroStyle = {
  display: "grid",
  gap: "0.75rem",
  padding: "2rem",
  borderRadius: "28px",
  background: "linear-gradient(135deg, rgba(255,250,245,0.94), rgba(255,239,222,0.9))",
  border: "1px solid var(--border)",
  boxShadow: "var(--shadow)",
} as const;

export function RunDetailLive({ initialRun, initialTasks }: RunDetailLiveProps) {
  const [run, setRun] = useState(initialRun);
  const [tasks, setTasks] = useState(initialTasks);
  const [autoCompare, setAutoCompare] = useState<AutoCompare | null>(null);

  useEffect(() => {
    let active = true;

    async function loadAutoCompare() {
      try {
        const response = await getAutoCompare(initialRun.run_id);
        if (active) {
          setAutoCompare(response);
        }
      } catch {
        if (active) {
          setAutoCompare(null);
        }
      }
    }

    void loadAutoCompare();

    return () => {
      active = false;
    };
  }, [initialRun.run_id]);

  useEffect(() => {
    if (!["pending", "running"].includes(run.status)) {
      return;
    }

    let active = true;
    const interval = window.setInterval(async () => {
      try {
        const [nextRun, nextTasks, nextAutoCompare] = await Promise.all([
          getRunDetail(run.run_id),
          getRunTasks(run.run_id),
          getAutoCompare(run.run_id),
        ]);
        if (!active) {
          return;
        }
        setRun(nextRun);
        setTasks(nextTasks);
        setAutoCompare(nextAutoCompare);
      } catch {
        // Keep the last good payload and retry on the next poll.
      }
    }, 1500);

    return () => {
      active = false;
      window.clearInterval(interval);
    };
  }, [run.run_id, run.status]);

  const compareHref =
    autoCompare?.baseline_run_id && autoCompare.comparison
      ? `/compare?baseline_run_id=${encodeURIComponent(
          autoCompare.baseline_run_id,
        )}&candidate_run_id=${encodeURIComponent(autoCompare.candidate_run_id)}`
      : null;

  return (
    <>
      <section style={heroStyle}>
        <p style={{ margin: 0, color: "var(--muted)" }}>{run.run_id}</p>
        <h1 style={{ margin: 0 }}>Run status: {run.status}</h1>
        <p style={{ margin: 0 }}>
          Dataset {run.dataset_id} · Agent {run.agent_version.version_name} · Scorer{" "}
          {run.scorer_config.name}
        </p>
        <p style={{ margin: 0 }}>
          {run.completed_tasks}/{run.total_tasks} completed · {run.failed_tasks} failed · adapter{" "}
          {run.adapter_type}
        </p>
        <p style={{ margin: 0, color: "var(--muted)" }}>
          Snapshot {run.dataset_snapshot_id ?? "n/a"} · {run.baseline ? "Baseline run" : "Candidate run"}
          {run.experiment_tag ? ` · Experiment ${run.experiment_tag}` : ""}
        </p>
        {run.notes ? <p style={{ margin: 0, color: "var(--muted)" }}>{run.notes}</p> : null}
        {compareHref ? (
          <Link href={compareHref} style={{ color: "var(--accent)" }}>
            Open auto-compare ({autoCompare?.selection_reason?.replaceAll("_", " ")})
          </Link>
        ) : autoCompare?.baseline_run_id ? (
          <p style={{ margin: 0, color: "var(--muted)" }}>
            Suggested baseline: {autoCompare.baseline_run_id} ({autoCompare.selection_reason})
          </p>
        ) : (
          <p style={{ margin: 0, color: "var(--muted)" }}>
            No baseline suggestion yet for this run.
          </p>
        )}
      </section>

      <RunTaskTable runTasks={tasks} />
    </>
  );
}
