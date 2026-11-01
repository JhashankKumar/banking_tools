import { render, screen } from "@testing-library/react";
import { describe, expect, test } from "vitest";

import { alertSchema } from "@/features/alerts/schemas";
import { ALERT_JSON } from "@/test/fixtures";

import { WhyItFiredCard } from "./WhyItFiredCard";

const tile = (label: string) =>
  screen.getByText(label, { selector: "p" }).nextElementSibling?.textContent;

describe("WhyItFiredCard", () => {
  test("same-currency alert shows both amounts in that currency", () => {
    render(
      <WhyItFiredCard alert={alertSchema.parse(ALERT_JSON)} rule={undefined} />,
    );

    expect(tile("In")).toBe("₹48,500.00");
    expect(tile("Out")).toBe("₹45,000.00");
    expect(screen.queryByText("Rate")).toBeNull();
  });

  test("converted alert shows each amount in its own currency, the conversion and the rate", () => {
    const alert = alertSchema.parse({
      ...ALERT_JSON,
      id: "AL-ROT-TX-9302",
      metrics: {
        ...ALERT_JSON.metrics,
        incoming_amount: "85000.00",
        incoming_currency: "INR",
        outgoing_amount: "1000.00",
        outgoing_currency: "USD",
        currency: "INR",
        converted_transaction_id: "TX-9302",
        converted_amount: "83450.00",
        fx_rate: "83.45",
      },
    });

    render(<WhyItFiredCard alert={alert} rule={undefined} />);

    expect(tile("In")).toBe("₹85,000.00");
    expect(tile("Out")).toBe("USD\u00a01,000.00");
    expect(tile("Out in INR")).toBe("₹83,450.00");
    expect(tile("Rate")).toBe("83.45 (recorded)");
  });

  test("same-currency ROT alert keeps minutes for elapsed and window", () => {
    render(
      <WhyItFiredCard alert={alertSchema.parse(ALERT_JSON)} rule={undefined} />,
    );

    expect(tile("Elapsed")).toBe("5 m 28 s");
    expect(tile("Window")).toBe("30 m");
  });

  test("fan-out alert shows incoming, transfers, total sent on and share", () => {
    const alert = alertSchema.parse({
      ...ALERT_JSON,
      id: "AL-FOS-TX-9006",
      rule: { id: "FAN_OUT_SPLIT", version: "1", title: "Fan-out split" },
      metrics: {
        incoming_transaction_id: "TX-9001",
        incoming_amount: "200000.00",
        currency: "INR",
        outgoing_count: "5",
        outgoing_total: "195000.00",
        onward_share: "0.97",
        elapsed_seconds: "750",
        window_seconds: "1800",
        min_transfers: "3",
        min_onward_share: "0.80",
      },
    });

    render(<WhyItFiredCard alert={alert} rule={undefined} />);

    expect(tile("In")).toBe("₹2,00,000.00");
    expect(tile("Transfers")).toBe("5");
    expect(tile("Sent on")).toBe("₹1,95,000.00");
    expect(tile("Share")).toBe("97 %");
    expect(tile("Elapsed")).toBe("12 m 30 s");
    expect(screen.queryByText("Out", { selector: "p" })).toBeNull();
  });

  test("fan-in alert shows payers, collected total and the onward transfer", () => {
    const alert = alertSchema.parse({
      ...ALERT_JSON,
      id: "AL-FIC-TX-8906",
      rule: { id: "FAN_IN_COLLECT", version: "1", title: "Fan-in collect" },
      metrics: {
        payer_count: "5",
        incoming_count: "5",
        incoming_total: "71000.00",
        outgoing_transaction_id: "TX-8906",
        outgoing_amount: "68000.00",
        currency: "INR",
        onward_share: "0.95",
        elapsed_seconds: "1452",
        window_seconds: "1800",
      },
    });

    render(<WhyItFiredCard alert={alert} rule={undefined} />);

    expect(tile("Payers")).toBe("5");
    expect(tile("Collected")).toBe("₹71,000.00");
    expect(tile("Out")).toBe("₹68,000.00");
    expect(tile("Share")).toBe("95 %");
  });

  test("circular-flow alert shows hops, amounts and durations in hours", () => {
    const alert = alertSchema.parse({
      ...ALERT_JSON,
      id: "AL-CIR-TX-4003",
      rule: { id: "CIRCULAR_FLOW", version: "1", title: "Circular flow" },
      metrics: {
        hops: "3",
        start_transaction_id: "TX-4001",
        start_amount: "30000.00",
        returned_amount: "28000.00",
        currency: "INR",
        return_ratio: "0.93",
        elapsed_seconds: "18000",
        window_seconds: "86400",
      },
    });

    render(<WhyItFiredCard alert={alert} rule={undefined} />);

    expect(tile("Hops")).toBe("3");
    expect(tile("Sent")).toBe("₹30,000.00");
    expect(tile("Returned")).toBe("₹28,000.00");
    expect(tile("Share")).toBe("93 %");
    expect(tile("Elapsed")).toBe("5 h");
    expect(tile("Window")).toBe("24 h");
  });

  test.each([
    ["0.57", "57 %"],
    ["0.29", "29 %"],
    ["1.13", "113 %"],
  ])("share %s reads as %s, matching the explanation", (ratio, shown) => {
    const alert = alertSchema.parse({
      ...ALERT_JSON,
      rule: { id: "FAN_IN_COLLECT", version: "1", title: "Fan-in collect" },
      metrics: { currency: "INR", onward_share: ratio },
    });

    render(<WhyItFiredCard alert={alert} rule={undefined} />);

    expect(tile("Share")).toBe(shown);
  });
});
