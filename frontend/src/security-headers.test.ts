import { describe, expect, test } from "vitest";

import nextConfig from "../next.config";

describe("security headers", () => {
  test("every route forbids framing and MIME sniffing", async () => {
    const rules = (await nextConfig.headers?.()) ?? [];
    const all = rules.find((r) => r.source === "/:path*");
    const headers = Object.fromEntries(
      (all?.headers ?? []).map((h) => [h.key, h.value]),
    );

    expect(headers["Content-Security-Policy"]).toBe("frame-ancestors 'none'");
    expect(headers["X-Frame-Options"]).toBe("DENY");
    expect(headers["X-Content-Type-Options"]).toBe("nosniff");
    expect(headers["Referrer-Policy"]).toBe("same-origin");
  });
});
