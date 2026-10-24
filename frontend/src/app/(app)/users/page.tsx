"use client";

import { UserPlus } from "lucide-react";

import { PageHeader } from "@/components/layout/PageHeader";
import { QueryError } from "@/components/ui/QueryError";
import { Button } from "@/components/ui/Button";
import { Pagination } from "@/components/ui/Pagination";
import { StatePanel } from "@/components/ui/StatePanel";
import { UserFormDrawer } from "@/features/users/components/UserFormDrawer";
import { UsersTable } from "@/features/users/components/UsersTable";
import { useUsersPage } from "@/features/users/hooks/useUsersPage";

export default function UsersPage() {
  const p = useUsersPage();
  return (
    <div className="flex flex-col gap-5 px-8 pt-7 pb-9">
      <PageHeader
        title="Users"
        subtitle="Supervisors create users, set roles, and deactivate accounts. Every change is audited."
        action={
          !p.users.isError && (
            <Button variant="primary" onClick={p.openCreate}>
              <UserPlus aria-hidden size={16} />
              Create user
            </Button>
          )
        }
      />
      {p.users.isPending ? (
        <StatePanel kind="loading" title="Loading users" />
      ) : p.users.isError ? (
        <QueryError error={p.users.error} noun="Users" />
      ) : (
        <>
          <UsersTable users={p.rows} meId={p.meId} onEdit={p.openEdit} />
          {p.page && (
            <Pagination
              page={p.page}
              noun="users"
              order="A–Z"
              onOffset={p.setOffset}
            />
          )}
        </>
      )}
      {p.drawer.mode === "edit" ? (
        <UserFormDrawer
          mode="edit"
          user={p.drawer.user}
          isSelf={p.drawer.user.id === p.meId}
          open
          onClose={p.closeDrawer}
        />
      ) : (
        <UserFormDrawer
          mode="create"
          open={p.drawer.mode === "create"}
          onClose={p.closeDrawer}
        />
      )}
    </div>
  );
}
