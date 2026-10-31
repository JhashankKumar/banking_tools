"use client";

import { Button } from "@/components/ui/Button";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { KpiTiles } from "@/components/ui/KpiTiles";
import { QueryView } from "@/components/ui/QueryView";

import { useSafetyPage } from "../hooks/useSafetyPage";
import { SafetyResults } from "./SafetyResults";

const seconds = (ms: number) => `${(ms / 1000).toFixed(1)} s`;

export function SafetyChecksView() {
  const p = useSafetyPage();
  return (
    <div className="flex flex-col gap-5">
      {p.checks.isSuccess && (
        <div className="flex items-center gap-3">
          <Button variant="primary" disabled={p.running} onClick={p.start}>
            Run checks
          </Button>
          {p.running && (
            <p role="status" className="text-xs text-muted">
              Running the checks…
            </p>
          )}
        </div>
      )}
      <ErrorBanner error={p.error} />
      {p.run && (
        <div role="group" aria-label="Run summary">
          <KpiTiles
            tiles={[
              { label: "Passed", value: p.run.counts.passed },
              { label: "Failed", value: p.run.counts.failed, tone: "error" },
              { label: "Skipped", value: p.run.counts.skipped, tone: "review" },
              { label: "Duration", value: seconds(p.run.durationMs) },
            ]}
          />
        </div>
      )}
      <QueryView
        query={p.checks}
        noun="Safety checks"
        loading="Loading the safety checks"
      >
        {(checks) => (
          <SafetyResults checks={checks} results={p.run?.results ?? null} />
        )}
      </QueryView>
    </div>
  );
}
