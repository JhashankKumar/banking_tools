/** API-shaped JSON (snake_case, envelopes) matching the seeded FR-10482 data. */

export const ALERT_JSON = {
  id: "AL-ROT-TX-1002",
  rule: {
    id: "RAPID_ONWARD_TRANSFER",
    version: "1",
    title: "Rapid onward transfer",
  },
  entity: { type: "beneficiary", id: "BEN-B" },
  trigger_transaction_id: "TX-1002",
  transaction_ids: ["TX-1001", "TX-1002"],
  case_id: "FR-10482",
  triggered_at: "2026-09-15T04:37:42Z",
  explanation:
    "BEN-B received INR 48500.00 in TX-1001 and sent INR 45000.00 in TX-1002 5 minutes 28 seconds later. Signal for analyst review; not a finding of fraud.",
  metrics: {
    elapsed_seconds: "328",
    incoming_transaction_id: "TX-1001",
    incoming_amount: "48500.00",
    outgoing_transaction_id: "TX-1002",
    outgoing_amount: "45000.00",
    currency: "INR",
    window_seconds: "1800",
    min_onward_ratio: "0.50",
  },
  evidence_id: "EV-10482-AL-ROT-TX-1002",
  is_synthetic: true,
};

export const CASE_SUMMARY_JSON = {
  id: "FR-10482",
  title:
    "Rapid onward transfer — potential connected-funds pattern requiring review",
  status: "open",
  opened_at: "2026-09-15T05:00:00Z",
  alert_count: 1,
  transaction_count: 2,
  is_synthetic: true,
};

export const CASE_JSON = {
  id: "FR-10482",
  title: CASE_SUMMARY_JSON.title,
  status: "open",
  opened_at: "2026-09-15T05:00:00Z",
  alert_ids: ["AL-ROT-TX-1002"],
  transaction_count: 2,
  is_synthetic: true,
};

export const TRANSACTIONS_JSON = [
  {
    id: "TX-1001",
    source: { type: "account", id: "ACC-001" },
    destination: { type: "beneficiary", id: "BEN-B" },
    amount: "48500.00",
    currency: "INR",
    occurred_at: "2026-09-15T04:32:14Z",
    status: "settled",
    source_status: "SUCCESS",
    rail: "IMPS",
    reference: "SYN-REF-1001",
    description: null,
    reversal_of_transaction_id: null,
    evidence_id: "EV-10482-TX-1001",
  },
  {
    id: "TX-1002",
    source: { type: "beneficiary", id: "BEN-B" },
    destination: { type: "account", id: "ACC-C" },
    amount: "45000.00",
    currency: "INR",
    occurred_at: "2026-09-15T04:37:42Z",
    status: "settled",
    source_status: "SUCCESS",
    rail: "IMPS",
    reference: "SYN-REF-1002",
    description: null,
    reversal_of_transaction_id: null,
    evidence_id: "EV-10482-TX-1002",
  },
];

export const RULES_JSON = [
  {
    id: "RAPID_ONWARD_TRANSFER",
    version: "1",
    code: "ROT",
    title: "Rapid onward transfer",
    description:
      "An account or beneficiary receives a completed transfer and sends a separate completed transfer onward…",
    required_fields: [
      "source",
      "destination",
      "amount",
      "currency",
      "occurred_at",
      "status",
    ],
    false_positive_caveats: [
      "Salary, payroll, or business accounts that routinely pass funds through.",
      "Payment aggregators and merchants settling onward to their own accounts.",
    ],
    parameters: {
      window_seconds: "1800",
      min_onward_ratio: "0.50",
      min_incoming_amount: "INR:10000.00",
    },
  },
];

const edge = (tx: (typeof TRANSACTIONS_JSON)[number]) => ({
  transaction_id: tx.id,
  kind: "transfer",
  source: tx.source,
  destination: tx.destination,
  amount: tx.amount,
  currency: tx.currency,
  occurred_at: tx.occurred_at,
  status: tx.status,
  is_final: true,
  reversed_by: [],
  rail: tx.rail,
  reference: tx.reference,
  evidence_id: tx.evidence_id,
});

export const LIMITED_TO_DATASET =
  "Limited to records in this dataset. A path does not establish ownership, intent, available balance, or settlement finality.";

export const MONEY_PATHS_JSON = {
  case_id: "FR-10482",
  parameters: { max_hops: 3, window_hours: 24 },
  truncated: false,
  paths: [
    {
      hops: 2,
      is_cycle: false,
      has_non_final_edges: false,
      contains_reversal: false,
      returned_by_reversal: false,
      currencies: ["INR"],
      started_at: "2026-09-15T04:32:14Z",
      ended_at: "2026-09-15T04:37:42Z",
      elapsed_seconds: 328,
      limitations: [LIMITED_TO_DATASET],
      edges: TRANSACTIONS_JSON.map((tx, i) => ({ hop: i + 1, ...edge(tx) })),
    },
  ],
};

export const GRAPH_JSON = {
  case_id: "FR-10482",
  parameters: { window_hours: 24 },
  window: { start: "2026-09-14T04:32:14Z", end: "2026-09-16T04:37:42Z" },
  truncated: false,
  nodes: [
    {
      id: "ACC-001",
      type: "account",
      label: "Synthetic Customer One",
      status: "active",
      is_case_party: true,
      alert_ids: [],
    },
    {
      id: "ACC-C",
      type: "account",
      label: "ACC-C",
      status: "active",
      is_case_party: true,
      alert_ids: [],
    },
    {
      id: "BEN-B",
      type: "beneficiary",
      label: "Synthetic Beneficiary B",
      status: null,
      is_case_party: true,
      alert_ids: ["AL-ROT-TX-1002"],
    },
  ],
  edges: TRANSACTIONS_JSON.map((tx) => ({ ...edge(tx), in_case: true })),
};

export const page = <T>(data: T[], limit = 50) => ({
  data,
  page: { total: data.length, limit, offset: 0 },
});

/** fetch stub routing by path prefix; unmatched paths return 404 envelopes. */
export function routeFetch(routes: Record<string, () => Response>) {
  return (input: string | URL | Request) => {
    const url =
      typeof input === "string"
        ? input
        : input instanceof URL
          ? input.toString()
          : input.url;
    const path = url.replace(/^https?:\/\/[^/]+/, "");
    const key = Object.keys(routes)
      .sort((a, b) => b.length - a.length)
      .find((prefix) => path.startsWith(prefix));
    if (key) return Promise.resolve(routes[key]());
    return Promise.resolve(
      new Response(
        JSON.stringify({
          error: {
            code: "NOT_FOUND",
            message: "Not found",
            details: [],
            request_id: null,
          },
        }),
        {
          status: 404,
          headers: { "Content-Type": "application/json" },
        },
      ),
    );
  };
}
