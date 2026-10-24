import { expect, test } from "vitest";

import { ALERT_JSON } from "@/test/fixtures";

import { alertSchema } from "./schemas";

test("alert schema transforms snake_case and keeps money/metrics as strings", () => {
  const alert = alertSchema.parse(ALERT_JSON);

  expect(alert).toMatchObject({
    id: "AL-ROT-TX-1002",
    triggerTransactionId: "TX-1002",
    caseId: "FR-10482",
    triggeredAt: "2026-09-15T04:37:42Z",
    evidenceId: "EV-10482-AL-ROT-TX-1002",
    entity: { type: "beneficiary", id: "BEN-B" },
  });
  expect(alert.metrics.incoming_amount).toBe("48500.00");
  expect(typeof alert.metrics.elapsed_seconds).toBe("string");
});

test("alert schema rejects a non-UTC timestamp", () => {
  expect(() =>
    alertSchema.parse({
      ...ALERT_JSON,
      triggered_at: "2026-09-15T10:07:42+05:30",
    }),
  ).toThrow();
});
