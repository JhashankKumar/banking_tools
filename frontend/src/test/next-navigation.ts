import { vi } from "vitest";

/**
 * Shared stand-in for next/navigation. Use in a test file with
 * `vi.mock("next/navigation", () => import("@/test/next-navigation"));`
 * then assert on `router.push` / `router.replace`, or set `navigation.pathname` / `.search`.
 * setup.ts resets it after every test.
 */
export const router = {
  push: vi.fn(),
  replace: vi.fn(),
  back: vi.fn(),
  refresh: vi.fn(),
  prefetch: vi.fn(),
};
export const navigation = { pathname: "/", search: "" };

export const useRouter = () => router;
export const usePathname = () => navigation.pathname;
export const useSearchParams = () => new URLSearchParams(navigation.search);

export function resetNavigation() {
  Object.values(router).forEach((fn) => fn.mockReset());
  navigation.pathname = "/";
  navigation.search = "";
}
