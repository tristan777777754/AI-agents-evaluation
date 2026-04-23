"use client";

import { useState, type ReactNode } from "react";

type WorkbenchTabsProps = {
  datasetsPanel: ReactNode;
  launchPanel?: ReactNode;
  resultsPanel: ReactNode;
  comparePanel: ReactNode;
  registryPanel?: ReactNode;
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
  datasetsPanel,
  launchPanel,
  resultsPanel,
  comparePanel,
  registryPanel,
  draftsPanel,
  governancePanel,
}: WorkbenchTabsProps) {
  const tabs: TabConfig[] = [
    {
      id: "datasets",
      label: "1. Datasets",
      title: "Prepare the test set",
      description:
        "Upload or inspect the questions the agent will be evaluated against. Start here when the workspace has no dataset yet, or when you need to confirm item count, schema, and snapshots.",
      content: datasetsPanel,
    },
    {
      id: "runs",
      label: "2. Run",
      title: "Launch an evaluation",
      description:
        "Choose the dataset, agent version, scorer, and run settings. Use quick run when defaults are configured; use full launch when you need explicit control over dataset, scorer, tags, or sampling.",
      content: launchPanel,
    },
    {
      id: "results",
      label: "3. Results",
      title: "Read the run outcome",
      description:
        "Use this tab after a run finishes. It shows persisted summary metrics, recent run history, and links into task-level traces.",
      content: resultsPanel,
    },
    {
      id: "compare",
      label: "4. Compare",
      title: "Compare two runs",
      description:
        "Pick a completed baseline run and a completed candidate run from the same dataset. The compare view highlights metric deltas, regressions, improvements, and trace differences.",
      content: comparePanel,
    },
    {
      id: "registry",
      label: "5. Registry",
      title: "Manage versions and defaults",
      description:
        "Use this when you need a new agent version, a new agent entry, or default dataset/scorer settings for quick runs. Existing run history remains tied to immutable version snapshots.",
      content: registryPanel,
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
