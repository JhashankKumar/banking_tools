# Domain Model, API Contracts, and Money-Path Semantics

## Core entities
- Customer: synthetic identity associated with one or more accounts.
- Account: a synthetic account identifier and status.
- Beneficiary: a payment destination that may or may not be represented as an account.
- Transaction: directed transfer record with amount, currency, timestamp, status, source and destination.
- Alert: a detection event tied to a transaction, account, or rule.
- Case: an investigation workspace around one or more alerts.
- Evidence: a reference to a source record or deterministic finding.
- InvestigationRun: a single AI-assisted investigation attempt and its metadata.
- AuditEvent: actor, action, resource, time, outcome, and request/run correlation ID.

## Transaction fields
At minimum:
- `transaction_id`
- `source_entity_id`
- `destination_entity_id`
- `amount` as decimal
- `currency`
- `occurred_at` in UTC
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
- Exclude or separately label statuses that do not represent completed transfers.
- Return path edges with transaction IDs, amounts, currencies, timestamps, and statuses.
- If currencies differ, do not sum amounts without a documented exchange-rate source and timestamp.
- A path does not prove beneficial ownership, intent, or that money remained available.
- Arithmetic difference between transfers is not a current balance.
- Use deterministic traversal; the LLM may explain results but may not fabricate or alter them.

## Initial API endpoints
- `GET /api/v1/health`
- `GET /api/v1/dashboard/summary`
- `GET /api/v1/alerts`
- `GET /api/v1/alerts/{alert_id}`
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
