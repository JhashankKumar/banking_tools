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
        <div className="flex min-h-screen flex-col bg-page">
          <TopNav me={user} />
          <main className="flex flex-1 flex-col">{children}</main>
        </div>
      )}
    </QueryView>
  );
}
