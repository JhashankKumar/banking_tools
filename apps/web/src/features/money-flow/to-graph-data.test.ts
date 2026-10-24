import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, test } from "vitest";

import { GRAPH_JSON, MONEY_PATHS_JSON } from "@/test/fixtures";

import { PALETTE, reagraphTheme } from "./graph-theme";
import { caseGraphSchema, moneyPathsSchema } from "./schemas";
import { toGraphData } from "./to-graph-data";

const graph = caseGraphSchema.parse(GRAPH_JSON);
const [path] = moneyPathsSchema.parse(MONEY_PATHS_JSON).paths;
const all = { nodes: "all", edges: "all", theme: "light" } as const;
const light = PALETTE.light;

describe("toGraphData", () => {
  test("FR-10482 path edges are active and teal", () => {
    const data = toGraphData(graph, path, all);

    expect(data.actives.sort()).toEqual([
      "ACC-001",
      "ACC-C",
      "BEN-B",
      "TX-1001",
      "TX-1002",
    ]);
    expect(data.edges.find((e) => e.id === "TX-1001")?.fill).toBe(
      light.selected,
    );
    expect(data.nodes.find((n) => n.id === "BEN-B")?.fill).toBe(light.selected);
  });

  test("without a selected path, case parties are primary and nothing is active", () => {
    const data = toGraphData(graph, null, all);

    expect(data.actives).toEqual([]);
    expect(data.nodes.find((n) => n.id === "ACC-001")?.fill).toBe(
      light.primary,
    );
    expect(data.edges.find((e) => e.id === "TX-1001")?.fill).toBe(
      light.counterparty,
    );
  });

  test("beneficiary nodes use the user icon and alert nodes are flagged", () => {
    const data = toGraphData(graph, path, all);
    const ben = data.nodes.find((n) => n.id === "BEN-B");
    const acc = data.nodes.find((n) => n.id === "ACC-001");

    expect(ben?.icon).toContain("data:image/svg+xml");
    expect(ben?.icon).not.toBe(acc?.icon);
    expect(ben?.label).toBe("BEN-B ⚑");
    expect(ben?.data?.alert).toBe(true);
    expect(acc?.subLabel).toBe("Synthetic Customer One");
  });

  test("case-parties filter drops counterparties and their edges", () => {
    const withCounterparty = caseGraphSchema.parse({
      ...GRAPH_JSON,
      nodes: [
        ...GRAPH_JSON.nodes,
        {
          id: "ACC-OUT",
          type: "account",
          label: "ACC-OUT",
          status: "active",
          is_case_party: false,
          alert_ids: [],
        },
      ],
      edges: [
        ...GRAPH_JSON.edges,
        {
          ...GRAPH_JSON.edges[1],
          transaction_id: "TX-OUT",
          source: { type: "account", id: "ACC-C" },
          destination: { type: "account", id: "ACC-OUT" },
          in_case: false,
        },
      ],
    });

    const data = toGraphData(withCounterparty, path, { ...all, nodes: "case" });

    expect(data.nodes.map((n) => n.id)).not.toContain("ACC-OUT");
    expect(data.edges.map((e) => e.id)).not.toContain("TX-OUT");
  });

  test("money-path filter keeps only path edges and their nodes", () => {
    const extra = caseGraphSchema.parse({
      ...GRAPH_JSON,
      nodes: [
        ...GRAPH_JSON.nodes,
        {
          id: "ACC-X",
          type: "account",
          label: "ACC-X",
          status: "active",
          is_case_party: false,
          alert_ids: [],
        },
      ],
      edges: [
        ...GRAPH_JSON.edges,
        {
          ...GRAPH_JSON.edges[0],
          transaction_id: "TX-X",
          destination: { type: "account", id: "ACC-X" },
          in_case: false,
        },
      ],
    });

    const data = toGraphData(extra, path, { ...all, edges: "path" });

    expect(data.edges.map((e) => e.id).sort()).toEqual(["TX-1001", "TX-1002"]);
    expect(data.nodes.map((n) => n.id)).not.toContain("ACC-X");
  });

  test("pending edge is dashed and reversal edge is violet not dashed", () => {
    const g = caseGraphSchema.parse({
      ...GRAPH_JSON,
      edges: [
        { ...GRAPH_JSON.edges[0], status: "pending", is_final: false },
        {
          ...GRAPH_JSON.edges[1],
          kind: "reversal",
          status: "reversed",
          is_final: false,
        },
      ],
    });

    const data = toGraphData(g, null, all);

    expect(data.edges.find((e) => e.id === "TX-1001")?.dashed).toBe(true);
    const reversal = data.edges.find((e) => e.id === "TX-1002");
    expect(reversal?.dashed).toBe(false);
    expect(reversal?.fill).toBe(light.reversal);
  });

  test("edge label uses Indian money format and IST time", () => {
    const data = toGraphData(graph, path, all);

    expect(data.edges.find((e) => e.id === "TX-1001")?.label).toBe(
      "₹48,500.00 · 10:02:14",
    );
    expect(data.edges.every((e) => e.interpolation === "curved")).toBe(true);
  });

  test("path edges beyond the neighbourhood are added with their parties", () => {
    const g = caseGraphSchema.parse({
      ...GRAPH_JSON,
      nodes: GRAPH_JSON.nodes.slice(0, 2),
      edges: GRAPH_JSON.edges.slice(0, 0),
    });

    const data = toGraphData(g, path, all);

    expect(data.edges.map((e) => e.id).sort()).toEqual(["TX-1001", "TX-1002"]);
    expect(data.nodes.map((n) => n.id).sort()).toEqual([
      "ACC-001",
      "ACC-C",
      "BEN-B",
    ]);
  });

  test("nodes are laid out left to right in time order, path on the centre line", () => {
    const data = toGraphData(graph, path, all);
    const pos = Object.fromEntries(
      data.nodes.map((n) => [
        n.id,
        n.data?.position as { x: number; y: number },
      ]),
    );

    expect(pos["ACC-001"].x).toBeLessThan(pos["BEN-B"].x);
    expect(pos["BEN-B"].x).toBeLessThan(pos["ACC-C"].x);
    expect([pos["ACC-001"].y, pos["BEN-B"].y, pos["ACC-C"].y]).toEqual([
      0, 0, 0,
    ]);
  });

  test("counterparties sit off the centre line", () => {
    const g = caseGraphSchema.parse({
      ...GRAPH_JSON,
      nodes: [
        ...GRAPH_JSON.nodes,
        {
          id: "ACC-OUT",
          type: "account",
          label: "ACC-OUT",
          status: "active",
          is_case_party: false,
          alert_ids: [],
        },
      ],
      edges: [
        ...GRAPH_JSON.edges,
        {
          ...GRAPH_JSON.edges[1],
          transaction_id: "TX-OUT",
          source: { type: "account", id: "ACC-C" },
          destination: { type: "account", id: "ACC-OUT" },
          occurred_at: "2026-09-15T06:00:00Z",
          in_case: false,
        },
      ],
    });

    const out = toGraphData(g, path, all).nodes.find((n) => n.id === "ACC-OUT");

    expect((out?.data?.position as { y: number }).y).not.toBe(0);
  });

  test("dark theme uses dark palette", () => {
    const data = toGraphData(graph, path, { ...all, theme: "dark" });

    expect(data.edges.find((e) => e.id === "TX-1001")?.fill).toBe(
      PALETTE.dark.selected,
    );
  });
});

test("graph palette matches the CSS theme tokens", () => {
  const css = readFileSync(
    resolve(process.cwd(), "src/app/globals.css"),
    "utf8",
  ).toLowerCase();
  for (const [theme, colors] of Object.entries(PALETTE)) {
    const block = css
      .split(
        theme === "dark"
          ? ':root[data-theme="dark"]'
          : ':root[data-theme="light"]',
      )[1]
      .split("}")[0];
    for (const [name, hex] of Object.entries(colors)) {
      expect(block, `${theme} ${name}`).toContain(
        `--${name}: ${hex.toLowerCase()};`,
      );
    }
  }
});

test.each(["light", "dark"] as const)(
  "%s reagraph label colours are concrete hex (three.js has no 'transparent')",
  (theme) => {
    const { node, edge } = reagraphTheme(theme);
    for (const label of [node.label, node.subLabel, edge.label]) {
      for (const value of [label?.color, label?.stroke, label?.activeColor])
        if (value !== undefined) expect(value).toMatch(/^#[0-9a-f]{6}$/);
    }
  },
);
