"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import type { Me } from "@/features/auth/schemas";
import { navItemsFor } from "@/lib/permissions";

import { cx } from "../ui/cx";
import { ThemeSwitch } from "./ThemeSwitch";
import { UserMenu } from "./UserMenu";

export function TopNav({ me }: { me: Me }) {
  const pathname = usePathname();
  return (
    <header className="flex items-center gap-7 border-b border-line bg-surface px-6 py-3.5">
      <Link href="/" className="flex items-center gap-2.5">
        <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-primary text-sm font-bold text-on-primary">
          ◆
        </span>
        <span className="text-[15px] font-bold text-ink">
          OpenFraud Investigator
        </span>
      </Link>
      <nav aria-label="Main" className="flex gap-5">
        {navItemsFor(me.role).map((item) => {
          const active =
            pathname === item.href || pathname.startsWith(`${item.href}/`);
          return (
            <Link
              key={item.href}
              href={item.href}
              aria-current={active ? "page" : undefined}
              className={cx(
                "text-sm",
                active
                  ? "font-semibold text-primary"
                  : "font-medium text-muted hover:text-ink",
              )}
            >
              {item.label}
            </Link>
          );
        })}
      </nav>
      <div className="ml-auto flex items-center gap-4">
        <ThemeSwitch />
        <UserMenu me={me} />
      </div>
    </header>
  );
}
