import { afterEach, describe, expect, test, vi } from "vitest";

import { COPILOT_TIMEOUT_MS, REQUEST_TIMEOUT_MS } from "@/lib/config";
import { jsonResponse, stubFetch } from "@/test/http";

import { askQuestion, fetchChats } from "./api";

describe("copilot request timeouts", () => {
  afterEach(() => vi.restoreAllMocks());

  // A live run may take the API's 90 s deadline plus one 30 s model call.
  test("asking waits for a whole copilot run", async () => {
    const timeout = vi.spyOn(AbortSignal, "timeout");
    stubFetch(jsonResponse({}, 200));

    await askQuestion("FR-10482", { chatId: null, question: "Why?" }).catch(
      () => undefined,
    );

    expect(timeout).toHaveBeenCalledWith(COPILOT_TIMEOUT_MS);
    expect(COPILOT_TIMEOUT_MS).toBeGreaterThanOrEqual(120_000);
  });

  test("other requests keep the short timeout", async () => {
    const timeout = vi.spyOn(AbortSignal, "timeout");
    stubFetch(jsonResponse({}, 200));

    await fetchChats("FR-10482").catch(() => undefined);

    expect(timeout).toHaveBeenCalledWith(REQUEST_TIMEOUT_MS);
  });
});
