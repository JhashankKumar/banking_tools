"use client";

import type { ReactNode } from "react";

import { StatePanel } from "@/components/ui/StatePanel";
import { useMe } from "@/features/auth/queries";
import { userMessage } from "@/lib/api-error";
import { ApiError } from "@/lib/api-error";

import { TopNav } from "./TopNav";

export function AppShell({ children }: { children: ReactNode }) {
  const me = useMe();
  if (me.isPending)
    return <StatePanel kind="loading" title="Loading your session" />;
  if (me.isError) {
    return (
      <StatePanel
        kind="error"
        title="Could not load your session"
        message={userMessage(me.error, "Please sign in again.")}
        requestId={me.error instanceof ApiError ? me.error.requestId : null}
      />
    );
  }
  return (
    <div className="flex min-h-screen flex-col bg-page">
      <TopNav me={me.data} />
      <main className="flex flex-1 flex-col">{children}</main>
    </div>
  );
}
