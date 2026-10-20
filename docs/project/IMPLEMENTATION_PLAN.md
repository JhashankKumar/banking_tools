# Incremental Implementation Plan

Build a vertical slice that works end-to-end before broadening the system.

## Milestone 0 — Repository and developer experience
- Create repository structure and documentation.
- Add license, contribution, code of conduct, security policy, environment example.
- Add format/lint/test commands and CI.
- Add Docker Compose for PostgreSQL and application services only when the initial app is ready.
Acceptance: a contributor can follow setup instructions and run the smallest checks.

## Milestone 1 — Synthetic domain and API
- Define schema and migrations.
- Generate deterministic synthetic accounts, transactions, alerts, and case FR-10482.
- Implement health, case detail, and transaction endpoints.
- Add database-backed users, login, role-based permission checks, Supervisor user management, and audit events (moved from Milestone 6; see ADR 0001 #15).
Acceptance: seeded data can be retrieved via API by an authorized role; unauthenticated and unauthorized requests are denied; no real customer data.

## Milestone 2 — Deterministic detection
- Define a documented rule contract.
- Add a few transparent rules with explanations and source IDs.
- Test positive and negative scenarios.
Acceptance: every alert indicates why it fired and references source records.

## Milestone 3 — Money-flow graph
- Build a directed graph from authorized transaction records.
- Implement bounded, time-windowed traversal.
- Return path edges with source IDs, amount, currency, timestamp, status.
Acceptance: FR-10482 path is deterministic and covered by tests.

## Milestone 4 — UI vertical slice
- Dashboard/alert list, case view, graph, evidence panel.
- Typed API client and clear loading/empty/error states.
Acceptance: a user can open FR-10482 and inspect the two-hop path.

## Milestone 5 — AI copilot
- Add model provider interface and OpenRouter adapter (open-weight models only).
- Add bounded tool registry and investigation endpoint.
- Add evidence-linked response schema and citations validation.
Acceptance: model explains the deterministic path without changing its facts; fake provider tests run without an OpenRouter key or network access.

## Milestone 6 — Security and adversarial tests
- Test prompt injection, unauthorized access, invalid tools, output grounding, audit logging.
Acceptance: all defined negative tests pass; limitations documented.

## Milestone 7 — Benchmark and open-source polish
- Add scenario families and reproducible evaluation.
- Publish actual measured results and caveats.
- Improve README screenshots/demo, issue templates, contribution guide, first issues.
Acceptance: a new contributor can reproduce the demo and evaluation from scratch.

## Work protocol for a coding agent
At the start of each milestone:
1. Inspect current files and git status.
2. Summarize current architecture and gaps.
3. Propose a small plan with files to create/change.
4. Implement only the current milestone.
5. Run tests, lint, type checks, and build relevant to the changes.
6. Report exact commands and results honestly.
7. List assumptions, known issues, and next milestone.
Do not silently skip failed checks or claim a command passed if it was not run.
