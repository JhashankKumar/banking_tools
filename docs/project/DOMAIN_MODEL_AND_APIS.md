# Domain Model, API Contracts, and Money-Path Semantics

## Core entities

Accounts and beneficiaries are separate tables. A graph node references exactly one of them via a typed reference (`account` | `beneficiary`).

- Customer: synthetic identity associated with one or more accounts.
- Account: a synthetic account identifier and status.
- Beneficiary: a payment destination that may or may not be represented as an account.
- Transaction: directed transfer record with amount, currency, timestamp, status, source and destination.
- Alert: a detection event tied to a transaction, account, or rule.
- Case: an investigation workspace around one or more alerts.
- Evidence: its own table. Each row has a stable ID (`EV-…`), the case it belongs to, a type (`transaction`, `alert`, `rule_result`, `derived_calculation`), a pointer to the source record (table + record ID), and an evidence label (`observed_fact`, `derived_fact`, `indicator`, `hypothesis`, `unknown`). AI citations use `EV-…` IDs only.
- InvestigationRun: a single AI-assisted investigation attempt and its metadata.
- AuditEvent: actor, action, resource, time, outcome, and request/run correlation ID.

## Transaction fields

At minimum:

- `transaction_id`
- `source_entity_id`
- `destination_entity_id`
- `amount` as decimal
- `currency`
- `occurred_at` stored in UTC; displayed in IST (Asia/Kolkata) at the UI boundary
- `status`
- `reference` or trace ID
- optional `reversal_of_transaction_id`
- synthetic data provenance/scenario ID where appropriate

Do not assume that a transfer being present means it settled successfully. Model statuses explicitly. Reversals and duplicate records must be represented or called out.

## Money-path semantics

- Graph is directed: source entity → destination entity.
- A hop is one recorded transaction edge.
- Start from a case-relevant account/transaction.
- Apply a configured time window and maximum hop count.
- Include pending and reversed transactions in paths; every edge carries its status, and the path response flags whether it contains any non-final edge.
- Return path edges with transaction IDs, amounts, currencies, timestamps, and statuses.
- If currencies differ, do not sum amounts without a documented exchange-rate source and timestamp.
- A path does not prove beneficial ownership, intent, or that money remained available.
- Arithmetic difference between transfers is not a current balance.
- Use deterministic traversal; the LLM may explain results but may not fabricate or alter them.

### As implemented (Milestone 3, `app/modules/graph/`)

- **Starts:** every transaction linked to the case.
- **Time-respecting:** each next hop occurs at or after the previous one (equal timestamps ordered by transaction ID) and within `window_hours` of the path's first hop.
- **No revisits:** a party appears once per path, except that returning to the first party closes a **cycle** and stops the path. No transaction appears twice.
- **Maximal paths only:** a path that is a contiguous part of a longer returned path is dropped (FR-10482 returns one 2-hop path, not also the 1-hop tail).
- **Caps:** `max_hops` 1–5 (default 3), `window_hours` 1–168 (default 24), 50 paths, 10,000 expansions. Any cap hit sets `truncated: true`; the hop limit adds a limitation to that path but does not stop the search for other paths. The expansion budget is split equally across the case's start transactions, and the 50-path cap is filled round-robin by start, so one busy start cannot hide the others. At most 20,000 transactions are loaded per request (only each start's own window); hitting the work limit or that row cap adds the limitation "The search reached its work limit; some paths may be missing or incomplete."
- **Edges:** `kind` is `reversal` when the record reverses another, else `transfer`; `is_final` is false unless the status is `posted`/`settled` and no reversal record points at it; `reversed_by` lists reversal record IDs; `evidence_id` is the case's evidence for that transaction or `null`.
- **Limitations** are fixed sentences chosen by code (`app/modules/graph/paths.py`): dataset-only (always), non-final edges, reversal present, hop limit reached, mixed currencies, cycle, returned by reversal, work limit reached. A path that ends with a reversal record back to its first party is flagged `returned_by_reversal` and is **not** a cycle.
- **No arithmetic** across edges in responses (no sums, differences, or balances).

### Case graph (`GET /api/v1/cases/{case_id}/graph?window_hours=24`)

The MVP graph view (ADR 0001 #18): case parties (every account/beneficiary on the case's transactions) plus every transaction, any status, that touches a case party between the earliest case transaction − window and the latest + window. One level of counterparties; onward tracing is the money-paths endpoint. At most 200 edges; case transactions are always kept (and are not counted against the cap), and the remaining room goes to the neighbour transactions closest in time to a case transaction, so a busy counterparty's distant history cannot crowd out activity around the case. `truncated` when cut. Nodes carry `label`, account `status`, `is_case_party`, and `alert_ids`; edges use the same fields as money-path edges plus `in_case`.

## Initial API endpoints

- `GET /api/v1/health` (liveness) and `GET /api/v1/health/ready` (database reachable)
- `POST /api/v1/auth/token` (OAuth2 password form → bearer token), `GET /api/v1/auth/me`
- `GET /api/v1/users`, `POST /api/v1/users`, `PATCH /api/v1/users/{user_id}` (Supervisor only)
- `GET /api/v1/dashboard/summary`
- `GET /api/v1/alerts?case_id=&rule_id=` and `GET /api/v1/alerts/{alert_id}` (alert IDs: `AL-<rule code>-<trigger transaction>`)
- `GET /api/v1/rules` (detection rule catalog)
- `GET /api/v1/cases` (paginated case list with `alert_count`, `transaction_count`)
- `GET /api/v1/cases/{case_id}`
- `GET /api/v1/cases/{case_id}/transactions`
- `GET /api/v1/cases/{case_id}/money-paths?max_hops=3&window_hours=24`
- `GET /api/v1/cases/{case_id}/graph?window_hours=24`
- `GET /api/v1/cases/{case_id}/evidence`
- `POST /api/v1/cases/{case_id}/investigations`
- `GET /api/v1/investigations/{run_id}`
- `GET /api/v1/audit-logs`

Use pagination for list endpoints. Enforce sensible limits for `max_hops`, window, result count, and payload size. Never trust IDs supplied by the client without checking authorization.

## Example AI response contract

Return structured fields similar to:

- `summary`: concise neutral summary.
- `findings`: list of claims, each with `evidence_ids`.
- `money_paths`: deterministic paths from the graph service.
- `limitations`: missing, ambiguous, or unverified information.
- `recommended_review_actions`: suggestions for human review, not actions taken.
- `investigation_run_id`: traceability.
- `model_metadata`: provider/model/version when available, without leaking secrets.

Every factual claim that depends on records must reference valid evidence IDs. If no evidence supports a claim, the system should say the information is unavailable or unverified.
