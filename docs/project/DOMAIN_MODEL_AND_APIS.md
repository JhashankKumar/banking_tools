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

## Initial API endpoints
- `GET /api/v1/health` (liveness) and `GET /api/v1/health/ready` (database reachable)
- `POST /api/v1/auth/token` (OAuth2 password form → bearer token), `GET /api/v1/auth/me`
- `GET /api/v1/users`, `POST /api/v1/users`, `PATCH /api/v1/users/{user_id}` (Supervisor only)
- `GET /api/v1/dashboard/summary`
- `GET /api/v1/alerts?case_id=&rule_id=` and `GET /api/v1/alerts/{alert_id}` (alert IDs: `AL-<rule code>-<trigger transaction>`)
- `GET /api/v1/rules` (detection rule catalog)
- `GET /api/v1/cases/{case_id}`
- `GET /api/v1/cases/{case_id}/transactions`
- `GET /api/v1/cases/{case_id}/money-paths?max_hops=3&window_hours=24`
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
