"use client";

import { useQueryClient } from "@tanstack/react-query";
import { LogOut } from "lucide-react";
import { useRouter } from "next/navigation";

import type { Me } from "@/features/auth/schemas";
import { logout } from "@/features/auth/api";
import { ROLE_LABEL } from "@/lib/permissions";

export function UserMenu({ me }: { me: Me }) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const signOut = async () => {
    await logout().catch(() => undefined);
    queryClient.clear();
    router.replace("/login");
  };
  return (
    <div className="flex items-center gap-3">
      <span className="text-sm font-medium text-ink">
        <span className="font-mono">{me.username}</span> · {ROLE_LABEL[me.role]}
      </span>
      <button
        type="button"
        onClick={() => void signOut()}
        className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs text-muted hover:bg-raised hover:text-ink"
      >
        <LogOut aria-hidden size={14} /> Sign out
      </button>
    </div>
  );
}
