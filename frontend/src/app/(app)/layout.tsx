import { AppShell } from "@/components/layout/AppShell";

/**
 * Signed-in pages are not instant: AppShell renders them only after the session (`/me`) loads
 * in the browser, and the pages fetch their own data client-side. Opting out stops Next.js from
 * validating (and reporting as "dropped") pages it cannot render on the server by design.
 */
export const instant = false;

export default function AppLayout({ children }: LayoutProps<"/">) {
  return <AppShell>{children}</AppShell>;
}
