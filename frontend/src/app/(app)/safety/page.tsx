"use client";

import { PageLayout } from "@/components/layout/PageLayout";
import { KnownLimitations } from "@/features/safety/components/KnownLimitations";
import { SafetyChecksView } from "@/features/safety/components/SafetyChecksView";

export default function SafetyPage() {
  return (
    <PageLayout
      title="Safety checks"
      subtitle="Runs scripted attacks against the real defences. Uses a scripted model; no data changes; no model cost."
    >
      <SafetyChecksView />
      <KnownLimitations />
    </PageLayout>
  );
}
