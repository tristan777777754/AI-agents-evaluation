"use client";

import { useState, type ReactNode } from "react";

type WorkbenchTabsProps = {
  registryPanel?: ReactNode;
  datasetsPanel: ReactNode;
  launchPanel?: ReactNode;
  resultsPanel: ReactNode;
  comparePanel: ReactNode;
  draftsPanel: ReactNode;
  governancePanel: ReactNode;
};

type TabConfig = {
  id: string;
  label: string;
  title: string;
  description: string;
  content: ReactNode;
};

export function WorkbenchTabs({
  registryPanel,
  datasetsPanel,
  launchPanel,
  resultsPanel,
  comparePanel,
  draftsPanel,
  governancePanel,
}: WorkbenchTabsProps) {
  const tabs: TabConfig[] = [
    {
      id: "agent-setup",
      label: "1. Agent Setup",
      title: "Define what you want to evaluate",
      description:
        "Create or inspect the agent and immutable agent versions before running evaluations. A compare only makes sense when each run is tied to a clear version snapshot, model, prompt hash, and configuration.",
      content: registryPanel,
    },
    {
      id: "datasets",
      label: "2. Datasets",
      title: "Prepare the test set",
      description:
        "Upload or inspect the questions the agent will be evaluated against. Start here when the workspace has no dataset yet, or when you need to confirm item count, schema, and snapshots.",
      content: datasetsPanel,
    },
    {
      id: "runs",
      label: "3. Run",
      title: "Launch an evaluation",
      description:
        "Choose the dataset, agent version, scorer, and run settings. Use quick run when defaults are configured; use full launch when you need explicit control over dataset, scorer, tags, or sampling.",
      content: launchPanel,
    },
    {
      id: "results",
      label: "4. Results",
      title: "Read the run outcome",
      description:
        "Use this tab after a run finishes. It shows persisted summary metrics, recent run history, and links into task-level traces.",
      content: resultsPanel,
    },
    {
      id: "compare",
      label: "5. Compare",
      title: "Compare two runs",
      description:
        "Pick a completed baseline run and a completed candidate run from the same dataset. The compare view highlights metric deltas, regressions, improvements, and trace differences.",
      content: comparePanel,
    },
    {
      id: "drafts",
      label: "6. Drafts",
      title: "Grow the dataset deliberately",
      description:
        "Generate or review candidate dataset items before they become trusted benchmark inputs. Drafts are useful after reviewing failures or expanding regression coverage.",
      content: draftsPanel,
    },
    {
      id: "governance",
      label: "7. Governance",
      title: "Audit contracts and scorer credibility",
      description:
        "This is the engineering audit area. Check phase contracts, backend health, scorer calibration, and governance metadata after the main evaluation path is working.",
      content: governancePanel,
    },
  ].filter((tab) => tab.content);
  const [activeTabId, setActiveTabId] = useState(tabs[0]?.id ?? "datasets");
  const activeTab = tabs.find((tab) => tab.id === activeTabId) ?? tabs[0];

  return (
    <section className="tab-workbench" aria-label="Workbench steps">
      <div className="tab-list" role="tablist" aria-label="Main workbench steps">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            id={`${tab.id}-tab`}
            type="button"
            role="tab"
            aria-selected={tab.id === activeTab.id}
            aria-controls={`${tab.id}-panel`}
            className="tab-button"
            onClick={() => setActiveTabId(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <section
        id={`${activeTab.id}-panel`}
        role="tabpanel"
        aria-labelledby={`${activeTab.id}-tab`}
        className="tab-panel"
      >
        <div className="tab-intro">
          <p className="eyebrow">Current Step</p>
          <h2>{activeTab.title}</h2>
          <p>{activeTab.description}</p>
        </div>
        <div className="tab-content">{activeTab.content}</div>
      </section>
    </section>
  );
}
