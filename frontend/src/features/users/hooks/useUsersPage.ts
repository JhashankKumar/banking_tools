"use client";

import { useState } from "react";

import { useMe } from "@/features/auth/queries";
import { useListFilters } from "@/lib/use-list-filters";

import { useUsers } from "../queries";
import type { User } from "../schemas";

type DrawerState =
  { mode: "closed" } | { mode: "create" } | { mode: "edit"; user: User };

export function useUsersPage() {
  const list = useListFilters({});
  const [drawer, setDrawer] = useState<DrawerState>({ mode: "closed" });
  const users = useUsers({ limit: list.limit, offset: list.offset });
  const me = useMe();

  return {
    users,
    meId: me.data?.id,
    drawer,
    openCreate: () => setDrawer({ mode: "create" }),
    openEdit: (user: User) => setDrawer({ mode: "edit", user }),
    closeDrawer: () => setDrawer({ mode: "closed" }),
    setOffset: list.setOffset,
  };
}
