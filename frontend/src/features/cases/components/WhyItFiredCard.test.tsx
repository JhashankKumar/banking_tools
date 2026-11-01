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
});
