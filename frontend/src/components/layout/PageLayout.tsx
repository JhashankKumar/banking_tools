import type { ReactNode } from "react";

import { PageHeader } from "./PageHeader";

/** Standard page frame: spacing, the page heading, and an optional header action. */
export function PageLayout({
  title,
  subtitle,
  action,
  children,
}: {
  title: string;
  subtitle: string;
  action?: ReactNode;
  children: ReactNode;
}) {
  return (
    <div className="flex flex-col gap-5 px-8 pt-7 pb-9">
      <PageHeader title={title} subtitle={subtitle} action={action} />
      {children}
    </div>
  );
}
