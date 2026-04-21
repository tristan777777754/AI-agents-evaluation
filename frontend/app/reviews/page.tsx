import Link from "next/link";

import { ReviewQueuePanel } from "@/components/review-queue-panel";
import { getReviewQueue } from "@/lib/runs";

export default async function ReviewsPage() {
  const queue = await getReviewQueue();

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
        Back to workbench
      </Link>

      <section
        style={{
          display: "grid",
          gap: "0.75rem",
          padding: "2rem",
          borderRadius: "28px",
          background: "linear-gradient(135deg, rgba(255,250,245,0.94), rgba(255,239,222,0.9))",
          border: "1px solid var(--border)",
          boxShadow: "var(--shadow)",
        }}
      >
        <p style={{ margin: 0, color: "var(--muted)" }}>Phase 7 persisted reviewer workflow</p>
        <h1 style={{ margin: 0 }}>Review Queue</h1>
        <p style={{ margin: 0, color: "var(--muted)" }}>
          Review-needed task runs stay backed by real score and trace records. Open any case to
          leave a verdict and note.
        </p>
      </section>

      <ReviewQueuePanel queue={queue} />
    </main>
  );
}
