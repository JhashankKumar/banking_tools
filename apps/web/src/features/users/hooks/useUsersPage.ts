"use client";

import { useState } from "react";

import { useMe } from "@/features/auth/queries";

import { useUsers } from "../queries";
import type { User } from "../schemas";

const PAGE_SIZE = 50;

type DrawerState =
  { mode: "closed" } | { mode: "create" } | { mode: "edit"; user: User };

export function useUsersPage() {
  const [offset, setOffset] = useState(0);
  const [drawer, setDrawer] = useState<DrawerState>({ mode: "closed" });
  const users = useUsers({ limit: PAGE_SIZE, offset });
  const me = useMe();

  return {
    users,
    rows: users.data?.items ?? [],
    page: users.data?.page,
    meId: me.data?.id,
    drawer,
    openCreate: () => setDrawer({ mode: "create" }),
    openEdit: (user: User) => setDrawer({ mode: "edit", user }),
    closeDrawer: () => setDrawer({ mode: "closed" }),
    setOffset,
  };
}
