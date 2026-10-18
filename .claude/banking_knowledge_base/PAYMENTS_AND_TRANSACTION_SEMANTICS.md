# Payments and Transaction Semantics

## 1. India-oriented payment rails (high-level)
- UPI: real-time retail payment system built around interoperable payment addresses and bank accounts; a UPI ID/VPA is an identifier, not proof of the legal identity of its user.
- IMPS: immediate payment service used for instant electronic transfers.
- NEFT: electronic funds transfer system with processing/settlement in batches at defined intervals; actual transaction status and posting depend on the bank and rail.
- RTGS: real-time gross settlement, typically used for high-value transfers under the applicable rules.
- Cards: authorization, clearing, settlement, reversals, refunds, chargebacks/disputes, and ledger postings can be distinct events.
- SWIFT: primarily a financial messaging network; a SWIFT message is not itself proof that final settlement occurred.
- ACH: a term used for automated clearing house payment systems in some jurisdictions, especially the United States; do not use it as a synonym for Indian payment rails.

This is a conceptual summary. Current product limits, operating hours, settlement rules, and participant procedures must be verified against the relevant official source and date before being encoded.

## 2. Transaction record fields
Recommended fields for the synthetic project:
- transaction ID
- source entity ID and destination entity ID
- amount and currency
- rail/payment method
- source-system status and normalized status
- initiated, posted, and settled timestamps when available
- source system and record ID
- end-to-end or network reference when available
- parent/related transaction ID for reversal, return, refund, or dispute
- ingestion timestamp
- scenario ID and synthetic-data marker

Do not assume all fields exist for every rail.

## 3. Transaction relationship types
A graph may include:
- transfer: source → destination
- reversal: event related to an earlier transaction
- refund/return: value returned under a defined process
- authorization: permission or hold event, not necessarily a completed transfer
- ownership/association: relationship between an entity and an account or identifier, requiring a source and confidence
Keep these edge types distinct. A reversal is not always equivalent to deleting the original transaction.

## 4. Traceability
Each edge shown in the graph must be backed by a transaction record. Provide:
- source record ID
- amount and currency
- relevant timestamp and its meaning
- status and source
- path hop number
- limitations or missing information
If the source data conflicts, show the conflict rather than silently choosing one value.

## 5. Money path example
Synthetic example:
- TX-1001: ACC-001 → BEN-B, INR 48,500, 10:02:14.
- TX-1002: BEN-B → ACC-C, INR 45,000, 10:07:42.
- Time difference: 5 minutes 28 seconds.
- Amount difference: INR 3,500.

Valid statement: “The supplied records show a transfer of INR 48,500 from ACC-001 to BEN-B, followed 5 minutes 28 seconds later by a transfer of INR 45,000 from BEN-B to ACC-C.”

Invalid statements without additional evidence:
- “BEN-B kept exactly INR 3,500.”
- “The full amount was laundered.”
- “ACC-C belongs to the same criminal.”
- “The transfer was settled and irreversible.”
- “Fraud is confirmed.”

## 6. Graph traversal constraints
- Use directed edges and deterministic traversal.
- Bound the maximum number of hops, time window, and number of results.
- Preserve transaction status and time semantics.
- Avoid cycles causing unbounded traversal.
- Expose whether a path uses pending, reversed, or otherwise non-final records.
- If graph data is incomplete, say the path is limited to records available in the dataset.
