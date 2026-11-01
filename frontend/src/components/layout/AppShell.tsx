"use client";

import type { ReactNode } from "react";

import { QueryView } from "@/components/ui/QueryView";
import { useMe } from "@/features/auth/queries";

import { TopNav } from "./TopNav";

export function AppShell({ children }: { children: ReactNode }) {
  const me = useMe();
  return (
    <QueryView query={me} noun="Your session" loading="Loading your session">
      {(user) => (
        <div className="flex h-dvh flex-col bg-page">
          <TopNav me={user} />
          <main className="flex min-h-0 flex-1 flex-col overflow-y-auto">
            {children}
          </main>
        </div>
      )}
    </QueryView>
  );
}
