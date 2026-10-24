import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterEach, vi } from "vitest";

import { resetNavigation } from "./next-navigation";

// Vitest runs without globals, so Testing Library's automatic cleanup is registered here,
// together with the resets every test needs (stubbed fetch/env, router mock, theme).
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  vi.unstubAllEnvs();
  resetNavigation();
  localStorage.clear();
  document.documentElement.dataset.theme = "light";
});
