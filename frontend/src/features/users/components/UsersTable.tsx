import { Ban, Check, Lock } from "lucide-react";

import { Button } from "@/components/ui/Button";
import { Chip } from "@/components/ui/Chip";
import { StatusChip, type StatusStyles } from "@/components/ui/StatusChip";
import { Table, Td, Th } from "@/components/ui/Table";
import { formatDateTime } from "@/lib/format";
import { ROLE_LABEL } from "@/lib/permissions";

import type { User } from "../schemas";

const ACCOUNT_STYLES: StatusStyles<"active" | "inactive"> = {
  active: { tone: "success", icon: Check, label: "Active" },
  inactive: { tone: "neutral", icon: Ban, label: "Inactive" },
};

export function UsersTable({
  users,
  meId,
  onEdit,
}: {
  users: User[];
  meId: string | undefined;
  onEdit: (user: User) => void;
}) {
  return (
    <Table>
      <thead>
        <tr>
          <Th>Username</Th>
          <Th>Role</Th>
          <Th>Status</Th>
          <Th>Created (IST)</Th>
          <Th>
            <span className="sr-only">Actions</span>
          </Th>
        </tr>
      </thead>
      <tbody>
        {users.map((u) => {
          const isMe = u.id === meId;
          return (
            <tr key={u.id} aria-label={u.username}>
              <Td>
                <span className="flex items-center gap-2 font-mono">
                  {u.username}
                  {isMe && <Chip tone="primary">You</Chip>}
                </span>
              </Td>
              <Td>
                <Chip tone={u.role === "supervisor" ? "primary" : "neutral"}>
                  {ROLE_LABEL[u.role]}
                </Chip>
              </Td>
              <Td>
                <StatusChip
                  value={u.isActive ? "active" : "inactive"}
                  styles={ACCOUNT_STYLES}
                  outline
                />
              </Td>
              <Td className="font-mono whitespace-nowrap text-muted">
                {formatDateTime(u.createdAt)}
              </Td>
              <Td className="text-right">
                <span className="inline-flex items-center gap-3">
                  {isMe && (
                    <span className="inline-flex items-center gap-1.5 text-muted">
                      <Lock aria-hidden size={12} />
                      Role and status locked
                    </span>
                  )}
                  <Button
                    variant="ghost"
                    aria-label={`Edit ${u.username}`}
                    onClick={() => onEdit(u)}
                    className="px-2.5 py-1 text-xs"
                  >
                    Edit
                  </Button>
                </span>
              </Td>
            </tr>
          );
        })}
      </tbody>
    </Table>
  );
}
