import { describe, expect, test } from "vitest";

import {
  formatDateTime,
  formatElapsed,
  formatMoney,
  formatTime,
} from "./format";

describe("format", () => {
  test("formats INR in the Indian style", () => {
    expect(formatMoney("48500.00", "INR")).toBe("₹48,500.00");
    expect(formatMoney("950000.00", "INR")).toBe("₹9,50,000.00");
  });

  test("other currencies show their code, never an ambiguous symbol", () => {
    expect(formatMoney("1000.00", "USD")).toBe("USD\u00a01,000.00");
  });

  test("does not throw for the no-currency code", () => {
    expect(() => formatMoney("1200.00", "XXX")).not.toThrow();
  });

  test("shows times in IST", () => {
    expect(formatDateTime("2026-09-15T04:32:14Z")).toBe(
      "15 Sep 2026, 10:02:14 IST",
    );
    expect(formatTime("2026-09-15T04:32:14Z")).toBe("10:02:14");
  });

  test("formats elapsed seconds", () => {
    expect(formatElapsed(328)).toBe("5 m 28 s");
    expect(formatElapsed(45)).toBe("45 s");
    expect(formatElapsed(1800)).toBe("30 m");
  });
});
