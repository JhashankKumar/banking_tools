import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { screen } from "@testing-library/react";
import { describe, expect, test } from "vitest";

import { renderWithClient } from "@/test/render";

import {
  KnownLimitations,
  LIMITATION_HEADINGS,
  LIMITATIONS_PATH,
} from "./KnownLimitations";

describe("KnownLimitations", () => {
  test("lists the same headings as the limitations document", () => {
    const doc = readFileSync(
      resolve(__dirname, "../../../../..", LIMITATIONS_PATH),
      "utf8",
    );
    const headings = [...doc.matchAll(/^## (.+)$/gm)].map((m) => m[1]);

    expect(LIMITATION_HEADINGS).toEqual(headings);
  });

  test("shows each heading and the document path", () => {
    renderWithClient(<KnownLimitations />);

    for (const h of LIMITATION_HEADINGS)
      expect(screen.getByText(h)).toBeVisible();
    expect(screen.getByText(LIMITATIONS_PATH)).toBeVisible();
  });
});
