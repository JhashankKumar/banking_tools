"use client";

import { UserPlus } from "lucide-react";

import { PageLayout } from "@/components/layout/PageLayout";
import { Button } from "@/components/ui/Button";
import { Pagination } from "@/components/ui/Pagination";
import { QueryView } from "@/components/ui/QueryView";
import { UserFormDrawer } from "@/features/users/components/UserFormDrawer";
import { UsersTable } from "@/features/users/components/UsersTable";
import { useUsersPage } from "@/features/users/hooks/useUsersPage";

export default function UsersPage() {
  const p = useUsersPage();
  return (
    <PageLayout
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
    >
      <QueryView query={p.users} noun="Users" loading="Loading users">
        {(data) => (
          <>
            <UsersTable users={data.items} meId={p.meId} onEdit={p.openEdit} />
            <Pagination
              page={data.page}
              noun="users"
              order="A–Z"
              onOffset={p.setOffset}
            />
          </>
        )}
      </QueryView>
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
    </PageLayout>
  );
}
