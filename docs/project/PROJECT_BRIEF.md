# Project Brief — OpenFraud Investigator

## Product name
OpenFraud Investigator

## Repository
`openfraud-investigator`

## Short description
An open-source AI copilot for fraud investigation, transaction graph analysis, and evidence-grounded financial-crime workflows.

## Tagline
Trace the money. Connect the evidence. Investigate with AI.

## Problem hypothesis
A fraud analyst receives an alert and must assemble transaction history, related accounts, beneficiary activity, previous alerts, and supporting evidence before deciding what to review or escalate. Cross-system evidence assembly and case-narrative preparation may be labor-intensive. This is a workflow hypothesis to validate, not a claim that banks lack fraud systems.

## Product goal
Build a reproducible, self-hostable demonstration that helps an investigator:
1. Review a synthetic fraud alert.
2. Explore transactions related to an account or beneficiary.
3. Trace money movement across multiple hops.
4. See which deterministic rules triggered and why.
5. Ask an AI copilot questions over retrieved, authorized evidence.
6. Receive source-linked explanations with uncertainty and missing evidence clearly stated.
7. Review an audit trail of investigation actions.

## Primary demo
Synthetic case `FR-10482`:
- `ACC-001` sends ₹48,500 to `BEN-B` at illustrative time `10:02:14`, transaction `TX-1001`.
- `BEN-B` sends ₹45,000 to `ACC-C` at illustrative time `10:07:42`, transaction `TX-1002`.
- The second transfer is 5 minutes 28 seconds after the first.
- Arithmetic difference: ₹3,500. This is not proof that the amount remains in the beneficiary's balance; other transactions, fees, reversals, and balance changes may exist.
- The times and transactions are illustrative synthetic records, not real financial activity.

The application should show the path:
`ACC-001 --TX-1001 / ₹48,500--> BEN-B --TX-1002 / ₹45,000--> ACC-C`

## Facts versus conclusions
A path is evidence of recorded transfers in the supplied dataset. It does not by itself prove fraud, intent, account ownership, authorization, final settlement, or the current balance. The app must use neutral wording such as “potential connected-funds pattern requiring review,” not “confirmed fraud,” unless a separate, authorized adjudication record explicitly says so.

## Intended users
- Fraud analyst: reviews alerts, explores evidence, drafts investigation notes.
- Supervisor: reviews cases and investigator actions.
- Auditor: views permitted audit records.
These are demo roles. Authorization must be enforced server-side.

## Scope for the first release
- Synthetic data generator and documented scenarios.
- PostgreSQL-backed accounts, transactions, alerts, cases, evidence, investigation runs, and audit logs.
- Deterministic rule engine with explanations.
- Case transaction graph (one case's neighbourhood within a time window) and bounded, time-respecting path traversal.
- FastAPI REST API.
- Next.js/TypeScript investigator UI.
- Open-weight LLMs called through OpenRouter, behind a provider interface, with per-user and per-IP rate limits.
- Allowlisted AI tools and evidence-grounded answers.
- Authentication/authorization boundary, audit logging, adversarial tests.
- Docker Compose, CI checks, clear setup instructions, license, contribution and security docs.

## Explicit non-goals
- No real customer data or production bank integrations.
- No real payment execution, account freezing, blocking, or irreversible action.
- No autonomous final fraud decision.
- No direct LLM access to arbitrary SQL or unrestricted database credentials.
- No claims of production readiness or real-world fraud accuracy from synthetic tests.
- No microservices, Kubernetes, Kafka, Redis, vector database, or dedicated graph database unless later justified by measured requirements.

## Open-source / Hacktoberfest goals
- Public GitHub repository.
- Use an OSI-approved code license such as Apache-2.0, subject to dependency/license review.
- Clear `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, and good-first-issue tasks.
- Publish a reproducible synthetic evaluation benchmark and actual measured results.
- Check the exact model artifact license separately; open-weight does not automatically mean OSI-approved open source.
